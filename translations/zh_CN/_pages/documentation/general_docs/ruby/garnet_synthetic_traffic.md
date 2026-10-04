---
layout: documentation
title: "Garnet Synthetic Traffic"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/garnet_synthetic_traffic/
author: Jason Lowe-Power
---

# Garnet 合成流量（Garnet Synthetic Traffic）

Garnet Synthetic Traffic 提供了一个在受控输入下模拟 [Garnet 网络](/documentation/general_docs/ruby/garnet-2)的框架。这对于网络测试/调试，或使用合成流量进行纯网络模拟很有用。

**注意：garnet 合成流量注入器只能与 [Garnet_standalone](/documentation/general_docs/ruby/Garnet_standalone.md) 一致性协议配合使用。**

## 相关文件

* configs/example/garnet_synth_traffic.py：调用网络测试器的文件
* src/cpu/testers/garnet_synthetic_traffic：实现该测试器的文件。
  * GarnetSyntheticTraffic.py
  * GarnetSyntheticTraffic.hh
  * GarnetSyntheticTraffic.cc

## 如何运行

首先用 [Garnet_standalone](/documentation/general_docs/ruby/Garnet_standalone.md) 一致性协议构建 gem5。Garnet_standalone 协议与指令集架构无关，因此我们用 NULL 指令集架构构建它。

对于 gem5 <= 23.0：

```
scons build/NULL/gem5.debug PROTOCOL=Garnet_standalone
```

对于 gem5 >= 23.1

```
scons defconfig build/NULL build_opts/NULL
scons setconfig build/NULL RUBY_PROTOCOL_GARNET_STANDALONE=y
scons build/NULL/gem5.debug
```

示例命令：

```
./build/NULL/gem5.debug configs/example/garnet_synth_traffic.py  \
        --num-cpus=16 \
        --num-dirs=16 \
        --network=garnet \
        --topology=Mesh_XY \
        --mesh-rows=4  \
        --sim-cycles=1000 \
        --synthetic=uniform_random \
        --injectionrate=0.01
```

## 参数化选项

| **系统配置** |  **说明**  |
|------------|-----------|
| **--num-cpus** | cpu 数量。即网络中源（注入）节点的数量。 |
| **--num-dirs** | 目录数量。即网络中目的（弹出）节点的数量。 |
| **--network** | 网络模型：simple 或 garnet。运行合成流量请使用 garnet。 |
| **--topology** | 把 cpu 与 dir 连接到网络路由器/交换机的拓扑。关于不同拓扑的更多细节见（此处）[Interconnection_Network#Topology]。 |
| **--mesh-rows** | mesh 的行数。仅在 ''--topology'' 为 ''Mesh_*'' 或 ''MeshDirCorners_*'' 时有效。 |



| **网络配置** | **说明** |
|------------|-----------|
| **--router-latency** | garnet 路由器中默认的流水线级数。必须 >= 1。可在拓扑文件中按路由器逐个覆盖。 |
| **--link-latency** | 网络中每条链路的默认延迟。必须 >= 1。可在拓扑文件中按链路逐个覆盖。 |
| **--vcs-per-vnet** | 每个虚拟网络的 VC 数量。 |
| **--link-width-bits** | garnet 网络内所有链路的位宽。默认 = 128。 |



| **流量注入** | **说明** |
|------------|-----------|
| **--sim-cycles** | 模拟应当运行的总周期数。 |
| **--synthetic** | 要注入的合成流量类型。目前支持以下合成流量模式：'uniform_random'、'tornado'、'bit_complement'、'bit_reverse'、'bit_rotation'、'neighbor'、'shuffle' 和 'transpose'。 |
| **--injectionrate** | 流量注入速率，单位 packets/node/cycle。可以取 0 到 1 之间的任意小数值。小数点后的精度位数可由 ''--precision'' 控制，它在 ''garnet_synth_traffic.py'' 中默认为 3。 |
| **--single-sender-id** | 仅从该发送方注入。要从所有节点发送，设为 -1。 |
| **--single-dest-id** | 仅向该目的方发送。要按合成流量模式指定的所有目的方发送，设为 -1。 |
| **--num-packets-max** | 每个 cpu 节点要注入的最大数据包数。默认值为 -1（一直注入到 sim-cycles）。 |
| **--inj-vnet** | 仅在该 vnet（0、1 或 2）中注入。0 和 1 是 1-flit，2 是 5-flit。设为 -1 则在所有 vnet 中随机注入。 |


## Garnet 合成流量的实现
合成流量注入器实现在 GarnetSyntheticTraffic.cc 中。生成与发送一个数据包所涉及的步骤序列如下。

* 每个周期，每个 cpu 进行一次伯努利试验，概率等于 --injectionrate，以决定是否生成数据包。
* 如果 --num-packets-max 非负，每个 cpu 在生成 --num-packets-max 个数据包后停止生成新数据包。注入器在 --sim-cycles 之后终止。
* 如果 cpu 必须生成新数据包，它会根据合成流量类型（--synthetic）计算新数据包的目的地。
* 该目的地被嵌入数据包地址中块偏移之后的比特位。
* 生成的数据包被随机标记为 ReadReq、INST_FETCH 或 WriteReq，并发送到 Ruby Port（src/mem/ruby/system/RubyPort.hh/cc）。
* Ruby Port 把该数据包分别转换为 RubyRequestType:LD、RubyRequestType:IFETCH 和 RubyRequestType:ST，并把它发送给 Sequencer，后者再把它发送给 Garnet_standalone 缓存控制器。
* 缓存控制器从数据包地址中提取目的目录。
* 缓存控制器把 LD、IFETCH 和 ST 分别注入虚拟网络 0、1 和 2。
  * LD 和 IFETCH 作为控制数据包（8 字节）注入，而 ST 作为数据数据包（72 字节）注入。
* 该数据包穿越网络并到达目录。
* 目录控制器直接把它丢弃。

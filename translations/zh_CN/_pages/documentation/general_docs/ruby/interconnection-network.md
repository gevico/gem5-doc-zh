---
layout: documentation
title: "Interconnection network"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/interconnection-network/
author: Jason Lowe-Power
---

# 互连网络（Interconnection Network）

这里介绍 gem5 的 ruby 内存系统中互连网络模型的各个组件。

## 如何调用网络

**Simple 网络**：

```
./build/<ISA>/gem5.debug \
                      configs/example/ruby_random_test.py \
                      --num-cpus=16  \
                      --num-dirs=16  \
                      --network=simple
                      --topology=Mesh_XY  \
                      --mesh-rows=4
```

默认网络是 simple，默认拓扑是 crossbar。

**Garnet 网络**：

```
./build/<ISA>/gem5.debug \
                      configs/example/ruby_random_test.py  \
                      --num-cpus=16 \
                      --num-dirs=16  \
                      --network=garnet2.0 \
                      --topology=Mesh_XY \
                      --mesh-rows=4
```

## 拓扑 {#Topology}

各个控制器之间的连接通过 python
文件指定。所有外部链路（控制器与路由器之间）都是
双向的。所有内部链路（路由器之间）都是单向的
—— 这允许按方向为每条链路设置权重，以影响路由
决策。

- **相关文件**：
    - **src/mem/ruby/network/topologies/Crossbar.py**
    - **src/mem/ruby/network/topologies/CrossbarGarnet.py**
    - **src/mem/ruby/network/topologies/Mesh_XY.py**
    - **src/mem/ruby/network/topologies/Mesh_westfirst.py**
    - **src/mem/ruby/network/topologies/MeshDirCorners_XY.py**
    - **src/mem/ruby/network/topologies/Pt2Pt.py**
    - **src/mem/ruby/network/Network.py**
    - **src/mem/ruby/network/BasicLink.py**
    - **src/mem/ruby/network/BasicRouter.py**



- **拓扑说明**：
  - **Crossbar**：每个控制器（L1/L2/目录）都连接到
    一个简单的交换机。每个交换机都连接到一个中央交换机
    （建模 crossbar）。可以通过命令行
    用 **--topology=Crossbar** 调用。
  - **CrossbarGarnet**：每个控制器（L1/L2/目录）都
    通过一个 garnet 路由器（它在内部建模 crossbar 与分配器）连接到其他每个
    控制器。可以通过命令行用 **--topology=CrossbarGarnet** 调用。
  - **Mesh_\***：该拓扑要求目录数量
    等于 cpu 数量。路由器/交换机数量
    等于系统中的 cpu 数量。
    每个路由器/交换机连接到一个 L1、一个 L2（如果存在）
    以及一个目录。mesh 的行数**必须
    指定**，通过 **--mesh-rows**。该参数也支持
    创建非对称 mesh。
      - **Mesh_XY**：采用 XY 路由的 mesh。所有 x 方向链路
        权重为 1，而所有 y 方向链路
        权重为 2。这会强制所有消息先使用 X 链路，
        再使用 Y 链路。可以通过命令行
        用 **--topology=Mesh_XY** 调用
      - **Mesh_westfirst**：采用 west-first 路由的 mesh。所有
        西向链路权重为 1，其他所有链路权重为 2。这会强制所有
        消息先使用西向链路，再使用
        其他链路。可以通过命令行
        用 **--topology=Mesh_westfirst** 调用
  - **MeshDirCorners_XY**：该拓扑要求目录数量
    等于 4。路由器/交换机数量
    等于系统中的 cpu 数量。每个路由器/交换机
    连接到一个 L1、一个 L2（如果存在）。每个角落上的
    路由器/交换机连接到一个目录。可以通过命令行
    用 **--topology=MeshDirCorners_XY** 调用。mesh 的
    行数**必须指定**，通过
    **--mesh-rows**。使用 XY 路由算法。
  - **Pt2Pt**：每个控制器（L1/L2/目录）都
    通过直接链路连接到其他每个控制器。可以通过
    命令行调用
  - **Pt2Pt**：全对全点对点连接

![](http://pwp.gatech.edu/ece-synergy/wp-content/uploads/sites/332/2016/10/topologies.jpg)

**在每种拓扑中，每条链路和每个路由器都可以单独传入参数来覆盖默认值（在 BasicLink.py 和
BasicRouter.py 中）**：

  - **链路参数：**
      - **latency**：在链路内传输的延迟。
      - **weight**：与该链路关联的权重。该参数由
        路由表在决定路由时使用，详见后面的[路由](Interconnection_Network#Routing "wikilink")。
      - **bandwidth_factor**：仅由 simple 网络用于指定
        链路的字节宽度。它会转换为带宽
        乘数（simple/SimpleLink.cc），单条链路的
        带宽变为带宽乘数 x endpoint_bandwidth
        （在 SimpleNetwork.py 中指定）。在 garnet 中，带宽由
        GarnetNetwork.py 中的 ni_flit_size 指定）


  - **内部链路参数：**
      - **src_outport**：源路由器输出端口名称的字符串。
      - **dst_inport**：目的路由器输入端口的名称
        字符串。

路由器可以用这两个参数在 garnet2.0 中实现自定义路由
算法

  - **路由器参数：**
      - **latency**：每个路由器的延迟。仅由
        garnet2.0 支持。

## 路由 {#Routing}

**基于表的路由（默认）：** 基于拓扑，使用最短
路径图遍历来填充每个
路由器/交换机上的*路由表*。这在 src/mem/ruby/network/Topology.cc 中完成。默认路由算法基于表，并尝试
选择链路跨越数最少的路径。可以在拓扑文件中为链路赋予权重，以建模不同的路由算法。例如，
在 Mesh_XY.py 和 MeshDirCorners_XY.py 中，Y 方向链路被赋予
权重 2，而 X 方向链路被赋予权重 1，从而
产生 XY 遍历。在 Mesh_westfirst.py 中，西向链路被
赋予权重 1，其他所有链路被赋予权重 2。在 garnet2.0 中，
路由算法在权重相等的链路之间随机选择。
在 simple 网络中，它在权重相等的链路之间静态选择。

**自定义路由算法：** 在 garnet2.0 中，我们提供了额外
支持来实现自定义（包括自适应）路由算法（见
src/mem/ruby/network/garnet2.0/RoutingUnit.cc 中的 outportComputeXY()）。
链路的 src_outport 与 dst_inport 字段可用于为每条链路指定
自定义名称（例如 mesh 中的方向），这些名称可以在
garnet 内部用于实现任何路由算法。可以通过设置
--routing-algorithm=2 从命令行选择自定义路由
算法。见 configs/network/Network.py 和
src/mem/ruby/network/garnet2.0/GarnetNetwork.py

## 流控与路由器微架构

Ruby 支持两种网络模型：Simple 与 Garnet，它们分别在详细
建模与模拟速度之间取舍。

### Simple 网络

Ruby 中的默认网络模型是 simple 网络。

- **相关文件**：
    - **src/mem/ruby/network/Network.py**
    - **src/mem/ruby/network/simple**
    - **src/mem/ruby/network/simple/SimpleNetwork.py**

## 配置

Simple 网络使用 Network.py 中的通用网络参数：

- **number_of_virtual_networks**：虚拟网络的最大数量。
      实际活跃的虚拟网络数量
      由协议决定。
- **control_msg_size**：控制消息的字节大小。
      默认是 8。Network.cc 中的 **m_data_msg_size** 被设为
      块的字节大小 + control_msg_size。

其他参数在 simple/SimpleNetwork.py 中指定：

- **buffer_size**：每个交换机输入和
  输出端口缓冲区的大小。值为 0 表示无限缓冲。
- **endpoint_bandwidth**：网络端点的
  带宽，单位为千分之一字节。
- **adaptive_routing**：启用基于
  输出缓冲区占用情况的自适应路由。

## 交换机模型

Simple 网络建模逐跳的网络遍历，但省略了
交换机内部的详细建模。交换机在
simple/PerfectSwitch.cc 中建模，链路在
simple/Throttle.cc 中建模。流控通过在发送前监控
输出链路上的可用缓冲区和可用带宽来实现。

![Simple_network.jpg]({{ site.baseurl }}/assets/img/Simple_network.jpg "Simple_network.jpg")


### Garnet2.0

新的（2016 年）Garnet2.0 网络的细节见
**[此处](garnet-2)**。

## 用合成流量运行网络

互连网络可以以独立方式运行并馈入
合成流量。我们建议用 garnet2.0 这样做。

**[用合成流量独立运行 Garnet]({{ site.baseurl }}/documentation/general_docs/ruby/garnet_synthetic_traffic)**

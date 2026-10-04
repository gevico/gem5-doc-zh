---
layout: documentation
title: "Garnet 2.0"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/garnet-2/
author: Jason Lowe-Power
---

**gem5 Ruby 互连网络的更多细节见
[此处](/documentation/general_docs/ruby/interconnection-network/)。**

### Garnet2.0：面向异构 SoC 的片上网络模型

Garnet2.0 是 gem5 内部一个详细的互连网络模型。它
正在积极开发中，带有更多功能的补丁会
定期推入 gem5。**其他与 garnet 相关的补丁和
正在开发的工具支持（不属于仓库的一部分）见**
[Georgia Tech 的 Garnet 页面](http://synergy.ece.gatech.edu/tools/garnet)。

Garnet2.0 建立在最初发表于
[2009 年](http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=4919636%7CISPASS)的 Garnet 模型之上。

如果你使用 Garnet 的工作促成了发表的论文，请引用
以下论文：

```
    @inproceedings{garnet,
      title={GARNET: A detailed on-chip network model inside a full-system simulator},
      author={Agarwal, Niket and Krishna, Tushar and Peh, Li-Shiuan and Jha, Niraj K},
      booktitle={Performance Analysis of Systems and Software, 2009. ISPASS 2009. IEEE International Symposium on},
      pages={33--42},
      year={2009},
      organization={IEEE}
    }
```

Garnet2.0 提供了片上网络路由器的周期精确微架构实现。它利用了 gem5 的 ruby 内存系统模型所提供的 [拓扑](
/documentation/general_docs/ruby/interconnection-network#Topology) 与[路由](
/documentation/general_docs/ruby/interconnection-network#Routing) 基础设施。默认路由器是
最先进的单周期流水线。可以支持在任何路由器中
增加任意数量的周期延迟，只需在拓扑中指定。

通过为路由器和链路设置适当的延迟，Garnet2.0 还可以用于建模片外互连网络。

- **相关文件**：
  - **src/mem/ruby/network/Network.py**
  - **src/mem/ruby/network/garnet2.0/GarnetNetwork.py**
  - **src/mem/ruby/network/Topology.cc**

## 调用方式

通过加上 **--network=garnet2.0** 可以启用 garnet 网络。

## 配置

Garnet2.0 使用 Network.py 中的通用网络参数：

- **number_of_virtual_networks**：虚拟网络的最大数量。
  实际活跃的虚拟网络数量
  由协议决定。
- **control_msg_size**：控制消息的字节大小。
  默认是 8。Network.cc 中的 **m_data_msg_size** 被设为
  块的字节大小 + control_msg_size。

其他参数在 garnet2.0/GarnetNetwork.py 中指定：

- **ni_flit_size**：flit 的字节大小。flit 是
  从一个路由器向另一个路由器发送信息的
  粒度。默认是 16（=\> 128 位）。\[该默认值 16
  使控制消息能放入 1 个 flit、数据
  消息能放入 5 个 flit\]。Garnet 要求
  ni_flit_size 与 bandwidth_factor（在
  network/BasicLink.py 中）相同，因为它不建模网络内的可变带宽。
  也可以从命令行用 **--link-width-bits** 设置。
- **vcs_per_vnet**：每个虚拟网络（VC）数量
  。默认是 4。也可以从命令行
  用 **--vcs-per-vnet** 设置。
- **buffers_per_data_vc**：数据消息类中每个 VC 的
  flit 缓冲区数量。由于数据消息占用 5 个 flit，该
  值可以在 1-5 之间。默认是 4。
- **buffers_per_ctrl_vc**：控制消息类中每个 VC 的
  flit 缓冲区数量。由于控制消息占用 1 个 flit，
  且一个 VC 一次只能持有一条消息，该值必须为
  1。默认是 1。
- **routing_algorithm**：0：基于权重表（默认），1：XY，
  2：自定义。更多细节见下文。

## 拓扑

Garnet2.0 利用了 gem5 的 ruby 内存系统模型
所提供的
[拓扑](/documentation/general_docs/ruby/interconnection-network#Topology)
基础设施
。任何异构拓扑都可以被建模。拓扑文件中的每个路由器都可以被赋予
独立的延迟，以覆盖默认值。此外，每条链路
都有 2 个可选参数：src_outport 和 dst_inport，它们是
每条链路的源与目的路由器的输出和输入端口名称
字符串。它们可以在 garnet2.0 内部用于
实现自定义路由算法，如下文所述。例如，在
Mesh 中，从西到东的链路其 src_outport 被设为 "west"，而
dst_inport" 被设为 "east"。

- **网络组件**：
    - **GarnetNetwork**：这是实例化所有网络接口、路由器和链路的
      顶层对象。
      Topology.cc 调用相应方法来添加 NI 与路由器之间的“外部链路”，
      以及路由器之间的“内部链路”。
    - **NetworkInterface**：每个 NI 一侧通过 MsgBuffer 接口连接到一个一致性
      控制器，另一侧有一条通往路由器的链路。每条协议消息都会被放入
      一个单 flit 的控制消息或（默认 5 个 flit 的）数据消息（取决于
      其 vnet），并注入路由器。多个 NI 可以
      连接到同一个路由器（例如在 Mesh 拓扑中，
      缓存和 dir 控制器通过各自的 NI 连接到同一个
      路由器）。
    - **Router**：路由器管理输出链路的仲裁，以及
      路由器之间的流控。
    - **NetworkLink**：网络链路承载 flit。它们可以是
      3 种类型之一：EXT_OUT_（路由器到 NI）、EXT_IN_（NI 到路由器）
      和 INT_（内部路由器到路由器）
    - **CreditLink**：信用链路在
      路由器之间传递 VC/缓冲区信用以实现流控。

## 路由

Garnet2.0 利用了 gem5 的 ruby 内存系统模型
所提供的
[路由](/documentation/general_docs/ruby/interconnection-network#Routing)基础设施
。默认路由
算法是采用最短路径的确定性基于表的路由算法。链路权重
可用于让某些链路优先于其他链路。
关于路由表如何填充的细节见 src/mem/ruby/network/Topology.cc。

**自定义路由**：为建模自定义路由算法（例如自适应），我们
提供了一个框架：用 src_outport 与
dst_inport 方向为每条链路命名，并在 garnet 内部使用它们来实现路由
算法。例如，在 Mesh 中，west-first 可以通过
沿着 "west" 输出端口链路发送 flit，直到该 flit 不再有
任何 X 方向跳数，然后随机（或基于下一个路由器 VC
的可用情况）选择其中一条剩余链路。见
src/mem/ruby/network/garnet2.0/RoutingUnit.cc 中 outportComputeXY() 的实现。类似地，
可以实现 outportComputeCustom()，并通过在命令行加入
--routing-algorithm=2 来调用。

**多播消息**：所建模的网络在网络内部没有硬件
多播支持。多播消息会在网络接口处
被拆分为多条单播消息。

## 流控

该设计使用虚拟通道流控。每个 VC 可以容纳一个
数据包。设计中有两类 VC —— 控制与数据。二者的
缓冲区深度都可以从
GarnetNetwork.py 独立控制。默认值是 1 个 flit 深的控制 VC 和
4 个 flit 深的数据 VC。控制数据包的默认大小为 1 个 flit，
数据数据包为 5 个 flit。

## 路由器微架构

garnet2.0 路由器执行以下动作：

1.  **缓冲区写（BW）**：到来的 flit 被缓冲在其 VC 中。
2.  **路由计算（RC）** 被缓冲的 flit 计算其输出端口，
    该信息被存储在其 VC 中。
3.  **交换机分配（SA）**：所有被缓冲的 flit 尝试为
    下一个周期预留交换机端口。\[分配以
    *分离*方式发生：首先，每个输入使用
    输入仲裁器选出一个输入 VC，后者放置一个交换机请求。然后，每个输出
    端口通过输出仲裁器解决冲突\]。有序
    虚拟网络中的所有仲裁器都是*排队式*的，以维持点对点顺序。
    其他所有仲裁器都是*轮询式*的。
4.  **VC 选择（VS）**：SA 的赢家从其输出端口选择一个空闲 VC（如果是
    HEAD/HEAD_TAIL flit）。
5.  **交换机穿越（ST）**：赢得 SA 的 flit 穿越 crossbar
    交换机。
6.  **链路穿越（LT）**：来自 crossbar 的 flit 穿越链路
    到达下一个路由器。

在默认设计中，BW、RC、SA、VS 和 ST 都在 1 个周期内完成。LT
在下一个周期发生。

**多周期路由器**：可以通过在拓扑文件中指定
每个路由器的延迟，或修改
src/mem/ruby/network/BasicRouter.py 中的默认路由器延迟来建模多周期路由器。这是
通过让被缓冲的 flit 在路由器中等待（latency-1）
个周期后才具备 SA 资格来实现的。

## 缓冲区管理

每个路由器输入端口都有 number_of_virtual_networks 个 Vnet，每个
Vnet 有 vcs_per_vnet 个 VC。控制 Vnet 中的 VC 深度为
buffers_per_ctrl_vc（默认 = 1），数据 Vnet 中的 VC 深度
为 buffers_per_data_vc（默认 = 4）。**信用用于传递
空闲 VC 的信息以及每个 VC 中的缓冲区数量。**

## 一次网络穿越的生命周期

  - NetworkInterface.cc::wakeup()
      - 每个 NI 一端连接到一个一致性协议控制器，
        另一端连接到一个路由器。
      - 从一致性协议缓冲区接收相应
        vnet 中的消息，把它们转换为网络数据包并发送
        到网络中。
          - garnet2.0 增加了在此处捕获网络跟踪的
            能力 \[开发中\]。
      - 从网络接收 flit，提取协议消息
        并把相应 vnet 中的消息发送到一致性协议缓冲区。
      - 与其所连接的路由器一起管理流控（即信用）。
      - NI 上消费 flit/信用的输出链路会被放入
        全局事件队列，时间戳设为下一个周期。
        事件队列会调用消费者中的 wakeup 函数。

<!-- end list -->

  - NetworkLink.cc::wakeup()
      - 从 NI/路由器接收 flit，并在
        m_latency 个周期延迟后把它发送给 NI/路由器
      - 每条链路的默认延迟值可以从命令行
        设置（见 configs/network/Network.py）
      - 每条链路的延迟可以在拓扑文件中覆盖
      - 链路的消费者（NI/路由器）会被放入全局事件
        队列，时间戳设为 m_latency 个周期之后。事件队列
        会调用消费者中的 wakeup 函数。

<!-- end list -->

  - Router.cc::wakeup()
      - 遍历所有 InputUnit 并调用它们的 wakeup()
      - 遍历所有 OutputUnit 并调用它们的 wakeup()
      - 调用 SwitchAllocator 的 wakeup()
      - 调用 CrossbarSwitch 的 wakeup()
      - 当路由器的任何模块（InputUnit、OutputUnit、SwitchAllocator、CrossbarSwitch）
        在该周期有就绪的 flit/信用需要处理时，
        就会调用路由器的 wakeup 函数。

<!-- end list -->

  - InputUnit.cc::wakeup()
      - 如果上游路由器在该周期就绪，就从它读取输入
        flit
      - 对于 HEAD/HEAD_TAIL flit，执行路由计算，并在
        VC 中更新路由。
      - 把该 flit 缓冲（m_latency - 1）个周期，并从该周期起把它标记为
        可参与 SwitchAllocation。
          - 每个路由器的默认延迟可以从命令行
            设置（见 configs/network/Network.py）
          - 每个路由器的延迟（即流水线级数）可以在
            拓扑文件中设置。

<!-- end list -->

  - OutputUnit.cc::wakeup()
      - 如果下游路由器在该周期就绪，就从它读取输入
        信用
      - 在相应的输出 VC 状态中递增信用。
      - 如果该信用携带的 is_free_signal 为
        true，则把该输出 VC 标记为空闲

<!-- end list -->

  - SwitchAllocator.cc::wakeup()
      - 注意：SwitchAllocator 在其中执行 VC 仲裁与
        选择。
      - SA-I（或 SA-i）：在每个输入端口遍历所有输入 VC，
        并以轮询方式选择一个。
          - 对于 HEAD/HEAD_TAIL flit，只选择其输出端口
            至少有一个空闲输出 VC 的输入 VC。
          - 对于 BODY/TAIL flit，只选择其输出 VC 中
            有信用的输入 VC。
      - 从该 VC 为输出端口放置一个请求。
      - SA-II（或 SA-o）：遍历所有输出端口，并以轮询方式选择
        一个（在 SA-I 期间放置了请求的）输入 VC 作为
        该输出端口的赢家。
          - 对于 HEAD/HEAD_TAIL flit，执行 outvc 分配（即
            从输出端口选择一个空闲 VC。
          - 对于 BODY/TAIL flit，递减输出 vc 中的一个信用。
      - 从输入 VC 中读出该 flit，并把它发送到
        CrossbarSwitch
      - 为该输入 VC 向上游路由器发送一个 increment_credit 信号。
          - 对于 HEAD_TAIL/TAIL flit，在该信用中把 is_free_signal 标记为 true。
          - 输入单元通过信用链路把该信用发送给
            上游路由器。
      - 重新调度 Router，使其在下一个周期为任何已就绪
        可在下个周期参与 SA 的 flit 唤醒。

<!-- end list -->

  - CrossbarSwitch.cc::wakeup()
      - 遍历所有输入端口，并把获胜的 flit 从其
        输出端口发送到输出链路上。
      - 路由器上消费 flit 的输出链路会被放入
        全局事件队列，时间戳设为下一个周期。事件队列
        会调用消费者中的 wakeup 函数。

<!-- end list -->

  - NetworkLink.cc::wakeup()
      - 从 NI/路由器接收 flit，并在
        m_latency 个周期延迟后把它发送给 NI/路由器
      - 每条链路的默认延迟值可以从命令行
        设置（见 configs/network/Network.py）
      - 每条链路的延迟可以在拓扑文件中覆盖
      - 链路的消费者（NI/路由器）会被放入全局事件
        队列，时间戳设为 m_latency 个周期之后。事件队列
        会调用消费者中的 wakeup 函数。

## 用合成流量运行 Garnet2.0

Garnet2.0 可以以独立方式运行并馈入合成
流量。细节描述见：**[Garnet 合成
流量](/documentation/general_docs/ruby/garnet_synthetic_traffic)**

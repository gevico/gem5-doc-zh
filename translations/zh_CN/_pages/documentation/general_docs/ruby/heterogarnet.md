---
layout: documentation
title: "HeteroGarnet (Garnet 3.0)"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/heterogarnet/
author: Srikant Bharadwaj
---

**gem5 Ruby 互连网络的更多细节见[此处]({{ site.baseurl }}/documentation/general_docs/ruby/interconnection-network "wikilink")。**
**较早 Garnet 版本的细节见[此处]({{ site.baseurl }}/documentation/general_docs/ruby/garnet-2 "wikilink")。**

### HeteroGarnet：面向多样化互连系统的详细模拟器
[HeteroGarnet](https://doi.org/10.1109/DAC18072.2020.9218539) 在广受欢迎的 Garnet 2.0 网络模型基础上加以改进，支持对新兴互连系统进行准确模拟。具体来说，HeteroGarnet 增加了对时钟域孤岛（clock-domain island）、支持多个频率域的网络交叉（network crossing）以及可连接多条物理链路的网络接口控制器的支持。它还通过引入新的可配置串行器-解串器（Serializer-Deserializer）组件，支持可变带宽的链路与路由器。HeteroGarnet 以 Garnet 3.0 的形式集成到 gem5 仓库中。

HeteroGarnet 建立在最初发表于
[2009 年](https://doi.org/10.1109/ISPASS.2009.4919636)的 Garnet 模型之上。

如果你使用 HeteroGarnet 的工作促成了发表的论文，请引用
以下论文：

```
    @inproceedings{heterogarnet,
        author={Bharadwaj, Srikant and Yin, Jieming and Beckmann, Bradford and Krishna, Tushar},
        booktitle={2020 57th ACM/IEEE Design Automation Conference (DAC)},
        title={Kite: A Family of Heterogeneous Interposer Topologies Enabled via Accurate Interconnect Modeling},
        year={2020},
        volume={},
        number={},
        pages={1-6},
        doi={10.1109/DAC18072.2020.9218539}
	}
```



## 拓扑构建
HeteroGarnet 允许用户以 python 配置文件作为拓扑来配置复杂拓扑。
整体拓扑配置可以包含系统的完整互连定义，包括
任何异构组件。定义拓扑的一般流程包括以下步骤：

1. 确定系统中路由器的总数并实例化它们。
    1. 使用 **Router** 类实例化各个路由器。
    2. 根据需求配置每个路由器的属性，例如时钟域、支持的 flit 宽度。
```
routers = Router(id, latency, clock_domain,
                flit_width, supported_vnets,
                vcs_per_vnet)
```

2. 使用外部物理互连连接那些连接端点的路由器（例如核心、缓存、目录）。
    1. 使用 **ExternalLink** 类实例化连接端点的链路。
    2. 根据需求配置每条外部链路的属性，例如时钟域、链路宽度。
    3. 根据互连拓扑在两端启用时钟域交叉（CDC）和串行器-解串器（SerDes）单元。
```
external_link = ExternalLink(id, latency, clock_domain,
                             flit_width, supported_vnets,
                             serdes_enable, cdc_enable)
````

3. 根据拓扑连接网络内的各个路由器。
    1. 使用 **InternalLink** 类实例化连接端点的链路。
    2. 根据需求配置每条内部链路的属性，例如时钟域、链路宽度。
    3. 根据互连拓扑在两端启用时钟域交叉和串行器-解串器单元。
```
internal_link = InternalLink(id, latency, clock_domain,
                             flit_width, supported_vnets,
                             serdes_enable, cdc_enable)
```

Garnet 3.0 还提供了若干预配置脚本（./configs/Network/Network.py），它们会自动完成其他一些步骤，例如实例化网络接口、域交叉和 SerDes 单元。下面讨论用于配置拓扑的各类单元。


## 物理链路
Garnet 中的物理链路模型表示互连导线本身。一条链路是单个实体，拥有自己的延迟、宽度以及可传输的 flit 类型。链路还支持基于信用（credit）的反压机制。与升级后的 Garnet 3.0 路由器类似，每条 Garnet 3.0 链路都可以用相应参数配置其工作频率和宽度。这使工作在不同频率的链路和路由器可以相互连接。

## 网络接口
网络接口控制器（NIC）是位于网络端点（例如缓存、DMA 节点）与互连系统之间的对象。NIC 从控制器接收消息，并把它们转换为固定长度的 flit（flow control unit，流控单元）。这些 flit 的大小根据输出物理链路适当确定。网络接口还管理输出与输入 flit 的流控和缓冲。Garnet 3.0 允许把多个端口连接到单个端点。因此 NIC 决定某条消息/flit 应被调度到哪里。

## 时钟域交叉单元
为了支持多个时钟域，Garnet 3.0 引入了时钟域交叉（CDC）单元，如下图所示（左），它由先进先出（FIFO）缓冲区组成，可以实例化在网络模型中的任何位置。CDC 单元使系统中可以存在不同时钟域的体系结构。每个 CDC 单元的延迟可配置，也可以根据连接到它的时钟域动态计算。这使 DVFS 技术可以被准确建模，因为 CDC 延迟通常是生产者与消费者工作频率的函数。

## 串行器-解串器单元
在建模 SoC 与异构体系结构时，另一项关键特性是支持系统中不同的互连宽度。考虑 GPU 内两个路由器之间的一条链路，以及内存控制器与片上内存之间的一条链路。这两条链路可能宽度不同。为支持这种配置，Garnet 3.0 引入了如下图所示的串行器-解串器单元，它在位宽边界处把 flit 转换为合适的宽度。这些 SerDes 单元与上一小节描述的 CDC 单元类似，可以实例化在 Garnet 3.0 拓扑中的任何位置。

![SerDes_CDC.png]({{ site.baseurl }}/assets/img/SerDes_CDC.png)

## 路由
路由算法决定 flit 如何在拓扑中传输。路由策略的目标是在最小化竞争的同时最大化互连所提供的带宽。Garnet 3.0 提供了若干标准路由策略供用户选择。

### 路由策略
针对 flit 在互连网络中的无死锁路由，已有若干通用路由
策略被提出。

### 基于表的路由
Garnet 还具有基于表的路由策略，用户可以选择它以通过基于权重的机制设置自定义路由策略。权重较低的链路优先于配置了较高权重的链路。



## 流控与缓冲管理

流控机制决定互连系统中的缓冲区分配。一个好的流控系统旨在最小化缓冲区分配对系统中消息总体延迟的影响。这些机制的实现往往涉及对互连系统内物理数据包的微观管理。

缓存控制器生成的一致性消息通常被拆分为固定长度的 flit（流控单元）。携带一条消息的一组 flit 通常称为一个数据包，它可能包含 head-flit、body-flit 和 tail-flit，用于携带消息内容以及数据包自身的任何额外元数据。已有若干流控技术被提出，并在不同粒度的资源分配上实现。

Garnet 3.0 实现了基于信用的 flit 级流控机制，并支持虚拟通道。

### 虚拟通道
网络中的虚拟通道（VC）充当独立队列，可以在两个路由器或仲裁器之间共享物理导线（物理链路）。虚拟通道主要用于缓解队头阻塞，也用作避免死锁的手段。

### 缓冲区反压
大多数互连网络的实现都不允许在传输过程中丢弃数据包或 flit。因此需要通过反压机制严格管理 flit。

### 基于信用的反压
基于信用的反压机制常用于低延迟地实现 flit 停顿。信用通过每次发送 flit 时递减总缓冲数，来跟踪下一个中间目的地处可用的缓冲区数量。当目的地腾出缓冲时，它会把信用回送。

互连系统中的路由器在网络内执行仲裁、缓冲分配和流控。路由器微架构的目标是在为 flit 提供最小逐跳延迟的同时，最小化路由器内的竞争。路由器微架构的复杂度还影响互连系统的总体能耗与面积。


## Garnet 3.0 中一条消息的一生
本节描述消息在缓存控制器单元生成之后，在 NoC 中的完整历程。我们以 Garnet 3.0 为例描述该过程，但总体建模原则也可以推广到其他软件模拟/建模工具。

![HeteroGarnet_Life.png]({{ site.baseurl }}/assets/img/HeteroGarnet_Life.png)

系统的整体流程在上图中详细展示。它展示了一个简单示例场景：一个缓存控制器生成一条发往另一个缓存控制器的消息，二者通过物理链路、串行器-解串器单元和时钟域交叉经由路由器相连。

### 消息注入
源缓存控制器创建一条消息，并把一个或多个缓存控制器指定为目的地。该消息随后被注入消息队列。缓存控制器通常有若干用于不同消息类型的输出与输入消息缓冲区。

### 转换为 flit。
每个缓存控制器都附有一个网络接口控制器单元（NIC）。该 NIC 被唤醒并消费消息队列中的消息。每条消息随后先被转换为单播消息，再根据输出物理链路所支持的大小被拆分为固定长度的 flit。然后这些 flit 根据下一跳缓冲区的可用情况，通过某条输出链路被调度发送。输出链路的选择取决于目的地、路由策略和消息类型。

### 传输到本地路由器。
每个网络接口都连接到一个或多个“本地”路由器，它们之间可能通过“外部”链路连接。一旦某个 flit 被调度，它就会通过这些外部链路传输，在经过一段确定的延迟之后把该 flit 送达路由器。

### 路由器仲裁。
该 flit 唤醒路由器，后者是一个多级单元。路由器包含输入缓冲区、VC 分配、交换机仲裁和 crossbar 单元。到达时，该 flit 首先被放入一个输入缓冲队列。路由器中有若干个输入缓冲队列竞争下一条输出链路和下一跳的 VC。这是通过 VC 分配与交换机仲裁级完成的。一旦某个 flit 被选中发送，crossbar 级就把该 flit 导向输出链路。随着输入缓冲空间为下一个到达的 flit 腾出，会向 NIC 回送一个信用。

### 串行化-解串行化。
串行化-解串行化（SerDes）是一个可选单元，可以根据设计需求启用。SerDes 单元消费 flit 并把它适当转换为输出 flit 大小。除操作数据包之外，SerDes 还通过串行化或解串行化信用单元来处理信用系统。


## 面积、功耗与能耗模型
Orion2.0 与 DSENT 之类的框架为 NoC 路由器与链路的各个构建块提供了面积与功耗模型。HeteroGarnet 把 DSENT 作为外部工具集成进来，在模拟结束时报告面积、功耗和能耗（能耗取决于活动量）。

---
layout: documentation
title: "简介"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/
author: Jason Lowe-Power
---

# Ruby

Ruby 为内存子系统实现了一个详细的模拟模型。它建模包含性/排他性缓存层次结构，支持各种替换策略、一致性（coherence）协议实现、互连（interconnection）网络、DMA 与内存控制器，以及各种发起内存请求并处理响应的 sequencer。这些模型模块化、灵活且高度可配置。这些模型的三个关键方面是：

1.  关注点分离 —— 例如，一致性协议的
    规范与替换策略、缓存索引映射相互独立，网络拓扑
    也与其实现分开指定。
2.  丰富的可配置性 —— 几乎任何影响内存
    层次结构功能与时序的方面都可以控制。
3.  快速原型开发 —— 使用一种高层级规范语言 SLICC
    来指定各种控制器的功能。

下图取自 ISCA 2005 的 GEMS 教程，展示了
Ruby 中主要组件的高层视图。
![ruby_overview.jpg](/assets/img/Ruby_overview.jpg)

关于以教程方式学习 Ruby，请参见 [Learning gem5 第三部分](/documentation/learning_gem5/part3/)

### SLICC + 一致性协议：

***[SLICC](slicc)*** 是 *Specification Language for
Implementing Cache Coherence* 的缩写。它是一种领域特定语言，用于指定缓存一致性协议。本质上，缓存一致性协议的行为就像一个状态机（state machine）。SLICC 用于指定该状态机的行为。由于目标是尽可能贴近地建模硬件，SLICC 对可以指定的状态机施加了约束。例如，SLICC 可以限制单个周期内可以发生的转换数量。除协议规范之外，SLICC 还把内存模型中的一些组件组合在一起。如下图所示，状态机从互连网络的输入端口获取输入，并把输出排队到网络的输出端口，从而把缓存/内存控制器与互连网络本身连接在一起。

![slicc_overview.jpg](/assets/img/Slicc_overview.jpg)

支持以下缓存一致性协议：

1.  **[MI_example](MI_example)**：示例协议，单级
    缓存。
2.  **[MESI_Two_Level](MESI_Two_Level)**：单芯片，
    两级缓存，严格包含层次结构。
3.  **[MOESI_CMP_directory](MOESI_CMP_directory)**：
    多芯片，两级缓存，非包含（既非严格
    包含也非排他）层次结构。
4.  **[MOESI_CMP_token](MOESI_CMP_token)**：两级缓存。
    待补充。
5.  **[MOESI_hammer](MOESI_hammer)**：单芯片，两级
    私有缓存，严格排他层次结构。
6.  **[Garnet_standalone](Garnet_standalone)**：用于
    以独立方式运行 Garnet 网络的协议。
7.  **MESI Three Level**：三级缓存，
    严格包含层次结构。基于 MESI Two Level，额外增加一个 L0 缓存。
8.  **[CHI](CHI)**：实现 Arm AMBA5 CHI 事务的灵活协议。
    支持可配置的缓存层次结构，并同时支持 MESI 或 MOESI 一致性。

协议中常用的记法与数据结构已在[此处](cache-coherence-protocols)详细描述。

### 协议无关的内存组件

1.  **Sequencer**
2.  **Cache Memory**
3.  **替换策略（Replacement Policy）**
4.  **内存控制器**

一般而言，与缓存一致性协议无关的组件包括 Sequencer、Cache Memory 结构、缓存替换策略以及内存控制器。Sequencer 类负责把来自处理器的加载/存储/atomic 内存请求送入内存子系统（包括缓存与片外内存）。每个内存请求在被内存子系统完成时，也会通过 Sequencer 把响应送回处理器。系统中每个被模拟的硬件线程（或核心）都有一个 Sequencer。Cache Memory 建模组相联缓存结构，其大小、相联度、替换策略均可参数化。系统中的 L1、L2、L3 缓存（如果存在）都是 Cache Memory 的实例。缓存替换策略与 Cache Memory 保持模块化分离，因此不同的 Cache Memory 实例可以使用各自选择的替换策略。目前发行版中随附两种替换策略 —— LRU 和 Pseudo-LRU。内存控制器负责模拟并服务所有在被模拟系统的全部片上缓存中未命中的请求。内存控制器目前较为简单，但忠实建模了 DRAM bank 竞争与 DRAM 刷新。它还建模了 DRAM 缓冲区的 close-page 策略。

### 互连网络

互连网络把内存层次结构的各个组件（缓存、内存、dma 控制器）连接在一起。

![Interconnection_network.jpg](/assets/img/Interconnection_network.jpg
"Interconnection_network.jpg")

互连网络的关键组件有：

1.  **拓扑**
2.  **路由**
3.  **流控**
4.  **路由器微架构**

***关于网络模型实现的更多细节描述见
[此处](Interconnection_Network)。***

另一种选择是用外部模拟器 [TOPAZ](https://github.com/ceunican/tpzsimul) 替换互连网络。该
模拟器可以直接在 gem5 中运行，并在原始 ruby 网络模拟器的基础上增加了
大量特性。它包括新的高级路由器
微架构、新的拓扑、精度-性能可调的路由器模型、加速网络模拟的机制等。

## Ruby 中一次内存请求的一生

本节将给出高层级概述，说明 Ruby 整体如何服务一次内存
请求，以及它会经过 Ruby 中的哪些组件。至于各组件内部的详细操作，
请参阅前面各节对每个组件的单独描述。

1.  来自 gem5 某个核心或硬件上下文的内存请求通过 ***RubyPort::recvTiming***
    接口（在 src/mem/ruby/system/RubyPort.hh/cc 中）进入
    Ruby 的管辖范围。被模拟系统中 RubyPort 的实例数量等于
    硬件线程上下文或核心的数量（对于
    *非多线程*核心）。每个核心侧的端口都与一个对应的 RubyPort
    相连。
2.  该内存请求以 gem5 数据包（packet）的形式到达，RubyPort 负责
    把它转换为 Ruby 各组件都能理解的 RubyRequest 对象。它还会判断
    该请求是否针对某个 PIO，并把数据包引导到正确的
    PIO。最后，一旦它生成了对应的 RubyRequest
    对象并确认该请求是*普通*内存请求
    （不是 PIO 访问），它就通过该端口所连接的 Sequencer
    对象的 ***Sequencer::makeRequest*** 接口把请求传递下去
    （变量 *ruby_port* 持有指向它的指针）。可以看到 Sequencer 类本身
    是 RubyPort 类的派生类。
3.  正如描述 Ruby 的 Sequencer 类那一节所述，
    被模拟系统中 Sequencer 对象的数量等于
    硬件线程上下文的数量（也等于系统中
    RubyPort 对象的数量），并且 Sequencer 对象与硬件线程上下文之间是一一
    映射。一旦内存请求到达 ***Sequencer::makeRequest***，它就
    为该请求进行各种记账和资源分配，最后把请求推入
    Ruby 的一致性缓存层次结构以满足该请求，同时计入
    服务它的延迟。请求是在计入 L1 缓存访问延迟之后，
    通过把请求入队到 *mandatory queue* 而推入缓存层次结构的。
    *mandatory queue*（变量名 *m_mandatory_q_ptr*）实际上充当了
    Sequencer 与 SLICC 生成的缓存一致性文件之间的接口。
4.  L1 缓存控制器（由 SLICC 按一致性
    协议规范生成）从 *mandatory queue* 中取出请求，
    查找缓存，进行必要的一致性状态转换，
    并按需把请求推入下一级缓存层次结构。SLICC
    生成的 Ruby 代码中不同控制器和组件通过
    Ruby 的 *MessageBuffer* 类
    （src/mem/ruby/buffers/MessageBuffer.cc/hh）实例相互通信，它
    可以作为有序或无序的缓冲或队列。此外，满足一次内存请求的
    不同步骤中的延迟也会通过相应地调度入队与出队操作来计入。
    如果请求的缓存块可以在 L1 缓存中找到且具有
    所需的一致性权限，该请求就被满足并
    立即返回。否则，请求会通过 *MessageBuffer* 被推入下一
    级缓存层次结构。请求可以一路到达 Ruby 的内存控制器（在许多协议中也称为
    Directory）。一旦请求被满足，它就会
    通过 *MessageBuffer* 沿层次结构向上推送。
5.  *MessageBuffer* 也是一致性消息进入所建模的片上互连的入口。
    MessageBuffer 按所指定的互连拓扑连接。一致性
    消息因此相应地经由该片上互连传输。
6.  一旦所请求的缓存块在 L1 缓存中以所需
    一致性权限可用，L1 缓存控制器就会通过调用相应 Sequencer 对象的
    ***readCallback*** 或 **writeCallback**''方法（取决于请求类型）来通知它。
    注意在这些 Sequencer 方法被调用时，服务该请求的
    延迟已经被隐式计入。
7.  Sequencer 随后清除对应请求的记账信息，然后调用
    ***RubyPort::ruby_hit_callback*** 方法。这最终把请求结果
    返回给前端（gem5）中对应核心/硬件上下文的端口。

## 目录结构

  - **src/mem/**
      - **protocols**：一致性协议的 SLICC 规范
      - **slicc**：SLICC 解析器与代码生成器的实现
      - **ruby**
          - **common**：常用数据结构，例如 Address
            （带位操作方法）、histogram、data block
          - **filters**：各种 Bloom filter（来自 GEMS 的旧代码）
          - **network**：互连实现、示例拓扑
            规范、网络功耗计算、用于连接控制器的消息缓冲区
          - **profiler**：缓存事件、内存控制器
            事件的性能分析
          - **recorder**：缓存预热与访问跟踪记录
          - **slicc_interface**：消息数据结构、各种
            映射（例如地址到目录节点的映射）、工具函数
            （例如地址与整数之间的转换、把地址转换为
            缓存行地址）
          - **structures**：协议无关的内存组件 ——
            CacheMemory、DirectoryMemory
          - **system**：粘合组件 —— Sequencer、RubyPort、
            RubySystem

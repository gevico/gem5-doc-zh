---
layout: documentation
title: Simple CPU 模型
doc: gem5 文档
parent: cpu_models
permalink: /documentation/general_docs/cpu_models/SimpleCPU
---
# **SimpleCPU**
SimpleCPU 是一个纯功能性的顺序（in-order）模型，适用于不需要详细模型的场合。这可以包括预热阶段、驱动宿主机的客户端系统，或者仅仅测试某个程序能否正常工作。

它最近已被重写以支持新的内存系统（memory system），现在被拆分为三个类：

**目录**


  1. [**BaseSimpleCPU**](#basesimplecpu)
  2. [**AtomicSimpleCPU**](#atomicsimplecpu)
  3. [**TimingSimpleCPU**](#timingsimplecpu)

## **BaseSimpleCPU**
BaseSimpleCPU 有以下几项用途：
  * 持有体系结构状态，以及各个 SimpleCPU 模型共用的统计信息（statistics）。
  * 定义用于检查中断、建立取指请求、处理执行前准备、处理执行后动作，以及把 PC 推进到下一条指令的函数。这些函数在各个 SimpleCPU 模型之间也是共用的。
  * 实现 ExecContext 接口。

BaseSimpleCPU 不能单独运行。你必须使用继承自 BaseSimpleCPU 的类之一，即 AtomicSimpleCPU 或 TimingSimpleCPU。

## **AtomicSimpleCPU**
AtomicSimpleCPU 是使用 atomic 内存访问的 SimpleCPU 版本（细节见[内存系统（memory system）](../memory_system/index.html#access-types)）。它利用 atomic 访问的延迟估计来估算整体的缓存访问时间。AtomicSimpleCPU 派生自 BaseSimpleCPU，实现了读写内存的函数，也实现了 tick 函数，后者定义了每个 CPU 周期发生的事情。它定义了用于连接内存的端口，并把 CPU 连接到缓存。

![AtomicSimpleCPU](/assets/img/AtomicSimpleCPU.jpg)

## **TimingSimpleCPU**
TimingSimpleCPU 是使用 timing 内存访问的 SimpleCPU 版本（细节见[内存系统（memory system）](../memory_system/index.html#access-types)）。它在缓存访问上停顿，等待内存系统响应后再继续。与 AtomicSimpleCPU 一样，TimingSimpleCPU 也派生自 BaseSimpleCPU，并实现了同一组函数。它定义了用于连接内存的端口，并把 CPU 连接到缓存。它还定义了处理内存对所发出访问的响应所需的函数。

![TimingSimpleCPU](/assets/img/TimingSimpleCPU.jpg)

---
layout: documentation
title: "gem5 内存系统（gem5 memory system）"
doc: gem5 文档
parent: memory_system
permalink: /documentation/general_docs/memory_system/gem5_memory_system/
author: Djordje Kovacevi
---

# gem5 内存系统（Memory System）

本文档介绍 gem5 中的内存子系统，重点放在 CPU 发起简单内存事务（读或写）时的程序流程。

## 模型层次

本文档使用的模型由两个乱序（out-of-order，O3）ARM v7
CPU、各自对应的 L1 数据缓存以及 Simple Memory 组成。它通过
以以下参数运行 gem5 创建：

```
configs/example/fs.py –-caches –-cpu-type=arm_detailed –-num-cpus=2
```

Gem5 使用以 Simulation Object 为基类的派生对象作为构建
内存系统的基本单元。它们通过端口连接，并具有既定的主/从
层次关系。数据流由主端口发起，而响应消息
和探听查询出现在从端口上。


![模型的 Simulation Object 层次](/assets/img/gem5_MS_Fig1.PNG)


## CPU

数据[缓存（Cache）](http://doxygen.gem5.org/release/current/classgem5_1_1cache.html)对象
实现了标准的缓存结构：

![DCache Simulation Objet](/assets/img/gem5_MS_Fig2.PNG)

详细描述 O3 CPU 模型不在本文档的范围之内，因此
这里只给出与该模型相关的几点说明：

**读访问**通过向通往 DCache
对象的端口发送消息来发起。如果 DCache 拒绝该消息（因为被阻塞或忙碌），CPU 会
清空流水线，稍后重新尝试该访问。收到来自 DCache 的回复消息（ReadRep）时，该访问
完成。

**写访问**通过把请求存入存储缓冲（store buffer）来发起，存储缓冲的
内容每个 tick 被清空并发送到 DCache。DCache 也可能拒绝该
请求。收到来自 DCache 的写回复（WriteRep）消息时，写访问
完成。

加载与存储缓冲（分别对应读访问与写访问）不对
活跃内存访问的数量施加任何限制。因此，
CPU 未完成的内存访问请求的最大数量并不由 CPU Simulation
Object 限制，而是由底层内存系统模型限制。

**拆分内存访问（split memory access）**已实现。

CPU 发送的消息包含被访问区域的内存类型（Normal、Device、Strongly
Ordered 以及可缓存性）。不过，模型的其他部分并不使用
这些信息，它们对内存类型采取了更简化的处理方式。

## 数据缓存对象

数据[缓存（Cache）](http://doxygen.gem5.org/release/current/classgem5_1_1Cache.html)对象
实现了标准的缓存结构：

**命中缓存的读**（匹配特定缓存标签，且 Valid 与 Read
标志已置位）会在可配置的时间之后完成（通过向 CPU 发送 ReadResp）。
否则，该请求会被转发到未命中状态保持寄存器
（[MSHR](http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html)）块。

**命中缓存的写**（匹配特定缓存标签，且 Valid、Read 与
Write 标志已置位）会在相同的可配置时间之后完成（通过向 CPU 发送 WriteResp）。
否则，该请求会被转发到未命中状态保持寄存器（MSHR）块。

**未命中缓存的读**会被转发到 [MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 块。

**未命中缓存的写**会被转发到 WriteBuffer 块。

**被逐出（且为脏）的缓存行**会被转发到 WriteBuffer 块。

如果以下任一条件成立，CPU 对数据[缓存（Cache）](
http://doxygen.gem5.org/release/current/classgem5_1_1Cache.html)的访问会被阻塞：

* [MSHR](http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 块已满。
（MSHR 缓冲区的大小是可配置的。）
* Writeback 块已满。（该块缓冲区的大小是可配置的。）
* 针对同一内存缓存行的未完成内存访问数量
已达到可配置的阈值 —— 详见 [MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 与 Write Buffer 的说明。

处于阻塞状态的数据[缓存（Cache）](
http://doxygen.gem5.org/release/current/classgem5_1_1Cache.html)会拒绝来自从端口（来自 CPU）的任何请求，无论
其结果会是缓存命中还是未命中。注意，主端口上到来的消息（响应消息与探听请求）
永远不会被拒绝。

在不可缓存内存区域上发生[缓存（Cache）](
http://doxygen.gem5.org/release/current/classgem5_1_1Cache.html)命中时（按 ARM ARM 的说法属于非预期行为），
会使该缓存行失效并从内存取回数据。

### 标签与数据块

[缓存（Cache）](
http://doxygen.gem5.org/release/current/classgem5_1_1Cache.html)行（在源码中称为块）按可配置的相联度和大小
组织成组。它们具有以下状态标志：

* **Valid**。它持有数据，地址标签有效
* **Read**。未置位该标志时不会接受任何读请求。例如，
  当缓存行有效但正在等待写标志以
  完成写访问时，它就是不可读的。
* **Write**。它可以接受写。置有 Write 标志的缓存行表示
  Unique 状态 —— 没有其他缓存内存持有该副本。
* **Dirty**。它在被逐出时需要回写。

如果地址标签匹配且 Valid 与 Read 标志
已置位，则读访问会命中该缓存行。如果地址标签匹配且 Valid、Read
与 Write 标志已置位，则写访问会命中该缓存行。

### MSHR 与写缓冲队列

未命中状态保持寄存器（[MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html)）队列持有
CPU 需要读访问下层内存的未完成内存请求列表。它们包括：

* 命中缓存的读未命中。
* 命中缓存的写未命中。
* 未命中缓存的读。

WriteBuffer 队列持有以下内存请求：

* 未命中缓存的写。
* 被逐出（且为脏）缓存行的回写。

![MSHR 与写缓冲块](/assets/img/gem5_MS_Fig3.PNG)

每个内存请求都会被分配到对应的 [MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 对象（上图中的 READ 或 WRITE），
该对象表示为了完成这些命令而必须读或写的特定内存块（缓存行）。如上方
图所示，针对同一缓存行的命中缓存的读/写共享一个 [MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 对象，并将通过
一次内存访问完成。

块的大小（因而也是对下层内存的读/写访问大小）为：

* 命中缓存的访问与回写时为缓存行的大小；
* 未命中缓存的访问时由 CPU 指令指定。

总体而言，数据[缓存（Cache）](
http://doxygen.gem5.org/release/current/classgem5_1_1Cache.html)模型只区分两种内存类型：

* 普通可缓存内存。它总是按写回（write back）、读分配与写
  分配（read and write allocate）处理。
* 普通不可缓存、Device 与 Strongly Ordered 类型被同等对待（作为
  不可缓存内存）

### 内存访问顺序

每个 CPU 读/写请求（在从端口上出现时）都会被分配一个唯一的顺序号。
[MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 对象的顺序号从
第一次被分配的读/写复制而来。

来自这两个队列的内存读/写按顺序执行
（依据所分配的顺序号）。当两个队列都不为空时，
模型会执行来自 [MSHR](
http://doxygen.gem5.org/release/current/classgem5_1_1MSHR.html) 块的内存读，除非 WriteBuffer
已满。不过它总是会保持针对同一（或重叠）内存缓存行（块）的读/写顺序。

概括如下：

* 对命中缓存内存的访问顺序不会被保持，除非它们针对
  同一缓存行。例如，访问 #1、#5 和 #10 会在同一个 tick 中
  同时完成（仍按顺序）。访问 #5 会在 #3 之前完成。
* 所有未命中缓存的写顺序会被保持。Write#6 总是在 Write#13
  之前完成。
* 所有未命中缓存的读顺序会被保持。Read#2 总是在 Read#8
  之前完成。
* 未命中缓存的一次读与一次写的顺序不一定会被保持，
  除非它们的访问区域重叠。因此，Write#6 总是在
  Read#8 之前完成（它们针对同一内存块）。但 Write#13 可能
  在 Read#8 之前完成。

## Coherent Bus 对象


![Coherent Bus 对象](/assets/img/gem5_MS_Fig4.PNG)


Coherent Bus 对象为探听协议提供基本支持：

从端口上的所有请求都会被转发到相应的主端口。
对可缓存内存区域的请求也会被转发到其他从端口（作为
探听请求）。

主端口的回复会被转发到相应的从端口。

主端口的探听请求会被转发到所有从端口。

从端口的探听回复会被转发到发起该请求的端口。
（注意探听请求的来源可以是从端口，也可以是主端口。）

在发生以下任一事件后，总线会在可配置的一段时间内
宣告自己处于阻塞状态：

* 一个数据包被发送（或发送失败）到某个从端口。
* 一条回复消息被发送到某个主端口。
* 来自某个从端口的探听响应被发送到另一个从端口。

处于阻塞状态的总线会拒绝以下到来的消息：

* 从端口请求。
* 主端口回复。
* 主端口探听请求。

## Simple Memory 对象

它永远不会阻塞从端口上的访问。

内存读/写立即生效。（读或写在收到
请求时执行）。

回复消息在可配置的一段时间之后被发送。

## 消息流

### 内存访问顺序

下图展示了命中具有 Valid
与 Read 标志的 Data Cache 行的读访问：

![读命中（缓存行中必须置位 Read 标志）](/assets/img/gem5_MS_Fig5.PNG)

缓存未命中的读访问会产生以下消息序列：

![带探听回复的读未命中](/assets/img/gem5_MS_Fig6.PNG)

注意，总线对象永远不会同时收到来自 DCache2 和 Memory 对象的响应。
它把同一个 ReadReq 包（消息）对象同时发送给内存和数据
缓存。当 Data Cache 想要回复探听请求时，它会给该消息
打上 MEM_INHIBIT 标志，告诉 Memory 对象不要处理该消息。

### 内存访问顺序

下图展示了命中 DCache1 中具有
Valid 与 Write 标志的缓存行的写访问：

![写命中（缓存行中置位 Write 标志）](/assets/img/gem5_MS_Fig7.PNG)

下一张图展示了命中 DCache1 中具有 Valid 但未置位
Write 标志的缓存行的写访问 —— 这属于写未命中。DCache1 发出 UpgradeReq 以
获得写权限。DCache2::snoopTiming 会使被命中的缓存行
失效。注意 UpgradeResp 消息不携带数据。

![写未命中 —— 标签匹配但未置位 Write 标志](/assets/img/gem5_MS_Fig8.PNG)

下一张图展示了 DCache 中的写未命中。ReadExReq 会使 DCache2 中的缓存行
失效。ReadExResp 携带内存缓存行的内容。

![未命中 —— 没有匹配的标签](/assets/img/gem5_MS_Fig9.PNG)

---
layout: documentation
title: "Classic 缓存（classic cache）"
doc: gem5 文档
parent: memory_system
permalink: /documentation/general_docs/memory_system/classic_caches/
author: Jason Lowe-Power
---

# Classic 缓存

默认缓存是一个非阻塞缓存，带有用于读未命中和写未命中的 MSHR（miss status holding
register，未命中状态保持寄存器）和 WB（Write Buffer，写缓冲）。缓存也可以
启用预取（通常用于最后一级缓存）。

gem5 中实现了多种可选的[替换策略]({{ site.baseurl }}/documentation/general_docs/memory_system/replacement_policies)和[索引
策略]({{ site.baseurl }}/documentation/general_docs/memory_system/indexing_policies)。它们分别定义了：给定一个地址时可用于块替换的
候选块，以及如何利用地址信息找到块的位置。默认情况下，
缓存行采用 [LRU（最近最少使用）]({{ site.baseurl }}/documentation/general_docs/memory_system/replacement_policies)进行替换，
并采用[组相联（Set Associative）]({{ site.baseurl }}/documentation/general_docs/memory_system/indexing_policies)策略进行索引。


# 互连

### 交叉开关（Crossbar）

交叉开关中有两类流量：内存映射数据包和
探听（snooping）数据包。内存映射请求沿内存
层次结构向下，响应沿内存层次结构向上（原路返回）。
探听请求水平传播并沿缓存层次结构向上，
探听响应水平传播并沿层次结构向下（原路
返回）。普通探听水平传播，快速探听沿缓存
层次结构向上。

![总线连接]({{ site.baseurl }}/assets/img/Bus.png)

### 桥接（Bridge）

### 其他……

# 调试

classic 内存系统中有一项功能，可以在调试器（例如 gdb）中显示某个特定块的一致性状态。该功能建立在 classic 内存系统对功能访问的支持之上。（注意该功能目前极少使用，可能存在缺陷。）

如果你注入一个命令设置为 PrintReq 的功能请求，该数据包会像常规功能请求一样遍历内存系统，但对于任何匹配的对象（其他排队的数据包、缓存块等），它只会打印出关于该对象的一些信息。

Port 上有一个名为 printAddr() 的辅助方法，它接收一个地址，构造合适的 PrintReq 数据包并注入它。由于它使用与普通功能请求相同的机制传播，因此需要从一个能让它遍历整个内存系统的端口注入，例如在 CPU 处。MemTest、AtomicSimpleCPU 和 TimingSimpleCPU 对象上都有辅助的 printAddr() 方法，它们只是在其各自的缓存端口上调用 printAddr()。（注意：后两者未经测试。）

综合起来，你可以这样做：

```
(gdb) set print object
(gdb) call SimObject::find(" system.physmem.cache0.cache0.cpu")
$4 = (MemTest *) 0xf1ac60
(gdb) p (MemTest*)$4
$5 = (MemTest *) 0xf1ac60
(gdb) call $5->printAddr(0x107f40)

system.physmem.cache0.cache0
  MSHRs
    [107f40:107f7f] Fill   state:
      Targets:
        cpu: [107f40:107f40] ReadReq
system.physmem.cache1.cache1
  blk VEM
system.physmem
  0xd0
```

……这表明 cache0.cache0 为该地址分配了一个 MSHR 来服务来自 CPU 的目标 ReadReq，但它尚未开始服务（否则会被相应标记）；该块在 cache1.cache1 中是有效（valid）、独占（exclusive）且已修改（modified）的，并且该字节在物理内存中的值为 0xd0。

显然这不一定是你要的全部信息，但相当有用。欢迎扩展。还有一个当前未被使用的 verbosity 参数，可以利用它来实现不同级别的输出。

注意，额外的 "p (MemTest*)$4" 是必要的：虽然 "set print object" 会显示派生类型，但在 gdb 内部仍然认为该指针是基类型，因此如果你试图直接在 $4 指针上调用 printAddr，会得到：

```
(gdb) call $4->printAddr(0x400000)
Couldn't find method SimObject::printAddr
```

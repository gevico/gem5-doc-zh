---
layout: documentation
title: Devices
parent: fullsystem
doc: gem5 文档
permalink: documentation/general_docs/fullsystem/devices
---

# 全系统（full-system）模式下的设备

## I/O 设备基类

src/dev/\*_device.\* 中的基类让设备的创建相当容易。
必须实现的类和虚函数如下。
在阅读以下内容之前，先熟悉[内存系统（memory system）](../memory_system)会有所帮助。

### PioPort

PioPort 类是一个程序控制 I/O（programmed I/O）端口，所有对某个地址范围
敏感的设备都会使用它。
该端口接收所有内存访问类型，并把它们归结为设备必须响应的一个 `read()` 和一个 `write()` 调用。
设备还必须提供 `addressRanges()` 函数，用它返回自己感兴趣的地址范围。
如有需要，一个设备可以有多个 PIO 端口。
不过在通常情形下，它只会有一个端口，并在 `addressRange()` 函数被调用时返回多个范围。只有在你的设备希望与两个内存对象分别建立连接时，才有必要使用多个 PIO 端口。

### PioDevice

这是所有对地址范围敏感的设备所继承的基类。
有三个纯虚函数是所有设备都必须实现的：`addressRanges()`、`read()` 和 `write()`。
选择所处模式等“魔法”由 PioPort 处理，因此设备无需操心。

每个设备的参数应放在派生自 `PioDevice::Params` 的 Params 结构体中。

### BasicPioDevice

由于大多数 PioDevice 只响应一个地址范围，`BasicPioDevice` 提供了 `addressRanges()`，
以及普通 pio 延迟和设备所响应地址的参数。
由于设备大小通常不可配置，因此没有为此使用参数，任何继承该类的对象都应在构造函数中把自己的大小写入 pioSize。

### DmaPort

DmaPort（在 dma_device.hh 中）只用于设备发起的访问。
必须提供 `recvTimingResp()` 方法，用于接收对其所发出请求的响应（无论是否被 nack）。
该端口有两个公有方法：`dmaPending()`，返回 dma 端口是否忙碌（例如它仍在尝试把上一个请求的所有片段发送出去）。
把所有代码用于把请求切分成合适大小的块、收集可能存在的多个响应并响应设备，都是通过 `dmaAction()` 完成的。
向该函数传入命令、起始地址、大小、完成事件以及可能的数据，它会在请求完成后执行完成事件的 `process()` 方法。
内部代码使用 `DmaReqState` 来管理它已收到哪些块，并判断何时执行完成事件。

### DmaDevice

这是 DMA 非 PCI 设备会继承的基类，不过目前 M5 中并不存在这类设备。该类有一些方法 `dmaWrite()`、`dmaRead()`，用于从 DMA 读或写操作中选择相应的命令。

### NIC 设备

gem5 模拟器（simulator）有两种不同的网络接口卡（Network Interface Card，NIC）设备，可用于通过模拟的以太网链路把两个模拟实例连接在一起。

#### 获取以太网链路上的数据包列表

你可以通过创建一个 Etherdump 对象、设置它的 file 参数，并把 EtherLink 上的 dump 参数设为该对象，来获取以太网链路上的数据包列表。
用我们的 fs.py 示例配置很容易做到这一点，只需加上命令
行选项 \-\-etherdump=\<filename\>。生成的文件将以 \<file\> 命名，并采用标准 pcap 格式。
该文件可以用 [wireshark](https://www.wireshark.org/) 或任何其他理解 pcap 格式的工具读取。


### PCI 设备
```
To do: Explanation of platforms and systems, how they’re related, and what they’re each for
```

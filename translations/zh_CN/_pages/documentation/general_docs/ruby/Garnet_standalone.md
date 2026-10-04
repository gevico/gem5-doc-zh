---
layout: documentation
title: "Garnet standalone"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/Garnet_standalone/
author: Jason Lowe-Power
---

# Garnet 独立模式（Garnet Standalone）

这是一个哑元缓存一致性协议，用于以独立方式运行 Garnet。
该协议与 [Garnet 合成流量]({{ site.baseurl }}/documentation/general_docs/ruby/garnet_synthetic_traffic)
注入器配合使用。

### 相关文件

  - **src/mem/protocols**
      - **Garnet_standalone-cache.sm**：缓存控制器规范
      - **Garnet_standalone-dir.sm**：目录控制器
        规范
      - **Garnet_standalone-msg.sm**：消息类型规范
      - **Garnet_standalone.slicc**：容器文件

### 缓存层次结构

该协议假定单级缓存层次结构。缓存的作用只是把消息从
cpu 发送到合适的目录（依据地址）和合适的虚拟网络（依据
消息类型）。它不跟踪任何状态。事实上，与其他协议不同，它不会
创建任何 CacheMemory。目录接收来自
缓存的消息，但不回送任何消息。该协议的目标是
支持仅对互连网络进行模拟/测试。

### 稳定状态与不变式

| 状态   | 不变式                        |
| ------ | --------------------------------- |
| **I**  | 所有缓存块的默认状态 |

### 缓存控制器

  - 请求、响应、触发：
      - 来自核心的 Load、Instruction fetch、Store。

网络测试器（在 src/cpu/testers/networktest/networktest.cc 中）
生成 **ReadReq**、**INST_FETCH** 和
**WriteReq** 类型的数据包，RubyPort（在 src/mem/ruby/system/RubyPort.hh/cc 中）把它们分别转换为 **RubyRequestType:LD**、
**RubyRequestType:IFETCH** 和 **RubyRequestType:ST**。这些消息
经 Sequencer 到达缓存控制器。这些
消息的目的地由流量类型决定，并嵌入在地址中。
更多细节见[此处]({{ site.baseurl }}/documentation/general_docs/debugging_and_testing/directed_testers/ruby_random_tester)。

  - 主要操作：
      - 缓存的作用只是充当底层互连网络中的源节点。
        它不跟踪任何状态。
      - 当收到来自核心的 **LD** 时：
          - 它返回命中，并且
          - 把地址映射到一个目录，并为它发出类型为 **MSG**、大小为 **Control**（8 字节）的消息，
            放在请求 vnet（0）中。
          - 注意：通过取消注释 Network_test-cache.sm 中 *a_issueRequest*
            动作里相应的行，也可以让 vnet 0 广播，
            而不是向某个特定目录发送定向消息
      - 当收到来自核心的 **IFETCH** 时：
          - 它返回命中，并且
          - 把地址映射到一个目录，并为它发出类型为 **MSG**、大小为 **Control**（8 字节）的消息，
            放在转发 vnet（1）中。
      - 当收到来自核心的 **ST** 时：
          - 它返回命中，并且
          - 把地址映射到一个目录，并为它发出类型为 **MSG**、大小为 **Data**（72 字节）的消息，
            放在响应 vnet（2）中。
      - 注意：请求、转发和响应只是用来
        区分各个 vnet，在该协议中没有任何物理
        意义。

### 目录控制器

  - 请求、响应、触发：
      - 来自各核心的 **MSG**

  - 主要操作：
      - 目录的作用只是充当底层互连网络中的目的节点。
        它不跟踪任何状态。
      - 目录在收到消息时直接把其到来队列弹出。

### 其他特性

   该协议只假定 3 个 vnet。
  - 只应在运行 [Garnet 合成
        流量]({{ site.baseurl }}/documentation/general_docs/ruby/garnet_synthetic_traffic)时使用它。

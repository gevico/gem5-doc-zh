---
layout: documentation
title: "MI example"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/MI_example/
author: Jason Lowe-Power
---

# MI 示例

### 协议概述

  - 这是一个简单的缓存一致性（cache coherence）协议，用于说明
    如何用 SLICC 编写协议规范。
  - 该协议假定单级缓存层次结构。缓存对
    每个节点都是私有的。缓存由目录
    控制器保持一致。由于层次结构只有一级，因此没有
    包含/排他（inclusion/exclusion）要求。
  - 该协议不区分加载与存储。
  - 该协议无法实现 LL/SC 指令的语义，
    因为命中 LL/SC 序列内某个块的外部 GETS 请求会
    夺走独占权限，从而导致 SC
    指令失败。

### 相关文件

  - **src/mem/protocols**
      - **MI_example-cache.sm**：缓存控制器规范
      - **MI_example-dir.sm**：目录控制器规范
      - **MI_example-dma.sm**：dma 控制器规范
      - **MI_example-msg.sm**：消息类型规范
      - **MI_example.slicc**：容器文件

### 稳定状态与不变式

| 状态   | 不变式                                                                                                       |
| ------ | ------------------------------------------------------------------------------------------------------------ |
| **M**  | 该缓存块已被本节点访问过（读/写）。没有其他节点持有该缓存块的副本                                             |
| **I**  | 本节点上的该缓存块无效                                                                                        |

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。**

### 缓存控制器

  - 请求、响应、触发：
      - 来自核心的 Load、Instruction fetch、Store
      - 来自自身的 Replacement
      - 来自目录控制器的 Data
      - 来自目录控制器的转发请求（intervention）
      - 来自目录控制器的回写确认
      - 来自目录控制器的失效（在 dma 活动时）

![MI_example_cache_FSM.jpg](/assets/img/MI_example_cache_FSM.jpg
"MI_example_cache_FSM.jpg")

  - 主要操作：
      - 当收到来自核心的 **load/Instruction fetch/Store** 请求时：
          - 它检查对应的块是否处于
            M 状态。若是，则返回命中
          - 否则，如果处于 I 状态，它就向
            目录控制器发起 GETX 请求

     - 当收到来自自身的 **replacement** 触发时：
          - 它逐出该块，并向
            目录控制器发出回写请求
          - 它等待目录控制器的确认
            （以避免竞态）

     - 当收到来自目录控制器的**转发请求**时：
          - 这意味着当其他节点生成该请求时，该块
            在本节点处于 M 状态
          - 它把该块直接发送给请求节点
            （缓存到缓存的传输）
          - 它从本节点逐出该块

     - **失效（Invalidation）**与替换类似

### 目录控制器

  - 请求、响应、触发：
      - 来自各核心的 GETX，发往各核心的 Forwarded GETX
      - 来自内存的 Data，发往各核心的 Data
      - 来自各核心的回写请求，发往
        各核心的回写确认
      - 来自 DMA 控制器的 DMA 读、写请求

![MI_example_dir_FSM.jpg](/assets/img/MI_example_dir_FSM.jpg
"MI_example_dir_FSM.jpg")

  - 主要操作：
      - 目录跟踪哪个核心以 M
        状态持有某个块。它把该核心指定为该块的所有者（owner）。
      - 当收到来自某个核心的 **GETX** 请求时：
          - 如果该块不存在，则发起内存取数据请求
          - 如果该块已存在，那么意味着该请求
            来自其他某个核心
              - 在这种情况下，会向原所有者
                发送转发请求
              - 该块的所有权被转移给请求者
      - 当收到来自某个核心的**回写**请求时：
          - 如果该核心是所有者，数据会被写入内存，
            并向该核心发送确认
          - 如果该核心不是所有者，则回送 NACK
              - 这可能发生在竞态条件下
              - 该核心在另一个核心的转发请求
                还在途中时逐出了该块，而目录
                已经把所有权改给了该核心
              - 逐出该块的核心会保留数据，直到转发
                请求到达
      - 当收到 **DMA** 访问（读/写）时
          - 会向所有者节点发送失效（如果有）。否则
            从内存取数据。
          - 这确保可用的数据是最新的。

### 其他特性

  - MI 协议不支持 LL/SC 语义。来自远程
        核心的加载会使该缓存块失效。
  - 该协议没有任何超时机制。

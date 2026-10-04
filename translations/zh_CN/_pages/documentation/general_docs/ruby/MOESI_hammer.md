---
layout: documentation
title: "MOESI hammer"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/MOESI_hammer/
author: Jason Lowe-Power
---

# MOESI Hammer

这是 AMD Hammer 协议的一个实现，该协议用于
AMD 的 Hammer 芯片（也称为 Opteron 或 Athlon 64）。该协议
既实现了最初的 HyperTransport 协议，也实现了
更新的 ProbeFilter 协议。该协议还包括全位
目录（full-bit directory）模式。

### 相关文件

  - **src/mem/protocols**
      - **MOESI_hammer-cache.sm**：缓存控制器规范
      - **MOESI_hammer-dir.sm**：目录控制器规范
      - **MOESI_hammer-dma.sm**：dma 控制器规范
      - **MOESI_hammer-msg.sm**：消息类型规范
      - **MOESI_hammer.slicc**：容器文件

### 缓存层次结构

该协议实现两级私有缓存层次结构。它为每个
核心分配独立的指令 L1 缓存、数据 L1 缓存以及统一的 L2 缓存。这些缓存对每个核心都是私有的，
并由同一个共享缓存控制器控制。该协议在 L1 与
L2 缓存之间强制排他（exclusion）
关系。

### 稳定状态与不变式

| 状态   | 不变式                                                                                                                                                                                                          |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MM** | 该缓存块由本节点独占持有，并且可能在本地已被修改（类似传统的 "M" 状态）。                                                                                           |
| **O**  | 该缓存块归本节点所有。它未被本节点修改。没有其他节点以独占模式持有该块，但可能存在共享者。                                                      |
| **M**  | 该缓存块以独占模式持有，但尚未写入（类似传统的 "E" 状态）。没有其他节点持有该块的副本。该状态下不允许存储。                                  |
| **S**  | 该缓存行持有数据最新、正确的副本。系统中的其他处理器也可能以共享状态持有该数据的副本。该状态下该缓存行可以读取，但不能写入。 |
| **I**  | 该缓存行无效，不持有数据的有效副本。                                                                                                                                               |

### 缓存控制器

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。**

MOESI_hammer 支持缓存刷写。要刷写一个缓存行，缓存
控制器首先向目录发出 GETF 请求以阻塞该
行直到刷写完成，然后发出 PUTF 并
回写该缓存行。

![MOESI_hammer_cache_FSM.jpg](/assets/img/MOESI_hammer_cache_FSM.jpg
"MOESI_hammer_cache_FSM.jpg")

### 目录控制器

与典型的目录协议不同，MOESI_hammer 的内存模块
不包含任何目录状态，而是把请求广播给系统中的
所有处理器。同时，它从
DRAM 取数据并把响应转发给请求者。

probe filter：待补充

#### **稳定状态与不变式**

| 状态   | 不变式                                                               |
| ------ | -------------------------------------------------------------------- |
| **NX** | 非所有者，存在 probe filter 条目，块在所有者处处于 O。               |
| **NO** | 非所有者，存在 probe filter 条目，块在所有者处处于 E/M。             |
| **S**  | 数据干净，存在指向当前所有者的 probe filter 条目。                   |
| **O**  | 数据干净，存在 probe filter 条目。                                   |
| **E**  | 独占所有者，无 probe filter 条目。                                   |

#### **控制器**

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。**

![MOESI_hammer_dir_FSM.jpg](/assets/img/MOESI_hammer_dir_FSM.jpg
"MOESI_hammer_dir_FSM.jpg")

---
layout: documentation
title: "Ruby 简介"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/MSIintro/
author: Jason Lowe-Power
---

## Ruby 简介

Ruby 源自 [Multifacet GEMS 项目](http://research.cs.wisc.edu/gems/)，提供详细的缓存（cache）、缓存一致性（cache coherence）模型，以及详细的网络模型 Garnet。

Ruby 很灵活，可以描述广播式、目录式、基于令牌、基于区域等多种一致性实现，也便于扩展新的模型。

在许多配置中，Ruby 可以替换经典内存系统（memory system）。gem5 的经典 MemObject 与 Ruby 之间提供了接口，但总体而言，经典缓存（cache）与 Ruby 不能直接混用。

本部分将从协议（protocol）描述出发，逐步完成一个示例，包括实现、调试和运行。

开始之前，先了解 Ruby 的基本结构。最重要的组成部分是控制器，也称状态机（state machine）。控制器通过 SLICC 状态机（state machine）文件实现。

SLICC 是描述一致性协议（protocol）的领域专用语言，全称为 Specification Language including Cache Coherence。文件以 `.sm` 结尾，表示它们是*状态机（state machine）*文件。每个文件描述状态、某个事件触发时从起始状态到结束状态的转换，以及转换中执行的动作。

每个一致性协议（protocol）包含多个 SLICC 文件。gem5 源码中用 Python 编写的 SLICC 编译器，将它们转换成一组生成文件，包括 SimObject 声明、SimObject 的 C++ 实现和其他 C++ 对象的实现。生成的 C++ 文件随后与 gem5 的其余源码一起编译。

本教程采用一次编译一种一致性协议（protocol）的构建方式。例如，可以编译性能较低的示例 `MI_example`，也可以选择 `MESI_Two_Level`。切换到 `MESI_Two_Level` 时，需要重新构建，让 SLICC 生成对应的代码。[编译章节]({{ site.baseurl }}/documentation/learning_gem5/part3/MSIbuilding/)会进一步说明。

> **译注**：原文把 `MI_example` 称为默认协议（protocol），并称 gem5 一次只能编译一种；这些描述对应旧版构建方式。较新版本可支持在一个构建中启用多种协议（protocol），默认配置也可能不同，应以所用版本的构建配置为准。

下面开始实现第一个一致性协议（protocol）。

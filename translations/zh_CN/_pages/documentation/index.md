---
layout: documentation
title: gem5 文档
doc: gem5 文档
parent: gem5_documentation
permalink: /documentation/
author: Jason Lowe-Power
---

# gem5 文档

## gem5 Bootcamp 2024

自 gem5 v24.0 起，学习如何使用 gem5 最全面、最新的指南是
[2024 年夏季 gem5 bootcamp](https://bootcamp.gem5.org/) 的材料。

## 学习 gem5

**注意：Learning gem5 的许多部分已经过时。其中一些章节已根据 2024 年 gem5 bootcamp 的内容针对 gem5 v24.1 更新，但其他章节尚未更新。请谨慎使用！**

[Learning gem5](learning_gem5/introduction/) 由 Jason Lowe-Power 撰写，以较大篇幅介绍如何使用 gem5 开展计算机体系结构研究。
对于打算在研究项目中大量使用 gem5 的初级研究者来说，这是一个极好的资源。

它从[如何创建配置脚本](learning_gem5/part1/simple_config)开始，介绍 gem5 的工作细节。
接着介绍如何[修改和扩展](learning_gem5/part2/environment) gem5 以用于你的研究，包括[创建 `SimObject`](learning_gem5/part2/helloobject)、[使用 gem5 的事件驱动（event-driven）模拟基础设施](learning_gem5/part2/events)，以及[添加内存系统对象](learning_gem5/part2/memoryobject)。
在 [Learning gem5 第三部分](learning_gem5/part3/MSIintro)中，详细讨论了 [Ruby 缓存一致性（cache coherence）模型]({{ site.baseurl }}/documentation/general_docs/ruby)，包括一个完整的 MSI 缓存一致性协议实现。

Learning gem5 还会陆续推出更多部分，包括：
* CPU 模型与指令集架构（ISA）
* 调试 gem5
* **你的想法可以写在这里！**

注意：这部分内容是从 learning.gem5.org 迁移过来的，因此迁移带来了一些小问题（例如链接缺失、格式不佳）。
如果发现任何错误，请联系 Jason（jason@lowepower.com）或创建一个 PR！

## gem5 101

[gem5 101](learning_gem5/gem5_101) 是一组作业，大多来自威斯康星大学的研究生计算机体系结构课程（CS 752、CS 757 和 CS 758），可帮助你学会用 gem5 做研究。

## gem5 API 文档

基于 doxygen 的文档见：<http://doxygen.gem5.org/release/current/index.html>

## 其他 gem5 通用文档

请查看页面左侧的导航！

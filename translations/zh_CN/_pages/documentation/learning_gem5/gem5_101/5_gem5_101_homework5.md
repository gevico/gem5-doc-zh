---
layout: documentation
title: "作业 5"
doc: 学习 gem5
parent: gem5_101
permalink: /documentation/learning_gem5/gem5_101/homework-5
authors:
---

# CS 752 作业 5：高级计算机体系结构（architecture）I（2015 年秋季，唯一班级）

**截止日期：10 月 28 日，星期三。**

**独立完成，不接受迟交。**

原课程联系人：Nilay Vaish，<nilay@cs.wisc.edu>。

本作业有两个目标：练习创建新的 SimObject，并研究缓存（cache）设计的权衡。

原文提供更新的 `caches.py`，用于替换[上次作业配置包](https://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4-configs.tar.gz)中的配置文件。

> **译注**：本页为历史作业，原文的 `{$urlbase}` 未展开。已根据课程地址恢复可用链接；更新文件的历史地址为 `https://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw5/caches.py`，翻译时返回 HTTP 403，无法验证内容。原文交替使用 `cache.py` 与 `caches.py`，应以取得的实际文件名为准。

## 第一步：实现 NMRU 替换策略（replacement policy）

参考[原课程教程](http://pages.cs.wisc.edu/~david/courses/cs752/Spring2015/gem5-tutorial/index.html)，其第二部分介绍如何创建 NMRU 策略。

## 第二步：实现 PLRU 替换策略（replacement policy）

遵循与实现 NMRU 类似的步骤，改为实现伪 LRU。它使用二叉树记录一组中哪些块相对更久未被使用。Mikko Lipasti 的[课程幻灯片](https://ece752.ece.wisc.edu/lect11-cache-replacement.pdf)解释了该算法。

> **译注**：原文这一段写成 `NRU`，根据第一步和后面的选项，应指 `NMRU`。两者并非可以任意互换的名称。

## 第三步：探索体系结构（architecture）设计

假想公司 Entil 的 CEO 请你为基于乱序（out-of-order）`O3CPU` 的新处理器设计 L1 数据缓存（cache）。营销负责人称，大多数客户的工作负载（workload）集中在矩阵乘法核心计算上。由于这类计算访存密集，Entil 希望通过更好的设计超过竞争对手 AMM，即 Advanced Micro Machines。

下载[分块矩阵乘法实现](https://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw5/mm.cpp)，使用 128×128 的输入矩阵，即 `./mm 128`。

L1D 可选 `Random`、`NMRU` 和 `PLRU` 三种替换策略（replacement policy）。本题假设：随着相联度增加，NMRU 和 PLRU 的成本上升，而 Random 的成本不变，因此 Random 可以采用更高相联度。此外，NMRU 和 PLRU 需要更新访问标签中的最近使用信息，限制 CPU 时钟频率。本题假设这一代 O3 CPU 的最高频率为 2.3 GHz。

约束如下：

| 约束 | Random | NMRU | PLRU |
| --- | --- | --- | --- |
| 最大相联度 | 16 | 8 | 8 |
| 查找时间 | 100 ps | 500 ps | 666 ps |

给 Entil CEO 写一页备忘录，说明全部实验配置、模拟（simulation）结果，以及最终推荐的 L1 数据缓存（cache）设计。还应回答：

- 16 路组相联比 8 路表现更好、更差或相近，原因是什么？
- Random、NMRU、PLRU 中哪种更好，还是没有明显优胜者？为什么？
- 对此工作负载（workload），替换方式与相联度是否重要，还是收益主要来自时钟周期变化？解释设计为何重要或不重要。

## 提交内容

原课程要求发送邮件给 Nilay Vaish <nilay@cs.wisc.edu> 和 David Wood 教授 <david@cs.wisc.edu>，主题为 `[CS752 Homework5]`。

1. 写明姓名与学号，以下文件打包为 zip 附件。
2. 包含全部 gem5 修改的补丁。
3. 所有实验的 `stats.txt` 和 `config.ini`。
4. 回答上述问题的简短 PDF 报告。

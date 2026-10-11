---
layout: documentation
title: "作业 4"
doc: 学习 gem5
parent: gem5_101
permalink: /documentation/learning_gem5/gem5_101/homework-4
authors:
---

# CS 752 作业 4：高级计算机体系结构（architecture）I（2015 年秋季，唯一班级）

**原文截止日期：10 月 7 日，星期一。**

**独立完成，不接受迟交。**

原课程联系人：**Nilay Vaish**，<nilay@cs.wisc.edu>。

> **译注**：本页为历史作业。原文日期存在矛盾：2015 年 10 月 7 日实际为星期三，以上保留原记录。

作者于 2015 年 9 月 28 日提出本作业，因此它带有探索性质，研究利用指令级并行的两种方式：分支预测与谓词执行。

考虑以下代码：

```cpp
  if (x < y)
     x = y;
```

至少可以生成两种汇编实现。

1. 使用分支：

```
    compare x, y
    jump if not less L
    move x, y
  L:
```

2. 使用条件移动：

```
  compare x, y
  conditionally move x to y.
```

应该选择哪一种？本作业通过实验加深理解。

## 实验步骤

1. 阅读 Linux 创建者和维护者 Linus Torvalds 关于 `cmov` 的[讨论](http://yarchive.net/comp/linux/cmov.html)。其中提供了比较分支与条件移动性能的 C 程序。在你选择的 x86 处理器上运行两个版本的 `choose()`，每个至少运行 10 次，报告平均时间和标准差。如果波动很大，增加迭代次数，通常有助于稳定结果。

2. 在 gem5 中使用默认配置的乱序（out-of-order）处理器运行相同的两个版本。把迭代次数降到 1,000,000，因为 100,000,000 对模拟器（simulator）而言过多。报告哪种实现更快，以及预测的分支总数和预测错误数。

----

3. SPAA 2015 的一篇[避免分支的算法论文](http://dl.acm.org/citation.cfm?id=2755580)提出，减少分支的图算法可能优于使用分支的实现。下面检验这一观点。

论文给出无向图连通分量算法的两个版本：一个使用分支，另一个使用条件移动。作者实现了两者，但条件移动版本无法仅靠其尝试的内联汇编顺利完成，因此修改了生成的汇编。作业提供 [C++11 源码](http://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4/connected-components.cpp)、[汇编代码](http://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4/connected-components.s)和[静态可执行文件](http://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4/connected-components)。直接编译 C++11 源码不能精确复现这份汇编和可执行文件，因为其中的 `cmov` 部分经过手动修改。

输入数据包括[小图](http://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4/small.graph)、[中图](http://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4/medium.graph)和[大图](http://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/hw4/large.graph.gz)。阅读源码，了解如何传入运行选项。

- **a.** 在真实 x86 处理器上运行两个版本，只使用大图。按第一步要求报告耗时的均值与标准差。
- **b.** 在 gem5 中运行两个版本，只使用小图和中图。统计代码标记区间的性能、预测分支数及错误预测百分比，并提供第二步要求的数据。

## 提交内容

原课程要求发送邮件给 Nilay Vaish <nilay@cs.wisc.edu> 和 David Wood 教授 <david@cs.wisc.edu>，主题为 `[CS752 Homework4]`。

**提交一个 PDF 文件**，包含第一、第二、第三步所有问题的答案。

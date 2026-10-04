---
layout: documentation
title: "Visualization"
doc: gem5 文档
parent: cpu_models
permalink: /documentation/general_docs/cpu_models/visualization/
---

# 可视化
本页介绍各类已集成到 gem5 中、或可与 gem5 配合使用的信息可视化方式。

## O3 流水线查看器
o3 流水线查看器是一个基于文本的乱序（out-of-order）CPU 流水线查看器。它显示指令何时被取指（f）、译码（d）、重命名（n）、分派（p）、发射（i）、完成（c）和退休（r）。对于理解一段不太长的代码序列中流水线在何处停顿或清空，它非常有用。在会换行的彩色视图旁边，显示当前指令退休的 tick、该指令的 pc、其反汇编，以及该指令的 o3 序列号。

![o3pipeviewer]({{ site.baseurl }}/assets/img/O3pipeview.png)

要生成你在上面看到的那种输出行，首先需要用 o3 cpu 运行一次实验：

```./build/ARM/gem5.opt --debug-flags=O3PipeView --debug-start=<first tick of interest> --debug-file=trace.out configs/example/se.py --cpu-type=detailed --caches -c <path to binary> -m <last cycle of interest>```

然后你可以运行脚本来生成类似上面的跟踪（trace）（此例中 500 是每个时钟（2GHz）的 tick 数）：

```./util/o3-pipeview.py -c 500 -o pipeview.out --color m5out/trace.out```

你可以通过把文件交给 less 来以彩色查看输出：

```less -r pipeview.out```

当 CYCLE_TIME（-c）设置错误时，输出中的右方括号可能不会对齐到同一列。CYCLE_TIME 的默认值是 1000。请注意。

该脚本还有一些内置帮助：（输入 ‘./util/o3-pipeview.py --help’ 查看帮助）。

## Minor 查看器
关于 minor 查看器的新页面（minor_view）尚未创建，其文档请参阅[旧页面](http://pages.cs.wisc.edu/~swilson/gem5-docs/minor.html#trace)。

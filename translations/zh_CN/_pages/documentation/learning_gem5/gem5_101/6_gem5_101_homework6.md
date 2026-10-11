---
layout: documentation
title: "作业 6"
doc: 学习 gem5
parent: gem5_101
permalink: /documentation/learning_gem5/gem5_101/homework-6
authors:
---

# CS 758：多核处理器编程（2013 年秋季，唯一班级）

**GPU 作业日期：10 月 30 日。**

**独立完成，不接受迟交。**

> **译注**：仓库（repository）实际收录的是 CUDA/GPGPU 课程作业，与 gem5 101 总览中第六部分的多核全系统（full-system）实验介绍不一致。本页按实际原文翻译。集群访问方法、CUDA 5.5 工具及提交要求属于 2013 年课程背景。

作业文件与资料：

- [模板文件](https://pages.cs.wisc.edu/~david/courses/cs758/Fall2013/handouts/homeworks/hw6-dist.tgz)
- Euler 集群使用入门：原文件为 `http://wacc.wisc.edu/documentation/EulerWalkthrough.pdf`，翻译时该域名已无法解析。

本作业帮助你熟悉 CUDA 通用 GPU 计算平台，并练习 GPU 专用优化。给定一个能在 GPU 上运行的基础算法实现，逐步应用优化原则改进它。

**提示：** CUDA 出错时，诊断信息可能晦涩且不充分，建议尽早开始。原课程要求遇到问题时在课程邮件列表讨论。

## 问题

再次实现 Ocean 算法，将 GPU 优化版本与作业 1 的实现比较。模板中也提供了作业 1 的简单实现，可以使用。

## 硬件

原课程使用 Euler 集群，通过邮件分配用户名与临时密码，并要求及时修改密码。硬件配置见上面的集群教程。

## 提交运行任务

作业最初通过 Torque 队列运行，后来改为直接在 `euler01` 上运行。原操作步骤如下：

```sh
local $ ssh user@euler.wacc.wisc.edu
euler $ ssh euler01
euler01 $ scp <username>@ale-01.cs.wisc.edu:/p/course/cs758-david/public/html/Fall2013/handouts/homeworks/hw6-dist.tgz .
euler01 $ tar -x -f hw6-dist.tgz
euler01 $ mv hw4-dist hw6
euler01 $ cd hw6
euler01 $ make
euler01 $ ./serial_ocean.sh
```

原文建议让代码尽快结束，不要长时间保持 `cuda-gdb` 打开，因为当时发现过它阻碍其他 GPU 访问的缺陷。

原集群硬件资料介绍了可用设备，但上方所列历史链接现已失效。作业使用 Fermi 系列 Tesla 2070/2050 或 GTX 480。原文将它们统一写为 448 个 CUDA 核心、14 个 SM。

> **译注**：Tesla C2050/C2070 为 448 个 CUDA 核心、14 个 SM；GTX 480 通常为 480 个核心、15 个 SM，原文对此有误。后文比较题中的 448 也应结合实际设备理解。

CUDA 5.5 随附的 `computeprof` 可汇总 NVIDIA GPU 性能计数器。原文建议通过 `ssh -X` 登录以转发 X 图形界面，再运行 `/usr/local/cuda/5.5.22/cuda/bin/computeprof`；在校内网络使用可获得更高带宽。可以用它定位各实现的性能瓶颈。

## 补充资料

原课程同期，Dan Negrut 开设 GPU Computing（ME964），原文提供了课程页面 `http://sbel.wisc.edu/Courses/ME964/2013/` 与[问答论坛](http://sbel.wisc.edu/Forum/viewforum.php?f=15)。前者在翻译时返回 HTTP 404，可从 [SBEL 网站](https://sbel.wisc.edu/)查找现有资料；原课程页面内容未在本仓库（repository）中保存。

## 第一步：移植 CPU 算法

[模板文件](https://pages.cs.wisc.edu/~david/courses/cs758/Fall2013/handouts/homeworks/hw6-dist.tgz)中的 `cuda_ocean_kernels.cu` 在 `#ifdef VERSION1` 后提供 `ocean_kernel`。它虽然更冗长，但基本上直接移植了 `omp_ocean.c` 中采用 OpenMP 静态划分的算法。每个线程负责红黑 Ocean 网格中的一片位置，并更新这些位置。阅读代码，理解其工作方式。

> **译注**：原文此处链接写作 `hw4-dist.tgz`，但该资源不存在。已核对可用的 `hw6-dist.tgz`，其中确实包含 `cuda_ocean_kernels.cu` 和 `omp_ocean.c`；压缩包内部目录仍名为 `hw4-dist`。原文内联标识符周围的 `@@` 是旧 wiki 格式残留，本页已去除。

- **a.** 解释访存分歧（memory divergence），以及它为何会降低 SIMT 模型下的性能。
- **b.** 描述 `ocean_kernel` 的 `VERSION1` 中的访存分歧。
- **c.** 改变线程块和网格大小，找出最佳配置；相对于一个线程块、一个线程的“单线程”实现，加速比是多少？输入为 `4098 4098 100`。
- **d.** 相对于单线程 CPU 实现，加速比是多少？输入同样为 `4098 4098 100`。

## 第二步：减少访存分歧，将算法改为“SIMD”式访问

实现 `ocean_kernel` 的 `VERSION2`。不再让每个线程独立负责一整片数组，而是让同一线程块内的线程处理相邻位置。例如红色迭代中，线程 0 处理元素 0，线程 1 处理元素 2，线程 3 处理元素 6，依此类推。

- **a.** 该实现还在哪些地方存在访存分歧？
- **b.** 改变线程块和网格大小，找出最佳配置。
- **c.** 与 `VERSION1` 比较，两者各自采用最佳线程块配置，输入为 `4098 4098 100`。

## 第三步：调整数据结构，进一步减少访存分歧

实现 `ocean_kernel` 的 `VERSION3`。不再用一个平面数组表示整个网格，而是拆成红色单元数组和黑色单元数组。先编写两个辅助核函数，分别把 `grid` 拆成 `red_grid`、`black_grid`，以及把两者重新合并回 `grid`。

也可以尝试其他优化，但需要在报告中说明。

- **a.** 与 `VERSION2` 相比，性能如何？符合预期吗？
- **b.** 分别测量各核函数和内存复制的时间，包括 `ocean_kernel`、拆分与合并数组的核函数。哪些操作占时最多？如何影响整体耗时？`computeprof` 可帮助汇总。
- **c.** 改变线程块和网格大小，找出最佳配置。问题规模变化时，最佳配置会变吗？
- **d.** 解释分支分歧（branch divergence），以及它为何会降低 SIMT 性能。你的实现是否存在分支分歧，出现在哪里？
- **e.** Euler 每个节点有两个 Intel Xeon E5520 处理器；按原题给定的 GPU 核心数，你预期 GPU 与 CPU 的性能如何比较？设备规格差异见前面的译注。
- **f.** 运行自己的 OpenMP 版本或模板提供的版本，比较 CPU 与 GPU 哪个更快，并解释原因。用 `omp_ocean.sh` 运行 OpenMP 版本，问题规模分别取 1026、2050、4098 和 8194，每次 100 个时间步。
- **g.** 你如何评价 CUDA，以及更一般的 SIMT 编程方式？

## 建议

- 尽早开始。
- 原课程的计算资源由 Dan Negrut 教授提供，请体谅共享资源的使用者。

## 提交内容

原课程要求在上课开始时提交**纸质**作业，包含：

- GPU 核函数的打印件。
- 所有问题的答案及相应图表。

**每页都要写上姓名。**

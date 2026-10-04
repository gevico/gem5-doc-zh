---
layout: documentation
title: "Compiling Workloads"
doc: gem5 文档
parent: compiling_workloads
permalink: /documentation/general_docs/compiling_workloads/
author: "Hoa Nguyen"
---

# 编译工作负载（workload）

## 交叉编译器

交叉编译器是指在一套指令集架构（ISA）上运行、但生成在另一套指令集架构上运行的可执行文件的编译器。
如果你想模拟使用某种特定指令集架构（例如 Alpha）的系统，却又无法访问真正的 Alpha 硬件，就可能需要交叉编译器。

交叉编译器有多种来源，以下是其中一些。

1. [ARM](https://packages.debian.org/stretch/gcc-arm-linux-gnueabihf)。
2. [RISC-V](https://github.com/riscv/riscv-gnu-toolchain)。

## QEMU

另一种选择是使用 QEMU 和磁盘镜像，在模拟（emulation）中运行所需的指令集架构。
要创建更新的磁盘镜像，请参见[这一页]({{ site.baseurl }}/documentation/general_docs/fullsystem/disk)。
下面是一段在 Ubuntu 12.04 64 位下用 qemu 处理镜像文件的 YouTube 视频。
<iframe width="560" height="315" src="https://www.youtube.com/embed/Oh3NK12fnbg" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

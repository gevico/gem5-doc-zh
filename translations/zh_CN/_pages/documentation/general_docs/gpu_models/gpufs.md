---
layout: documentation
title: 全系统（full-system）AMD GPU 模型
doc: gem5 文档
parent: gpu_models
permalink: /documentation/general_docs/gpu_models/gpufs
---

# **全系统（full-system）AMD GPU 模型**

全系统（Full System）AMD GPU 模型在 "gfx9" 指令集架构（ISA）层面（而不是中间语言层面）模拟 GPU。本页将概述如何使用该模型、该模型使用的软件栈，并提供详述该模型及其实现方式的资源。**建议使用 Full System 而不是 System Emulation，因为 Full System 支持最新版本的 GPU 软件栈。**

## 需求

全系统（Full System）GPU 模型主要设计用于在不做修改的情况下、以原生软件栈模拟独立 GPU（discrete GPU）。这意味着模拟中的 CPU 部分并未配置为详细模拟 —— 只有 GPU 是详细的。[ROCm 软件栈](https://rocm.docs.amd.com/en/latest/)把使用范围限制在 [ROCm 文档](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html)中列出的官方支持的 gfx9 设备上。目前 gem5 提供 Vega10（gfx900）、MI210/MI250X（gfx90a）和 MI300X（gfx942）的配置。

*注意：* 旧版 ROCm 中先前支持的 "gfx9" 设备在大多数情况下仍然可用（gfx900、gfx906）。正如 ROCm 文档所述，对于预构建的 ROCm 库，这些设备可能导致运行时错误。

CPU 部分的代码最好使用 KVM CPU 模型进行快进。由于该软件栈是 x86 的，你需要一台启用了 KVM 的 x86 Linux 宿主机（host）才能高效运行 Full System。在非 x86 宿主机上或 KVM 不可用时，也可以使用 atomic CPU。细节见[不使用 KVM 运行](#Running-without-kvm)一节。

## **使用该模型**

本指南中有若干处假定 gem5 和 gem5-resources 位于同一个基础目录下。

[gem5 仓库](https://github.com/gem5/gem5)包含 GPU 模型的基础代码。
[gem5-resources 仓库](https://github.com/gem5/gem5-resources/)包含为 Full System 创建磁盘镜像所需的文件，并附带若干可用于上手该模型的示例应用。我们建议用户从 [square](https://resources.gem5.org/resources/square) 开始，因为它简单、经过大量测试，并且运行速度相对较快。

#### 构建 gem5

GPU 模型需要 GPU_VIPER 缓存一致性（cache coherence）协议，该协议在 Ruby 中实现，而 Full System 软件栈只在被模拟的 X86 环境中受支持。VEGA_X86 构建选项使用 GPU_VIPER 协议和 x86。因此，必须使用 VEGA_X86 构建选项构建 gem5：

```
scons build/VEGA_X86/gem5.opt
```

Full System GPU 模型构建方式与仅 CPU 版本的 gem5 类似。关于如何构建 gem5（包括构建线程数、链接器选项和 gem5 二进制目标）请参考[构建 gem5](https://www.gem5.org/documentation/general_docs/building) 文档。

#### 构建磁盘镜像与内核

与仅 CPU 版本的 gem5 一样，Full System GPU 模型也需要磁盘镜像和内核才能运行。[gem5-resources 仓库](https://github.com/gem5/gem5-resources/)提供了一个一步式磁盘镜像构建器，用于创建装有所需全部软件的 GPU 模型磁盘镜像。

在已克隆 gem5 和 gem5-resources 的基础目录下，进入 [gem5-resources/src/x86-ubuntu-gpu-ml](https://github.com/gem5/gem5-resources/tree/stable/src/x86-ubuntu-gpu-ml)。该目录包含一个可一步创建磁盘镜像的文件 `./build.sh`。构建磁盘依赖 [packer](https://www.packer.io/) 工具，而 packer 以后端方式使用 [QEMU](https://www.qemu.org/)。排障请参见 [BUILDING.md](https://github.com/gem5/gem5-resources/blob/stable/src/x86-ubuntu-gpu-ml/BUILDING.md) 指南。通常，可以用以下命令一步创建磁盘镜像：

```
./build.sh
```

该过程大约需要 15-20 分钟，且主要受下载速度限制，因为大部分时间花在下载 Ubuntu 软件包上。

构建磁盘镜像的同时也会提取 Linux 内核。提取出的 Linux 内核*必须*与该磁盘镜像搭配使用。换句话说，你不能给 gem5 传入任意内核，否则 GPU 驱动可能无法成功加载。

该过程完成后，你的环境中应包含：
* 磁盘镜像：`gem5-resources/src/x86-ubuntu-gpu-ml/disk-image/x86-ubuntu-gpu-ml`
* 内核：`gem5-resources/src/x86-ubuntu-gpu-ml/vmlinux-gpu-ml`

#### 构建 GPU 应用

GPU 模型设计用于运行未经修改的 GPU 二进制程序。如果你有一个能在 AMD GPU 硬件上运行、且该硬件在 gem5 中受支持的应用，你就可以在 gem5 中运行同一个二进制程序。注意由于这是模拟（simulation），需要把应用缩小到合理规模，才能在现实的时间内完成模拟。

为 GPU 模型构建应用，类似于被模拟指令集架构与宿主机不一致时的[交叉编译](https://www.gem5.org/documentation/general_docs/compiling_workloads/)。你要么必须在本地安装开发工具，要么可以使用 Docker 之类的容器化方案。gem5 在 [util/dockerfiles/gpu-fs](https://github.com/gem5/gem5/tree/stable/util/dockerfiles/gpu-fs) 中提供了用于构建 GPU 应用的 Docker 镜像。你可以构建该镜像，也可以使用 gem5 提供的镜像 `ghcr.io/gem5/gpu-fs`。该 docker 镜像提供特定版本的 ROCm。Dockerfile 中的 ROCm 版本必须与用于模拟 gem5 的磁盘镜像上的 ROCm 版本一致。docker 与磁盘镜像的版本会随 gem5 发布而同步。下面的说明展示了一个使用 GitHub 容器镜像仓库（ghcr.io）上预构建 gem5 docker 的示例。

[Square](https://github.com/gem5/gem5-resources/tree/stable/src/gpu/square) 是 gem5-resources 中提供的一个简单应用，可用于上手该模型。一般而言，gem5-resources 的 `src/gpu` 目录包含用于构建原生应用的 `Makefile.default`，以及包含带 [m5ops](https://www.gem5.org/documentation/general_docs/m5ops/) 注解（只能在 gem5 中运行）的应用的 `Makefile.gpufs`。

要用 gem5 提供的 docker 镜像构建 square，进入 square 目录并使用 `Makefile.default`：

```
cd gem5-resources/src/gpu/square
docker run --rm -u $UID:$GID -v $PWD:$PWD -w $PWD ghcr.io/gem5/gpu-fs make -f Makefile.default
```

square 二进制程序随后应位于 `gem5-resources/src/gpu/square/bin.default/square.default`

#### 测试 GPU 应用

GPU 模型提供多种 gfx9 配置来模拟 GPU 应用。这些配置指定指令集架构（例如 gfx942、gfx90a），并且一般是尺寸最小的设备。*它们并不意图代表真实硬件的测量结果*。在 gem5 仓库中，这些配置是：
* MI300X：`configs/example/gpufs/mi300.py`
* MI210 / MI250：`configs/example/gpufs/mi200.py`

GPU 模型使用基于配置脚本的配置方式（即不是[标准库](https://www.gem5.org/documentation/gem5-stdlib/overview)），以命令行参数作为修改模拟参数的主要方式。不过，大多数常见配置选项由顶层脚本设置（例如 `configs/example/gpufs/mi300.py`）。主要的必需参数是磁盘镜像、内核和应用。

使用上面创建的磁盘镜像与内核，以及上面构建的 square 二进制程序，可以用以下命令运行 square：

```
build/VEGA_X86/gem5.opt configs/example/gpufs/mi300.py --disk-image gem5-resources/src/x86-ubuntu-gpu-ml/disk-image/x86-ubuntu-gpu-ml --kernel gem5-resources/src/x86-ubuntu-gpu-ml/vmlinux-gpu-ml --app gem5-resources/src/gpu/square/bin.default/square.default
```

在 Full System 中，模拟器的输出和被模拟系统的输出显示在两个不同的位置。默认情况下，gem5 输出打印到运行 gem5 的终端。被模拟终端输出位于 gem5 输出目录中，默认是 `m5out`。

在 gem5 结束之后（或运行期间），Full System 模拟的输出可在 `m5out/system.pc.com_1.device` 中查看。对于 square 示例，应用在成功完成时会向被模拟终端输出打印 "PASSED!"。

#### 使用 Python 或 shell 脚本

诸如 PyTorch、TensorFlow 等 Python 脚本以及 shell 脚本，都可以直接作为 `--app` 命令行的值传入。例如，下面这个极简的 PyTorch 应用保存为 `pytorch_test.py` 后可以直接运行：

```
#!/usr/bin/env python3

import torch

x = torch.rand(5, 3).to('cuda')
y = torch.rand(3, 5).to('cuda')

z = x @ y
```

例如：

```
build/VEGA_X86/gem5.opt configs/example/gpufs/mi300.py --disk-image gem5-resources/src/x86-ubuntu-gpu-ml/disk-image/x86-ubuntu-gpu-ml --kernel gem5-resources/src/x86-ubuntu-gpu-ml/vmlinux-gpu-ml --app ./pytorch_test.py
```

#### 输入文件

GPU 模型的配置文件被设计为把传给 `--app` 选项的文件复制到模拟器中。**Full System gem5 无法读取你宿主机（host）上的文件！** 如果你的应用需要输入文件，必须把它们复制到磁盘镜像中。相关做法见[扩展磁盘镜像](https://github.com/gem5/gem5-resources/blob/stable/src/x86-ubuntu-gpu-ml/BUILDING.md)的说明。

如果你的应用需要输入文件，建议创建一个 shell 脚本并把该 shell 脚本传给 `--app` 选项。该 shell 脚本中的路径应相对于磁盘镜像中的路径来写，因为它会在 gem5 内运行。例如，如果你的应用需要 `foo.dat`，可以创建这样的 shell 脚本：

```
#!/bin/bash

# We have previously copied foo.dat to /data outside of simulation.
cd /data
my_gpu_app -i foo.dat
```

## 高级用法

#### 不使用 KVM 运行

在宿主机不是 x86 或 KVM 不可用时，也可以使用 AtomicSimpleCPU。要启用 Atomic CPU，你需要修改配置（例如 `configs/example/gpufs/mi300.py`），把 `args.cpu_type = "X86KvmCPU"` 替换为 `args.cpu_type = "AtomicSimpleCPU"`。

注意这会让模拟的 CPU 部分最多慢 100 倍。可以使用[检查点（checkpoint）](https://www.gem5.org/documentation/general_docs/checkpoints/)来加速。

#### 检查点（checkpoint）

所提供的配置脚本开箱即可在 Linux 启动完成后进行检查点化。使用 atomic CPU 时建议这样做。要在启动后创建检查点，只需在命令行中加入 `--checkpoint-dir` 并给出放置检查点的目录。例如：

```
build/VEGA_X86/gem5.opt configs/example/gpufs/mi300.py --disk-image gem5-resources/src/x86-ubuntu-gpu-ml/disk-image/x86-ubuntu-gpu-ml --kernel gem5-resources/src/x86-ubuntu-gpu-ml/vmlinux-gpu-ml --app gem5-resources/src/gpu/square/bin.default/square.default --checkpoint-dir square-cpt
```

随后可以恢复该检查点，重新模拟该应用所需的时间会显著减少。要恢复检查点，把 `--checkpoint-dir` 选项替换为 `--restore-dir`：

```
build/VEGA_X86/gem5.opt configs/example/gpufs/mi300.py --disk-image gem5-resources/src/x86-ubuntu-gpu-ml/disk-image/x86-ubuntu-gpu-ml --kernel gem5-resources/src/x86-ubuntu-gpu-ml/vmlinux-gpu-ml --app gem5-resources/src/gpu/square/bin.default/square.default --restore-dir square-cpt
```

也可以使用 `m5_checkpoint(..)` [伪指令]()或在 python 配置中于某个退出事件之后进行检查点化。例如，可以用 `--exit-at-gpu-task=-1` 启用内核退出事件，并修改配置，通过检查 `configs/example/gpufs/runfs.py` 中当前的任务编号，在第 *N* 个内核处创建检查点。

注意目前不支持在 GPU 内核内部进行检查点化。因此，必须在没有 GPU 内核运行时创建检查点。

#### 构建 GPU 自定义应用

如果你想构建不属于 gem5-resources 的应用，你会希望把该 GPU 应用面向 `gfx90a`（MI210 和 MI250）、`gfx942`（MI300X）或两者一并构建。例如：

```
hipcc my_gpu_app.cpp -o my_gpu_app --offload-arch=gfx90a,gfx942
```

按照 [ROCm Linux 文档](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/)中的步骤设置好包管理器并安装 rocm-dev 包之后，你可以在 x86 Linux 宿主机上不使用 docker 镜像来构建。

#### 修改 GPU 配置

`configs/example/gpufs/` 中的配置是与 `configs/example/gpufs/runfs.py` 对接、并为特定设备设置有意义的默认值的辅助配置。该文件中一些值得关注的参数包括计算单元数量、GPU 拓扑、系统内存大小和 CPU 类型。

其中一些参数*只*修改 gem5 中的值，而不改变被模拟的设备。特别是 dgpu_mem_size 参数并不改变设备驱动所看到的内存量，它在 C++ 中被硬编码为 16GB。修改该值会导致 gem5 fatal。

支持的 cpu_type 为 X86KvmCPU 和 AtomicSimpleCPU，因为 timing CPU 不支持模拟独立 GPU 所需的非连续 Ruby 网络。

其他与 GPU 相关的参数可在 `configs/example/gpufs/system/amdgpu.py` 中找到，该文件为 GPU 创建计算单元。所有可用选项见 `src/gpu-compute/GPU.py` 中的 ComputeUnit 类。注意并非所有可能的选项组合都能被测试。诸如队列大小和延迟之类的选项通常可以安全修改。

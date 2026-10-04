---
layout: documentation
title: AMD VEGA GPU 模型
doc: gem5 文档
parent: gpu_models
permalink: /documentation/general_docs/gpu_models/vega
---

# **系统模拟（system emulation）AMD VEGA GPU 模型**

目录

1. [使用该模型](#Using-the-model)
2. [ROCm](#ROCm)
3. [文档与教程](#Documentation-and-Tutorials)

AMD VEGA GPU 是一个在 VEGA 指令集架构（ISA）层面（而不是中间语言层面）模拟 GPU 的模型。本页将概述如何使用该模型、该模型使用的软件栈，并提供详述该模型及其实现方式的资源。

## **使用该模型**

目前 gem5 中的 AMD VEGA GPU 模型在 stable 和 develop 分支上受支持。

[gem5 仓库](https://github.com/gem5/gem5)带有一个位于 `util/dockerfiles/gcn-gpu/` 的 dockerfile。该 dockerfile 包含运行 GPU 模型所需的驱动和库。该 docker 镜像的预构建版本托管在 `ghcr.io/gem5-test/gcn-gpu:v23-1`。
[gem5-resources 仓库](https://github.com/gem5/gem5-resources/)也附带若干示例应用，可用于验证模型是否正确运行。我们建议用户从 [square](https://resources.gem5.org/resources/square) 开始，因为它简单、经过大量测试，并且运行速度相对较快。

#### 使用该镜像
该 docker 镜像可以从 ghcr.io 拉取，也可以自行构建。

从源码构建 docker 镜像：
```
# Working directory: gem5/util/dockerfiles/gcn-gpu
docker build -t <image_name> .
```

拉取预构建的 docker 镜像（注意 `v23-1` 标签，以获得与该发布版本
匹配的正确镜像）：

```
docker pull ghcr.io/gem5-test/gcn-gpu:v23-1
```

你也可以在 docker run 命令中直接使用 `ghcr.io/gem5-test/gcn-gpu:v23-1` 作为镜像而无需事先拉取，它会自动被拉取。
#### 使用该镜像构建 gem5
关于如何在 docker 中构建 gem5 的示例，见 gem5 resources 中的 square（[gem5 resources](https://github.com/gem5/gem5-resources/tree/stable/src/gpu/square/)）。注意：这些说明假定你会自动拉取最新镜像。

#### 使用该镜像构建并运行 GPU 应用
关于如何在 docker 中构建和运行 GPU 应用的示例，见 [gem5 resources](https://github.com/gem5/gem5-resources/tree/stable/src/gpu/)。

## **ROCm**

AMD VEGA GPU 模型在设计上具有足够高的保真度，因而无需模拟运行时。相反，该模型使用 Radeon Open Compute 平台（ROCm）。ROCm 是 AMD 提供的一个开放平台，实现了[异构系统架构（HSA）](http://www.hsafoundation.com/)原则。关于 HSA 标准的更多信息见 HSA Foundation 网站。关于 ROCm 的更多信息见 [ROCm 网站](https://rocmdocs.amd.com/en/latest/)

#### ROCm 的模拟支持
该模型目前可与系统调用模拟（syscall emulation，SE）模式和全系统（full-system，FS）模式配合使用。

在 SE 模式下，所有内核级驱动功能都完全在 gem5 的 SE 模式层内建模。具体来说，被模拟的 GPU 驱动支持它从用户态代码接收的必要 `ioctl()` 命令。被模拟的 GPU 驱动源码见：

* GPU 计算驱动：`src/gpu-compute/gpu_compute_driver.[hh|cc]`

* HSA 设备驱动：`src/dev/hsa/hsa_driver.[hh|cc]`

HSA 驱动代码建模了 HSA 代理的基本功能；HSA 代理是任何可被 HSA 运行时作为目标、并接受 Architected Query Language（AQL）数据包的设备。AQL 数据包是所有 HSA 代理的标准格式，主要用于在 GPU 上启动内核。`HSADriver` 基类持有指向该设备的 HSA 数据包处理器的指针，并定义任何 HSA 设备的接口。HSA 代理不一定是 GPU，也可以是通用加速器、CPU、NIC 等。

`GPUComputeDriver` 派生自 `HSADriver`，是 `HSADriver` 的设备专用实现。它提供了 GPU 特有 `ioctl()` 调用的实现。

`src/dev/hsa/kfd_ioctl.h` 头文件必须与 ROCt 附带的 `kfd_ioctl.h` 头文件一致。被模拟的驱动依赖该文件来解释 thunk 使用的 `ioctl()` 代码。

在 FS 模式下，使用真实的 amdgpu Linux 驱动，并像在真实机器上一样安装它。该驱动的源码反而可以在 [ROCK-Kernel-Driver](https://github.com/RadeonOpenCompute/ROCK-Kernel-Driver) 仓库中找到。

#### ROCm 工具链与软件栈
AMD VEGA GPU 模型在 FS 模式下支持到 ROCm 5.4，在 SE 模式下支持到 4.0。

SE 模式下需要以下 ROCm 组件：
* [Heterogeneous Compute Compiler (HCC)](https://github.com/RadeonOpenCompute/hcc)
* [Radeon Open Compute runtime (ROCr)](https://github.com/RadeonOpenCompute/ROCR-Runtime)
* [Radeon Open Compute thunk (ROCt)](https://github.com/RadeonOpenCompute/ROCT-Thunk-Interface)
* [HIP](https://github.com/ROCm-Developer-Tools/HIP)

以下额外组件用于构建和运行机器学习程序：
* [hipBLAS](https://github.com/ROCmSoftwarePlatform/hipBLAS/)
* [rocBLAS](https://github.com/ROCmSoftwarePlatform/rocBLAS/)
* [MIOpen](https://github.com/ROCmSoftwarePlatform/MIOpen/)
* [rocm-cmake](https://github.com/RadeonOpenCompute/rocm-cmake/)
* [PyTorch](https://pytorch.org/)（仅 FS 模式）
* [Tensorflow](https://www.tensorflow.org/) —— 特指 tensorflow-rocm python 包（仅 FS 模式）

关于在本地安装这些组件的信息，可以在 Ubuntu 16 机器上沿用 GCN3 dockerfile（`util/dockerfiles/gcn-gpu/`）中的命令。

## **文档与教程**

注意 VEGA 指令集架构（ISA）是源自 GCN3 的更新、超集式的 ISA。因此，以下论文、教程和文档的内容同样适用于 VEGA。

#### GPU 模型
描述（撰写本文时）采用 GCN3 ISA 的 gem5 GPU 模型。VEGA 是源自 GCN3 的更新、超集式的 ISA。因此以下论文的内容同样适用）
* [HPCA 2018](https://ieeexplore.ieee.org/document/8327041)

#### gem5 GCN3 ISCA 教程
涵盖有关 gem5 中 GPU 体系结构、GCN3 ISA 与软硬件接口的信息，并介绍 ROCm。
* [gem5 GCN3 ISCA 网页](http://www.gem5.org/events/isca-2018)
* [gem5 GCN3 ISCA 幻灯片](http://old.gem5.org/wiki/images/1/19/AMD_gem5_APU_simulator_isca_2018_gem5_wiki.pdf)

#### VEGA ISA
* [VEGA ISA](https://gpuopen.com/documentation/amd-isa-documentation/)

#### ROCm 文档
包含关于 ROCm 栈的进一步文档，以及使用 ROCm 的编程指南。
* [ROCm 网页](https://rocmdocs.amd.com/en/latest/)

#### AMDGPU LLVM 信息
* [LLVM AMDGPU](https://llvm.org/docs/AMDGPUUsage.html)

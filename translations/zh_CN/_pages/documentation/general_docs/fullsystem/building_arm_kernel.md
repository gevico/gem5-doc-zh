---
layout: documentation
title: "Building ARM Kernel"
doc: gem5 文档
parent: fullsystem
permalink: /documentation/general_docs/fullsystem/building_arm_kernel
---

# 构建 ARM 内核

本页包含为在 ARM 上运行的 gem5 构建最新内核的说明。

如果你不想自己构建内核（或磁盘镜像），仍然可以[下载
预构建版本](./guest_binaries)。

## 前置条件
这些说明针对无头（headless）系统，即更像“服务器”风格、没有帧缓冲的系统。本说明使用下方所列仓库中已知可用的最新标签编写，不过各节的表格中也列出了已知可用的先前标签。要在 x86 宿主机（host）上构建内核，你需要 ARM 交叉编译器和设备树编译器。如果你运行的是相当新的 Ubuntu 或 Debian 版本，可以通过 apt 获取所需软件：

```
apt-get install  gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu device-tree-compiler
```

如果你无法使用这些现成的编译器，从 ARM 获取所需编译器的次简便方式是：
- [Cortex A 交叉编译器](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-a/downloads)
- [Cortex RM 交叉编译器](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm/downloads)

下载（其中一个）并确保其二进制程序在你的 `PATH` 上。

根据交叉编译器的具体来源，下文使用的编译器名称可能需要小幅调整。

要真正运行内核，你需要下载或编译 gem5 的
引导加载程序。细节见本文档的[引导加载程序](#bootloaders)一节。

## Linux 4.x
较新的 ARM gem5 内核（v4.x 及更高）基于原版 Linux 内核，通常只有少量补丁以使其更好地配合 gem5 工作。这些补丁是可选的，你也应该能够使用原版内核。不过这需要你自己配置内核。较新的内核在 AArch32 和 AArch64 下都使用 VExpress\_GEM5\_V1 gem5 平台。

# 检取内核
要检取内核，请执行以下命令：

```
git clone https://gem5.googlesource.com/arm/linux
```

该仓库为每个 gem5 内核发布版本提供一个标签，并为每个主要 Linux 修订版本提供工作分支。标签和分支列表见[项目页面](https://gem5-review.googlesource.com/#/admin/projects/arm/linux)。克隆命令默认会检出最新的发布分支。要检出 v4.14 分支，请在仓库中执行：
```
git checkout -b gem5/v4.14
```

# 构建内核
要编译内核，请在仓库中执行以下命令：

```
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- gem5_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j `nproc`
```

测试刚构建好的内核：

```
./build/ARM/gem5.opt configs/example/arm/starter_fs.py --kernel=/tmp/linux-arm-gem5/vmlinux \
    --disk-image=ubuntu-18.04-arm64-docker.img
```

# 引导加载程序 {#bootloaders}
gem5 有两个不同的引导加载程序：一个用于 32 位内核，一个用于 64 位内核。它们可以用以下命令编译：

```
make -C system/arm/bootloader/arm
make -C system/arm/bootloader/arm64
```

# 设备树二进制文件（Device Tree Blob）
向操作系统描述硬件所需的 DTB 文件随 gem5 一起提供。要构建它们，请执行命令：

```
make -C system/arm/dt
```

我们建议仅在你打算修改这些设备树文件时才使用它们。如果不打算修改，我们建议依靠 DTB 自动生成：在不带 --dtb 选项的情况下运行 FS 脚本时，gem5 会根据所实例化的平台自动即时生成 DTB。

编译好这些二进制程序后，把它们放入你
`M5_PATH` 中的 binaries 目录。

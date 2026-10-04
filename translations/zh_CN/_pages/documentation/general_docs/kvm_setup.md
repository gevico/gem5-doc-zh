---
layout: page
title: 在你的机器上配置并使用 KVM
permalink: /documentation/general_docs/using_kvm/
author: Mahyar Samani and Bobby R. Bruce
---

基于内核的虚拟机（Kernel-based Virtual Machine，KVM）是一个 Linux 内核模块，允许创建由内核管理的虚拟机。
在较新的 x86 和 ARM 处理器上，KVM 支持硬件辅助虚拟化，使虚拟机可以接近原生速度运行。
gem5 的 `KVMCPU` 在 gem5 中启用了该特性，代价是 gem5 不会记录体系结构层面的统计信息。
使用 `KVMCPU` 时可以通过 `perf` 选择性地收集一些统计信息（statistics），但该选项需要 `root` 权限。

要使用 gem5 的 `KVMCPU` 来快进你的模拟（simulation），你必须拥有支持 KVM 的处理器，并且机器上已安装 KVM。
本页将指导你在机器上启用 KVM，并将其与 gem5 配合使用。

注意：以下教程假定使用 X86 Linux 宿主机（host）。
本教程的某些部分可能不适用于其他体系结构或不同的操作系统。
目前 KVM 支持 X86 和 ARM 模拟（simulation）（分别需要 X86 和 ARM 宿主机）。

## 确认系统兼容性

要查看你的处理器是否支持硬件虚拟化，请运行以下命令：

```console
grep -E -c '(vmx|svm)' /proc/cpuinfo
```

如果该命令返回 0，说明你的处理器不支持硬件虚拟化。
如果该命令返回 1 或更大，说明你的处理器支持硬件虚拟化

你可能还需要确保在 BIOS 中启用了它。
具体操作因厂商和型号而异。
更多信息请查阅你的主板手册。

最后，建议你在宿主机上使用 64 位内核。
在宿主机上使用 32 位内核的限制如下：

* 只能为虚拟机分配 2GB 内存
* 只能创建 32 位虚拟机。

这会严重限制 KVM 在 gem5 模拟中的可用性。

## 启用 KVM

要让 KVM 直接与 gem5 配合工作，必须安装以下依赖项：

```console
sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
```

接下来，你需要把用户加入 `kvm` 和 `libvirt` 组。
运行以下两条命令：

```console
sudo adduser `id -un` libvirt
sudo adduser `id -un` kvm
```

之后，你需要退出再重新登录你的账号。
如果你使用 SSH，请断开所有会话并重新登录。
现在，如果运行下面的 `groups` 命令，你应该能看到 `kvm` 和 `libvirt`。

## 验证 KVM 是否可用

"configs/example/gem5_library/x86-ubuntu-run-with-kvm.py" 文件是一个 gem5 配置，它会创建一个使用 KVM 启动 Ubuntu 24.04 镜像的模拟。
可以通过以下方式执行：

```console
scons build/ALL/gem5.opt -j`nproc`
./build/ALL/gem5.opt configs/example/gem5_library/x86-ubuntu-run-with-kvm.py
```

如果你使用的是预编译的 gem5 二进制程序，请使用以下命令：

```console
gem5 configs/example/gem5_library/x86-ubuntu-run-with-kvm.py

```

如果模拟成功运行，说明你已成功安装 KVM，并可以将其与 gem5 配合使用。

## `KVMCPU`、快进与 `perf`

`perf` 是 Linux 中的一项功能，允许用户访问性能计数器。
默认情况下，`KVMCPU` 会启用 `perf` 来收集统计信息，例如已执行的指令数。
通常，`perf` 需要一些系统权限才能设置。
否则你会看到相关的权限问题，例如 `kernel.perf_event_paranoid` 值过高。

不过，如果你想快进模拟，并且不打算收集快进阶段的统计信息，可以选择在使用 `KVMCPU` 时不使用 `perf`。
`KVMCPU` 这个 SimObject 有一个名为 `usePerf` 的参数，用于指定 `KVMCPU` 是否应使用 `perf` 收集统计信息。
该选项默认启用。

下面是一个关闭 `perf` 的示例：
[https://github.com/gem5/gem5/blob/stable/configs/example/gem5\_library/x86-ubuntu-run-with-kvm-no-perf.py](https://github.com/gem5/gem5/blob/stable/configs/example/gem5_library/x86-ubuntu-run-with-kvm-no-perf.py)。

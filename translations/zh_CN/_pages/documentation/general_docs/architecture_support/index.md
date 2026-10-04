---
layout: documentation
title: "Architecture Support"
doc: gem5 文档
parent: architecture_support
permalink: /documentation/general_docs/architecture_support/
---

# 体系结构支持（Architecture Support）

{: .outdated-notice}
本页中的信息和超链接可能不准确。

## Alpha

Gem5 对基于 DEC Tsunami 的系统建模。
除了支持 4 个核心的普通 Tsunami 系统之外，我们还有一个支持 64 个核心的扩展（需要定制的 PALcode 和打过补丁的 Linux 内核）。
对用户级代码而言，被模拟的系统看起来像 Alpha 21264，包括 BWX、MVI、FIX 和 CIX。
出于历史原因，该处理器执行基于 EV5 的 PALcode。

它可以启动未经修改的 Linux 2.4/2.6、FreeBSD 或 L4Ka::Pistachio，也可以在系统调用模拟（syscall emulation）模式下运行应用程序。
很多年前还可以启动 HP/Compaq 的 Tru64 5.1 操作系统。
不过我们已不再积极维护该能力，目前它无法工作。

## ARM

gem5 中的 ARM 体系结构模型支持搭载多处理器扩展的 ARM® 体系结构的 [ARMv8-A](https://developer.arm.com/docs/den0024/latest/armv8-a-architecture-and-processors/armv8-a) 版本。
这包括 AArch32 和 AArch64 两种状态。
在 AArch32 中，这包括对 [Thumb®](https://www.embedded.com/introduction-to-arm-thumb/)、Thumb-2、VFPv3（32 个双精度寄存器变体）和 [NEON™](https://developer.arm.com/architectures/instruction-sets/simd-isas/neon) 以及大物理地址扩展（LPAE）的支持。
目前不支持的体系结构可选特性有 [TrustZone®](https://developer.arm.com/ip-products/security-ip/trustzone)、ThumbEE、[Jazelle®](https://en.wikipedia.org/wiki/Jazelle) 和[虚拟化](https://developer.arm.com/docs/100942/0100/aarch64-virtualization)。

在全系统（full-system）模式下，gem5 能够启动单处理器或多处理器 Linux，以及用 ARM 编译器构建的裸机应用。
较新的 Linux 版本（配合 gem5 的 DTB 使用时）开箱即可工作；我们还提供带定制配置和定制驱动的 gem5 专用 Linux 内核。此外，静态链接的 Linux 二进制程序可以在 ARM 的系统调用模拟（syscall emulation）模式下运行。

## POWER

gem5 中对 POWER 指令集架构（ISA）的支持目前仅限于系统调用模拟（syscall emulation），并基于 [POWER ISA v3.0B](https://ftp.libre-soc.org/PowerISA_public.v3.0B.pdf)。
它建模一个大端 32 位处理器。
大多数常见指令都可用（足以运行所有 SPEC CPU2000 整数基准测试）。
浮点指令可用，但支持可能不完整。
尤其是浮点状态与控制寄存器（FPSCR）通常完全不更新。
不支持向量指令。

对 POWER 的全系统支持需要大量工作，目前没有在开发。
不过，如果有兴趣推进，可以从 [Tim](mailto:timothy.jones@cl.cam.ac.uk) 处获取一批朝此方向起步的在研补丁。

## SPARC

gem5 模拟器（simulator）对 UltraSPARC T1 处理器（UltraSPARC Architecture 2005）的单个核心建模。

它可以像 Sun T1 体系结构模拟器工具那样启动 Solaris（使用特定宏构建虚拟机管理程序（hypervisor），并使用 HSMID 虚拟磁盘驱动）。
全系统 SPARC 的多处理器支持从未完成。
在系统调用模拟（syscall emulation）下，gem5 支持运行 Linux 或 Solaris 二进制程序。
新版本的 Solaris 不再支持生成 gem5 所需的静态编译二进制程序。

## x86

gem5 模拟器（simulator）中的 X86 支持包括一个带 64 位扩展的通用 x86 CPU，它更接近 AMD 的体系结构版本而不是 Intel 的，但也不严格等同于任何一方。
未经修改的 Linux 内核可以在 UP 和 SMP 配置下启动，并且有可用于加速启动的补丁。
SSE 和 3dnow 已实现，但 x87 浮点的大部分尚未实现。
大部分工作集中在 64 位模式上，但兼容模式和传统模式也得到了一定支持。
实模式足以引导 AP，但没有经过广泛测试。
Linux 和标准 Linux 二进制程序会用到的体系结构特性均已实现且应该可以工作，但其他部分可能不行。
在系统调用模拟（syscall emulation）模式下支持 64 位和 32 位 Linux 二进制程序。

## MIPS


## RISC-V


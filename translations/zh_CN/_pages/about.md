---
layout: page
title: 关于
parent: about
permalink: /about/
---


gem5 模拟器（simulator）是一个模块化平台，用于计算机系统体系结构（architecture）研究，涵盖系统级体系结构以及处理器微架构（microarchitecture）。

gem5 是一个开源的计算机体系结构模拟器，在学术界和工业界均有使用。
它已持续开发 15 年，最初在密歇根大学名为 m5 项目，在威斯康星大学名为 GEMS 项目。
自 [2011 年 m5 与 GEMS 合并]({{ site.baseurl }}/publications/#original-paper)以来，gem5 已被超过 [2900 篇论文](https://scholar.google.com/scholar?cites=5769943816602695435)引用。
许多工业研究实验室都在使用 gem5，包括 ARM Research、AMD Research、Google、Micron、Metempsy、HP、Samsung 等。

---

## 功能特性

#### 多种可互换的 CPU 模型。
gem5 提供四种基于解释执行的 CPU 模型：一个简单的单 CPI CPU、一个顺序（in-order）CPU 的详细模型，以及一个乱序（out-of-order）CPU 的详细模型。
这些 CPU 模型共用同一套高层级的指令集架构（ISA）描述。此外，gem5 还提供一个基于 KVM 的 CPU，利用虚拟化加速模拟（simulation）。

#### 事件驱动（event-driven）的内存系统（memory system）。
gem5 提供一个详细的、[事件驱动内存系统]({{ site.baseurl }}/documentation/general_docs/memory_system)，其中包括缓存（cache）、
交叉开关、探听过滤器，以及一个快速且精确的 DRAM 控制器模型，用于
刻画现有及新兴存储器的性能影响，例如 LPDDR3/4/5、DDR3/4、
GDDR5、HBM1/2/3、HMC、WideIO1/2。这些组件可以灵活组合，
例如用于建模带有异构存储器的复杂多级非均匀缓存层次结构。

#### 支持多种指令集架构
gem5 将指令集语义与 CPU 模型解耦，从而能够有效地[支持多种指令集架构]({{ site.baseurl }}/documentation/general_docs/architecture_support)。目前 gem5 支持 Alpha、ARM、SPARC、MIPS、POWER、RISC-V 和 x86 指令集架构。
不过，并非所有客户机（guest）平台都能在所有宿主机（host）平台上运行（最典型的是 Alpha 需要小端硬件）。

#### 同构与异构多核
CPU 模型与缓存可以按任意拓扑组合，构建同构和异构多核系统。MOESI 探听缓存
一致性（cache coherence）协议负责保持缓存一致。

#### 全系统（full-system）能力
  - **ARM**：gem5 可以建模 Realview ARM 平台上多达 64 个（异构）核心，并启动
       [未经修改的 Linux]({{ site.baseurl }}/documentation/general_docs/fullsystem/building_arm_kernel) 和
       [Android]({{ site.baseurl }}/documentation/general_docs/fullsystem/building_android_m)，并可混合使用
       顺序与乱序 CPU。ARM 实现支持
       32 位或 64 位内核与应用程序。
  - **x86**：gem5 模拟器支持标准 PC 平台，可启动未经修改的 Linux
  - **RISC-V**：对 RISC-V 特权级指令集规范的支持仍在开发中。
  - **SPARC**：gem5 模拟器对 UltraSPARC T1 处理器的单个核心建模，
       其详细程度足以像 Sun T1 体系结构模拟器工具那样启动 Solaris
       （使用特定宏构建虚拟机管理程序（hypervisor），并使用
       HSMID 虚拟磁盘驱动）。
  - **Alpha**：gem5 对 DEC Tsunami 系统的建模详细程度足以
       启动未经修改的 Linux 2.4/2.6、FreeBSD 或 L4Ka::Pistachio。
       我们过去也曾启动过 HP/Compaq 的 Tru64 5.1 操作系统，
       但现已不再积极维护该能力。

#### 仅应用程序支持
在仅应用程序（非全系统）模式下，gem5 可以通过 Linux 模拟执行各种
体系结构/操作系统的二进制程序。

#### 多系统能力
可以在单个模拟进程内实例化多个系统。结合全系统建模，该特性允许模拟完整的
客户端-服务器网络。

#### 功耗与能量建模
gem5 的对象按操作系统可见的功耗域和时钟域（clock domain）组织，从而可以开展
一系列功耗与能效实验。gem5 开箱即支持由操作系统控制的动态电压与频率（DVFS）调节，
为未来高能效系统的研究提供了完整平台。
不过，现有的 DVFS 文档已经过时。你可以查看
[旧版 wiki](http://old.gem5.org/Running_gem5.html#Experimenting_with_DVFS) 中的该页面。

#### 基于跟踪（trace）的 CPU
该 CPU 模型可以回放弹性跟踪（elastic trace），这些跟踪由挂在乱序 CPU 模型上的探针生成，带有依赖信息与时序标注。
[跟踪 CPU 模型]({{ site.baseurl }}/documentation/general_docs/cpu_models/TraceCPU)关注的是以快速且合理精确的方式探索内存系统（缓存层次结构、互连（interconnect）与主存）的性能，而不是使用详细的 CPU 模型。

#### 与 SystemC 协同仿真。
gem5 可以[被纳入 SystemC 仿真](http://old.gem5.org/wiki/images/4/4c/2015_ws_09_2015-06-14_Gem5_ISCA.pptx)，实际上作为
SystemC 事件内核中的一个线程运行，并在两个世界之间保持事件与时间线同步。
该功能使 gem5 组件能够与多种片上系统（SoC）组件模型互操作，例如互连、设备与加速器。
项目还提供了 SystemC 事务级建模（TLM）的封装。

#### NoMali GPU 模型。
gem5 内置一个 [NoMali GPU 模型](http://old.gem5.org/wiki/images/5/53/2015_ws_04_ISCA_2015_NoMali.pdf)，它与
Linux 和 Android 的 GPU 驱动栈兼容，因此无需软件渲染。
NoMali GPU 不产生任何输出，但能确保以 CPU 为中心的实验得到具有代表性的结果。

---

## 许可

gem5 模拟器（simulator）采用 Berkeley 风格的开源许可发布。
大致而言，只要保留我们的版权声明，你可以自由地以任何方式使用我们的代码。
更多细节请参见源码下载包中的 LICENSE 文件。请注意，gem5 中源自其他项目的部分
同样受其原始来源的许可限制约束。

---

## 致谢

gem5 模拟器（simulator）的研发得到了多个来源的慷慨支持，
包括美国国家科学基金会、AMD、ARM、
Hewlett-Packard、IBM、Intel、MIPS 和 Sun。从事 gem5 工作的个人
还获得了 Intel、Lucent 以及
Alfred P. Sloan 基金会提供的奖学金支持。

本材料中表达的任何观点、发现、结论或建议
均属于作者本人，不一定反映
美国国家科学基金会（NSF）或任何其他资助方的立场。

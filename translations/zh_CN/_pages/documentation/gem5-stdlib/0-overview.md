---
layout: documentation
title: Standard Library Overview
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/overview
author: Bobby R. Bruce
---

## gem5 标准库（standard library）概览

与编程语言中的标准库类似，gem5 标准库旨在为 gem5 用户提供常用的组件（component）、特性与功能，目标是提升他们的工作效率。
gem5 stdlib 在 [v21.1](https://github.com/gem5/gem5/tree/v21.1.0.0) 中以 alpha 发布状态引入（当时称为 "gem5 components"），并自 [v21.2](https://github.com/gem5/gem5/tree/v21.2.0.0) 起正式发布。

对于初次接触 gem5 标准库的用户，以下教程有助于理解如何用 gem5 stdlib 更好地创建 gem5 模拟（simulation）。
其中包含一篇关于构建系统调用模拟（syscall emulation）与全系统（full-system）模拟的教程，以及一篇关于如何扩展该库并做贡献的指南。
gem5 仓库中的 [`configs/examples/gem5_library`](https://github.com/gem5/gem5/tree/stable/configs/example/gem5_library) 目录也包含使用该库的示例脚本。

以下小节概述 gem5 stdlib 的各个包及其预期用途。

**注意：与标准库相关的文档/教程等已针对 v24.1 发布版本更新。
在继续之前，请确保你使用的是正确版本的 gem5。**

作为 [gem5 2022 Bootcamp]({{ site.baseurl }}/events/boot-camp-2022) 的一部分，stdlib 曾作为教程讲授。
该教程的幻灯片见[此处](https://raw.githubusercontent.com/gem5bootcamp/gem5-bootcamp-env/main/assets/slides/using-gem5-02-gem5-stdlib-tutorial.pdf)。
该教程的录像见[此处](https://www.youtube.com/watch?v=vbruiMyIFsA)。

[2024 年 gem5 Bootcamp](https://bootcamp.gem5.org/#02-Using-gem5/01-stdlib) 也涵盖了 stdlib。

<!-- Could use a nice picture here showing the main modules of the stdlib and how they relate -->

## gem5 stdlib components 包及其设计理念

gem5 stdlib components 包是 gem5 stdlib 的核心部分。
使用它，用户可以借助简单的组件构建复杂系统，这些组件通过标准化 API 相互连接。

指引 components 包开发的类比是用现成组件组装一台计算机。
在组装计算机时，人们可以挑选组件、把它们插到板卡上，并假定板卡与组件之间的接口已被设计成“插上就能用”。
例如，人们可以从板卡上取下某个处理器，换上一个兼容同一插槽的不同处理器，而无需改动配置中的其他任何部分。
虽然这种设计理念总有局限，但 components 包采用了高度模块化、可扩展的设计，同一类型的组件尽可能可以互换。

components 包的核心是*板卡（board）*这一概念。
它的作用类似于真实系统中的主板。
虽然它可能包含嵌入式缓存、控制器及其他复杂组件，但它的主要用途是暴露标准化接口，供其他硬件加入，并处理它们之间的通信。
例如，可以把一个内存设备和一个处理器加到一个板卡上，由板卡负责通信，而内存或处理器的设计者无需考虑这一点，只要它们符合已知的 API。

通常，gem5 components 包的*板卡*需要声明以下三种组件：

1. *处理器（processor）* ：系统处理器。一个处理器组件至少包含一个*核心（core）*，其类型可以是 Atomic、O3、Timing 或 KVM。
2. *内存系统（memory）*：内存系统，例如 DDR3_1600。
3. *缓存层次结构（cache hierarchies）*：该组件定义处理器与主存之间的所有组件，尤其是缓存配置。在最简单的配置中，它会直接把内存连接到处理器。

全系统（full-system）模拟所需的其他设备（它们在不同模拟之间很少变化）由板卡处理。

因此，组件的一个典型用法可能如下：

```python

cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16kB",
    l1d_assoc=8,
    l1i_size="16kB",
    l1i_assoc=8,
    l2_size="256kB",
    l2_assoc=16,
    num_l2_banks=1,
)

memory = SingleChannelDDR3_1600(size="3GB")

processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=1)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)
```

以下教程会更详细地介绍如何使用 components 包创建 gem5 模拟。

## gem5 resources 包

gem5 stdlib 的 resource 包用于获取并纳入资源（resource）。
在 gem5 的语境中，资源是模拟中所使用、或被模拟所使用，但不直接用于构建被模拟系统的东西。
通常它们是应用程序、内核、磁盘镜像、基准测试（benchmark）或测试。

由于这些资源可能难以找到或难以创建，我们作为 [gem5-resources]({{ site.baseurl }}/documentation/general_docs/gem5_resources) 的一部分提供了预构建资源。
例如，通过 gem5-resources，用户可以下载一个与 gem5 已知兼容的 Ubuntu 18.04 磁盘镜像，
而无需自行配置。

gem5 stdlib resource 包的一个核心特性是：它允许用户*自动获取*用于其模拟的预构建 gem5 资源。
用户可以在其 Python 配置文件中指定需要某个 gem5 资源；运行时，该包会检查宿主机上是否有本地副本，如果没有则下载它。

教程会更详细地演示如何使用 resource 包，这里先给出一个典型模式：

```python
from gem5.resources.resource import Resource

resource = Resource("riscv-disk-img")

print(f"The resources is available at {resource.get_local_path()}")
```

这会获取 `riscv-disk-img` 资源并在本地存储，供 gem5 模拟使用。

resource 包引用的资源可在 [gem5 Resources 网站](https://resources.gem5.org)和 [gem5 Resources 仓库](https://github.com/gem5/gem5-resources)查看。强烈建议通过该网站了解有哪些资源可用以及可以从哪里下载。

## Simulate 包

simulate 包用于运行 gem5 模拟。
虽然该模块替用户处理了一些样板代码，但它的主要用途是为我们所说的*退出事件（Exit Event）*提供默认行为和 API。
退出事件是指模拟因某种原因退出。

退出事件的一个典型例子是 `Workbegin` 退出事件。
它用于表明已到达关注区域（Region-of-Interest，ROI）。
通常该退出用于让用户开始记录统计信息，或切换到更详细的 CPU 模型。
在 stdlib 之前，用户需要精确指定这类退出事件时的预期行为。
模拟会退出，而配置脚本中会包含指定下一步做什么的 Python 代码。
现在有了 simulate 包，这类事件有了默认行为（统计信息被重置），并且有便于用户用自己所需行为覆盖该默认行为的接口。

关于退出事件的更多信息见 [M5ops 文档](https://www.gem5.org/documentation/general_docs/m5ops/)。

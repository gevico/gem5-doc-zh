---
layout: documentation
title: X86 Full-System Tutorial
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/x86-full-system-tutorial
author: Bobby R. Bruce
---

## 用 gem5 标准库（standard library）构建 x86 全系统（full-system）模拟

gem5 标准库背后的关键理念之一，是让用户以最小的投入模拟大型复杂系统。
实现方式是：对所模拟系统的性质做出合理假设，并以“说得通”的方式连接各个组件。
虽然这牺牲了一些灵活性，但它极大简化了在 gem5 中模拟典型硬件配置的工作。
总体理念是让*常见情形*变简单。

在本教程中，我们将构建一个 X86 模拟，它能够运行全系统（full-system）模拟、启动 Ubuntu 操作系统并运行基准测试（benchmark）。
该系统将利用 gem5 的核心切换能力，在 KVM 快进模式下启动操作系统，然后切换到详细 CPU 模型运行基准测试，并在双核配置中使用 MESI Two Level Ruby 缓存层次结构。
如果不使用 gem5 库，这需要数百行 Python 代码，迫使用户指定每个 IO 组件以及缓存层次结构究竟如何设置等细节。
这里我们将展示，使用 gem5 标准库后这项任务能有多简单。

首先我们构建 ALL 二进制程序。这样就能运行任何指令集架构（包括 X86）的模拟：

```sh
scons build/ALL/gem5.opt -j <number of threads>
```

如果你使用预构建的 gem5 二进制程序，则无需这一步。

首先创建一个新的 Python 文件。
下文中我们称之为 `x86-ubuntu-run.py`。

开始时先加入 import 语句：

```python
from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires
```

与其他 Python 脚本一样，这些只是我们脚本中所需的类/函数。
它们都包含在 gem5 二进制程序中，因此无需从别处获取。

一个良好的开头是用 `requires` 函数指定运行该脚本需要什么样的 gem5 二进制程序/环境：

```python
requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    kvm_required=True,
)
```

这里我们声明需要 gem5 编译为可运行 X86 指令集架构并支持 MESI Two Level 协议。
我们还要求宿主机（host）系统具有 KVM。
**注意：请确保你的宿主机系统支持 KVM。如果你的系统不支持，请删除这里的 `kvm_required` 检查**。
KVM 只有在宿主平台与被模拟的指令集架构相同时才能工作（例如 X86 宿主机与 X86 模拟）。关于在 gem5 中使用 KVM 的更多信息见[此处](https://www.gem5.org/documentation/general_docs/using_kvm/)。

这个 `requires` 调用不是必须的，但为运行该脚本的人提供了一道良好的安全网。
否则，由于 gem5 二进制程序不兼容而出现的错误可能让人难以理解。

接下来我们开始指定系统中的组件。
先从*缓存层次结构*开始：

```python
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
    num_l2_banks=1,
)
```

这里我们设置一个 MESI Two Level（ruby）缓存层次结构。
通过构造函数，我们把 L1 数据缓存和 L1 指令缓存设为 32 KiB，L2 缓存设为 256 KiB。

接下来设置*内存系统*：

```python
memory = SingleChannelDDR3_1600(size="2GiB")
```

这相当简单，也应该很直观：大小为 2GiB 的单通道 DDR3 1600 配置。
**注意：** 默认情况下 `SingleChannelDDR3_1600` 组件的大小是 8GiB。
不过，由于 [X86Board 的一个已知限制](https://gem5.atlassian.net/browse/GEM5-1142)，我们无法使用大于 3GiB 的内存系统。
因此我们必须设置该大小。

接下来设置*处理器*：

```python
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=2,
)
```

这里我们使用 gem5 标准库特有的 `SimpleSwitchableProcessor`。
该处理器可用于用户在模拟过程中把一种核心换成另一种核心的模拟。
`starting_core_type` 参数指定以哪种 CPU 类型开始模拟。
在本例中是 KVM 核心。
**（注意：如果你的宿主机系统不支持 KVM，该模拟将无法运行。你必须把它改为其他 CPU 类型，例如 `CPUTypes.ATOMIC`）**
`switch_core_type` 参数指定模拟中切换到哪种 CPU 类型。
在本例中我们将从 KVM 核心切换到 TIMING 核心。
最后一个参数 `num_cores` 指定处理器中的核心数量。

使用该处理器，用户可以调用 `processor.switch()` 在起始核心与切换核心之间来回切换，我们将在本教程后面演示。

接下来把这些组件加入*板卡*：

```python
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)
```

这里我们使用 `X86Board`。
这是用于在全系统（full-system）模式下模拟典型 X86 系统的板卡。
至少需要指定 `clk_freq`、`processor`、`memory` 和 `cache_hierarchy` 参数。
这最终确定了我们的系统设计。

现在我们设置该系统要运行的工作负载（workload）：

```python
workload = obtain_resource("x86-ubuntu-24.04-boot-with-systemd")
board.set_workload(workload)
```

`obtain_resource` 函数获取 X86 Ubuntu 24.04 启动工作负载。
该工作负载包含内核资源、传给内核的参数、磁盘镜像资源，以及一个指示 `board.set_workload()` 被调用时 gem5 所使用的底层函数的字符串。
你可以在 gem5 Resources 网站上该工作负载页面的 [Raw](https://resources.gem5.org/resources/x86-ubuntu-24.04-boot-with-systemd/raw?database=gem5-resources&version=3.0.0) 标签页下看到这些细节。

你也可以用 `set_kernel_disk_workload()` 代替 `set_workload()`，分别设置磁盘镜像和内核资源。
当你想使用自己的资源，或在[gem5 resources 网站](resources.gem5.org)上未作为工作负载提供的资源组合时，可以使用它。

**注意：如果用户希望使用自己的资源（即不是作为 gem5-resources 一部分预构建的资源），可以参阅[此处](../general_docs/gem5_resources)的教程。[2024 gem5 bootcamp 网站](https://bootcamp.gem5.org/#02-Using-gem5/02-gem5-resources)上也有相关教程**

使用 `set_kernel_disk_workload()` 函数时，你还可以传入一个可选的 `readfile_contents` 参数。
它会在系统启动后作为 bash 脚本运行；如果磁盘镜像中安装了基准测试，可以用它在系统启动后启动基准测试。
示例见[此处](https://resources.gem5.org/resources/x86-ubuntu-24.04-npb-ua-b/raw?database=gem5-resources&version=2.0.0)

最后，我们通过以下内容指定模拟如何运行：

```python
def exit_event_handler():
    print("First exit: kernel booted")
    yield False  # gem5 is now executing systemd startup
    print("Second exit: Started `after_boot.sh` script")
    # The after_boot.sh script is executed after the kernel and systemd have
    # booted.
    # Here we switch the CPU type to Timing.
    print("Switching to Timing CPU")
    processor.switch()
    yield False  # gem5 is now executing the `after_boot.sh` script
    print("Third exit: Finished `after_boot.sh` script")
    # The after_boot.sh script will run a script if it is passed via
    # readfile_contents. This is the last exit event before the simulation exits.
    yield True


simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)
simulator.run()
```

这里需要注意的是 `on_exit_event` 参数。
我们可以在这里覆盖默认行为。

`on_exit_event` 参数是一个 Python 字典，包含退出事件与 [Python 生成器](https://wiki.python.org/moin/Generators)。
在本教程中我们用 `exit_event_handler` 生成器处理 `ExitEvent.EXIT` 类型的退出事件。
该工作负载所用的 Ubuntu 24.04 磁盘镜像资源中有三个 `EXIT` 退出事件。
如果没有定义退出事件处理器，模拟会在第一个退出事件（发生在内核完成启动之后）后结束。
yield `False` 让模拟继续，yield `True` 则结束模拟。
在第二个退出事件之后，我们把核心从 KVM 切换到 TIMING，然后 yield `False` 继续模拟。
在第三个退出事件之后，我们 yield `True`，结束模拟。

至此脚本的设置完成。要执行该脚本，我们运行：

```bash
./build/ALL/gem5.opt x86-ubuntu-run.py
```

如果你使用预构建的二进制程序，可以用以下命令执行该模拟：

```sh
gem5 hello-world.py
```

你可以在 `m5out/system.pc.com_1.device` 中看到模拟器的输出。

下面是完整的配置脚本。
它与 gem5 仓库中 `configs/example/gem5_library/x86-ubuntu-run-with-kvm.py` 的示例脚本非常接近。

```python
from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    kvm_required=True,
)

cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
    num_l2_banks=1,
)

memory = SingleChannelDDR3_1600(size="2GiB")

processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=2,
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

workload = obtain_resource("x86-ubuntu-24.04-boot-with-systemd")
board.set_workload(workload)


def exit_event_handler():
    print("First exit: kernel booted")
    yield False  # gem5 is now executing systemd startup
    print("Second exit: Started `after_boot.sh` script")
    # The after_boot.sh script is executed after the kernel and systemd have
    # booted.
    # Here we switch the CPU type to Timing.
    print("Switching to Timing CPU")
    processor.switch()
    yield False  # gem5 is now executing the `after_boot.sh` script
    print("Third exit: Finished `after_boot.sh` script")
    # The after_boot.sh script will run a script if it is passed via
    # readfile_contents. This is the last exit event before the simulation exits.
    yield True


simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)
simulator.run()

```

回顾本教程学到的内容：

* `requires` 函数可用于指定脚本对 gem5 与宿主机的需求。
* `SimpleSwitchableProcessor` 可用于创建能把核心换成其他核心的配置。
* `X86Board` 可用于设置全系统（full-system）模拟。
* 它的工作负载可以通过 `set_workload()` 设置为工作负载资源，或通过 `set_kernel_disk_workload()` 分别设置内核与磁盘镜像资源。
* `set_kernel_disk_workload()` 函数接受一个 `readfile_contents` 参数。
它会被当作脚本处理，在系统启动完成后执行。
* `Simulator` 模块允许用 Python 生成器覆盖退出事件。

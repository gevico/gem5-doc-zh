---
layout: documentation
title: "为配置脚本添加缓存（cache）"
doc: 学习 gem5
parent: part1
permalink: /documentation/learning_gem5/part1/cache_config/
author: Jason Lowe-Power
---

为 gem5 v24.1 编写更复杂的配置
===============================

**注意：以下内容取自 2024 gem5 Boot Camp 第二部分第一节，幻灯片见[此处](https://bootcamp.gem5.org/#02-Using-gem5/01-stdlib)。**

上一节介绍了 gem5 Python 配置脚本的基础知识，其中的 `X86DemoBoard` 已预先配置好缓存（cache）、内存等组件。本节将使用 gem5 标准库中的其他组件来配置模拟（simulation）。

> **译注：版本范围。** 本章前半部分面向 v24.1 标准库；后半部分保留 v21.0 风格的直接配置示例。示例、输出和版本要求均沿用原文，应结合对应版本阅读。

gem5 标准库是什么
----------------------------------

gem5 标准库提供一组预定义组件，可以在配置脚本中用它们描述系统。没有标准库时，你必须自行定义模拟（simulation）的每一个部分，即使是最基础的系统，也可能需要数百行脚本。

基本思想
---------

gem5 采用模块化、面向对象的设计，可以把它理解为一组能够相互连接、组成模拟（simulation）系统的组件。组件主要分为以下几类：

- 板卡（board）：系统的骨架，其他组件接入其中。它还包含设备、工作负载（workload）等系统级内容，并负责协调组件之间的连接。
- 处理器：连接到板卡（board），包含一个或多个核心。
- 缓存（cache）层次结构：由一组缓存（cache）组成，连接处理器和内存系统（memory system）。
- 内存系统（memory system）：由内存控制器与内存设备组成，连接到缓存（cache）层次结构。

与 gem5 模型的关系
---------------------------

gem5 的 C++ 代码定义可配置的模型，在大多数 gem5 文献中称为 SimObject。标准库中预先编写的 Python 脚本负责实例化这些模型，并用统一的 API 将它们封装成“组件”。

模型的粒度较细；组件的粒度较粗，通常包含多个使用合理参数（parameter）实例化的模型。例如，单个核心可以是一个模型，而组件可以是由多个核心构成的处理器，同时定义总线连接，并设置合适的参数（parameter）。

要创建新组件，可以继承标准库中的现有组件，也可以编写全新组件。这样便能自行选择组件内部的模型及其参数（parameter）值。

编写配置脚本
-----------------------------------

首先创建配置文件：

```bash
mkdir configs/tutorial/part1/
touch configs/tutorial/part1/components.py
```

添加导入语句：

```python
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
```

接着创建缓存（cache）层次结构：

```python
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16KiB",
    l1d_assoc=8,
    l1i_size="16KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
    num_l2_banks=1,
)
```

`MESITwoLevelCacheHierarchy` 表示一个采用 MESI 协议（protocol）的两级缓存（cache）层次结构，使用 Ruby 内存模型。gem5 缓存（cache）的更多信息见[此处](https://bootcamp.gem5.org/#02-Using-gem5/05-cache-hierarchies)。该组件通过参数（parameter）指定 L1、L2 的容量和相联度。

接着创建内存系统（memory system）：

```python
memory = SingleChannelDDR4_2400()
```

该组件表示一个单通道 DDR3 内存系统（memory system）。可以用容量参数（parameter）指定被模拟系统的内存大小。可以减小容量以节省模拟（simulation）时间，也可以使用该内存类型的默认容量，例如单通道 DDR3 默认为 8 GiB。标准库也提供多通道内存，详见 2024 gem5 Boot Camp 的[相关幻灯片](https://bootcamp.gem5.org/#02-Using-gem5/06-memory)。

然后添加处理器：

```python
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, isa=ISA.ARM, num_cores=1)
```

`SimpleProcessor` 允许选择底层核心使用的模型，`cpu_type` 参数（parameter）指定 CPU 模型类型。

接着创建板卡（board），并接入这些组件：

```python
board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)
```

`SimpleBoard` 可以在系统调用模拟（syscall emulation，SE）模式下运行任意受支持的指令集架构（ISA）。它之所以称为 “Simple”，是因为 SE 模式相对简单。大多数其他板卡（board）绑定特定指令集架构（ISA），需要更复杂的设计才能运行全系统（full-system，FS）模拟（simulation）。

标准库的板卡（board）位于 `src/python/gem5/components/boards`，演示用的预配置版本位于 `src/python/gem5/prebuilt/demo`。

设置工作负载（workload）：

```python
board.set_workload(obtain_resource("arm-gapbs-bfs-run"))
```

`obtain_resource` 下载运行指定工作负载（workload）所需的文件。这里的 `arm-gapbs-bfs-run` 是 GAP Benchmark Suite 中的广度优先搜索（BFS）程序。全部 gem5 资源可在 [gem5 resources 网站](https://resources.gem5.org/)浏览。

> **译注：** 原文所链接的 `arm-gapbs-bfs-run?version=1.0.0` 资源详情页在翻译时返回 HTTP 404。代码中的资源标识按原文保留，使用时应结合对应版本的资源目录核对；详情页失效本身不能证明所有旧版客户端都无法取得资源。

接着设置模拟（simulation）：

```python
simulator = Simulator(board=board)
simulator.run()
```

现在可以运行：

```bash
./build/ALL/gem5.opt configs/tutorial/part1/components.py

```

输出应类似如下：

```txt
gem5 Simulator System.  https://www.gem5.org
gem5 is copyrighted software; use the --copyright option for details.

gem5 version 24.1.0.0
gem5 compiled Dec 13 2024 14:59:49
gem5 started Dec 16 2024 16:34:29
gem5 executing on amarillo, pid 575999
command line: ./build/ALL/gem5.opt gem5-dev/testing-website-tutorial/tutorial/part1/components.py

info: Using default config
Global frequency set at 1000000000000 ticks per second
src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
board.remote_gdb: Listening for connections on port 7003
src/sim/simulate.cc:199: info: Entering event queue @ 0.  Starting simulation...
src/mem/ruby/system/Sequencer.cc:704: warn: Replacement policy updates recently became the responsibility of SLICC state machines. Make sure to setMRU() near callbacks in .sm files!
src/sim/syscall_emul.cc:86: warn: ignoring syscall set_robust_list(...)
src/sim/syscall_emul.cc:97: warn: ignoring syscall rseq(...)
      (further warnings will be suppressed)
src/sim/mem_state.cc:448: info: Increasing stack size by one page.
src/sim/syscall_emul.hh:1117: warn: readlink() called on '/proc/self/exe' may yield unexpected results in various settings.
      Returning '/home/bees/.cache/gem5/arm-gapbs-bfs'
src/arch/arm/insts/pseudo.cc:174: warn:         instruction 'bti' unimplemented
src/sim/syscall_emul.cc:86: warn: ignoring syscall mprotect(...)
src/sim/syscall_emul.cc:86: warn: ignoring syscall sched_getaffinity(...)
src/sim/mem_state.cc:448: info: Increasing stack size by one page.
src/sim/mem_state.cc:448: info: Increasing stack size by one page.
Generate Time:       0.00503
Build Time:          0.00201
Graph has 1024 nodes and 10496 undirected edges for degree: 10
Trial Time:          0.00011
Trial Time:          0.00010
Trial Time:          0.00010
Trial Time:          0.00009
Trial Time:          0.00011
Trial Time:          0.00010
Trial Time:          0.00010
Trial Time:          0.00010
Trial Time:          0.00010
Trial Time:          0.00013
Average Time:        0.00010

```

gem5 stdlib 的文件结构
--------------------------

gem5 stdlib 位于 `src/python/gem5/`，这里重点关注 `components` 与 `prebuilt` 两个目录：

```txt
gem5/src/python/gem5/components
----/boards
----/cachehierarchies
----/memory
----/processors

gem5/src/python/gem5/prebuilt
----/demo
----/riscvmatched
```

`components` 包含构建系统所需的组件。`prebuilt` 包含各种预配置系统，包括 x86、ARM、RISC-V 的演示系统，以及为 SiFive Unmatched 建模的 `riscvmatched`。

```txt
gem5/src/python/gem5/components
----/boards
    ----/simple
    ----/arm_board
    ----/riscv_board
    ----/x86_board
----/cachehierarchies
----/memory
----/processors
```

其他组件接入板卡（board）。按本节所述版本，`SimpleBoard` 仅支持 SE 模式，`ArmBoard` 仅支持 FS 模式，`X86Board` 和 `RiscvBoard` 同时支持两者。

```text
gem5/src/python/gem5/components
----/boards
----/cachehierarchies
    ----/chi
    ----/classic
    ----/ruby
----/memory
----/processors
```

缓存（cache）层次结构通过固定接口连接处理器和内存：

- Ruby：详细建模缓存一致性（cache coherence）和互连（interconnect）。
- CHI：在 Ruby 中实现基于 Arm CHI 的协议（protocol）。
- Classic 缓存（cache）：由多级交叉开关组成，一致性机制不易扩展。

从 gem5 v24.1 起，ALL 构建可以使用所有 Ruby 缓存一致性（cache coherence）协议（protocol）；预编译二进制程序采用的就是这种构建。

```txt
gem5/src/python/gem5/components
----/boards
----/cachehierarchies
----/memory
    ----/single_channel
    ----/multi_channel
    ----/dramsim
    ----/dramsys
    ----/hbm
----/processors
```

`memory` 目录包含预配置的 (LP)DDR3/4/5 DIMM，提供单通道和多通道内存系统（memory system）。它也集成了 DRAMSim 和 DRAMSys；原文指出，达到准确建模并不一定需要它们，但它们有助于进行模型对比。`hbm` 目录提供 HBM 堆栈模型。

```txt
gem5/src/python/gem5/components
----/boards
----/cachehierarchies
----/memory
----/processors
    ----/generators
    ----/simple
    ----/switchable
```

`processors` 目录主要提供可进一步定制的处理器。

流量发生器会生成合成流量，对外表现为处理器；支持线性、随机及其他更复杂的访问模式。

简单处理器使用默认参数（parameter）和一种指令集架构（ISA）。可切换处理器则允许在模拟（simulation）期间更换处理器类型。

进一步理解处理器
------------------

处理器由核心组成。每个核心持有一个 `BaseCPU` 成员，它才是实际的 CPU 模型。`Processor` 负责与 `CacheHierarchy` 和 `Board` 交互，是按一定结构组织起来的一组核心，通过标准接口定义核心之间、核心与外部组件及板卡（board）之间的连接。

**gem5 提供三类主要处理器模型；把另外两种执行方式也计入时，可以说有四类或五类。**

- `CPUTypes.TIMING`：简单的顺序（in-order）CPU 模型。这是“单周期”CPU：指令获取完成后立即执行，访存操作计入内存系统（memory system）的延迟。适合部分以内存为中心的研究，但不适合大多数需要详细处理器行为的研究。
- `CPUTypes.O3`：基于 Alpha 21264 的详细乱序（out-of-order）CPU 模型，包含 ROB、物理寄存器、LSQ 等结构。如果需要定制模型内部参数（parameter），不要仅使用 `SimpleProcessor`。
- `CPUTypes.MINOR`：高性能顺序（in-order）核心模型，具有可配置的四级流水线。需要定制其内部配置时，同样不要仅使用 `SimpleProcessor`。
- `CPUTypes.ATOMIC`：用于后文介绍的 atomic 模式。
- `CPUTypes.KVM`：[2024 gem5 Boot Camp](https://bootcamp.gem5.org/#02-Using-gem5/08-accelerating-simulation) 对此有详细介绍。

FS 与 SE 模式
-------------

SE 模式把应用程序的系统调用交由宿主操作系统处理，因此无需模拟操作系统，也能运行应用程序。它还可以访问宿主资源，例如用于动态链接的库文件。

不能简单地把 SE 模式看成“更快的 FS”：你必须理解实际建模了什么，以及省略的内容是否会影响结果。gem5 无法保证实现所有系统调用；Linux 变化很快，虽然开发者努力覆盖常见用例，仍然无法涵盖全部情况。遇到未实现的系统调用，可以自行实现、在确认合理的情况下忽略，或者使用 FS 模式。需要提升权限的二进制程序也不能在 SE 模式下正常工作，应使用 FS 模式。

FS 模式覆盖 SE 模式所能执行的任务，并且能模拟更多系统行为，但进入感兴趣的执行区间可能更慢：如果不采用加速手段，每次都需要等待操作系统启动。

由于 SE 模式不模拟操作系统，可能遗漏由系统调用、I/O 或操作系统触发的重要事件，使被模拟系统无法准确反映真实系统。应仔细判断它是否适合自己的用例；拿不准时，通常应选择 FS 模式，而不是冒险使用 SE 模式。

完整启动示例
-----------------

在 x86 系统上完整启动 Ubuntu 24.04 的配置示例见 [gem5 stdlib 文档]({{ site.baseurl }}/documentation/gem5-stdlib/x86-full-system-tutorial)。为了完成整个启动过程，需要定义退出事件处理器：

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
    # m5 readfile. This is the last exit event before the simulation exits.
    yield True

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)
```

第一次退出事件发生时，生成器产生 `False`，继续模拟（simulation）。第二次事件发生时，先切换 CPU，再产生 `False`。第三次事件发生时，产生 `True`，结束模拟（simulation）。

退出事件有多种类型，`Simulator` 为它们提供默认行为，也允许覆盖这些行为。

```python
ExitEvent.EXIT
ExitEvent.CHECKPOINT
ExitEvent.FAIL
ExitEvent.SWITCHCPU
ExitEvent.WORKBEGIN
ExitEvent.WORKEND
ExitEvent.USER_INTERRUPT
ExitEvent.MAX_TICK
```

核心概念：由 Simulator 对象控制模拟（simulation）
--------------------------------------------------

模型，即 SimObject，是细粒度对象，在 Python 脚本中相互连接，组成模拟（simulation）系统。组件则是由一组已配置模型构成的粗粒度对象，由标准库提供。使用标准库时，可以选择板卡（board），再通过接入其中的组件来指定系统特性。

`Simulator` 接受板卡（board）并启动模拟（simulation），同时提供控制 API，用于设置停止与恢复条件、在运行时替换组件，以及决定何时开始和结束等。源码见 [src/python/gem5/simulate/simulator.py](https://github.com/gem5/gem5/blob/stable/src/python/gem5/simulate/simulator.py)。

`Simulator` 的参数（parameter）如下：

- `board`：要模拟的板卡（board），必填。
- `full_system`：是否采用全系统（full-system）模式，通常无需显式指定。

  > **译注：** 原文称默认值为 `False`；相应标准库接口使用 `None` 表示由板卡（board）推断，两者含义不同。较新版本还将此参数（parameter）标记为弃用。
- `on_exit_event`：用于控制模拟（simulation）的数据结构。退出可能由多种原因触发，它允许定制相应行为，上面已有示例。
- `checkpoint_path`：从检查点（checkpoint）恢复时使用的路径，后文会进一步介绍。
- `id`：可选的本次模拟（simulation）名称，供 `multisim` 使用，后文再介绍。

一些常用函数如下：

- `run()`：运行模拟（simulation）。
- `get/set_max_ticks(max_tick)`：获取或设置停止时的绝对 tick 值；达到限制时会产生可处理的 `MAX_TICK` 退出事件。
- `schedule_max_insts(inst_number)`：设置停止前执行的指令数量，达到限制时产生可处理的 `MAX_INSTS` 退出事件。多核情况下，任何一个核心达到这一数量都会触发事件。
- `get_stats()`：以字典形式返回统计信息。

更多细节见 [src/python/gem5/simulate/simulator.py](https://github.com/gem5/gem5/blob/stable/src/python/gem5/simulate/simulator.py)。

创建新的标准库组件
-----------------------------------------

gem5 标准库的设计强调扩展与封装，而非为所有配置都提供参数（parameter）。如果需要不同的内部配置，应通过面向对象的继承机制扩展组件。

下面扩展 `BaseCPUProcessor`，创建一个包含单个乱序（out-of-order）核心的 ARM 处理器。首先导入所需对象：

```python
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.isas import ISA

from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from m5.objects import ArmO3CPU
from m5.objects import TournamentBP
```

创建子类，定制核心的参数（parameter）：

```python
class MyOutOfOrderCore(BaseCPUCore):
    def __init__(self, width, rob_size, num_int_regs, num_fp_regs):
        super().__init__(ArmO3CPU(), ISA.ARM)
        self.core.fetchWidth = width
        self.core.decodeWidth = width
        self.core.renameWidth = width
        self.core.issueWidth = width
        self.core.wbWidth = width
        self.core.commitWidth = width

        self.core.numROBEntries = rob_size

        self.core.numPhysIntRegs = num_int_regs
        self.core.numPhysFloatRegs = num_fp_regs

        self.core.branchPred = TournamentBP()

        self.core.LQEntries = 128
        self.core.SQEntries = 128
```

然后使用这个核心创建处理器。`BaseCPUProcessor` 接受由 `BaseCPUCore` 对象组成的列表。这里仅创建一个核心，并向它传入参数（parameter）：

```python
class MyOutOfOrderProcessor(BaseCPUProcessor):
    def __init__(self, width, rob_size, num_int_regs, num_fp_regs):
        cores = [MyOutOfOrderCore(width, rob_size, num_int_regs, num_fp_regs)]
        super().__init__(cores)
```

利用这些组件配置模拟（simulation）所需的处理器：

```python
my_ooo_processor = MyOutOfOrderProcessor(
    width=8, rob_size=192, num_int_regs=256, num_fp_regs=256
)
```

最后设置其余部分：

```python
main_memory = SingleChannelDDR4_2400(size="2GB")

cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16kB",
    l1d_assoc=8,
    l1i_size="16kB",
    l1i_assoc=8,
    l2_size="256kB",
    l2_assoc=16,
    num_l2_banks=1,
)
board = SimpleBoard(
    processor=my_ooo_processor,
    memory=main_memory,
    cache_hierarchy=cache_hierarchy,
    clk_freq="3GHz",
)

board.set_workload(obtain_resource("arm-gapbs-bfs-run"))

simulator = Simulator(board)
simulator.run()
```

假设脚本名为 `config.py`，可以用以下命令运行：

```bash
./build/ALL/gem5.opt config.py
```

如果使用预构建的二进制程序，则执行：

```bash
gem5 config.py
```

gem5 v21.0：为配置脚本添加缓存（cache）
====================================================

以[上一章的配置脚本]({{ site.baseurl }}/documentation/learning_gem5/part1/simple_config/)为起点，下面构建更复杂的系统，加入如下图所示的缓存（cache）层次结构。这部分内容还会说明如何为脚本添加命令行参数（parameter），并为理解 gem5 统计输出打下基础。

![具有两级缓存（cache）层次结构的系统配置。]({{ site.baseurl }}/pages/static/figures/advanced_config.png)

创建缓存（cache）对象
----------------------

这里使用 Classic 缓存（cache），因为系统只有一个 CPU，暂不关注缓存一致性（cache coherence）的详细建模，也就不需要使用后续 Ruby 章节中的模型。我们将扩展 `Cache` SimObject 并配置它，首先需要了解其参数（parameter）。

> **Classic 缓存（cache）与 Ruby**
>
> gem5 提供两套不同的片上缓存（cache）建模子系统：Classic 与 Ruby。这源于项目的历史：gem5 由密歇根大学的 m5 与威斯康星大学的 GEMS 合并而来。GEMS 使用 Ruby，Classic 则来自 m5 代码库，名称中的 “classic” 也由此而来。
>
> Ruby 旨在详细建模缓存一致性（cache coherence）。其中的 SLICC 语言用于定义缓存一致性（cache coherence）协议（protocol）。Classic 则实现了经过简化、扩展性较弱的 MOESI 协议（protocol）。
>
> 选择时，应先明确研究对象。如果要修改一致性协议（protocol），或其行为可能对结果产生主要影响，应使用 Ruby；如果这些行为不是研究重点，则可以使用 Classic。
>
> 原文提出，gem5 的长期目标之一是将两种模型统一为一个完整模型。

### Cache

`Cache` SimObject 的声明位于 `src/mem/cache/Cache.py`。这个 Python 文件定义可配置的参数（parameter）；实例化 SimObject 时，gem5 会把它们传给 C++ 实现。`Cache` 继承自 `BaseCache`。

`BaseCache` 包含许多参数（parameter）。例如，`assoc` 是整数；`write_buffers` 等项带有默认值，此处为 8。`Param.*` 接受两个位置实参时，第一个是默认值，第二个是说明；只接受一个时，该实参是说明，表示未设置默认值。例如 `tag_latency = Param.Cycles("Tag lookup latency")` 只提供标签查找延迟的说明。

> **译注：** 原文将“第一个实参为字符串”作为区分依据，并不准确。时间、容量等类型的默认值也可以是字符串；应根据实参数量与对应类型判断。

其中许多参数（parameter）没有默认值，必须在调用 `m5.instantiate()` 前设置。

* * * * *

为了创建指定配置的缓存（cache），先在 `simple.py` 所在的 `configs/tutorial/part1` 目录中创建 `caches.py`，导入将要扩展的 SimObject：

```
from m5.objects import Cache
```

然后像扩展普通 Python 类一样扩展缓存（cache）类，并为新类型命名。先定义 L1：

```
class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
```

这里设置了若干没有默认值的参数（parameter）。所有配置选项及其必填、可选属性，都应查看对应 SimObject 的源码；这里主要查看 `BaseCache`。

现在已经通过继承设置了 `BaseCache` 中大部分无默认值的参数（parameter）。接着从 `L1Cache` 派生出 `L1DCache` 和 `L1ICache`：

```
class L1ICache(L1Cache):
    size = '16kB'

class L1DCache(L1Cache):
    size = '64kB'
```

再定义一个采用合理配置的 L2 缓存（cache）：

```
class L2Cache(Cache):
    size = '256kB'
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
```

必要参数（parameter）设置完成后，只需实例化这些子类，并接入互连（interconnect）。不过，将大量对象连接到复杂网络会使配置脚本迅速膨胀，难以阅读。因此先给 `Cache` 子类添加辅助函数。它们本质上都是 Python 类，可以使用普通 Python 类的所有功能。

为 `L1Cache` 添加 `connectCPU` 和 `connectBus`，分别连接 CPU 与总线：

```
def connectCPU(self, cpu):
    # need to define this in a base class!
    raise NotImplementedError

def connectBus(self, bus):
    self.mem_side = bus.cpu_side_ports
```

指令和数据缓存（cache）对应的 CPU 端口（port）名称不同，因此需要分别实现 `connectCPU`。两个子类变为：

```
class L1ICache(L1Cache):
    size = '16kB'

    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port

class L1DCache(L1Cache):
    size = '64kB'

    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port
```

最后，为 `L2Cache` 添加分别连接内存侧与 CPU 侧总线的函数：

```
def connectCPUSideBus(self, bus):
    self.cpu_side = bus.mem_side_ports

def connectMemSideBus(self, bus):
    self.mem_side = bus.cpu_side_ports
```

完整文件见 [`configs/learning_gem5/part1/caches.py`](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part1/caches.py)。

在简单配置中加入缓存（cache）
------------------------------------

现在把刚创建的缓存（cache）加入[上一章]({{ site.baseurl }}/documentation/learning_gem5/part1/simple_config/)的脚本。先复制脚本，使用新的文件名：

```
cp ./configs/tutorial/part1/simple.py ./configs/tutorial/part1/two_level.py
```

像普通 Python 程序一样，在文件顶部、导入 `m5.objects` 之后，从 `caches.py` 导入所需名称：

```
from caches import *
```

创建 CPU 后，创建 L1 缓存（cache）：

```
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()
```

使用辅助函数连接 CPU 端口（port）：

```
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)
```

必须*删除*原先将 CPU 直接接到内存总线的两行代码：

```
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports
```

L2 只提供一个相应连接端口（port），不能直接同时连接两个 L1。因此需要创建 L2 总线，再用辅助函数把两个 L1 接到这条总线上：

```
system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)
```

接着创建 L2，将它分别连接到 L2 总线与内存总线：

```
system.l2cache = L2Cache()
system.l2cache.connectCPUSideBus(system.l2bus)
system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)
```

注意，在调用 `system.l2cache.connectMemSideBus` 之前，已经通过 `system.membus = SystemXBar()` 创建了内存总线，因此可以将它传入该函数。文件其余部分保持不变。至此，两级缓存（cache）配置就完整了。原文示例中，运行此脚本时 `hello` 在 57467000 个 tick 后结束。完整脚本见 [`configs/learning_gem5/part1/two_level.py`](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part1/two_level.py)。

为脚本添加参数（parameter）
--------------------------------

使用 gem5 做实验时，不宜每测试一组配置就手动修改脚本。可以为配置脚本加入命令行参数（parameter）。脚本本身是 Python，因此可以使用 Python 的命令行解析库。

虽然 `optparse` 已被弃用，但许多旧 gem5 脚本仍在使用它，因为 gem5 曾只要求 Python 2.5。原文这一版本所述的最低要求已提升为 Python 3.6，因此编写无需兼容旧脚本的新代码时，`argparse` 是更好的选择。`optparse` 的用法可查阅 Python 在线文档。

> **译注：** 原文使用 `pyoptparse`、`pyargparse` 等写法，这里按 Python 模块名译为 `optparse`、`argparse`；Python 最低版本要求属于本节历史背景，并非对当前 gem5 的要求。

在导入缓存（cache）类后，添加两级配置所需的选项：

```
import argparse

parser = argparse.ArgumentParser(description='A simple system with 2-level cache.')
parser.add_argument("binary", default="", nargs="?", type=str,
                    help="Path to the binary to execute.")
parser.add_argument("--l1i_size",
                    help=f"L1 instruction cache size. Default: 16kB.")
parser.add_argument("--l1d_size",
                    help="L1 data cache size. Default: Default: 64kB.")
parser.add_argument("--l2_size",
                    help="L2 cache size. Default: 256kB.")

options = parser.parse_args()
```

如果像上面那样通过选项传入二进制文件路径，应使用 `options.binary` 访问它。例如：

```
system.workload = SEWorkload.init_compatible(options.binary)
```

现在运行 `build/ALL/gem5.opt configs/tutorial/part1/two_level.py --help`，即可看到刚添加的选项。

接着把这些选项传给配置脚本中创建的缓存（cache）。修改 `two_level_opts.py`，将选项作为构造函数实参传入，随后再添加对应的构造函数：

```
system.cpu.icache = L1ICache(options)
system.cpu.dcache = L1DCache(options)
...
system.l2cache = L2Cache(options)
```

在 `caches.py` 中，为各个类添加 Python 构造函数 `__init__`。先处理基础 `L1Cache`：目前没有适用于它的选项，所以只需添加空构造函数，但不能漏掉父类构造函数调用。否则，gem5 的 SimObject 属性查找会失败，实例化时将出现 `RuntimeError: maximum recursion depth exceeded`。在类的静态成员之后添加：

```
def __init__(self, options=None):
    super(L1Cache, self).__init__()
    pass
```

在 `L1ICache` 中，用 `l1i_size` 设置容量。下面同时检查是否传入 `options`，以及命令行是否指定该选项；若没有，则保留此前定义的默认容量。

```
def __init__(self, options=None):
    super(L1ICache, self).__init__(options)
    if not options or not options.l1i_size:
        return
    self.size = options.l1i_size
```

`L1DCache` 使用同样的方式：

```
def __init__(self, options=None):
    super(L1DCache, self).__init__(options)
    if not options or not options.l1d_size:
        return
    self.size = options.l1d_size
```

统一的 `L2Cache` 也一样：

```
def __init__(self, options=None):
    super(L2Cache, self).__init__()
    if not options or not options.l2_size:
        return
    self.size = options.l2_size
```

修改完成后，可以在命令行中传入各级缓存（cache）的容量：

```
build/ALL/gem5.opt configs/tutorial/part1/two_level.py --l2_size='1MB' --l1d_size='128kB'
```

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 version 21.0.0.0
    gem5 compiled May 17 2021 18:05:59
    gem5 started May 18 2021 00:00:33
    gem5 executing on amarillo, pid 83118
    command line: build/X86/gem5.opt configs/tutorial/part1/two_level.py --l2_size=1MB --l1d_size=128kB

    Global frequency set at 1000000000000 ticks per second
    warn: No dot file generated. Please install pydot to generate the dot file and pdf.
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb: listening for remote gdb on port 7005
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 57467000 because exiting with last active thread context

完整脚本见 [`configs/learning_gem5/part1/caches.py`](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part1/caches.py) 和 [`configs/learning_gem5/part1/two_level.py`](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part1/two_level.py)。

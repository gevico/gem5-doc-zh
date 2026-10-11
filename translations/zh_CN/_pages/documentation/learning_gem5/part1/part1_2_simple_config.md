---
layout: documentation
title: "创建简单的配置脚本"
doc: 学习 gem5
parent: part1
permalink: /documentation/learning_gem5/part1/simple_config/
author: Jason Lowe-Power
---

创建简单的配置脚本
======================================

本章将带你编写一个简单的 gem5 模拟（simulation）脚本，并首次运行 gem5。这里假设你已经完成第一章，成功构建了 `build/ALL/gem5.opt` 可执行文件。

本章中的基础配置将为一个非常简单的系统建模：一个简单 CPU 核心连接到系统内存总线，一个 DDR3 内存通道也连接到这条总线。

> **译注：版本范围。** 本章先介绍 gem5 v24.1 的标准库示例，再介绍 v21.0 风格的底层配置。前者使用预配置的 `X86DemoBoard`，后者才是上述单核、单通道 DDR3 系统；两套示例应分别阅读。原文中的 `configs/examples` 和 `configs/examples/gem5-library` 与所引用源码目录的拼写不一致，请以对应版本源码中的 `configs/example` 和 `configs/example/gem5_library` 为准。

gem5 配置脚本
--------------------------

gem5 可执行文件接受一个 Python 脚本作为参数（parameter），由该脚本配置并执行模拟（simulation）。你需要在脚本中创建待模拟的系统及其各个组件，设置组件的参数（parameter），然后启动模拟（simulation）。

<!-- 配置脚本完全由用户定义，可以使用任何合法的 Python 代码。本书提供的示例大量使用 Python 的类和继承；脚本要写得简单还是复杂，由 gem5 用户自行决定。 -->

<!-- 许多已有脚本包罗万象，允许用户通过命令行指定几乎所有选项。本书从能够运行 gem5 的最简单脚本开始，再逐步扩展，帮助读者理解模拟脚本的工作方式。 -->

gem5 在 `configs/examples` 中提供了一些配置脚本示例。对于初学者，最相关的脚本位于 `configs/examples/gem5-library`。这些脚本使用 gem5 标准库；标准库提供的组件可以相互连接，组成完整系统。

---

> **关于 SimObject**
>
> gem5 的模块化设计以 **SimObject** 类型为核心。被模拟系统的大多数组件都是 SimObject，例如 CPU、缓存（cache）、内存控制器和总线。gem5 将这些对象的 `C++` 实现暴露给 Python，因此可以在 Python 配置脚本中创建 SimObject、设置其参数（parameter），并指定对象之间的交互关系。
>
> 更多信息见 [SimObject details](http://doxygen.gem5.org/release/current/classgem5_1_1SimObject.html#details)。

---

为 gem5 v24.1 编写配置脚本
================================================

**注意：本节内容取自 2024 gem5 Boot Camp 第一部分第二节，幻灯片见[此处](https://bootcamp.gem5.org/#01-Introduction/02-getting-started)。**

首先创建并打开一个新的配置文件：

```bash
mkdir configs/tutorial/part1/
touch configs/tutorial/part1/simple.py
```

这只是一个普通的 Python 文件，由 gem5 可执行文件内嵌的 Python 解释器执行。因此，你可以使用该 Python 环境提供的各种功能和库。

先添加基本配置所需的导入语句：

```python
from gem5.prebuilt.demo.x86_demo_board import X86DemoBoard
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
```

接着在脚本中添加一个板卡（board）：

```python
board = X86DemoBoard()
```

`X86DemoBoard` 是预先配置好的板卡（board），无需进一步配置即可作为完整系统使用。不过，不建议将它直接用于研究。

其源码位于 gem5 仓库（repository）的 [src/python/gem5/prebuilt/demo/x86_demo_board.py](https://github.com/gem5/gem5/blob/stable/src/python/gem5/prebuilt/demo/x86_demo_board.py)。它具有以下配置：

- 3 GiB 的 `DualChannelDDR4_2400` 内存。
- 一个使用 gem5 `TIMING` 模型的双核处理器。
- 私有 L1、共享 L2 的缓存（cache）层次结构：指令和数据缓存（cache）各为 64 KiB，L2 缓存（cache）为 8 MiB。

从 gem5 v24.1 起，`X86DemoBoard` 同时支持系统调用模拟（syscall emulation，SE）和全系统（full-system，FS）模式。

接着设置要在板卡（board）上运行的工作负载（workload）：

```python
board.set_workload(
    obtain_resource("x86-ubuntu-24.04-boot-no-systemd")
)
```

`obtain_resource` 函数用于下载工作负载（workload）和资源。对于 `x86-ubuntu-24.04-boot-no-systemd`，它会下载磁盘镜像与内核，并设置默认参数（parameter）。

这个工作负载（workload）会启动不使用 systemd 的 Ubuntu。它包含三个退出事件；每次触发退出事件时，都可以结束模拟（simulation）或执行其他操作。要改变这些事件发生时的行为，需要设置退出事件处理器。

不过，本例只运行 200 亿个 tick，即 20 ms 的模拟（simulation）时间：

```python
sim = Simulator(board)
sim.run(20_000_000_000) # 20 billion ticks or 20 ms
```

配置脚本准备好后，用以下命令运行：

```bash
./build/ALL/gem5.opt configs/tutorial/part1/simple.py
```

如果使用预构建的 gem5 二进制程序，则执行：

```bash
gem5 configs/tutorial/part1/simple.py
```

输出应类似如下：

```txt
gem5 Simulator System.  https://www.gem5.org
gem5 is copyrighted software; use the --copyright option for details.

gem5 version 24.1.0.0
gem5 compiled Dec 13 2024 14:59:49
gem5 started Dec 16 2024 13:07:46
gem5 executing on amarillo, pid 543078
command line: ./build/ALL/gem5.opt gem5-dev/testing-website-tutorial/tutorial/part1/simple.py

warn: The X86DemoBoard is solely for demonstration purposes. This board is not known to be be representative of any real-world system. Use with caution.
info: Using default config
warn: Max ticks has already been set prior to setting it through the run call. In these cases the max ticks set through the `run` function is used
Global frequency set at 1000000000000 ticks per second
warn: board.workload.acpi_description_table_pointer.rsdt adopting orphan SimObject param 'entries'
src/mem/dram_interface.cc:690: warn: DRAM device capacity (16384 Mbytes) does not match the address range assigned (2048 Mbytes)
src/mem/dram_interface.cc:690: warn: DRAM device capacity (16384 Mbytes) does not match the address range assigned (2048 Mbytes)
src/sim/kernel_workload.cc:46: info: kernel located at: /home/bees/.cache/gem5/x86-linux-kernel-5.4.0-105-generic
      0: board.pc.south_bridge.cmos.rtc: Real-time clock set to Sun Jan  1 00:00:00 2012
board.pc.com_1.device: Listening for connections on port 3467
src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
src/dev/intel_8254_timer.cc:128: warn: Reading current count from inactive timer.
board.remote_gdb: Listening for connections on port 7003
src/sim/simulate.cc:199: info: Entering event queue @ 0.  Starting simulation...
build/ALL/arch/x86/generated/exec-ns.cc.inc:27: warn: instruction 'fninit' unimplemented

```

为 gem5 v21.0 编写配置脚本
==============

创建配置文件
----------------------

首先创建并打开一个新的配置文件：

```bash
mkdir configs/tutorial/part1/
touch configs/tutorial/part1/simple.py
```

这是一个普通的 Python 文件，由 gem5 可执行文件内嵌的 Python 解释器执行，因此可以使用该环境提供的 Python 功能和库。

> **译注：** 原文把以下导入语句放在 HTML 注释中，因此网页不显示。若单独编写本节的旧版脚本，仍须先写入 `import m5` 和 `from m5.objects import *`，再创建 `System`。

<!-- 在文件中首先导入 m5 库以及已编译的所有 SimObject。

```python
import m5
from m5.objects import *
```
-->

接着创建第一个 SimObject，也就是待模拟的系统。`System` 对象将作为系统中其他所有对象的父对象。它保存许多功能层面的信息，而非时序层面的信息，例如物理内存地址范围、根时钟域（clock domain）、根电压域，以及全系统（full-system）模式使用的内核。创建系统 SimObject 与实例化普通 Python 类一样：

```python
system = System()
```

取得系统对象后，为它设置时钟。首先创建时钟域（clock domain），然后设置该域的时钟频率。给 SimObject 设置参数（parameter）与给 Python 对象的成员赋值完全相同，例如可以直接把频率设置为 1 GHz。最后还需要指定该时钟域（clock domain）所属的电压域。这里暂不研究系统功耗，因此使用电压域的默认配置。

```python
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()
```

接着设置内存的模拟（simulation）方式。这里使用 *timing* 模式；除快速前进和从检查点（checkpoint）恢复等特殊情况外，内存模拟（simulation）通常都使用这一模式。我们还设置一个大小为 512 MB 的内存地址范围，构成一个很小的系统。

在 Python 配置脚本中，需要指定容量时可以使用 `'512MB'` 这样的常用写法和单位；时间也可以写成 `'5ns'`。gem5 会自动把它们转换为各自统一的内部表示。

```python
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]
```

现在创建 CPU。先使用 gem5 中面向 x86 指令集架构（ISA）的简单时序 CPU：`X86TimingSimpleCPU`。在这一简化模型中，普通指令的执行按单周期处理，访存请求则经过内存系统（memory system），并计入相应的时序。直接实例化即可：

```python
system.cpu = X86TimingSimpleCPU()
```

如果使用 RISC-V 指令集架构（ISA），可以选择 `RiscvTimingSimpleCPU`；如果使用 ARM，则可以选择 `ArmTimingSimpleCPU`。本练习继续使用 x86。

然后创建系统内存总线：

```
system.membus = SystemXBar()
```

有了内存总线，就可以把 CPU 的缓存（cache）端口（port）接到总线上。由于本例没有缓存（cache），因此直接把指令侧和数据侧端口（port）连接到 `membus`：

```
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports
```

---

> **关于 gem5 的端口（port）**
>
> gem5 使用端口（port）抽象来连接内存系统（memory system）中的组件。内存对象可以有两类端口（port）：*请求端口（request port）*与*响应端口（response port）*。请求从前者发送到后者，响应则沿相反方向发送。连接时必须把请求端口（request port）与响应端口（response port）配对。
>
> 在 Python 配置文件中，只需用 `=` 将二者连接起来。例如：
>
> ```python
> system.cpu.icache_port = system.l1_cache.cpu_side
> ```
>
> 这里，CPU 的 `icache_port` 是请求端口（request port），而缓存（cache）的 `cpu_side` 是响应端口（response port）。两者放在 `=` 的哪一侧都能建立相同的连接。连接完成后，请求方就能向响应方发送请求。gem5 会在内部完成连接所需的处理，大多数用户无需关注其细节。
>
> gem5 的 Python 配置还有一个值得注意的特性：`=` 的一侧可以是单个端口（port），另一侧可以是端口（port）数组。例如：
>
> ```python
> system.cpu.icache_port = system.membus.cpu_side_ports
> ```
>
> 这里，`icache_port` 是请求端口（request port），`cpu_side_ports` 是响应端口（response port）数组。赋值时，gem5 会在数组中新增一个响应端口（response port），并将它连接到请求方。
>
> [MemObject 一章]({{ site.baseurl }}/documentation/learning_gem5/part2/memoryobject/)会进一步介绍这些接口。

---

接着还要连接几个端口（port），确保系统正常工作。为 CPU 创建中断控制器，并将其连接到内存总线；还要把系统的一个特殊端口（port）连接到 `membus`，供系统执行功能性内存读写。

> **译注：** 原文此处称为 “I/O controller”，而紧随其后的代码调用的是 `createInterruptController()`，因此这里按代码含义译为“中断控制器”。

把 PIO 和中断端口（port）接到内存总线是 x86 的特定要求，ARM 等其他指令集架构（ISA）不需要下面这三行额外连接代码。

```
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports
```

然后创建内存控制器，并将它连接到 `membus`。本例使用一个简单的 DDR3 控制器，负责整个系统的内存地址范围。

```
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports
```

完成这些连接后，被模拟系统就实例化好了，其结构如下图所示。

![不含缓存（cache）的简单系统配置。]({{ site.baseurl }}/pages/static/figures/simple_config.png)

接着设置 CPU 要执行的进程。这里采用系统调用模拟（syscall emulation，SE）模式，只需为 CPU 指定编译好的可执行文件。我们将运行 gem5 附带的、已经编译好的 “Hello world” 程序。也可以指定其他面向 x86 静态编译的应用程序。

> **全系统（full-system）与系统调用模拟（syscall emulation）**
>
> gem5 有两种运行模式：系统调用模拟（syscall emulation，SE）和全系统（full-system，FS）。FS 模式对完整硬件系统建模，并运行未经修改的内核，使用方式类似于运行虚拟机。
>
> SE 模式不对系统中的所有设备建模，而是重点模拟 CPU 与内存系统（memory system）。它不要求实例化真实系统所需的全部硬件设备，因此配置更简单。但它只仿真 Linux 系统调用，所以仅对用户态代码建模。
>
> 如果研究问题不需要对操作系统建模，而且希望获得更高的模拟（simulation）速度，可以使用 SE 模式。如果需要高保真系统建模，或者页表遍历等操作系统交互对研究很重要，就应使用 FS 模式。

首先创建进程对象，它也是一个 SimObject。然后将其命令设置为要执行的程序；该命令采用类似 `argv` 的列表形式，第一项为可执行文件，后续各项为程序的参数（parameter）。再把进程设为 CPU 的工作负载（workload），最后创建 CPU 内部的功能性执行上下文。

```
binary = 'tests/test-progs/hello/bin/x86/linux/hello'

# for gem5 V21 and beyond
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()
```

最后实例化系统并开始执行。先创建 `Root` 对象，再实例化模拟（simulation）。实例化过程会遍历在 Python 中创建的全部 SimObject，为它们创建对应的 `C++` 对象。

不一定要先创建 Python 对象，再逐个给成员赋值。也可以像下面的 `Root` 一样，通过关键字实参直接传入参数（parameter）。

```
root = Root(full_system = False, system = system)
m5.instantiate()
```

现在可以真正启动模拟（simulation）了。注意，gem5 已使用 Python 3 风格的 `print` 函数；`print` 不再是一条语句，必须以函数形式调用。

```
print("Beginning simulation!")
exit_event = m5.simulate()
```

模拟（simulation）结束后，可以检查系统状态：

```
print('Exiting @ tick {} because {}'
      .format(m5.curTick(), exit_event.getCause()))
```

运行 gem5
------------

简单脚本已经完成，完整版本可在 gem5 源码的 [configs/learning\_gem5/part1/simple.py](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part1/simple.py) 中找到。gem5 接受很多参数（parameter），但必需的位置实参只有配置脚本一个。因此，从 gem5 根目录运行：

```
build/ALL/gem5.opt configs/tutorial/part1/simple.py
```

输出应如下所示：

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 version 21.0.0.0
    gem5 compiled May 17 2021 18:05:59
    gem5 started May 17 2021 22:05:20
    gem5 executing on amarillo, pid 75197
    command line: build/X86/gem5.opt configs/tutorial/part1/simple.py

    Global frequency set at 1000000000000 ticks per second
    warn: No dot file generated. Please install pydot to generate the dot file and pdf.
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb: listening for remote gdb on port 7005
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 490394000 because exiting with last active thread context

修改配置文件中的参数（parameter）后，结果也会发生变化。例如，将系统时钟频率加倍，程序通常会在更短的模拟（simulation）时间内完成；将 DDR 控制器换为 DDR4，也可能改善性能。

还可以把 CPU 模型改为 `X86MinorCPU`，对顺序（in-order）CPU 建模；或改为 `X86O3CPU`，对乱序（out-of-order）CPU 建模。不过，`X86O3CPU` 不能直接使用这里的 `simple.py` 配置，因为它要求独立的指令和数据缓存（cache）。下一节的配置可以满足这一要求。

gem5 的 BaseCPU 派生类采用 `{ISA}{Type}CPU` 的命名格式。例如，RISC-V 的 Minor CPU 对应 `RiscvMinorCPU`。

可用的指令集架构（ISA）前缀为：

- Riscv
- Arm
- X86
- Sparc
- Power
- Mips

CPU 类型包括：

- AtomicSimpleCPU
- O3CPU
- TimingSimpleCPU
- KvmCPU
- MinorCPU

> **译注：** 原文列表将 `TimingSimpleCPU` 误写为 `TimingSimpleCPu`，此处按类名修正。具体版本支持哪些组合，应以该版本源码为准。

下一节将为配置添加缓存（cache），建立更复杂的系统模型。

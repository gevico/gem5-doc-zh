---
layout: documentation
title: Hello World Tutorial
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/hello-world-tutorial
author: Bobby R. Bruce
---

## 用 gem5 标准库（standard library）构建 “Hello World” 示例

在本教程中，我们将介绍如何用 gem5 组件（component）创建一个非常基础的模拟（simulation）。
该模拟将建立一个由单核处理器组成的系统，运行在 Atomic 模式下，直接连接到主存，没有缓存、I/O 或其他组件。
该系统将在系统调用模拟（syscall emulation，SE）模式下运行一个 X86 二进制程序。
该二进制程序将从 gem5-resources 获取，执行时会向 stdout 打印 "Hello World!" 字符串。

首先我们必须编译 gem5 的 ALL 构建：

```sh
# In the root of the gem5 directory
scons build/ALL/gem5.opt -j <number of threads>
```

自 gem5 v24.1 起，ALL 构建包含所有 Ruby 协议和所有指令集架构（ISA）。如果你使用预构建的 gem5 二进制程序，则无需这一步。

然后应创建一个新的 Python 文件（下文中我们称之为 `hello-world.py`）。
该文件的前几行应是所需的 import：

```python
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
```

所有这些库都包含在编译好的 gem5 二进制程序中。
因此你无需从别处获取它们。
`from gem5.` 表示我们从 `gem5` 标准库导入，而以 `from gem5.components` 开头的行从 gem5 components 包导入组件。
`from gem5.resources` 这一行表示我们从 resources 包导入，`from gem5.simulate` 则从 simulate 包导入。
这些包 `components`、`resources` 和 `simulate` 都是 gem5 标准库的一部分。

接下来我们开始指定系统。
gem5 库要求用户指定四个主要组件：*板卡（board）*、*缓存层次结构（cache hierarchy）*、*内存系统（memory system）*和*处理器（processor）*。

先从*缓存层次结构*开始：

```python
cache_hierarchy = NoCache()
```

这里我们使用 `NoCache()`。
这意味着我们声明系统中没有缓存层次结构（即没有缓存）。
在 gem5 库中，缓存层次结构是一个宽泛的说法，指处理器核心与主存之间存在的任何东西。
这里我们声明处理器直接连接到主存。

接下来声明*内存系统*：

```python
memory = SingleChannelDDR3_1600("1GiB")
```

`gem5.components.memory` 中可供选择的 memory 组件有很多。
这里我们使用单通道 DDR3 1600，并把大小设为 1 GiB。
需要注意的是，在这里设置大小在技术上是可以省略的。
如果不设置，`SingleChannelDDR3_1600` 会默认使用 8 GiB。

然后考虑*处理器*：

```python
processor = SimpleProcessor(cpu_type=CPUTypes.ATOMIC, num_cores=1, isa=ISA.X86)
```

`gem5.components` 中的 processor 是一个对象，它包含若干 gem5 CPU 核心，核心类型可为某一种或多种（`ATOMIC`、`TIMING`、`KVM`、`O3` 等）。
本示例使用的 `SimpleProcessor` 是一种所有 CPU 核心类型都相同的处理器。
它需要两个参数：`cpu_type`（我们设为 `ATOMIC`）和 `num_cores`（核心数量，我们设为 1）。

最后我们指定使用哪个*板卡*：

```python
board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)
```

虽然每个板卡的构造函数可能不同，但它们通常都要求用户指定*处理器*、*内存系统*和*缓存层次结构*，以及要使用的时钟频率。
在本示例中我们使用 `SimpleBoard`。
`SimpleBoard` 是一个非常基础、没有 I/O 的系统，只支持 SE 模式，并且只能配合 "classic" 缓存层次结构使用。

到这里，脚本中我们已经指定了模拟系统所需的一切。
当然，要运行有意义的模拟，我们还必须指定该系统要运行的工作负载（workload）。
为此我们加入以下行：

```python
binary = obtain_resource("x86-hello64-static")
board.set_se_binary_workload(binary)
```

`obtain_resource` 函数接受一个字符串，指定要从 [gem5-resources](/documentation/general_docs/gem5_resources) 获取哪个资源用于模拟。
所有 gem5 资源都可以在 [gem5 Resources 网站](https://resources.gem5.org)上找到。

如果宿主机上没有该资源，它会自动被下载。
在本示例中我们将使用 `x86-hello-64-static` 资源；
它是一个 x86、64 位、静态编译的二进制程序，会向 stdout 打印 "Hello World!"。
指定资源之后，我们通过板卡的 `set_se_binary_workload` 函数设置工作负载。
顾名思义，`set_se_binary_workload` 是用于设置在系统调用模拟（Syscall Execution）模式下执行的二进制程序的函数。

你可以在 [gem5 resources 网站](https://resources.gem5.org/)上查看和搜索可用资源。

设置模拟所需的全部内容就是这些。
接下来你只需构造并运行 `Simulator`：

```python
simulator = Simulator(board=board)
simulator.run()
```

回顾一下，你的脚本应如下所示：

```python
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

# Obtain the components.
cache_hierarchy = NoCache()
memory = SingleChannelDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=CPUTypes.ATOMIC, num_cores=1, isa=ISA.X86)

# Add them to the board.
board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the workload.
binary = obtain_resource("x86-hello64-static")
board.set_se_binary_workload(binary)

# Setup the Simulator and run the simulation.
simulator = Simulator(board=board)
simulator.run()
```

随后可以用以下命令执行它：

```sh
./build/ALL/gem5.opt hello-world.py
```

如果你使用预构建的二进制程序，可以用以下命令执行该模拟：

```sh
gem5 hello-world.py
```

如果配置正确，输出会类似：

```text
info: Using default config
Global frequency set at 1000000000000 ticks per second
src/mem/dram_interface.cc:690: warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (1024 Mbytes)
src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
board.remote_gdb: Listening for connections on port 7005
src/sim/simulate.cc:199: info: Entering event queue @ 0.  Starting simulation...
src/sim/syscall_emul.hh:1117: warn: readlink() called on '/proc/self/exe' may yield unexpected results in various settings.
src/sim/mem_state.cc:448: info: Increasing stack size by one page.
Hello world!
```

从这里应能明显看出，可以修改*板卡*的参数来测试其他设计。
例如，如果我们要测试 `TIMING` CPU 配置，就把*处理器*改为：

```python
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=1, isa=ISA.X86)
```

要做的事就这么多。
gem5 标准库会按需重新配置设计。

再举一例，考虑把某个组件换成另一个。
在这个设计中我们选择了 `NoCache`，但也可以使用其他 classic 缓存层次结构，例如 `PrivateL1CacheHierarchy`。
为此我们修改 `cache_hierarchy` 参数：

```python
# We import the cache hierarchy we want.
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import PrivateL1CacheHierarchy

...

# Then set it.
cache_hierarchy = PrivateL1CacheHierarchy(l1d_size="32KiB", l1i_size="32KiB")
```

注意这里 `PrivateL1CacheHierarchy` 要求用户指定 L1 数据与指令缓存的大小才能构造。
设计的其他部分无需改动。
gem5 标准库会按需纳入该缓存层次结构。

回顾本教程学到的内容：

* 可以使用 gem5 components 包，借助*处理器*、*缓存层次结构*、*内存系统*和*板卡*组件构建系统。
* 一般而言，同类型组件尽可能可以互换。例如，不同的*缓存层次结构*组件可以在设计中换入换出，而无需重新配置其他组件。
* *板卡*包含用于设置工作负载的函数。
* resources 包可用于从 gem5-resources 获取预构建资源。
它们通常是可以经由设置工作负载的函数运行的工作负载。
* simulate 包可用于在 gem5 模拟中运行一个板卡。

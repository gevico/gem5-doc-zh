---
layout: documentation
title: How To Create Your Own Board Using The gem5 Standard Library
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/develop-stdlib-board
author: Jasjeet Rangi, Kunal Pai
---

## 如何使用 gem5 标准库创建自己的板卡

在本教程中，我们将介绍如何使用 gem5 标准库创建自定义板卡。

本教程基于制作 _RiscvMatched_ 的过程，它是一个继承自 `MinorCPU` 的 RISC-V 预构建板卡。该板卡可在 `src/python/gem5/prebuilt/riscvmatched` 找到。

本教程将创建一个大小为 2 GiB 的单通道 DDR4 内存、一个使用 MinorCPU 和 RISC-V 指令集架构（ISA）的核心，不过同样的过程也可用于其他类型或大小的内存、指令集架构和核心。

同样，本教程将使用[开发你自己的组件教程](https://www.gem5.org/documentation/gem5-stdlib/develop-own-components-tutorial)中制作的 UniqueCacheHierarchy，不过也可以使用其他任何缓存层次结构。

首先，我们从导入所需的组件和 stdlib 特性开始。

``` python
from typing import List

from m5.objects import (
    AddrRange,
    BaseCPU,
    BaseMMU,
    IOXBar,
    Port,
    Process,
)
from m5.objects.RiscvCPU import RiscvMinorCPU

from gem5.components.boards.abstract_system_board import AbstractSystemBoard
from gem5.components.boards.se_binary_workload import SEBinaryWorkload
from gem5.components.cachehierarchies.classic.unique_cache_hierarchy import (
    UniqueCacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR4_2400
from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from gem5.isas import ISA
from gem5.utils.override import overrides
```

我们首先为板卡创建一个专用的 CPU 核心，它继承自所选 CPU 的某个指令集架构专用版本。
由于我们的指令集架构是 RISC-V，且所需的 CPU 类型是 MinorCPU，因此我们将继承 `RiscvMinorCPU`。
这样做是为了能设置自己的参数，使 CPU 符合我们的需求。
在本示例中我们将覆盖一个参数：`decodeToExecuteForwardDelay`（默认为 1）。
我们把这个新的 CPU 核心类型称为 `UniqueCPU`。

``` python
class UniqueCPU(RiscvMinorCPU):
    decodeToExecuteForwardDelay = 2
```

由于 `RiscvMinorCPU` 继承自 `BaseCPU`，我们可以用 `BaseCPUCore`（标准库为 `BaseCPU` 对象提供的包装，源码见 `src/python/gem5/components/processors/base_cpu_core.py`）把它纳入标准库。
`BaseCPUCore` 在构造时接受 `BaseCPU` 作为参数。
因此我们可以这样做：

```python
core = BaseCPUCore(core=UniqueCPU(), isa=ISA.RISCV)
```

<!-- **Note**: `BaseCPU` objects require a unique `core_id` to be specified upon construction. -->

接下来我们必须定义处理器。
在 gem5 标准库中，处理器是核心的集合。
在像我们这样的情况下，可以使用库中的 `BaseCPUProcessor`，它是一个包含 `BaseCPUCore` 对象的处理器（源码见 `src/python/gem5/components/processors/base_cpu_processor.py`）。
`BaseCPUProcessor` 需要一个 `BaseCPUCore` 列表。
因此：

```python
processor = BaseCPUProcessor(cores=[core])
```

接下来我们专注于构造承载这些组件的板卡。
所有板卡都必须继承 `AbstractBoard`，并且在大多数情况下还要继承 gem5 的 `System` simobject。
因此本例中我们的板卡将继承 `AbstractSystemBoard`；这是一个同时继承上述二者的抽象类。

为了能用 SE 模式运行模拟，我们还必须继承 `SEBinaryWorkload`。

所有 `AbstractBoard` 都必须指定 `clk_freq`（时钟频率）、`processor`、`memory` 和 `cache_hierarchy`。
我们已经有处理器，将使用 `UniqueCacheHierarchy` 作为 `cache_hierarchy`，并使用大小为 2GiB 的 `SingleChannelDDR4_2400` 作为内存。

我们把它称为 `UniqueBoard`，它应如下所示：

``` python
class UniqueBoard(AbstractSystemBoard, SEBinaryWorkload):
    def __init__(
        self,
        clk_freq: str,
    ) -> None:
        core = BaseCPUCore(core=UniqueCPU(), isa=ISA.RISCV)
        processor = BaseCPUProcessor(cores=[core])
        memory = SingleChannelDDR4_2400("2GiB")
        cache_hierarchy = UniqueCacheHierarchy()
        super().__init__(
            clk_freq=clk_freq,
            processor=processor,
            memory=memory,
            cache_hierarchy=cache_hierarchy,
        )
```

构造函数完成后，我们必须实现 `AbstractSystemBoard` 中的抽象方法。
这里查看 `/src/python/gem5/components/boards/abstract_system_board.py` 中 `AbstractBoard` 的源码会很有帮助。

你选择实现或不实现哪些抽象方法，取决于你要创建什么类型的系统。
在本示例中，诸如 `_setup_board` 之类的函数并不需要，因此我们用 `pass` 实现它们。
在其他情况下，对于该板卡上不存在的某些组件/特性、访问时应返回错误的情形，我们会使用 `NotImplementedError`。
例如，我们的板卡没有 IO 总线。
因此我们会让 `has_io_bus` 返回 `False`，并让 `get_io_bus` 在被调用时抛出 `NotImplementedError`。

除 `_setup_memory_ranges` 之外，`AbstractSystemBoard` 要求的许多特性我们都不实现。该板卡应如下所示：

``` python
class UniqueBoard(AbstractSystemBoard, SEBinaryWorkload):
    def __init__(
        self,
        clk_freq: str,
    ) -> None:
        core = BaseCPUCore(core=UniqueCPU(), isa=ISA.RISCV)
        processor = BaseCPUProcessor(cores=[core])
        memory = SingleChannelDDR4_2400("2GiB")
        cache_hierarchy = UniqueCacheHierarchy()
        super().__init__(
            clk_freq=clk_freq,
            processor=processor,
            memory=memory,
            cache_hierarchy=cache_hierarchy,
        )

    @overrides(AbstractSystemBoard)
    def _setup_board(self) -> None:
        pass

    @overrides(AbstractSystemBoard)
    def has_io_bus(self) -> bool:
        return False

    @overrides(AbstractSystemBoard)
    def get_io_bus(self) -> IOXBar:
        raise NotImplementedError(
            "UniqueBoard does not have an IO Bus. "
            "Use `has_io_bus()` to check this."
        )

    @overrides(AbstractSystemBoard)
    def has_dma_ports(self) -> bool:
        return False

    @overrides(AbstractSystemBoard)
    def get_dma_ports(self) -> List[Port]:
        raise NotImplementedError(
            "UniqueBoard does not have DMA Ports. "
            "Use `has_dma_ports()` to check this."
        )

    @overrides(AbstractSystemBoard)
    def has_coherent_io(self) -> bool:
        return False

    @overrides(AbstractSystemBoard)
    def get_mem_side_coherent_io_port(self) -> Port:
        raise NotImplementedError(
            "UniqueBoard does not have any I/O ports. Use has_coherent_io to "
            "check this."
        )

    @overrides(AbstractSystemBoard)
    def _setup_memory_ranges(self) -> None:
        memory = self.get_memory()
        self.mem_ranges = [AddrRange(memory.get_size())]
        memory.set_memory_range(self.mem_ranges)
```

至此就完成了为 gem5 标准库创建自定义板卡的过程。
完整板卡如下：

```python
from typing import List

from m5.objects import (
    AddrRange,
    BaseCPU,
    BaseMMU,
    IOXBar,
    Port,
    Process,
)
from m5.objects.RiscvCPU import RiscvMinorCPU

from gem5.components.boards.abstract_system_board import AbstractSystemBoard
from gem5.components.boards.se_binary_workload import SEBinaryWorkload
from gem5.components.cachehierarchies.classic.unique_cache_hierarchy import (
    UniqueCacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR4_2400
from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from gem5.isas import ISA
from gem5.utils.override import overrides


class UniqueCPU(RiscvMinorCPU):
    decodeToExecuteForwardDelay = 2


class UniqueBoard(AbstractSystemBoard, SEBinaryWorkload):
    def __init__(
        self,
        clk_freq: str,
    ) -> None:
        core = BaseCPUCore(core=UniqueCPU(), isa=ISA.RISCV)
        processor = BaseCPUProcessor(cores=[core])
        memory = SingleChannelDDR4_2400("2GiB")
        cache_hierarchy = UniqueCacheHierarchy()
        super().__init__(
            clk_freq=clk_freq,
            processor=processor,
            memory=memory,
            cache_hierarchy=cache_hierarchy,
        )

    @overrides(AbstractSystemBoard)
    def _setup_board(self) -> None:
        pass

    @overrides(AbstractSystemBoard)
    def has_io_bus(self) -> bool:
        return False

    @overrides(AbstractSystemBoard)
    def get_io_bus(self) -> IOXBar:
        raise NotImplementedError(
            "UniqueBoard does not have an IO Bus. "
            "Use `has_io_bus()` to check this."
        )

    @overrides(AbstractSystemBoard)
    def has_dma_ports(self) -> bool:
        return False

    @overrides(AbstractSystemBoard)
    def get_dma_ports(self) -> List[Port]:
        raise NotImplementedError(
            "UniqueBoard does not have DMA Ports. "
            "Use `has_dma_ports()` to check this."
        )

    @overrides(AbstractSystemBoard)
    def has_coherent_io(self) -> bool:
        return False

    @overrides(AbstractSystemBoard)
    def get_mem_side_coherent_io_port(self) -> Port:
        raise NotImplementedError(
            "UniqueBoard does not have any I/O ports. Use has_coherent_io to "
            "check this."
        )

    @overrides(AbstractSystemBoard)
    def _setup_memory_ranges(self) -> None:
        memory = self.get_memory()
        self.mem_ranges = [AddrRange(memory.get_size())]
        memory.set_memory_range(self.mem_ranges)

```

在此基础上，你可以创建一个运行脚本并测试你的板卡：

``` python
from unique_board import UniqueBoard

from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

board = UniqueBoard(clk_freq="1.2GHz")

# As we are using the RISCV ISA, "riscv-hello" should work.
board.set_se_binary_workload(obtain_resource("riscv-hello"))

simulator = Simulator(board=board)
simulator.run()
```

---
layout: documentation
title: Developing Your Own Components Tutorial
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/develop-own-components-tutorial
author: Bobby R. Bruce
---

## 开发你自己的 gem5 标准库组件

![gem5 组件库设计]({{ site.baseurl }}/assets/img/stdlib/gem5-components-design.png)

上图展示了 gem5 库组件的基本设计。
其中有四个重要的抽象类：`AbstractBoard`、`AbstractProcessor`、`AbstractMemorySystem` 和 `AbstractCacheHierarchy`。
每个 gem5 组件都继承其中之一，才能成为可在设计中使用的 gem5 组件。
构造 `AbstractBoard` 时必须指定一个 `AbstractProcessor`、一个 `AbstractMemorySystem` 和一个 `AbstractCacheHierarchy`。
有了这种设计，任何板卡都可以使用继承自 `AbstractProcessor`、`AbstractMemorySystem` 和 `AbstractCacheHierarchy` 的任意组件组合。
例如，以该图为参考，我们可以把一个 `SimpleProcessor`、一个 `SingleChannelDDR3_1600` 和一个 `PrivateL1PrivateL2CacheHierarchy` 加入一个 `X86Board`。
如果需要，我们还可以把 `PrivateL1PrivateL2CacheHierarchy` 换成另一个继承自 `AbstractCacheHierarchy` 的类。

在本教程中，我们设想某位用户希望创建一个新的缓存层次结构。
从图中可以看到，有两个继承 `AbstractCacheHierarchy` 的子类：`AbstractRubyCacheHierarchy` 和 `AbstractClassicCacheHierarchy`。
虽然你*可以*直接继承 `AbstractCacheHierarchy`，但我们建议继承这两个子类（取决于你想开发 ruby 还是 classic 缓存层次结构配置）。
我们将继承 `AbstractClassicCacheHierarchy` 类来创建一个 classic 缓存配置。

首先，我们应创建一个继承 `AbstractClassicCacheHierarchy` 的新 Python 类。
在本示例中我们把它称为 `UniqueCacheHierarchy`，放在文件 `unique_cache_hierarchy.py` 中：

```python
from m5.objects import (
    Port,
)

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import (
    AbstractClassicCacheHierarchy,
)


class UniqueCacheHierarchy(AbstractClassicCacheHierarchy):


    def __init__() -> None:
        AbstractClassicCacheHierarchy.__init__(self=self)

    def get_mem_side_port(self) -> Port:
        pass

    def get_cpu_side_port(self) -> Port:
        pass

    def incorporate_cache(self, board: AbstractBoard) -> None:
        pass
```

与每个抽象基类一样，都有必须实现的虚函数。
实现之后，`UniqueCacheHierarchy` 就可以在模拟中使用了。
`get_mem_side_port` 和 `get_cpu_side_port` 在 [AbstractClassicCacheHierarchy](https://github.com/gem5/gem5/blob/stable/src/python/gem5/components/cachehierarchies/classic/abstract_classic_cache_hierarchy.py) 中声明，而 `incorporate_cache` 在 [AbstractCacheHierarchy](https://github.com/gem5/gem5/blob/stable/src/python/gem5/components/cachehierarchies/abstract_cache_hierarchy.py) 中声明

`get_mem_side_port` 和 `get_cpu_side_port` 函数各返回一个 `Port`。
顾名思义，这些端口是板卡从内存侧和 cpu 侧访问缓存层次结构所用的端口。
所有 classic 缓存层次结构配置都必须指定它们。

`incorporate_cache` 函数是被调用以把缓存纳入板卡的函数。
该函数的内容会因缓存层次结构配置而异，但通常会检查它所连接的板卡，并使用板卡的 API 来连接该缓存层次结构。

在本示例中，我们假设用户希望实现一个私有 L1 缓存层次结构，为每个 CPU 核心包含一个数据缓存和一个指令缓存。
它实际上已在 gem5 stdlib 中实现为 [PrivateL1CacheHierarchy](https://github.com/gem5/gem5/blob/stable/src/python/gem5/components/cachehierarchies/classic/private_l1_cache_hierarchy.py)，但本示例中我们会重复这项工作。

首先我们实现 `get_mem_side_port` 和 `get_cpu_side_port` 函数：

```python
from m5.objects import (
    BadAddr,
    Port,
    SystemXBar,
)

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import (
    AbstractClassicCacheHierarchy,
)


class UniqueCacheHierarchy(AbstractClassicCacheHierarchy):

    def __init__(self) -> None:
        AbstractClassicCacheHierarchy.__init__(self=self)
        self.membus = SystemXBar(width=64)
        self.membus.badaddr_responder = BadAddr()
        self.membus.default = self.membus.badaddr_responder.pio

    def get_mem_side_port(self) -> Port:
        return self.membus.mem_side_ports

    def get_cpu_side_port(self) -> Port:
        return self.membus.cpu_side_ports

    def incorporate_cache(self, board: AbstractBoard) -> None:
        pass
```

这里我们使用了一条简单的内存总线。

接下来实现 `incorporate_cache` 函数：

```python
from m5.objects import (
    BadAddr,
    Cache,
    Port,
    SystemXBar,
)

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import (
    AbstractClassicCacheHierarchy,
)
from gem5.components.cachehierarchies.classic.caches.l1dcache import L1DCache
from gem5.components.cachehierarchies.classic.caches.l1icache import L1ICache
from gem5.components.cachehierarchies.classic.caches.mmu_cache import MMUCache


class UniqueCacheHierarchy(AbstractClassicCacheHierarchy):

    def __init__(self) -> None:
        AbstractClassicCacheHierarchy.__init__(self=self)
        self.membus = SystemXBar(width=64)
        self.membus.badaddr_responder = BadAddr()
        self.membus.default = self.membus.badaddr_responder.pio

    def get_mem_side_port(self) -> Port:
        return self.membus.mem_side_ports

    def get_cpu_side_port(self) -> Port:
        return self.membus.cpu_side_ports

    def incorporate_cache(self, board: AbstractBoard) -> None:
        # Set up the system port for functional access from the simulator.
        board.connect_system_port(self.membus.cpu_side_ports)

        for cntr in board.get_memory().get_memory_controllers():
            cntr.port = self.membus.mem_side_ports

        self.l1icaches = [
            L1ICache(size="32KiB")
            for i in range(board.get_processor().get_num_cores())
        ]

        self.l1dcaches = [
            L1DCache(size="32KiB")
            for i in range(board.get_processor().get_num_cores())
        ]
        # ITLB Page walk caches
        self.iptw_caches = [
            MMUCache(size="8KiB")
            for _ in range(board.get_processor().get_num_cores())
        ]
        # DTLB Page walk caches
        self.dptw_caches = [
            MMUCache(size="8KiB")
            for _ in range(board.get_processor().get_num_cores())
        ]

        if board.has_coherent_io():
            self._setup_io_cache(board)

        for i, cpu in enumerate(board.get_processor().get_cores()):

            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            self.l1icaches[i].mem_side = self.membus.cpu_side_ports
            self.l1dcaches[i].mem_side = self.membus.cpu_side_ports

            self.iptw_caches[i].mem_side = self.membus.cpu_side_ports
            self.dptw_caches[i].mem_side = self.membus.cpu_side_ports

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )

            int_req_port = self.membus.mem_side_ports
            int_resp_port = self.membus.cpu_side_ports
            cpu.connect_interrupt(int_req_port, int_resp_port)

    def _setup_io_cache(self, board: AbstractBoard) -> None:
        """Create a cache for coherent I/O connections"""
        self.iocache = Cache(
            assoc=8,
            tag_latency=50,
            data_latency=50,
            response_latency=50,
            mshrs=20,
            size="1kB",
            tgts_per_mshr=12,
            addr_ranges=board.mem_ranges,
        )
        self.iocache.mem_side = self.membus.cpu_side_ports
        self.iocache.cpu_side = board.get_mem_side_coherent_io_port()
```

至此就完成了创建我们自己的缓存层次结构所需的代码。

要使用这段代码，用户可以像导入其他任何 Python 模块一样导入它。
只要这段代码在 gem5 的 python 搜索路径中，你就可以导入它。
你也可以在 gem5 运行脚本开头加上 `import sys; sys.path.append(<path to new component>)`，把这个新组件的路径加入 python 搜索路径。

## 把你的组件贡献给 gem5 stdlib

在贡献你的组件之前，你需要把它移入 `src/` 目录，以便它被编译进 gem5 二进制程序。

### 把你的组件编译进 gem5 标准库

gem5 标准库代码位于 `src/python/gem5`。
基本目录结构如下：

```txt
gem5/
    components/                 # All the components to build the system to simulate.
        boards/                 # The boards, typically broken down by ISA target.
            experimental/       # Experimental boards.
        cachehierarchies/       # The Cache Hierarchy components.
            chi/                # CHI protocol cache hierarchies.
            classic/            # Classic cache hierarchies.
            ruby/               # Ruby cache hierarchies.
        memory/                 # Memory systems.
        processors/             # Processors.
    prebuilt/                   # Prebuilt systems, ready to use.
        demo/                   # Prebuilt System for demonstrations. (not be representative of real-world targets).
    resources/                  # Utilities used for referencing and obtaining gem5-resources.
    simulate/                   # A package for the automated running of gem5 simulations.
    utils/                      # General utilities.
```

我们建议把 `unique_cache_hierarchy.py` 放入 `src/python/gem5/components/cachehierarchies/classic/`。

在那之后，你需要把下面这一行加入 `src/python/SConscript`：

```scons
PySource('gem5.components.cachehierarchies.classic',
    'gem5/components/cachehierarchies/classic/unique_cache_hierarchy.py')
```

然后，当你重新编译 gem5 二进制程序时，`UniqueCacheHierarchy` 类就会被包含进来。
要在你自己的脚本中使用它，只需导入：

```python
from gem5.components.cachehierarchies.classic.unique_cache_hierarchy import UniqueCacheHierarchy

...

cache_hierarchy = UniqueCacheHierarchy()

...

```

### gem5 代码贡献与评审

如果你认为你对 gem5 stdlib 的新增内容对 gem5 社区有益，可以把它作为补丁提交。
如果你以前没有为 gem5 做过贡献，或需要回顾我们的流程，请遵循我们的[贡献指南]({{ site.baseurl }}/contributing)。

除常规贡献指南之外，我们强烈建议你对 stdlib 贡献做以下事情：

* **补充文档**：类和方法的文档应使用 [reStructured text](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) 编写。
请查看 stdlib 中的其他源码，了解通常如何编写。
* **使用 Python 类型标注**：利用 [Python typing 模块](https://docs.python.org/3/library/typing.html)指定参数与方法返回类型。
* **使用相对导入**：在 gem5 stdlib 内部，应使用相对导入来引用 stdlib 中的其他模块/包（即 `src/python/gem5` 中包含的内容）。
* **用 black 格式化**：请用 [Python black](https://pypi.org/project/black/) 格式化你的 Python 代码，最大行宽为 79：`black --line-length=79 <file/directory>`。
**注意**：Python black 并不总能强制行宽。
例如它不会缩短字符串长度。
某些行可能需要你手动缩短。

代码会像所有其他贡献一样通过 [GitHub](https://github.com/gem5/gem5) 评审。
不过我们要强调，我们不会仅仅因为补丁能工作、有测试就接受对库的修改；
我们需要被说服该贡献确实改进了库并使社区受益。
例如，某些小众组件如果被认为效用较低且会增加库的维护开销，可能不会被纳入。

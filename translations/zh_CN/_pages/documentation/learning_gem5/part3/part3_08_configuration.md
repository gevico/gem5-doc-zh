---
layout: documentation
title: "配置简单的 Ruby 系统"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/configuration/
author: Jason Lowe-Power
---

## MSI 协议（protocol）的配置脚本

先在 `configs/` 中新建配置目录。与其他 gem5 配置一样，需要一个运行脚本。可以从[简单配置章节]({{ site.baseurl }}/documentation/learning_gem5/part1/simple_config/)的 `simple.py` 开始，将其复制为新目录中的 `simple_ruby.py`。

稍作修改，用 Ruby 连接 CPU 与内存控制器。为了测试一致性，先改为两个 CPU。

```python
system.cpu = [X86TimingSimpleCPU(), X86TimingSimpleCPU()]
```

实例化内存控制器后，创建并设置整个缓存（cache）系统。将以下代码放在*创建 CPU 中断控制器之后、调用系统实例化之前*。

```python
system.caches = MyCacheSystem()
system.caches.setup(system, system.cpu, [system.mem_ctrl])
```

与[经典缓存（cache）配置示例]({{ site.baseurl }}/documentation/learning_gem5/part1/cache_config/)一样，另建一个文件保存相关配置。在其中定义 `MyCacheSystem`，并提供 `setup`，接收系统、CPU 和内存控制器。

可以[查看完整运行脚本](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part3/simple_ruby.py)。

### 配置缓存（cache）系统

创建 `msi_caches.py`，定义四个类：继承 `RubySystem` 的 `MyCacheSystem`；继承 SLICC 为两个状态机（state machine）生成的 SimObject 的 L1 与目录控制器；以及继承 `SimpleNetwork` 的 `MyNetwork`。

#### L1 缓存（cache）

`L1Cache` 继承 `L1Cache_Controller`，因为 SLICC 中的名称是 `L1Cache`。使用类变量和类方法分配 `version` 编号。同一种机器类型的实例必须从 0 开始依次编号，且互不重复，用于区分各个控制器。

```python
class L1Cache(L1Cache_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1
```

接着实现构造函数。

```python
def __init__(self, system, ruby_system, cpu):
    super(L1Cache, self).__init__()

    self.version = self.versionCount()
    self.cacheMemory = RubyCache(size = '16kB',
                           assoc = 8,
                           start_index_bit = self.getBlockSizeBits(system))
    self.clk_domain = cpu.clk_domain
    self.send_evictions = self.sendEvicts(cpu)
    self.ruby_system = ruby_system
    self.connectQueues(ruby_system)
```

CPU 对象用于获取时钟域（clock domain），`system` 用于获取块大小。这里设置在 SLICC 中声明的参数（parameter），例如 `cacheMemory`；`sequencer` 稍后再设置。容量和相联度在示例中直接指定；若实验需要灵活调整，可改为命令行选项。

然后定义辅助方法。通过对块大小取以 2 为底的对数，计算块内偏移占用的位数。另一个方法决定是否向 CPU 通知驱逐，以满足 CPU 模型和指令集架构（ISA）的要求。

```python
def getBlockSizeBits(self, system):
    bits = int(math.log(system.cache_line_size, 2))
    if 2**bits != system.cache_line_size.value:
        panic("Cache line size not a power of 2!")
    return bits

def sendEvicts(self, cpu):
    """True if the CPU model or ISA requires sending evictions from caches
       to the CPU. Three scenarios warrant forwarding evictions to the CPU:
       1. The O3 model must keep the LSQ coherent with the caches
       2. The x86 mwait instruction is built on top of coherence
       3. The local exclusive monitor in ARM systems
    """
    return True
```

> **译注**：原文称 `getBlockSizeBits` 计算索引位数，实际代码计算的是块内偏移位数，用于确定索引的起始位置。原文也将驱逐通知条件写成“乱序 CPU 且使用 x86 或 ARM”，但这段代码直接返回 `True`；其注释列出的是三种各自需要通知的情况：O3 的加载/存储队列、x86 的 `mwait`、ARM 的本地独占监视器。

最后实现 `connectQueues`，连接消息缓冲区与 Ruby 网络。先创建 sequencer 所需的 `mandatoryQueue`，再为控制器其余缓冲区创建对象。按示例的旧命名，发送缓冲区的 `master` 连接网络输入，接收缓冲区的 `slave` 连接网络输出。本例为简化设计，使用有序消息缓冲区。

```python
def connectQueues(self, ruby_system):
    self.mandatoryQueue = MessageBuffer()

    self.requestToDir = MessageBuffer(ordered = True)
    self.requestToDir.master = ruby_system.network.slave
    self.responseToDirOrSibling = MessageBuffer(ordered = True)
    self.responseToDirOrSibling.master = ruby_system.network.slave
    self.forwardFromDir = MessageBuffer(ordered = True)
    self.forwardFromDir.slave = ruby_system.network.master
    self.responseFromDirOrSibling = MessageBuffer(ordered = True)
    self.responseFromDirOrSibling.slave = ruby_system.network.master
```

> **译注**：这里保留原文的 `master/slave` 接口命名。较新版本通常使用 `out_port/in_port` 等名称；原文关于消息缓冲区“尚未使用 gem5 端口（port）实现”的说明也有版本限制，移植时应核对当前 Python 接口。

#### 目录

目录的实现类似，有三处主要差异。首先需要设置地址范围：每个目录对应负责特定范围的内存控制器，两者范围必须一致。Ruby 控制器的默认范围为 `AllMemory`。

其次，将请求端口（port）`memory` 连接到内存控制器。本例的 SLICC 内存读写动作（原文统称 `queueMemoryRead/Write`）通过这一路径访问内存。最后，在 `connectQueues` 中创建特殊的 `responseFromMemory`，类似 L1 的 `mandatoryQueue`。

```python
class DirController(Directory_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system, ranges, mem_ctrls):
        """ranges are the memory ranges assigned to this controller.
        """
        if len(mem_ctrls) > 1:
            panic("This cache system can only be connected to one mem ctrl")
        super(DirController, self).__init__()
        self.version = self.versionCount()
        self.addr_ranges = ranges
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        # Connect this directory to the memory side.
        self.memory = mem_ctrls[0].port
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.requestFromCache = MessageBuffer(ordered = True)
        self.requestFromCache.slave = ruby_system.network.master
        self.responseFromCache = MessageBuffer(ordered = True)
        self.responseFromCache.slave = ruby_system.network.master

        self.responseToCache = MessageBuffer(ordered = True)
        self.responseToCache.master = ruby_system.network.slave
        self.forwardToCache = MessageBuffer(ordered = True)
        self.forwardToCache.master = ruby_system.network.slave

        self.responseFromMemory = MessageBuffer()
```

#### Ruby 系统

`MyCacheSystem` 的构造函数较简单，检查构建环境中的 `PROTOCOL`，确保所用配置与编译的协议（protocol）一致。控制器需要引用 Ruby 系统，因此示例将它们的创建放在单独的 `setup` 中，以避免在构造过程中产生 SimObject 层级的循环依赖，导致 `m5.instantiate` 递归失败。

```python
class MyCacheSystem(RubySystem):

    def __init__(self):
        if buildEnv['PROTOCOL'] != 'MSI':
            fatal("This system assumes MSI from learning gem5!")

        super(MyCacheSystem, self).__init__()
```

`setup` 先创建网络，并设置虚拟网络数量。

然后实例化所有控制器。本例用一个列表统一保存，便于连接网络；更复杂的拓扑也可以采用多个列表。每个 CPU 配置一个 L1，整个系统配置一个目录。

随后为每个 CPU 创建 sequencer，引用指令和数据缓存（cache），以正确处理访问时序。更复杂的系统还需要为 DMA 控制器等对象配置相应接口。创建后，把各 sequencer 赋给对应 L1 的 `sequencer` 字段。

连接所有控制器与网络，并调用网络的 `setup_buffers`。

还需要创建 `RubyPortProxy`，连接系统的功能访问接口，例如在系统调用模拟（syscall emulation）模式下加载二进制文件。

最后连接 CPU。本例只有 CPU sequencer，因此第一个 CPU 对应第一个 sequencer，依此类推。还要按所用指令集架构（ISA）连接页表遍历与中断接口。

```python
def setup(self, system, cpus, mem_ctrls):
    self.network = MyNetwork(self)

    self.number_of_virtual_networks = 3
    self.network.number_of_virtual_networks = 3

    self.controllers = \
        [L1Cache(system, self, cpu) for cpu in cpus] + \
        [DirController(self, system.mem_ranges, mem_ctrls)]

    self.sequencers = [RubySequencer(version = i,
                            # I/D cache is combined and grab from ctrl
                            icache = self.controllers[i].cacheMemory,
                            dcache = self.controllers[i].cacheMemory,
                            clk_domain = self.controllers[i].clk_domain,
                            ) for i in range(len(cpus))]

    for i,c in enumerate(self.controllers[0:len(self.sequencers)]):
        c.sequencer = self.sequencers[i]

    self.num_of_sequencers = len(self.sequencers)

    self.network.connectControllers(self.controllers)
    self.network.setup_buffers()

    self.sys_port_proxy = RubyPortProxy()
    system.system_port = self.sys_port_proxy.slave

    for i,cpu in enumerate(cpus):
        cpu.icache_port = self.sequencers[i].slave
        cpu.dcache_port = self.sequencers[i].slave
        isa = buildEnv['TARGET_ISA']
        if isa == 'x86':
            cpu.interrupts[0].pio = self.sequencers[i].master
            cpu.interrupts[0].int_master = self.sequencers[i].slave
            cpu.interrupts[0].int_slave = self.sequencers[i].master
        if isa == 'x86' or isa == 'arm':
            cpu.itb.walker.port = self.sequencers[i].slave
            cpu.dtb.walker.port = self.sequencers[i].slave
```

#### 网络

最后实现网络。构造函数较简单，但需要将网络接口列表 `netifs` 初始化为空列表。

主要逻辑位于 `connectControllers`。它建立一个*非常简单、并不贴近实际硬件*的点对点全连接网络：每个控制器都能通过直接连接到达其他控制器。

Ruby 网络包含三部分：路由器；连接控制器与路由器的外部链路；连接两个路由器的内部链路。先为每个控制器创建路由器，再创建对应的外部链路，最后为任意两个不同路由器添加内部连接，形成全连接拓扑。

```python
class MyNetwork(SimpleNetwork):

    def __init__(self, ruby_system):
        super(MyNetwork, self).__init__()
        self.netifs = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):
        self.routers = [Switch(router_id = i) for i in range(len(controllers))]

        self.ext_links = [SimpleExtLink(link_id=i, ext_node=c,
                                        int_node=self.routers[i])
                          for i, c in enumerate(controllers)]

        link_count = 0
        self.int_links = []
        for ri in self.routers:
            for rj in self.routers:
                if ri == rj: continue # Don't connect a router to itself!
                link_count += 1
                self.int_links.append(SimpleIntLink(link_id = link_count,
                                                    src_node = ri,
                                                    dst_node = rj))
```

可以[查看完整的 msi_caches.py](https://github.com/gem5/gem5/blob/stable/configs/learning_gem5/part3/msi_caches.py)。

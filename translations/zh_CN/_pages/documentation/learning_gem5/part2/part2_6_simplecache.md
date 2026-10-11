---
layout: documentation
title: "创建简单的缓存（cache）对象"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/simplecache/
author: Jason Lowe-Power
---

创建简单的缓存（cache）对象
==============================

本章将在[上一章]({{ site.baseurl }}/documentation/learning_gem5/part2/memoryobject/)的内存对象框架中加入缓存（cache）逻辑。

SimpleCache SimObject
---------------------

先创建 [SConscript 文件]({{ site.baseurl }}/pages/static/scripts/part2/simplecache/SConscript)，再编写描述 SimObject 的 Python 文件。这个内存对象命名为 `SimpleCache`，相应的 Python 文件放在 `src/learning_gem5/simple_cache` 中。

```python
from m5.params import *
from m5.proxy import *
from MemObject import MemObject

class SimpleCache(MemObject):
    type = 'SimpleCache'
    cxx_header = "learning_gem5/simple_cache/simple_cache.hh"

    cpu_side = VectorResponsePort("CPU side port, receives requests")
    mem_side = RequestPort("Memory side port, sends requests")

    latency = Param.Cycles(1, "Cycles taken on a hit or to resolve a miss")

    size = Param.MemorySize('16kB', "The size of the cache")

    system = Param.System(Parent.any, "The system this cache is part of")
```

与[上一章]({{ site.baseurl }}/documentation/learning_gem5/part2/memoryobject/)相比，该文件有几处变化。首先，增加了访问延迟和容量两个参数（parameter）。[SimObject 参数（parameter）]({{ site.baseurl }}/documentation/learning_gem5/part2/parameters/)一章详细介绍了这类参数（parameter）。

其次，加入了 `System` 参数（parameter），指向这个缓存（cache）所连接的主系统。初始化时需要通过它获取系统的缓存（cache）块大小。这里使用特殊的*代理参数（parameter）* `Parent.any` 引用所属的系统对象。

Python 配置脚本实例化 `SimpleCache` 后，代理参数（parameter）会沿其父对象层级查找与 `System` 类型匹配的 SimObject。由于通常将 `System` 放在系统对象层级的顶层，`system` 参数（parameter）经常使用这种方式解析。

第三处区别是，`SimpleCache` 使用 `VectorPort`，取代 `SimpleMemobj` 中两个具有独立名称的 CPU 端口（port）`inst_port` 与 `data_port`。`VectorPort` 与普通端口（port）类似，例如也通过 `getPort` 获取，但允许连接多个对端。此前未使用的 `PortID idx` 参数（parameter）现在用来区分这些连接，因此配置起来更加灵活。

实现 SimpleCache
----------------------------

`SimpleCache` 的大部分代码与 `SimpleMemobj` 相同，主要修改构造函数和几个关键的内存对象方法。

首先，在构造函数中动态创建 CPU 一侧的端口（port），并根据 SimObject 参数（parameter）初始化新增的成员变量。

```cpp
SimpleCache::SimpleCache(SimpleCacheParams *params) :
    MemObject(params),
    latency(params->latency),
    blockSize(params->system->cacheLineSize()),
    capacity(params->size / blockSize),
    memPort(params->name + ".mem_side", this),
    blocked(false), outstandingPacket(nullptr), waitingPortId(-1)
{
    for (int i = 0; i < params->port_cpu_side_connection_count; ++i) {
        cpuPorts.emplace_back(name() + csprintf(".cpu_side[%d]", i), i, this);
    }
}
```

这里使用系统的 `cacheLineSize` 设置 `blockSize`，根据容量参数（parameter）与块大小计算可容纳的块数，并初始化后面需要的成员变量。最后，根据连接数量创建 `CPUSidePort`。由于 Python 文件中将 `cpu_side` 声明为 `VectorResponsePort`，生成的参数（parameter）结构会自动包含 `port_cpu_side_connection_count`；其名称取自 Python 中的端口（port）名。每个连接对应一个新的 `CPUSidePort`，加入 `SimpleCache` 的 `cpuPorts` 向量中。

还需要为 `CPUSidePort` 增加保存编号的成员变量，并将编号作为构造函数的参数（parameter）。

接下来实现 `getPort`。内存一侧只有一个端口（port），处理很简单；CPU 一侧则需要返回指定编号对应的端口（port）。

```cpp
Port &
SimpleCache::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "mem_side") {
        panic_if(idx != InvalidPortID,
                 "Mem side of simple cache not a vector port");
        return memPort;
    } else if (if_name == "cpu_side" && idx < cpuPorts.size()) {
        return cpuPorts[idx];
    } else {
        return ClockedObject::getPort(if_name, idx);
    }
}
```

`CPUSidePort` 与 `MemSidePort` 的实现几乎与 `SimpleMemobj` 相同。区别在于调用 `handleRequest` 时需要额外传入请求来源端口（port）的编号，否则无法将响应送回正确的对端。`SimpleMemobj` 可以根据原始请求属于指令还是数据访问来选择返回路径；`SimpleCache` 使用向量端口（port），仅靠这种分类已不足以确定来源。

新的 `handleRequest` 有两处变化。首先，保存请求来源的编号。由于 `SimpleCache` 采用阻塞设计，一次只允许一个未完成请求，因此只需保存一个编号。

其次，访问缓存（cache）的标签和数据需要时间。前面新增的延迟参数（parameter）正是为此准备的。`handleRequest` 使用事件，将实际访问推迟 `latency` 个周期。`clockEdge` 返回未来第 *n* 个时钟周期边沿对应的 *tick*。

```cpp
bool
SimpleCache::handleRequest(PacketPtr pkt, int port_id)
{
    if (blocked) {
        return false;
    }
    DPRINTF(SimpleCache, "Got request for addr %#x\n", pkt->getAddr());

    blocked = true;
    waitingPortId = port_id;

    schedule(new AccessEvent(this, pkt), clockEdge(latency));

    return true;
}
```

`AccessEvent` 比[事件处理章节]({{ site.baseurl }}/documentation/learning_gem5/part2/events/)中的 `EventWrapper` 稍复杂。这里需要把 `handleRequest` 收到的 `pkt` 传给事件处理函数，因此使用一个独立的事件类来保存它。只需实现 `process`，让其调用处理函数 `accessTiming`。构造事件时传入 `AutoDelete`，事件系统便会在 `process` 执行后自动删除这个动态分配的对象，无需手动释放。

> **译注**：这里介绍的是原文采用的自定义事件类写法；并不表示所有事件包装器都无法传递上下文。原文中的 `accessTming` 是 `accessTiming` 的拼写错误。

```cpp
class AccessEvent : public Event
{
  private:
    SimpleCache *cache;
    PacketPtr pkt;
  public:
    AccessEvent(SimpleCache *cache, PacketPtr pkt) :
        Event(Default_Pri, AutoDelete), cache(cache), pkt(pkt)
    { }
    void process() override {
        cache->accessTiming(pkt);
    }
};
```

现在实现事件处理函数 `accessTiming`。

```cpp
void
SimpleCache::accessTiming(PacketPtr pkt)
{
    bool hit = accessFunctional(pkt);
    if (hit) {
        pkt->makeResponse();
        sendResponse(pkt);
    } else {
        <miss handling>
    }
}
```

它先通过下面介绍的 `accessFunctional` 完成一次功能层面的缓存（cache）查找。若命中，该方法直接读写缓存（cache）；否则返回未命中。

命中时只需向请求方返回响应。首先调用数据包（packet）的 `makeResponse`，将其从请求转换为响应，例如把 `ReadReq` 改为 `ReadResp`；写请求同理。随后将响应发回 CPU。

`sendResponse` 与 `SimpleMemobj::handleResponse` 的工作相同，只是使用 `waitingPortId` 确定返回路径。必须在调用 `sendPacket` 之前解除 `SimpleCache` 的阻塞，因为 CPU 一侧可能立即调用 `sendTimingReq` 发起新请求。随后，如果对象已经能接收请求，就尝试向需要重试的 CPU 端口（port）发送通知。

```cpp
void SimpleCache::sendResponse(PacketPtr pkt)
{
    int port = waitingPortId;

    blocked = false;
    waitingPortId = -1;

    cpuPorts[port].sendPacket(pkt);
    for (auto& port : cpuPorts) {
        port.trySendRetry();
    }
}
```

* * * * *

回到 `accessTiming`，继续处理未命中的情况。先判断请求是否恰好覆盖一个完整的缓存（cache）块：若地址按块对齐，且请求大小等于块大小，就像 `SimpleMemobj` 那样将请求直接转发到内存。

如果请求小于一个块，则需要创建新的数据包（packet），从内存读取整个块。无论原始请求是读还是写，此时都先发出读请求，将整块数据装入缓存（cache）；若原始请求是写请求，待数据装入后再在缓存（cache）中执行写入。

新数据包（packet）的大小为 `blockSize`，调用 `allocate` 为其分配保存返回数据的空间。删除数据包（packet）时，这块空间也会释放。新数据包（packet）复用原来的请求对象，使内存一侧可以获取原始请求方和请求信息，用于统计。

最后，将原始 `pkt` 保存在成员变量 `outstandingPacket` 中，以便收到响应后恢复原请求，再通过内存端口（port）发送新数据包（packet）。

```cpp
void
SimpleCache::accessTiming(PacketPtr pkt)
{
    bool hit = accessFunctional(pkt);
    if (hit) {
        pkt->makeResponse();
        sendResponse(pkt);
    } else {
        Addr addr = pkt->getAddr();
        Addr block_addr = pkt->getBlockAddr(blockSize);
        unsigned size = pkt->getSize();
        if (addr == block_addr && size == blockSize) {
            DPRINTF(SimpleCache, "forwarding packet\n");
            memPort.sendPacket(pkt);
        } else {
            DPRINTF(SimpleCache, "Upgrading packet to block size\n");
            panic_if(addr - block_addr + size > blockSize,
                     "Cannot handle accesses that span multiple cache lines");

            assert(pkt->needsResponse());
            MemCmd cmd;
            if (pkt->isWrite() || pkt->isRead()) {
                cmd = MemCmd::ReadReq;
            } else {
                panic("Unknown packet type in upgrade size");
            }

            PacketPtr new_pkt = new Packet(pkt->req, cmd, blockSize);
            new_pkt->allocate();

            outstandingPacket = pkt;

            memPort.sendPacket(new_pkt);
        }
    }
}
```

收到内存响应，说明先前发生过未命中。首先把返回的数据插入缓存（cache）。

如果存在 `outstandingPacket`，最终应向原请求方返回它；否则，直接返回当前收到的 `pkt`。

如果当前响应对应的是为小请求扩展出来的整块读取，则要完成原请求：读请求将数据复制到 `outstandingPacket`，写请求则更新缓存（cache）。随后删除未命中处理过程中创建的临时数据包（packet）。

```cpp
bool
SimpleCache::handleResponse(PacketPtr pkt)
{
    assert(blocked);
    DPRINTF(SimpleCache, "Got response for addr %#x\n", pkt->getAddr());
    insert(pkt);

    if (outstandingPacket != nullptr) {
        accessFunctional(outstandingPacket);
        outstandingPacket->makeResponse();
        delete pkt;
        pkt = outstandingPacket;
        outstandingPacket = nullptr;
    } // else, pkt contains the data it needs

    sendResponse(pkt);

    return true;
}
```

### 缓存（cache）的功能逻辑

接下来实现 `accessFunctional` 与 `insert`，它们构成缓存（cache）逻辑的核心。

首先需要保存缓存（cache）内容。最简单的方式是使用从地址映射到数据的哈希表，为 `SimpleCache` 加入以下成员。

```cpp
std::unordered_map<Addr, uint8_t*> cacheStore;
```

访问时先使用 `Packet::getBlockAddr` 获取按块对齐的地址，再在哈希表中查找。如果没有对应条目，则返回 `false`，表示未命中。

若命中且为写请求，就把数据包（packet）中的数据写入缓存（cache）。`writeDataToBlock` 根据请求地址在块内的偏移和给定的块大小，将数据写到第一个参数（parameter）所指缓冲区的正确位置；目标块可以比请求数据更大。

若为读请求，则用缓存（cache）中的数据填充数据包（packet）。`setDataFromBlock` 进行相同的偏移计算，但数据流向相反：从第一个参数（parameter）指定的块中读取数据。

```cpp
bool
SimpleCache::accessFunctional(PacketPtr pkt)
{
    Addr block_addr = pkt->getBlockAddr(blockSize);
    auto it = cacheStore.find(block_addr);
    if (it != cacheStore.end()) {
        if (pkt->isWrite()) {
            pkt->writeDataToBlock(it->second, blockSize);
        } else if (pkt->isRead()) {
            pkt->setDataFromBlock(it->second, blockSize);
        } else {
            panic("Unknown packet type!");
        }
        return true;
    }
    return false;
}
```

最后实现 `insert`，内存一侧返回请求响应时调用它。

先检查容量。如果已有条目数达到容量上限，插入新块前就需要驱逐一个条目。以下代码利用 C++ `unordered_map` 的哈希桶接口随机选择要驱逐的条目。

驱逐时必须将数据写回下一级内存，因为它可能已被修改。为此创建一组新的 `Request` 和 `Packet`，命令使用 `MemCmd::WritebackDirty`，通过 `memPort` 发送，然后从存储映射中删除被驱逐的条目。

必要的驱逐完成后，为新块分配空间，在映射中加入新地址，并将响应数据写入。此前的未命中处理已把小请求扩展为整块请求，因此这里返回的数据大小等于缓存（cache）块大小。

```cpp
void
SimpleCache::insert(PacketPtr pkt)
{
    if (cacheStore.size() >= capacity) {
        // Select random thing to evict. This is a little convoluted since we
        // are using a std::unordered_map. See http://bit.ly/2hrnLP2
        int bucket, bucket_size;
        do {
            bucket = random_mt.random(0, (int)cacheStore.bucket_count() - 1);
        } while ( (bucket_size = cacheStore.bucket_size(bucket)) == 0 );
        auto block = std::next(cacheStore.begin(bucket),
                               random_mt.random(0, bucket_size - 1));

        RequestPtr req = new Request(block->first, blockSize, 0, 0);
        PacketPtr new_pkt = new Packet(req, MemCmd::WritebackDirty, blockSize);
        new_pkt->dataDynamic(block->second); // This will be deleted later

        DPRINTF(SimpleCache, "Writing packet back %s\n", pkt->print());
        memPort.sendTimingReq(new_pkt);

        cacheStore.erase(block->first);
    }
    uint8_t *data = new uint8_t[blockSize];
    cacheStore[pkt->getAddr()] = data;

    pkt->writeDataToBlock(data, blockSize);
}
```

> **译注**：原文称“超过容量”才驱逐，但代码使用的是 `>= capacity`，即插入前已满便驱逐。此处还直接调用 `sendTimingReq` 而未处理返回 `false` 的情况；这是教学示例的限制，不能据此认为写回永远不会被阻塞。完整实现应遵守上一章的重试与数据包（packet）所有权规则。

为缓存（cache）创建配置文件
------------------------------------

最后创建使用该对象的 Python 配置脚本。以[上一章]({{ site.baseurl }}/documentation/learning_gem5/part2/memoryobject/)为起点，设置容量等参数（parameter），例如 `1kB`。连接时不再分别使用 `data_port` 与 `inst_port`，而是两次连接 `cpu_side`。由于它是 `VectorPort`，会自动产生多个独立连接。

```python
import m5
from m5.objects import *

...

system.cache = SimpleCache(size='1kB')

system.cpu.icache_port = system.cache.cpu_side
system.cpu.dcache_port = system.cache.cpu_side

system.membus = SystemXBar()

system.cache.mem_side = system.membus.cpu_side_ports

...
```

可以[下载 Python 配置文件]({{ site.baseurl }}/pages/static/scripts/part2/simplecache/simple_cache.py)。运行后应看到 hello 程序的预期输出。

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan 10 2017 17:38:15
    gem5 started Jan 10 2017 17:40:03
    gem5 executing on chinook, pid 29031
    command line: build/X86/gem5.opt configs/learning_gem5/part2/simple_cache.py

    Global frequency set at 1000000000000 ticks per second
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb.listener: listening for remote gdb #0 on port 7000
    warn: CoherentXBar system.membus has no snooping ports attached!
    warn: ClockedObject: More than one power state change request encountered within the same simulation tick
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 56082000 because target called exit()

增大容量，例如改为 128 KB，应该能够提高系统性能。

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan 10 2017 17:38:15
    gem5 started Jan 10 2017 17:41:10
    gem5 executing on chinook, pid 29037
    command line: build/X86/gem5.opt configs/learning_gem5/part2/simple_cache.py

    Global frequency set at 1000000000000 ticks per second
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb.listener: listening for remote gdb #0 on port 7000
    warn: CoherentXBar system.membus has no snooping ports attached!
    warn: ClockedObject: More than one power state change request encountered within the same simulation tick
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 32685000 because target called exit()

添加统计信息
------------------------------

系统总执行时间是重要指标，但我们也可能需要命中率、未命中率等信息。为此给 `SimpleCache` 添加统计项。

先声明四个统计项，它们的类型位于 `Stats` 命名空间。`hits` 和 `misses` 是 `Scalar` 计数器；`missLatency` 是记录完成未命中访问所需时间的直方图；`hitRatio` 使用 `Formula`，由命中数和未命中数计算得到。

```cpp
class SimpleCache : public MemObject
{
  private:
    ...

    Tick missTime; // To track the miss latency

    Stats::Scalar hits;
    Stats::Scalar misses;
    Stats::Histogram missLatency;
    Stats::Formula hitRatio;

  public:
    ...

    void regStats() override;
};
```

接着重写 `regStats`，向 gem5 的统计系统注册这些统计项。为每一项提供基于所属 SimObject 名称的名称，以及文字说明。直方图还需要初始化桶数；公式统计项则直接用代码写出计算式。

```cpp
void
SimpleCache::regStats()
{
    // If you don't do this you get errors about uninitialized stats.
    MemObject::regStats();

    hits.name(name() + ".hits")
        .desc("Number of hits")
        ;

    misses.name(name() + ".misses")
        .desc("Number of misses")
        ;

    missLatency.name(name() + ".missLatency")
        .desc("Ticks for misses to the cache")
        .init(16) // number of buckets
        ;

    hitRatio.name(name() + ".hitRatio")
        .desc("The ratio of hits to the total accesses to the cache")
        ;

    hitRatio = hits / (hits + misses);

}
```

最后在运行过程中更新统计值。在 `accessTiming` 中，命中与未命中时分别增加 `hits` 和 `misses`；未命中时还记录当前时间，用于测量延迟。

```cpp
void
SimpleCache::accessTiming(PacketPtr pkt)
{
    bool hit = accessFunctional(pkt);
    if (hit) {
        hits++; // update stats
        pkt->makeResponse();
        sendResponse(pkt);
    } else {
        misses++; // update stats
        missTime = curTick();
        ...
```

收到响应后，使用 `sample` 向直方图加入本次测得的延迟。每次调用加入一个样本，直方图会自动调整桶宽以适应数据。

```cpp
bool
SimpleCache::handleResponse(PacketPtr pkt)
{
    insert(pkt);

    missLatency.sample(curTick() - missTime);
    ...
```

> **译注**：本节保留原文的旧版统计接口。较新 gem5 版本使用 `statistics` 命名空间及统计分组等接口，移植时需按所用版本调整。

完整代码可分别下载：[头文件]({{ site.baseurl }}/pages/static/scripts/part2/simplecache/simple_cache.hh)和[实现文件]({{ site.baseurl }}/pages/static/scripts/part2/simplecache/simple_cache.cc)。

再次运行配置脚本，查看 `stats.txt`。容量为 1 KB 时，约 91% 的访问命中，平均未命中延迟为 53334 ticks，约 53 ns。

    system.cache.hits                                8431                       # Number of hits
    system.cache.misses                               877                       # Number of misses
    system.cache.missLatency::samples                 877                       # Ticks for misses to the cache
    system.cache.missLatency::mean           53334.093501                       # Ticks for misses to the cache
    system.cache.missLatency::gmean          44506.409356                       # Ticks for misses to the cache
    system.cache.missLatency::stdev          36749.446469                       # Ticks for misses to the cache
    system.cache.missLatency::0-32767                 305     34.78%     34.78% # Ticks for misses to the cache
    system.cache.missLatency::32768-65535             365     41.62%     76.40% # Ticks for misses to the cache
    system.cache.missLatency::65536-98303             164     18.70%     95.10% # Ticks for misses to the cache
    system.cache.missLatency::98304-131071             12      1.37%     96.47% # Ticks for misses to the cache
    system.cache.missLatency::131072-163839            17      1.94%     98.40% # Ticks for misses to the cache
    system.cache.missLatency::163840-196607             7      0.80%     99.20% # Ticks for misses to the cache
    system.cache.missLatency::196608-229375             0      0.00%     99.20% # Ticks for misses to the cache
    system.cache.missLatency::229376-262143             0      0.00%     99.20% # Ticks for misses to the cache
    system.cache.missLatency::262144-294911             2      0.23%     99.43% # Ticks for misses to the cache
    system.cache.missLatency::294912-327679             4      0.46%     99.89% # Ticks for misses to the cache
    system.cache.missLatency::327680-360447             1      0.11%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::360448-393215             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::393216-425983             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::425984-458751             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::458752-491519             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::491520-524287             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::total                   877                       # Ticks for misses to the cache
    system.cache.hitRatio                        0.905780                       # The ratio of hits to the total access

容量为 128 KB 时，命中率略有提高，结果符合这个示例的预期。

    system.cache.hits                                8944                       # Number of hits
    system.cache.misses                               364                       # Number of misses
    system.cache.missLatency::samples                 364                       # Ticks for misses to the cache
    system.cache.missLatency::mean           64222.527473                       # Ticks for misses to the cache
    system.cache.missLatency::gmean          61837.584812                       # Ticks for misses to the cache
    system.cache.missLatency::stdev          27232.443748                       # Ticks for misses to the cache
    system.cache.missLatency::0-32767                   0      0.00%      0.00% # Ticks for misses to the cache
    system.cache.missLatency::32768-65535             254     69.78%     69.78% # Ticks for misses to the cache
    system.cache.missLatency::65536-98303             106     29.12%     98.90% # Ticks for misses to the cache
    system.cache.missLatency::98304-131071              0      0.00%     98.90% # Ticks for misses to the cache
    system.cache.missLatency::131072-163839             0      0.00%     98.90% # Ticks for misses to the cache
    system.cache.missLatency::163840-196607             0      0.00%     98.90% # Ticks for misses to the cache
    system.cache.missLatency::196608-229375             0      0.00%     98.90% # Ticks for misses to the cache
    system.cache.missLatency::229376-262143             0      0.00%     98.90% # Ticks for misses to the cache
    system.cache.missLatency::262144-294911             2      0.55%     99.45% # Ticks for misses to the cache
    system.cache.missLatency::294912-327679             1      0.27%     99.73% # Ticks for misses to the cache
    system.cache.missLatency::327680-360447             1      0.27%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::360448-393215             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::393216-425983             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::425984-458751             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::458752-491519             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::491520-524287             0      0.00%    100.00% # Ticks for misses to the cache
    system.cache.missLatency::total                   364                       # Ticks for misses to the cache
    system.cache.hitRatio                        0.960894                       # The ratio of hits to the total access

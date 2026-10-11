---
layout: documentation
title: "在内存系统（memory system）中创建 SimObject"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/memoryobject/
author: Jason Lowe-Power
---

在内存系统（memory system）中创建 SimObject
========================================

本章将创建一个位于 CPU 与内存总线之间的简单内存对象。在[下一章]({{ site.baseurl }}/documentation/learning_gem5/part2/simplecache/)中，我们会为它添加逻辑，将其变成一个非常简单、采用阻塞设计的单处理器缓存（cache）。

gem5 的请求端口（port）与响应端口（port）
---------------------------

实现内存对象之前，先了解 gem5 的请求与响应端口（port）接口。[创建简单的配置脚本]({{ site.baseurl }}/documentation/learning_gem5/part1/simple_config/)已经介绍过，所有内存对象都通过端口（port）连接；这些端口（port）为内存对象之间的交互规定了严格的接口。

端口（port）支持内存系统（memory system）的三种*访问模式*：时序访问（timing）、原子访问（atomic）和功能访问（functional）。其中最重要的是*时序模式*，它用于得到准确的时序模拟（simulation）结果；另外两种模式用于特定场景。

> **译注**：原文称只有时序模式才能产生“正确的模拟结果”，这里应理解为准确的时序和性能结果。原子访问与功能访问具有各自的用途，并不意味着其功能结果必然错误。

*原子模式*适合快速推进到感兴趣的模拟（simulation）区间，以及对模拟器（simulator）进行预热。该模式假定内存系统（memory system）不会生成事件，所有内存请求都沿一条较长的调用链完成。如果内存对象不用于快速推进或预热，就不必实现原子访问。

*功能模式*也可以理解为一种*调试模式*。它用于将宿主机的数据读入模拟器（simulator）的内存等操作，在系统调用模拟（syscall emulation）模式中使用得很多。例如，gem5 通过功能访问将 `process.cmd` 指定的二进制文件从宿主机加载到被模拟系统的内存中，让被模拟系统能够访问它。功能读取必须返回最新的数据，无论数据位于何处；功能写入则应更新该地址所有可能的有效数据副本，例如含有缓存（cache）的系统中，同一地址可能对应多个有效的缓存（cache）块。

### 数据包（packet）

gem5 使用 `Packet` 在端口（port）之间传送数据。`Packet` 关联一个内存请求对象，原文将它称为 `MemReq`。该请求对象保存发起数据包（packet）的原始请求信息，例如请求方、地址以及读写等请求属性。

数据包（packet）还包含一个 `MemCmd`，表示数据包（packet）*当前*的命令。命令可以在数据包（packet）的生命周期内变化，例如内存操作完成后，请求会转为响应。最常见的 `MemCmd` 包括 `ReadReq`（读请求）、`ReadResp`（读响应）、`WriteReq`（写请求）和 `WriteResp`（写响应）。此外还有用于缓存（cache）的写回请求 `WritebackDirty`、`WritebackClean`，以及许多其他命令类型。

数据包（packet）还保存请求的数据或指向数据的指针。创建时可以选择采用动态数据还是静态数据，对应不同的内存所有权与释放方式。

> **译注**：原文对 dynamic/static 的释放责任描述颠倒了。`dataStatic()` 接收由调用方管理、不能由 `Packet` 释放的数据；`dataDynamic()` 将数据的释放责任交给 `Packet`。当前接口中的请求对象类名为 `Request`，通过 `RequestPtr` 引用；阅读本章的 `MemReq` 时应结合所用版本理解。

在经典缓存（cache）模型中，数据包（packet）还是跟踪一致性状态的单位，因此其实现中有不少与经典缓存一致性（cache coherence）协议（protocol）相关的代码。不过，gem5 中内存对象之间的通信普遍使用数据包（packet），即使这些对象不直接参与一致性处理，例如 DRAM 控制器和 CPU 模型。

端口（port）中用于传送数据的接口接受 `Packet` 指针作为参数（parameter）。由于这种指针十分常用，gem5 为其定义了类型别名 `PacketPtr`。

### 端口（port）接口

gem5 有请求端口（port）和响应端口（port）两种端口（port）。实现内存对象时，至少需要实现其中一种：分别创建继承自 `RequestPort` 或 `ResponsePort` 的类。请求端口（port）发送请求、接收响应；响应端口（port）接收请求、发送响应。

下图展示了两者最简单的交互，使用的是时序模式。其他模式更简单，仅通过请求方与响应方之间的一条调用链完成访问。

![请求和响应均能被接收时的简单交互]({{ site.baseurl }}/pages/static/figures/requestor_responder_1.png)

如上所述，`sendTimingReq`、`recvTimingReq` 等传送接口都接受一个 `PacketPtr` 参数（parameter），表示要发送或接收的请求或响应。

请求方调用 `sendTimingReq` 发送请求数据包（packet）。它随即在同一条调用链中调用响应方的 `recvTimingReq`，并将同一个 `PacketPtr` 作为唯一的参数（parameter）传入。

`recvTimingReq` 返回 `bool`，返回值直接传回请求方。`true` 表示响应方接受了数据包（packet）；`false` 表示响应方暂时无法接收，请求需要在之后重试。

上图中，请求方先调用 `sendTimingReq`，进而调用响应方的 `recvTimingReq`。响应方返回 `true`，该值也成为 `sendTimingReq` 的返回值。随后请求方继续执行，响应方开展完成请求所需的操作，例如缓存（cache）会查找标签，判断是否存在与请求地址匹配的条目。

> **译注**：原文这一段将被调用的函数误写为 `recvTimingResp`；请求的接收函数应为 `recvTimingReq`。

响应方完成请求后，调用 `sendTimingResp` 将响应发回请求方。本例沿用请求的 `PacketPtr`，但它此时已经转换为响应数据包（packet）。调用会进入请求方的 `recvTimingResp`；如果该函数返回 `true`，响应方的 `sendTimingResp` 也返回 `true`，本次请求的交互即告完成。后面的示例会给出这些函数的具体实现。

请求方或响应方也可能在收到数据包（packet）时处于忙碌状态。下图展示了响应方在首次请求到达时忙碌的情况。

![响应方忙碌时的交互]({{ site.baseurl }}/pages/static/figures/requestor_responder_2.png)

此时响应方从 `recvTimingReq` 返回 `false`。请求方调用 `sendTimingReq` 得到 `false` 后，必须等待自身的 `recvReqRetry` 被调用，才能再次调用 `sendTimingReq`。图中只失败了一次，实际可能失败多次。注意，发送失败的数据包（packet）由请求方负责保存，响应方*不会*保留其指针。

同理，如果响应方发送响应时请求方忙碌，响应方必须等到自己的 `recvRespRetry` 被调用后，才能重试 `sendTimingResp`。

![请求方忙碌时的交互]({{ site.baseurl }}/pages/static/figures/requestor_responder_3.png)

这两种情况下，重试过程都可能在同一个调用栈中完成。例如，请求方调用 `sendRetryResp` 通知对方重试响应时，可能立即收到对方重发的响应，并在同一调用栈中进入 `recvTimingResp`。因此很容易因状态更新顺序错误而产生无限递归或其他缺陷。内存对象发送重试通知之前，必须在*当前时刻*就已经准备好接收新的数据包（packet）。

> **译注**：原文在重试说明中使用了 `sendTimingRequest`、`sendRespRetry`，并混用了请求和响应接收函数。这里统一按接口语义写为 `sendTimingReq`、`sendRetryResp` 和 `recvTimingResp`；请求方向对应 `sendRetryReq` 与 `recvReqRetry`。

简单内存对象示例
----------------------------

本节构建一个简单内存对象。起初，它只负责将 CPU 一侧的请求转发到内存一侧的总线，如下图所示。对象有一个面向内存的请求端口（port），用于向内存总线发送请求；还有两个面向 CPU 的响应端口（port），分别连接 CPU 的指令与数据缓存（cache）接口。[下一章]({{ site.baseurl }}/documentation/learning_gem5/part2/simplecache/)会添加逻辑，将它扩展成缓存（cache）。

![位于 CPU 与内存总线之间的简单内存对象]({{ site.baseurl }}/pages/static/figures/simple_memobj.png)

### 声明 SimObject

与[创建 HelloObject]({{ site.baseurl }}/documentation/learning_gem5/part2/helloobject/)时一样，第一步是创建描述 SimObject 的 Python 文件。将该对象命名为 `SimpleMemobj`，在 `src/learning_gem5/simple_memobj` 中创建相应文件。

```python
from m5.params import *
from m5.proxy import *
from m5.SimObject import SimObject

class SimpleMemobj(SimObject):
    type = 'SimpleMemobj'
    cxx_header = "learning_gem5/part2/simple_memobj.hh"

    inst_port = ResponsePort("CPU side port, receives requests")
    data_port = ResponsePort("CPU side port, receives requests")
    mem_side = RequestPort("Memory side port, sends requests")
```

对象继承 `SimObject`。我们需要在 C++ 实现中提供 `getPort`，让 gem5 能够取得此对象的端口（port）。

> **译注**：原文将 `SimObject::getPort` 称为纯虚函数；当前 gem5 的基类提供默认实现。这里的重点是：具有自定义端口（port）的对象需要重写该方法，并将无法识别的名称交给基类处理。

该对象的三个参数（parameter）都是端口（port）：两个连接 CPU 的指令和数据接口，另一个连接内存总线。它们没有默认值，只有简要说明。

请记住这些端口（port）的名称，后面实现 `SimpleMemobj` 和 `getPort` 时会显式使用它们。

可以[下载 SimObject 文件]({{ site.baseurl }}/pages/static/scripts/part2/memoryobject/SimpleMemobj.py)。还需要在新目录中创建 SConscript，声明这个 Python 文件；也可以[下载 SConscript]({{ site.baseurl }}/pages/static/scripts/part2/memoryobject/SConscript)。

### 定义 SimpleMemobj 类

先创建 `SimpleMemobj` 的头文件。

```cpp
#include "mem/port.hh"
#include "params/SimpleMemobj.hh"
#include "sim/sim_object.hh"

class SimpleMemobj : public SimObject
{
  private:

  public:

    /** constructor
     */
    SimpleMemobj(SimpleMemobjParams *params);
};
```

### 定义响应端口（port）类型

接下来为 CPU 一侧和内存一侧分别定义端口（port）类。由于其他对象不会使用这些类，我们将它们声明为 `SimpleMemobj` 的内部类。

先实现 CPU 一侧的响应端口（port），让它继承 `ResponsePort`。以下代码声明了需要重写的纯虚函数。

```cpp
class CPUSidePort : public ResponsePort
{
  private:
    SimpleMemobj *owner;

  public:
    CPUSidePort(const std::string& name, SimpleMemobj *owner) :
        ResponsePort(name, owner), owner(owner)
    { }

    AddrRangeList getAddrRanges() const override;

  protected:
    Tick recvAtomic(PacketPtr pkt) override { panic("recvAtomic unimpl."); }
    void recvFunctional(PacketPtr pkt) override;
    bool recvTimingReq(PacketPtr pkt) override;
    void recvRespRetry() override;
};
```

该类需要定义五个函数，还保存一个指向所属对象的成员变量 `owner`，以便调用所属对象的方法。

### 定义请求端口（port）类型

再定义内存一侧的请求端口（port），把来自 CPU 一侧的请求转发到内存系统（memory system）的其他部分。

```cpp
class MemSidePort : public RequestPort
{
  private:
    SimpleMemobj *owner;

  public:
    MemSidePort(const std::string& name, SimpleMemobj *owner) :
        RequestPort(name, owner), owner(owner)
    { }

  protected:
    bool recvTimingResp(PacketPtr pkt) override;
    void recvReqRetry() override;
    void recvRangeChange() override;
};
```

这个类只需重写三个纯虚函数。

### 定义 SimObject 接口

有了 `CPUSidePort` 和 `MemSidePort` 两个类型，就可以在 `SimpleMemobj` 中声明三个端口（port），并声明 `getPort`。gem5 在初始化阶段调用该函数，通过端口（port）连接内存对象。

```cpp
class SimpleMemobj : public SimObject
{
  private:

    <CPUSidePort declaration>
    <MemSidePort declaration>

    CPUSidePort instPort;
    CPUSidePort dataPort;

    MemSidePort memPort;

  public:
    SimpleMemobj(SimpleMemobjParams *params);

    Port &getPort(const std::string &if_name,
                  PortID idx=InvalidPortID) override;
};
```

可以[下载 SimpleMemobj 头文件]({{ site.baseurl }}/pages/static/scripts/part2/memoryobject/simple_memobj.hh)。

### 实现基本的 SimObject 方法

`SimpleMemobj` 的构造函数调用 `SimObject` 的构造函数，并初始化所有端口（port）。按照头文件中的定义，每个端口（port）的构造函数接受两个参数（parameter）：名称和指向所属对象的指针。名称可以是任意字符串，但通常与 Python SimObject 文件中的名称一致。此外，将 `blocked` 初始化为 `false`。

```cpp
#include "learning_gem5/part2/simple_memobj.hh"
#include "debug/SimpleMemobj.hh"

SimpleMemobj::SimpleMemobj(SimpleMemobjParams *params) :
    SimObject(params),
    instPort(params->name + ".inst_port", this),
    dataPort(params->name + ".data_port", this),
    memPort(params->name + ".mem_side", this), blocked(false)
{
}
```

然后实现获取端口（port）的 `getPort` 接口。该函数接受两个参数（parameter），其中 `if_name` 是*当前对象*的接口在 Python 中使用的变量名。

比较 `if_name`：如果是 Python 文件中的 `mem_side`，返回 `memPort`；如果是 `inst_port`，返回 `instPort`；如果是 `data_port`，返回数据端口（port）。否则将请求交给父类。

```cpp
Port &
SimpleMemobj::getPort(const std::string &if_name, PortID idx)
{
    panic_if(idx != InvalidPortID, "This object doesn't support vector ports");

    // This is the name from the Python SimObject declaration (SimpleMemobj.py)
    if (if_name == "mem_side") {
        return memPort;
    } else if (if_name == "inst_port") {
        return instPort;
    } else if (if_name == "data_port") {
        return dataPort;
    } else {
        // pass it along to our super class
        return SimObject::getPort(if_name, idx);
    }
}
```

### 实现请求与响应端口（port）的方法

两类端口（port）的实现相对简单，大多数方法只是把信息传给主体内存对象 `SimpleMemobj`。

先看 `getAddrRanges` 与 `recvFunctional`，它们直接调用 `SimpleMemobj` 的对应方法。

```cpp
AddrRangeList
SimpleMemobj::CPUSidePort::getAddrRanges() const
{
    return owner->getAddrRanges();
}

void
SimpleMemobj::CPUSidePort::recvFunctional(PacketPtr pkt)
{
    return owner->handleFunctional(pkt);
}
```

`SimpleMemobj` 中的实现也只是将请求传递到内存一侧。可以加入 `DPRINTF`，记录执行过程以便调试。

```cpp
void
SimpleMemobj::handleFunctional(PacketPtr pkt)
{
    memPort.sendFunctional(pkt);
}

AddrRangeList
SimpleMemobj::getAddrRanges() const
{
    DPRINTF(SimpleMemobj, "Sending new ranges\n");
    return memPort.getAddrRanges();
}
```

同理，`MemSidePort` 的 `recvRangeChange` 通过 `SimpleMemobj`，将地址范围变化通知转发给响应端口（port）。

```cpp
void
SimpleMemobj::MemSidePort::recvRangeChange()
{
    owner->sendRangeChange();
}
```

```cpp
void
SimpleMemobj::sendRangeChange()
{
    instPort.sendRangeChange();
    dataPort.sendRangeChange();
}
```

### 实现请求接收逻辑

`recvTimingReq` 稍复杂一些，需要判断 `SimpleMemobj` 能否接收请求。这里采用简单的阻塞设计，一次只允许一个尚未完成的请求。如果已有请求在处理，新到达的请求就会被拒绝。

为简化实现，`CPUSidePort` 保存自身接口的全部流量控制信息。增加布尔成员 `needRetry`，记录 `SimpleMemobj` 空闲后是否需要发送重试通知。若对象因已有请求而阻塞，就设置该标志，表示将来需要通知对方重试。

```cpp
bool
SimpleMemobj::CPUSidePort::recvTimingReq(PacketPtr pkt)
{
    if (!owner->handleRequest(pkt)) {
        needRetry = true;
        return false;
    } else {
        return true;
    }
}
```

`SimpleMemobj` 处理请求时，先检查是否正在等待另一个请求的响应。若已阻塞，返回 `false`，通知调用方暂时无法接收。否则将对象标记为阻塞，并通过内存端口（port）发送数据包（packet）。在 `MemSidePort` 中定义一个辅助方法，把流量控制细节封装起来。只要本对象成功接收了请求，`handleRequest` 就返回 `true`，后续发送的流量控制交由 `memPort` 负责。

```cpp
bool
SimpleMemobj::handleRequest(PacketPtr pkt)
{
    if (blocked) {
        return false;
    }
    DPRINTF(SimpleMemobj, "Got request for addr %#x\n", pkt->getAddr());
    blocked = true;
    memPort.sendPacket(pkt);
    return true;
}
```

接着实现 `MemSidePort::sendPacket`，处理对端响应端口（port）无法接收请求的情况。为此需要增加成员变量，保存被阻塞的数据包（packet）。无论发送的是请求还是响应，接收方不能接收时，都由发送方负责保留数据包（packet）。

该方法调用 `sendTimingReq`；如果失败，就将数据包（packet）保存在 `blockedPacket` 中，等待 `recvReqRetry` 到来后重发。实现还包含防御性检查，防止错误覆盖已有的 `blockedPacket`。

```cpp
void
SimpleMemobj::MemSidePort::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked!");
    if (!sendTimingReq(pkt)) {
        blockedPacket = pkt;
    }
}
```

收到重试通知时，再次调用刚才实现的 `sendPacket`，尝试重发。

```cpp
void
SimpleMemobj::MemSidePort::recvReqRetry()
{
    assert(blockedPacket != nullptr);

    PacketPtr pkt = blockedPacket;
    blockedPacket = nullptr;

    sendPacket(pkt);
}
```

### 实现响应接收逻辑

接收响应与接收请求类似。`MemSidePort` 收到响应后，通过 `SimpleMemobj` 将其转发到相应的 `CPUSidePort`。

```cpp
bool
SimpleMemobj::MemSidePort::recvTimingResp(PacketPtr pkt)
{
    return owner->handleResponse(pkt);
}
```

收到响应时，`SimpleMemobj` 应当处于阻塞状态，因为它正在等待这个响应。在将数据包（packet）发回 CPU 之前，必须先解除阻塞，而且必须在*调用 `sendTimingResp` 之前*完成。请求端口（port）可能在同一条调用链内接收响应并立即发送下一个请求，错误的状态更新顺序可能导致无限循环。

解除阻塞后，判断数据包（packet）属于指令访问还是数据访问，并从对应端口（port）发回。最后，由于对象已解除阻塞，可能还需要通知 CPU 一侧此前被拒绝的请求可以重试。

```cpp
bool
SimpleMemobj::handleResponse(PacketPtr pkt)
{
    assert(blocked);
    DPRINTF(SimpleMemobj, "Got response for addr %#x\n", pkt->getAddr());

    blocked = false;

    // Simply forward to the memory port
    if (pkt->req->isInstFetch()) {
        instPort.sendPacket(pkt);
    } else {
        dataPort.sendPacket(pkt);
    }

    instPort.trySendRetry();
    dataPort.trySendRetry();

    return true;
}
```

与 `MemSidePort` 中的辅助方法类似，`CPUSidePort` 也提供 `sendPacket` 来发送响应。它调用 `sendTimingResp`，后者进一步调用对端请求端口（port）的 `recvTimingResp`。如果对端暂时无法接收，就保存数据包（packet），稍后再发。

```cpp
void
SimpleMemobj::CPUSidePort::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked!");

    if (!sendTimingResp(pkt)) {
        blockedPacket = pkt;
    }
}
```

收到 `recvRespRetry` 时重发。该方法与上面的 `recvReqRetry` 相同，只负责再次尝试发送；本次重发仍然可能被拒绝。

```cpp
void
SimpleMemobj::CPUSidePort::recvRespRetry()
{
    assert(blockedPacket != nullptr);

    PacketPtr pkt = blockedPacket;
    blockedPacket = nullptr;

    sendPacket(pkt);
}
```

最后实现 `CPUSidePort` 的 `trySendRetry`。每当 `SimpleMemobj` 可能解除阻塞时，就调用这个方法。它检查 `recvTimingReq` 先前设置的 `needRetry`；若需要重试且满足发送条件，就调用 `sendRetryReq`，进而调用对端请求端口（port）的 `recvReqRetry`，本例中的对端就是 CPU。

```cpp
void
SimpleMemobj::CPUSidePort::trySendRetry()
{
    if (needRetry && blockedPacket == nullptr) {
        needRetry = false;
        DPRINTF(SimpleMemobj, "Sending retry req for %d\n", id);
        sendRetryReq();
    }
}
```

最后还需加入 `SimpleMemobj` 的 `create` 函数，完成这个文件。

```cpp
SimpleMemobj*
SimpleMemobjParams::create()
{
    return new SimpleMemobj(this);
}
```

> **译注**：以上显式实现 `Params::create()` 的写法来自旧版教程；较新版本通常由构建系统自动生成。请结合所用版本及[HelloObject 章节]({{ site.baseurl }}/documentation/learning_gem5/part2/helloobject/)的说明使用，避免重复定义。

可以[下载 SimpleMemobj 实现]({{ site.baseurl }}/pages/static/scripts/part2/memoryobject/simple_memobj.cc)。

下图展示 `CPUSidePort`、`MemSidePort` 与 `SimpleMemobj` 的关系，以及对端如何与本对象交互。粗体函数是本章需要实现的函数，非粗体函数是面向对端的接口。不同颜色表示经过对象的不同 API 路径，例如接收请求或更新地址范围。

![SimpleMemobj 与各端口（port）的交互]({{ site.baseurl }}/pages/static/figures/memobj_api.png)

当前对象只是将数据包（packet）从 CPU 一侧转发到内存一侧。修改 `handleRequest` 与 `handleResponse` 后，就能实现更丰富的功能，例如[下一章]({{ site.baseurl }}/documentation/learning_gem5/part2/simplecache/)的缓存（cache）。

### 创建配置文件

简单内存对象的实现已经完成。[下一章]({{ site.baseurl }}/documentation/learning_gem5/part2/simplecache/)会在此基础上加入缓存（cache）逻辑。先看看如何在配置文件中将 `SimpleMemobj` 加入系统。

配置以[简单配置脚本]({{ site.baseurl }}/documentation/learning_gem5/part1/simple_config/)为基础，将原先 CPU 直接连接内存总线的方式改为：实例化一个 `SimpleMemobj`，放在 CPU 与内存总线之间。

```python
import m5
from m5.objects import *

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

system.cpu = X86TimingSimpleCPU()

system.memobj = SimpleMemobj()

system.cpu.icache_port = system.memobj.inst_port
system.cpu.dcache_port = system.memobj.data_port

system.membus = SystemXBar()

system.memobj.mem_side = system.membus.cpu_side_ports

system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.mem_ctrl = DDR3_1600_8x8()
system.mem_ctrl.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

process = Process()
process.cmd = ['tests/test-progs/hello/bin/x86/linux/hello']
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system = False, system = system)
m5.instantiate()

print ("Beginning simulation!")
exit_event = m5.simulate()
print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
```

可以[下载配置脚本]({{ site.baseurl }}/pages/static/scripts/part2/memoryobject/simple_memobj.py)。运行它会得到以下输出。

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  5 2017 13:40:18
    gem5 started Jan  9 2017 10:17:17
    gem5 executing on chinook, pid 5138
    command line: build/X86/gem5.opt configs/learning_gem5/part2/simple_memobj.py

    Global frequency set at 1000000000000 ticks per second
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb.listener: listening for remote gdb #0 on port 7000
    warn: CoherentXBar system.membus has no snooping ports attached!
    warn: ClockedObject: More than one power state change request encountered within the same simulation tick
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 507841000 because target called exit()

开启 `SimpleMemobj` 调试标志后，可以看到 CPU 发出的内存请求和收到的响应。

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  5 2017 13:40:18
    gem5 started Jan  9 2017 10:18:51
    gem5 executing on chinook, pid 5157
    command line: build/X86/gem5.opt --debug-flags=SimpleMemobj configs/learning_gem5/part2/simple_memobj.py

    Global frequency set at 1000000000000 ticks per second
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
          0: system.memobj: Got request for addr 0x190
      77000: system.memobj: Got response for addr 0x190
      77000: system.memobj: Got request for addr 0x190
     132000: system.memobj: Got response for addr 0x190
     132000: system.memobj: Got request for addr 0x190
     187000: system.memobj: Got response for addr 0x190
     187000: system.memobj: Got request for addr 0x94e30
     250000: system.memobj: Got response for addr 0x94e30
     250000: system.memobj: Got request for addr 0x190
     ...

也可以将 CPU 模型改为乱序（out-of-order）模型 `X86O3CPU`。它允许同时存在多个未完成的内存请求，因此可能产生不同的地址访问序列。由于 `SimpleMemobj` 采用阻塞设计，使用乱序（out-of-order）CPU 时会出现许多停顿。

---
layout: documentation
title: "声明状态机（state machine）"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/cache-declarations/
author: Jason Lowe-Power
---

## 声明状态机（state machine）

先实现 MSI 协议（protocol）的 L1 缓存（cache）控制器。创建 `MSI-cache.sm`，使用以下代码声明状态机（state machine）。

```cpp
machine(MachineType:L1Cache, "MSI cache")
    : <parameters>
{
    <All state machine code>
}
```

SLICC 看起来很像 C++，一个状态机（state machine）文件类似于将类定义与实现都放在头文件中。许多 C++ 风格的语法在 SLICC 中也适用，但它并非 C++：一些 C++ 写法不受支持，SLICC 也有自己的扩展。

`MachineType:L1Cache` 将状态机（state machine）命名为 `L1Cache`。SLICC 用这个名称生成多种对象，例如代表控制器的 SimObject `L1Cache_Controller`。声明中还包含描述字符串 `"MSI cache"`。

SLICC 许多声明都要求提供描述。这是因为它最初用于描述一致性协议（protocol），而不是实现它们。如今这些文字有两个用途：解释变量、状态和事件的设计意图；在生成的 HTML 表格中提供更详细的说明。一致性协议（protocol）可能十分复杂，因此应认真填写这些描述。

## 状态机（state machine）参数（parameter）

`machine()` 声明后跟着冒号，再列出参数（parameter）。这些参数（parameter）会直接导出到生成的 SimObject 中。

MSI L1 缓存（cache）需要：

```cpp
machine(MachineType:L1Cache, "MSI cache")
: Sequencer *sequencer;
  CacheMemory *cacheMemory;
  bool send_evictions;

  <Message buffer declarations>

  {

  }
```

首先是 `Sequencer`，Ruby 通过它与 gem5 其他部分交互。它是带有接收请求接口的内存对象，能够接收 CPU 或其他请求端口（port）发来的访问，将 gem5 数据包（packet）转换为 `RubyRequest`，再放入状态机（state machine）的 `mandatoryQueue`。[输入端口（port）章节]({{ site.baseurl }}/documentation/learning_gem5/part3/cache-in-ports/)会详细介绍这个队列。

> **译注**：原文使用旧称 `master/slave port`，分别对应请求/响应端口（port）。此处按其职责译出。

其次是 `CacheMemory`，负责保存数据与缓存（cache）条目；具体实现、容量等可以在配置时指定。

还可以像普通 SimObject 那样添加其他参数（parameter）。本例的布尔值 `send_evictions` 用于通知乱序（out-of-order）CPU 的加载/存储队列：若某地址在推测性加载后被驱逐，CPU 可能需要取消并重新执行该加载。

仍在参数（parameter）区域内，即第一个左花括号之前，声明所需的消息缓冲区。它们是状态机（state machine）与 Ruby 网络之间的接口，负责发送和接收消息。本例为不同的虚拟网络及其传输方向分别配置缓冲区。

MSI 需要三个虚拟网络来避免死锁，例如不能让响应排在一个停滞的请求后面而无法前进。本例中，响应优先级最高，使用虚拟网络 2；转发请求其次，使用虚拟网络 1；普通请求最低，使用虚拟网络 0。为何需要这三个网络，可参考 Sorin 等人的书。

所需缓冲区声明如下：

```cpp
machine(MachineType:L1Cache, "MSI cache")
: Sequencer *sequencer;
  CacheMemory *cacheMemory;
  bool send_evictions;

  MessageBuffer * requestToDir, network="To", virtual_network="0", vnet_type="request";
  MessageBuffer * responseToDirOrSibling, network="To", virtual_network="2", vnet_type="response";

  MessageBuffer * forwardFromDir, network="From", virtual_network="1", vnet_type="forward";
  MessageBuffer * responseFromDirOrSibling, network="From", virtual_network="2", vnet_type="response";

  MessageBuffer * mandatoryQueue;

{

}
```

共五个缓冲区：两个 `To`、两个 `From`，以及一个特殊队列。`To` 用于向其他控制器发送消息，`From` 用于接收来自其他控制器的消息。

> **译注**：原文把 `To` 与 `From` 都类比为 slave 端口（port），容易引起混淆。这里直接说明消息流向；消息缓冲区并不等同于经典内存接口的请求/响应端口（port）。原文也混用了虚拟通道与虚拟网络，这里按示例的 `virtual_network` 字段称为虚拟网络。

两个 `To` 缓冲区分别发送低优先级请求与高优先级响应。网络编号本身不自动赋予优先级；优先级由控制器检查缓冲区的顺序决定。约定较大的编号代表较高优先级有助于阅读，但 Ruby 在这里主要通过编号区分网络：网络 2 上的消息只能进入同属网络 2 的缓冲区，不能跨网络跳转。

接收方向同样有两类消息：目录转发的请求，例如其他缓存（cache）请求写权限，而本地持有只读副本；以及对本控制器先前请求的响应。响应优先于转发请求。

特殊队列 `mandatoryQueue` 接收 `Sequencer` 从 gem5 数据包（packet）转换而来的 Ruby 请求。它不连接 Ruby 网络。注意，这个名称在实现中是硬编码的，必须准确写成 `mandatoryQueue`。

这一参数（parameter）区域会生成 SimObject 描述文件，所有条目都可以在 Python 配置中访问。生成的 `L1Cache_Controller.py` 看起来会很熟悉，但不要直接修改生成文件。

```python
from m5.params import *
from m5.SimObject import SimObject
from Controller import RubyController

class L1Cache_Controller(RubyController):
    type = 'L1Cache_Controller'
    cxx_header = 'mem/protocol/L1Cache_Controller.hh'
    sequencer = Param.RubySequencer("")
    cacheMemory = Param.RubyCache("")
    send_evictions = Param.Bool("")
    requestToDir = Param.MessageBuffer("")
    responseToDirOrSibling = Param.MessageBuffer("")
    forwardFromDir = Param.MessageBuffer("")
    responseFromDirOrSibling = Param.MessageBuffer("")
    mandatoryQueue = Param.MessageBuffer("")
```

## 状态声明

接下来声明所有稳定状态和瞬态状态。命名遵循 Sorin 等人的约定。例如 `IM_AD` 表示从 Invalid 向 Modified 转换，正在等待确认与数据。这些状态对应书中表 8.3 的第一列。

```cpp
state_declaration(State, desc="Cache states") {
    I,      AccessPermission:Invalid,
                desc="Not present/Invalid";

    // States moving out of I
    IS_D,   AccessPermission:Invalid,
                desc="Invalid, moving to S, waiting for data";
    IM_AD,  AccessPermission:Invalid,
                desc="Invalid, moving to M, waiting for acks and data";
    IM_A,   AccessPermission:Busy,
                desc="Invalid, moving to M, waiting for acks";

    S,      AccessPermission:Read_Only,
                desc="Shared. Read-only, other caches may have the block";

    // States moving out of S
    SM_AD,  AccessPermission:Read_Only,
                desc="Shared, moving to M, waiting for acks and 'data'";
    SM_A,   AccessPermission:Read_Only,
                desc="Shared, moving to M, waiting for acks";

    M,      AccessPermission:Read_Write,
                desc="Modified. Read & write permissions. Owner of block";

    // States moving to Invalid
    MI_A,   AccessPermission:Busy,
                desc="Was modified, moving to I, waiting for put ack";
    SI_A,   AccessPermission:Busy,
                desc="Was shared, moving to I, waiting for put ack";
    II_A,   AccessPermission:Invalid,
                desc="Sent valid data before receiving put ack. "Waiting for put ack.";
}
```

每个状态关联一种访问权限：`Invalid`、`NotPresent`、`Busy`、`Read_Only` 或 `Read_Write`。这些权限用于*功能访问*。功能访问类似调试访问，使模拟器（simulator）能够立即读取或更新数据，例如系统调用模拟（syscall emulation）模式中将文件内容直接加载到内存。

功能访问需要考虑所有可能持有目标地址的缓存（cache）。功能读取从具有只读或读写权限的有效副本取得数据，这些有效副本应当一致；功能写入则更新权限为忙碌、只读或读写的对应块。

> **译注**：原文称功能读取会访问“所有”匹配块；实际 Ruby 的读取路径会按权限和有效副本情况选择数据来源，不应理解为一定逐一读取所有副本。功能写入必须避免遗留旧副本。

## 事件声明

声明传入消息可能触发的所有事件，它们对应 Sorin 等人书中表 8.3 的第一行。

```cpp
enumeration(Event, desc="Cache events") {
    // From the processor/sequencer/mandatory queue
    Load,           desc="Load from processor";
    Store,          desc="Store from processor";

    // Internal event (only triggered from processor requests)
    Replacement,    desc="Triggered when block is chosen as victim";

    // Forwarded request from other cache via dir on the forward network
    FwdGetS,        desc="Directory sent us a request to satisfy GetS. We must have the block in M to respond to this.";
    FwdGetM,        desc="Directory sent us a request to satisfy GetM. We must have the block in M to respond to this.";
    Inv,            desc="Invalidate from the directory.";
    PutAck,         desc="Response from directory after we issue a put. This must be on the fwd network to avoid deadlock.";

    // Responses from directory
    DataDirNoAcks,  desc="Data from directory (acks = 0)";
    DataDirAcks,    desc="Data from directory (acks > 0)";

    // Responses from other caches
    DataOwner,      desc="Data from owner";
    InvAck,         desc="Invalidation ack from other cache after Inv";

    // Special event to simplify implementation
    LastInvAck,     desc="Triggered after the last ack is received";
}
```

## 自定义结构

接下来定义控制器要使用的结构。首先是 `Entry`，即 `CacheMemory` 保存的条目。它至少包含数据和状态，也可以增加其他信息。这里保存的是上面定义的 `State`，而非某个硬编码的公共状态类型。

抽象基类 `AbstractCacheEntry` 位于 `src/mem/ruby/slicc_interface/AbstractCacheEntry.hh`。若要在 SLICC 中使用其成员函数，需要在这里声明；本例没有用到。

```cpp
structure(Entry, desc="Cache entry", interface="AbstractCacheEntry") {
    State CacheState,        desc="cache state";
    DataBlock DataBlk,       desc="Data in the block";
}
```

还需要 TBE，即事务（transaction）缓冲区条目，用于保存瞬态期间的信息。它类似 MSHR，在本协议（protocol）中承担 MSHR 的职责，但也可能因其他用途分配。本例保存状态、数据，以及仍需等待的确认数量。`AcksOutstanding` 用于其他控制器返回确认而非数据的转换过程。

```cpp
structure(TBE, desc="Entry for transient requests") {
    State TBEState,         desc="State of block";
    DataBlock DataBlk,      desc="Data for the block. Needed for MI_A";
    int AcksOutstanding, default=0, desc="Number of acks left to receive.";
}
```

随后需要保存 TBE 的表。`TBETable` 在 SLICC 之外用 C++ 定义，因此需要声明这个外部类型及要调用的方法。实现位于 `src/mem/ruby/structures/TBETable.hh`，以刚才定义的 TBE 结构作为模板类型，后面会看到相关处理方式。

```cpp
structure(TBETable, external="yes") {
  TBE lookup(Addr);
  void allocate(Addr);
  void deallocate(Addr);
  bool isPresent(Addr);
}
```

`external="yes"` 告诉 SLICC 不必寻找该结构的实现，作用类似 C/C++ 中声明外部符号。

## 其他必要的声明与定义

最后完成一些通用代码：声明变量、声明需要使用的 `AbstractController` 方法，并实现相关接口。

首先声明保存 TBE 表的变量。只有在前面定义了 TBE 后，才知道表的确切类型，因此需要在 SLICC 中完成这一步。这里的写法比较特殊，是为了生成正确的 C++ 模板实例。SLICC 会给状态机（state machine）内部定义的类型加上名称前缀，例如 `TBE` 在 C++ 中实际为 `L1Cache_TBE`。

构造 `TBETable` 时还要传入一个来自 `AbstractController` 的参数（parameter）。由于它没有对应的 SLICC 名称，必须使用 C++ 中的成员名称。

```cpp
TBETable TBEs, template="<L1Cache_TBE>", constructor="m_number_of_TBEs";
```

理解这段代码后，你就掌握了 SLICC 中较为棘手的一种用法。

要在文件中调用 `AbstractController` 的方法，需先声明。本例只需要 `clockEdge()`：

```cpp
Tick clockEdge();
```

动作中还需要一些函数，用于设置和清除动作代码块可用的隐式变量。一个转换包含多个动作时，这些函数可能必不可少。[动作章节]({{ site.baseurl }}/documentation/learning_gem5/part3/cache-actions/)会详细解释。

```cpp
void set_cache_entry(AbstractCacheEntry a);
void unset_cache_entry();
void set_tbe(TBE b);
void unset_tbe();
```

`mapAddressToMachine` 也很有用。它允许在运行配置中调整分银行目录或缓存（cache）的地址映射，无需将映射规则硬编码进 SLICC 文件。

```cpp
MachineID mapAddressToMachine(Addr addr, MachineType mtype);
```

也可以在这里添加并实现自己的辅助函数。例如，用单个函数按地址获取缓存（cache）块。由于后续需要修改该块，这里使用 `return_by_pointer`，即返回指向原对象的访问方式，而非副本。`CacheMemory` 保存的是抽象类型，因此还需要转换为本文件定义的 `Entry` 类型。

```cpp
// Convenience function to look up the cache entry.
// Needs a pointer so it will be a reference and can be updated in actions
Entry getCacheEntry(Addr address), return_by_pointer="yes" {
    return static_cast(Entry, "pointer", cacheMemory.lookup(address));
}
```

接下来是各协议（protocol）间通常变化不大的接口代码：

`getState`
:   根据 TBE、条目和地址取得块状态，在事件触发时用于选择转换。通常优先使用有效 TBE 中的状态，否则使用有效条目的状态。

`setState`
:   根据 TBE、条目和地址更新块状态，在转换结束时设置最终状态。

`getAccessPermission`
:   获取块的访问权限，决定能否进行功能访问。与 `getState` 类似，优先查询有效 TBE，其次查询有效条目，否则认为该块不存在。

`setAccessPermission`
:   设置块的访问权限。

`functionalRead`
:   执行功能读取。TBE 可能持有更新的数据，因此先检查 TBE。`testAndRead` 和 `testAndWrite` 定义于 `src/mem/ruby/slicc_interface/Util.hh`。

`functionalWrite`
:   执行功能写入，可能需要同时更新 TBE 和条目中的数据。

```cpp
State getState(TBE tbe, Entry cache_entry, Addr addr) {
    // The TBE state will override the state in cache memory, if valid
    if (is_valid(tbe)) { return tbe.TBEState; }
    // Next, if the cache entry is valid, it holds the state
    else if (is_valid(cache_entry)) { return cache_entry.CacheState; }
    // If the block isn't present, then it's state must be I.
    else { return State:I; }
}

void setState(TBE tbe, Entry cache_entry, Addr addr, State state) {
  if (is_valid(tbe)) { tbe.TBEState := state; }
  if (is_valid(cache_entry)) { cache_entry.CacheState := state; }
}

AccessPermission getAccessPermission(Addr addr) {
    TBE tbe := TBEs[addr];
    if(is_valid(tbe)) {
        return L1Cache_State_to_permission(tbe.TBEState);
    }

    Entry cache_entry := getCacheEntry(addr);
    if(is_valid(cache_entry)) {
        return L1Cache_State_to_permission(cache_entry.CacheState);
    }

    return AccessPermission:NotPresent;
}

void setAccessPermission(Entry cache_entry, Addr addr, State state) {
    if (is_valid(cache_entry)) {
        cache_entry.changePermission(L1Cache_State_to_permission(state));
    }
}

void functionalRead(Addr addr, Packet *pkt) {
    TBE tbe := TBEs[addr];
    if(is_valid(tbe)) {
        testAndRead(addr, tbe.DataBlk, pkt);
    } else {
        testAndRead(addr, getCacheEntry(addr).DataBlk, pkt);
    }
}

int functionalWrite(Addr addr, Packet *pkt) {
    int num_functional_writes := 0;

    TBE tbe := TBEs[addr];
    if(is_valid(tbe)) {
        num_functional_writes := num_functional_writes +
            testAndWrite(addr, tbe.DataBlk, pkt);
        return num_functional_writes;
    }

    num_functional_writes := num_functional_writes +
            testAndWrite(addr, getCacheEntry(addr).DataBlk, pkt);
    return num_functional_writes;
}
```

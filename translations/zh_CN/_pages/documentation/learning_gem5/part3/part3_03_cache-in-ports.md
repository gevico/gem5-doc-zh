---
layout: documentation
title: "输入端口（port）代码块"
doc: 学习 gem5
parent: part3
permalink: documentation/learning_gem5/part3/cache-in-ports/
author: Jason Lowe-Power
---

## 输入端口（port）代码块

声明所需结构后，首先编写真正处理消息的 `in_port` 部分：根据传入消息决定*触发*哪个*事件*。

不过在此之前，需要先声明输出端口（port）。

```cpp
out_port(request_out, RequestMsg, requestToDir);
out_port(response_out, ResponseMsg, responseToDirOrSibling);
```

这里相当于为 `requestToDir` 和 `responseToDirOrSibling` 分别赋予 `request_out`、`response_out` 两个名称。后面向这些缓冲区入队消息时使用新名称。声明也指定了允许发送的消息类型，其详细定义位于稍后介绍的 `MSI-msg.sm`。

接下来编写 `in_port` 代码块。SLICC 有许多语法看起来像 `if` 语句块，但实际携带特定的生成规则。例如，`in_port()` 内的代码会被放入生成的 `L1Cache_Wakeup.cc`。

各个 `in_port` 按声明顺序执行，或者按显式指定的优先级执行。控制器被唤醒后，先检查第一个输入端口（port）；成功处理消息后，继续检查是否还有消息可处理。如果没有消息或没有触发事件，则检查下一个。

执行 `in_port` 时可能遇到三类停顿。第一类是达到每周期最大转换次数；这一上限由参数（parameter）控制，达到后需要等到下一周期。第二类是*资源停顿*，例如采用 `BankedArray` 带宽模型时，所需的缓存（cache）银行正在被占用。第三类是*协议（protocol）停顿*，由特殊动作触发，表示当前消息暂时不能处理。

原文强调，协议（protocol）停顿与资源停顿可能使其他消息也无法前进，因此虚拟网络的划分和检查顺序十分重要。尤其要避免高优先级队列的停滞阻碍解除依赖所需的消息。

> **译注**：原文将这两类停顿概括为阻止“所有”输入端口（port）执行。不同版本生成的唤醒逻辑可能继续检查其他队列，不能把该表述视为所有 Ruby 版本的统一调度规则；应结合所用版本的 `*_Wakeup.cc` 理解具体行为。

以下是 L1 控制器中最高优先级的输入路径，接收来自目录或其他缓存（cache）的响应。随后逐段解释。

```cpp
in_port(response_in, ResponseMsg, responseFromDirOrSibling) {
    if (response_in.isReady(clockEdge())) {
        peek(response_in, ResponseMsg) {
            Entry cache_entry := getCacheEntry(in_msg.addr);
            TBE tbe := TBEs[in_msg.addr];
            assert(is_valid(tbe));

            if (machineIDToMachineType(in_msg.Sender) ==
                        MachineType:Directory) {
                if (in_msg.Type != CoherenceResponseType:Data) {
                    error("Directory should only reply with data");
                }
                assert(in_msg.Acks + tbe.AcksOutstanding >= 0);
                if (in_msg.Acks + tbe.AcksOutstanding == 0) {
                    trigger(Event:DataDirNoAcks, in_msg.addr, cache_entry,
                            tbe);
                } else {
                    trigger(Event:DataDirAcks, in_msg.addr, cache_entry,
                            tbe);
                }
            } else {
                if (in_msg.Type == CoherenceResponseType:Data) {
                    trigger(Event:DataOwner, in_msg.addr, cache_entry,
                            tbe);
                } else if (in_msg.Type == CoherenceResponseType:InvAck) {
                    DPRINTF(RubySlicc, "Got inv ack. %d left\n",
                            tbe.AcksOutstanding);
                    if (tbe.AcksOutstanding == 1) {
                        trigger(Event:LastInvAck, in_msg.addr, cache_entry,
                                tbe);
                    } else {
                        trigger(Event:InvAck, in_msg.addr, cache_entry,
                                tbe);
                    }
                } else {
                    error("Unexpected response from other cache");
                }
            }
        }
    }
}
```

与输出声明类似，`response_in` 是后续引用的名称，`ResponseMsg` 是预期消息类型。每个 `in_port` 首先检查缓冲区中是否有当前可处理的消息；若没有，就跳过并检查下一个。

```cpp
in_port(response_in, ResponseMsg, responseFromDirOrSibling) {
    if (response_in.isReady(clockEdge())) {
        . . .
    }
}
```

如果存在可用消息，使用特殊的 `peek` 代码块查看队首。块内自动提供 `in_msg`，其类型由第二个参数（parameter）指定，此处为 `ResponseMsg`；`response_in` 指定要查看的缓冲区。

然后按传入地址取得缓存（cache）条目和 TBE。前面定义的 `getCacheEntry` 返回匹配的有效条目；若该块不存在，则返回无效结果。

由于收到的是本控制器先前请求的响应，TBE 表中*必须*存在有效条目。因此这里使用断言 `assert`。在一致性协议（protocol）中适当加入断言，能明显降低调试难度。

```cpp
peek(response_in, ResponseMsg) {
    Entry cache_entry := getCacheEntry(in_msg.addr);
    TBE tbe := TBEs[in_msg.addr];
    assert(is_valid(tbe));

    . . .
}
```

接下来根据消息选择事件。在此之前，先了解响应携带的字段。

创建 `MSI-msg.sm`，集中定义消息类型。这里的结构将供整个协议（protocol）的 SLICC 文件使用，稍后通过 `MSI.slicc` 包含它，类似 C/C++ 头文件中的全局定义。

加入以下代码：

```cpp
structure(ResponseMsg, desc="Used for Dir->Cache and Fwd message responses",
          interface="Message") {
    Addr addr,                   desc="Physical address for this response";
    CoherenceResponseType Type,  desc="Type of response";
    MachineID Sender,            desc="Node who is responding to the request";
    NetDest Destination,         desc="Multicast destination mask";
    DataBlock DataBlk,           desc="data for the cache line";
    MessageSizeType MessageSize, desc="size category of the message";
    int Acks,                    desc="Number of acks required from others";

    // This must be overridden here to support functional accesses
    bool functionalRead(Packet *pkt) {
        if (Type == CoherenceResponseType:Data) {
            return testAndRead(addr, DataBlk, pkt);
        }
        return false;
    }

    bool functionalWrite(Packet *pkt) {
        // No check on message type required since the protocol should read
        // data block from only those messages that contain valid data
        return testAndWrite(addr, DataBlk, pkt);
    }
}
```

消息仍是 SLICC 结构，但实现了 `Message` 接口。可以添加所需成员。首先是地址；注意成员名不能写成大写开头的 `Addr`，否则会与类型名称冲突。

其次是响应类型。本例有两类响应：数据，以及其他缓存（cache）使自身副本失效后返回的失效确认。为此，在同一文件的 `ResponseMsg` 声明*之前*定义枚举 `CoherenceResponseType`：

```cpp
enumeration(CoherenceResponseType, desc="Types of response messages") {
    Data,       desc="Contains the most up-to-date data";
    InvAck,     desc="Message from another cache that they have inv. the blk";
}
```

响应还记录发送方的 `MachineID`，它标识具体实例，例如目录 0 或缓存（cache）12。`MachineID` 包含 `MachineType`，如前面定义的 `L1Cache`，以及该类型实例的 `version` 编号。配置系统时会再次介绍编号。

所有消息都需要目的地和大小。目的地使用 `NetDest`，它以位图表示系统中的 `MachineID`，因而可以向灵活指定的一组接收者广播。消息大小的可选类型定义于 `src/mem/ruby/protocol/RubySlicc_Exports.sm`。

响应还可能携带数据块与预期确认数量，因此也把这些字段加入定义。

最后定义功能读取和功能写入方法，供 Ruby 在功能访问时检查传输中的消息。原文提醒，这部分支持在其对应版本中较为脆弱；目标地址仍有在途消息时，功能访问可能失败。

可以[查看完整的 MSI-msg.sm](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/MSI-msg.sm)。

了解响应的内容后，再看 `in_port` 如何选择事件。

```cpp
// If it's from the directory...
if (machineIDToMachineType(in_msg.Sender) ==
            MachineType:Directory) {
    if (in_msg.Type != CoherenceResponseType:Data) {
        error("Directory should only reply with data");
    }
    assert(in_msg.Acks + tbe.AcksOutstanding >= 0);
    if (in_msg.Acks + tbe.AcksOutstanding == 0) {
        trigger(Event:DataDirNoAcks, in_msg.addr, cache_entry,
                tbe);
    } else {
        trigger(Event:DataDirAcks, in_msg.addr, cache_entry,
                tbe);
    }
} else {
    // This is from another cache.
    if (in_msg.Type == CoherenceResponseType:Data) {
        trigger(Event:DataOwner, in_msg.addr, cache_entry,
                tbe);
    } else if (in_msg.Type == CoherenceResponseType:InvAck) {
        DPRINTF(RubySlicc, "Got inv ack. %d left\n",
                tbe.AcksOutstanding);
        if (tbe.AcksOutstanding == 1) {
            // If there is exactly one ack remaining then we
            // know it is the last ack.
            trigger(Event:LastInvAck, in_msg.addr, cache_entry,
                    tbe);
        } else {
            trigger(Event:InvAck, in_msg.addr, cache_entry,
                    tbe);
        }
    } else {
        error("Unexpected response from other cache");
    }
}
```

先判断发送方是目录还是另一个缓存（cache）。如果来自目录，就必须是数据响应，因为本例中目录不会通过此路径发送失效确认。

这里使用第二种调试手段 `error`：它与 `panic` 类似，停止模拟（simulation）并打印传入的字符串。

收到目录数据时，合并目录告知的确认总数与此前已收到确认所形成的计数后，待收确认数不应小于零。必须这样计算，是因为其他缓存（cache）的确认可能比目录的数据响应先到达。

> **译注**：`tbe.AcksOutstanding` 不是单纯的“已收到确认数”。在目录告知总数之前，每收到一个确认就将它减一；目录响应到来后再加上预期总数，得到仍需等待的数量。

因此有两种情况：所有确认已经到齐，现在才收到数据，对应表 8.3 中的 `data from dir acks==0`；或者仍需等待更多确认。代码检查这一条件，触发不同事件。

`trigger` 接受四个参数（parameter）：事件、操作对象的物理块地址、缓存（cache）条目和 TBE。事件来自前面的 `Event` 声明。地址通常与 `in_msg` 相同，但替换时使用被驱逐块的地址。若对应条目或 TBE 不存在，后两项可能无效。

动作中将通过隐式变量 `address`、`cache_entry` 和 `tbe` 使用后三个参数（parameter）。

转换成功后，只要尚未达到每周期转换上限，控制器就会再次执行输入逻辑；如果还有消息，就可能继续触发转换。

若响应来自其他缓存（cache），则按上面的代码触发其他事件。这些事件直接对应 Sorin 等人书中的表 8.3。

应尽量在 `in_port` 中完成决定动作组合的条件判断，让一个事件对应明确的执行路径。需要有条件地选择动作时，通常应通过不同状态或事件表示。

原因在于 Ruby 会在执行转换前检查资源，转换具有原子性：要么全部动作执行，要么都不执行。若动作内部的条件分支改变资源需求，SLICC 可能无法正确分析，进而造成异常性能、死锁或其他错误。

> **译注**：原文进一步要求动作内完全不能出现 `if`，但后续示例本身也含有条件判断。关键是不要让运行时分支破坏静态资源检查；并非所有不改变资源需求的条件语句都一概禁止。

处理完最高优先级的响应网络，再添加转发请求网络。首先在 `MSI-msg.sm` 中定义 `RequestMsg` 和枚举 `CoherenceRequestType`。这些是全局定义，*不要放在 MSI-cache.sm 中*。

也可以分别为转发请求和普通请求定义消息及枚举，但本例共用一套类型，以简化代码。

```cpp
enumeration(CoherenceRequestType, desc="Types of request messages") {
    GetS,       desc="Request from cache for a block with read permission";
    GetM,       desc="Request from cache for a block with write permission";
    PutS,       desc="Sent to directory when evicting a block in S (clean WB)";
    PutM,       desc="Sent to directory when evicting a block in M";

    // "Requests" from the directory to the caches on the fwd network
    Inv,        desc="Probe the cache and invalidate any matching blocks";
    PutAck,     desc="The put request has been processed.";
}
```

```cpp
structure(RequestMsg, desc="Used for Cache->Dir and Fwd messages",  interface="Message") {
    Addr addr,                   desc="Physical address for this request";
    CoherenceRequestType Type,   desc="Type of request";
    MachineID Requestor,         desc="Node who initiated the request";
    NetDest Destination,         desc="Multicast destination mask";
    DataBlock DataBlk,           desc="data for the cache line";
    MessageSizeType MessageSize, desc="size category of the message";

    bool functionalRead(Packet *pkt) {
        // Requests should never have the only copy of the most up-to-date data
        return false;
    }

    bool functionalWrite(Packet *pkt) {
        // No check on message type required since the protocol should read
        // data block from only those messages that contain valid data
        return testAndWrite(addr, DataBlk, pkt);
    }
}
```

转发请求的输入逻辑很直接，为不同请求类型触发对应事件。

```cpp
in_port(forward_in, RequestMsg, forwardFromDir) {
    if (forward_in.isReady(clockEdge())) {
        peek(forward_in, RequestMsg) {
            // Grab the entry and tbe if they exist.
            Entry cache_entry := getCacheEntry(in_msg.addr);
            TBE tbe := TBEs[in_msg.addr];

            if (in_msg.Type == CoherenceRequestType:GetS) {
                trigger(Event:FwdGetS, in_msg.addr, cache_entry, tbe);
            } else if (in_msg.Type == CoherenceRequestType:GetM) {
                trigger(Event:FwdGetM, in_msg.addr, cache_entry, tbe);
            } else if (in_msg.Type == CoherenceRequestType:Inv) {
                trigger(Event:Inv, in_msg.addr, cache_entry, tbe);
            } else if (in_msg.Type == CoherenceRequestType:PutAck) {
                trigger(Event:PutAck, in_msg.addr, cache_entry, tbe);
            } else {
                error("Unexpected forward message!");
            }
        }
    }
}
```

最后是 `mandatoryQueue`。它优先级最低，因此声明在文件中其他输入路径之后。它使用特殊消息类型 `RubyRequest`，包含两个地址：`LineAddress` 已按块对齐，`PhysicalAddress` 保存原始请求地址，可能没有按块对齐。还有其他字段可供更复杂的协议（protocol）使用；本例只需要 `LineAddress`。

> **译注**：原文给出的类型声明路径为 `src/mem/protocol/RubySlicc_Types.sm`，遗漏了 `ruby`；对应路径应为 `src/mem/ruby/protocol/RubySlicc_Types.sm`。

```cpp
in_port(mandatory_in, RubyRequest, mandatoryQueue) {
    if (mandatory_in.isReady(clockEdge())) {
        peek(mandatory_in, RubyRequest, block_on="LineAddress") {
            Entry cache_entry := getCacheEntry(in_msg.LineAddress);
            TBE tbe := TBEs[in_msg.LineAddress];

            if (is_invalid(cache_entry) &&
                    cacheMemory.cacheAvail(in_msg.LineAddress) == false ) {
                Addr addr := cacheMemory.cacheProbe(in_msg.LineAddress);
                Entry victim_entry := getCacheEntry(addr);
                TBE victim_tbe := TBEs[addr];
                trigger(Event:Replacement, addr, victim_entry, victim_tbe);
            } else {
                if (in_msg.Type == RubyRequestType:LD ||
                        in_msg.Type == RubyRequestType:IFETCH) {
                    trigger(Event:Load, in_msg.LineAddress, cache_entry,
                            tbe);
                } else if (in_msg.Type == RubyRequestType:ST) {
                    trigger(Event:Store, in_msg.LineAddress, cache_entry,
                            tbe);
                } else {
                    error("Unexpected type from processor");
                }
            }
        }
    }
}
```

这里引入两个新概念。首先，`peek` 的 `block_on="LineAddress"` 指定按块地址检查阻塞状态，用于使同一块上需要阻塞的后续请求等待当前操作完成。

其次，检查目标条目是否有效。如果不存在且相应组已没有空位，就必须驱逐其他条目。调用 `CacheMemory::cacheProbe`，按配置的替换策略（replacement policy）选择牺牲块，并取得其物理块地址。

触发 `Replacement` 时，必须使用*牺牲块的地址*及其条目、TBE。这样替换动作才会操作被驱逐的块，而不是新请求的块。还要注意，原始请求仍需保留在 `mandatoryQueue` 中，不能只因替换完成就将它弹出；应等该请求本身被处理后再移除。

不需要替换时，就根据请求类型触发 `Load` 或 `Store`。

---
layout: documentation
title: "MSI 目录实现"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/directory/
author: Jason Lowe-Power
---

## 实现 MSI 目录控制器

目录控制器与 L1 缓存（cache）控制器的实现方式很相似，只是采用不同的状态转换表。目录的状态机（state machine）见 Sorin 等人书中的表 8.2。本节主要介绍额外的 SLICC 细节，以及目录与缓存（cache）控制器的差异。先创建 `MSI-dir.sm`。

```cpp
machine(MachineType:Directory, "Directory protocol")
:
  DirectoryMemory * directory;
  Cycles toMemLatency := 1;

MessageBuffer *forwardToCache, network="To", virtual_network="1",
      vnet_type="forward";
MessageBuffer *responseToCache, network="To", virtual_network="2",
      vnet_type="response";

MessageBuffer *requestFromCache, network="From", virtual_network="0",
      vnet_type="request";

MessageBuffer *responseFromCache, network="From", virtual_network="2",
      vnet_type="response";

MessageBuffer *requestToMemory;

MessageBuffer *responseFromMemory;

{
. . .
}
```

目录控制器有 `DirectoryMemory` 和 `toMemLatency` 两个主要参数（parameter）。`DirectoryMemory` 的初始化覆盖*全部*物理内存，是完整目录，而非只保存部分目录信息的目录缓存（cache）。本例为每个 64 字节物理块保留条目指针，但具体条目在访问时才按需分配。

`toMemLatency` 用于向内存请求队列 `enqueue` 时建模目录延迟。L1 示例中延迟直接写在代码里，这里改为可配置值，默认 1 个周期。SLICC 中可以不提供默认值；如果提供，会传递给生成的 SimObject 参数（parameter）。

接下来声明消息缓冲区。它们的*虚拟网络编号必须与 L1 对应缓冲区一致*，Ruby 网络依靠这些编号在控制器之间传递消息。

另有两个特殊缓冲区 `requestToMemory` 和 `responseFromMemory`。它们类似 `mandatoryQueue`，但面向内存请求方向：前者将请求送往内存端口（port），后者接收该端口（port）返回的响应。稍后的动作会使用它们。

然后声明状态、事件及本地结构。

```cpp
state_declaration(State, desc="Directory states",
                  default="Directory_State_I") {
    // Stable states.
    // NOTE: These are "cache-centric" states like in Sorin et al.
    // However, The access permissions are memory-centric.
    I, AccessPermission:Read_Write,  desc="Invalid in the caches.";
    S, AccessPermission:Read_Only,   desc="At least one cache has the blk";
    M, AccessPermission:Invalid,     desc="A cache has the block in M";

    // Transient states
    S_D, AccessPermission:Busy,      desc="Moving to S, but need data";

    // Waiting for data from memory
    S_m, AccessPermission:Read_Write, desc="In S waiting for mem";
    M_m, AccessPermission:Read_Write, desc="Moving to M waiting for mem";

    // Waiting for write-ack from memory
    MI_m, AccessPermission:Busy,       desc="Moving to I waiting for ack";
    SS_m, AccessPermission:Busy,       desc="Moving to I waiting for ack";
}

enumeration(Event, desc="Directory events") {
    // Data requests from the cache
    GetS,         desc="Request for read-only data from cache";
    GetM,         desc="Request for read-write data from cache";

    // Writeback requests from the cache
    PutSNotLast,  desc="PutS and the block has other sharers";
    PutSLast,     desc="PutS and the block has no other sharers";
    PutMOwner,    desc="Dirty data writeback from the owner";
    PutMNonOwner, desc="Dirty data writeback from non-owner";

    // Cache responses
    Data,         desc="Response to fwd request with data";

    // From Memory
    MemData,      desc="Data from memory";
    MemAck,       desc="Ack from memory that write is complete";
}

structure(Entry, desc="...", interface="AbstractCacheEntry", main="false") {
    State DirState,         desc="Directory state";
    NetDest Sharers,        desc="Sharers for this block";
    NetDest Owner,          desc="Owner of this block";
}
```

`state_declaration` 指定了默认状态。SLICC 中许多对象都可以指定默认值，但这里必须使用生成后的 C++ 名称。本例由机器名 `Directory`、结构名 `State` 和状态名 `I` 组成 `Directory_State_I`。

注意，目录中的访问权限以*内存*为视角，而状态名称仍与 Sorin 等人的表格一样，以缓存（cache）为视角。例如缓存（cache）处于 Modified 时，内存副本可能已经过时。

`Entry` 的共享者集合和拥有者都使用 `NetDest`。共享者自然需要位图来表示多个 L1；拥有者使用相同类型，则便于直接复制到响应消息的目的地字段。`main="false"` 表明这不是控制器的主缓存（cache）条目，不参与相应的替换处理。`DirectoryMemory` 覆盖所有后备内存位置，因此无需替换策略（replacement policy）。

相较于表 8.2，本实现增加了几个瞬态状态，以处理尚未返回的内存访问。书中为简化描述，假定目录状态与数据一起保存在主存中；gem5 则需要显式等待内存响应。因此还加入了对应的内存响应事件。

接下来声明或实现必要函数。`getDirectoryEntry` 返回已有的有效条目；如果尚未分配，则按需创建，从而节省宿主机内存。

```cpp
Tick clockEdge();

Entry getDirectoryEntry(Addr addr), return_by_pointer = "yes" {
    Entry dir_entry := static_cast(Entry, "pointer", directory[addr]);
    if (is_invalid(dir_entry)) {
        // This first time we see this address allocate an entry for it.
        dir_entry := static_cast(Entry, "pointer",
                                 directory.allocate(addr, new Entry));
    }
    return dir_entry;
}

State getState(Addr addr) {
    if (directory.isPresent(addr)) {
        return getDirectoryEntry(addr).DirState;
    } else {
        return State:I;
    }
}

void setState(Addr addr, State state) {
    if (directory.isPresent(addr)) {
        if (state == State:M) {
            DPRINTF(RubySlicc, "Owner %s\n", getDirectoryEntry(addr).Owner);
            assert(getDirectoryEntry(addr).Owner.count() == 1);
            assert(getDirectoryEntry(addr).Sharers.count() == 0);
        }
        getDirectoryEntry(addr).DirState := state;
        if (state == State:I)  {
            assert(getDirectoryEntry(addr).Owner.count() == 0);
            assert(getDirectoryEntry(addr).Sharers.count() == 0);
        }
    }
}

AccessPermission getAccessPermission(Addr addr) {
    if (directory.isPresent(addr)) {
        Entry e := getDirectoryEntry(addr);
        return Directory_State_to_permission(e.DirState);
    } else  {
        return AccessPermission:NotPresent;
    }
}
void setAccessPermission(Addr addr, State state) {
    if (directory.isPresent(addr)) {
        Entry e := getDirectoryEntry(addr);
        e.changePermission(Directory_State_to_permission(state));
    }
}

void functionalRead(Addr addr, Packet *pkt) {
    functionalMemoryRead(pkt);
}

int functionalWrite(Addr addr, Packet *pkt) {
    if (functionalMemoryWrite(pkt)) {
        return 1;
    } else {
        return 0;
    }
```

然后实现目录的输出与输入端口（port），分别使用 `out_port` 与 `in_port`。与 L1 不同，此处的 `trigger` 不接收 TBE 或缓存（cache）条目，目录动作通过地址查找目录条目。

```cpp
out_port(forward_out, RequestMsg, forwardToCache);
out_port(response_out, ResponseMsg, responseToCache);

in_port(memQueue_in, MemoryMsg, responseFromMemory) {
    if (memQueue_in.isReady(clockEdge())) {
        peek(memQueue_in, MemoryMsg) {
            if (in_msg.Type == MemoryRequestType:MEMORY_READ) {
                trigger(Event:MemData, in_msg.addr);
            } else if (in_msg.Type == MemoryRequestType:MEMORY_WB) {
                trigger(Event:MemAck, in_msg.addr);
            } else {
                error("Invalid message");
            }
        }
    }
}

in_port(response_in, ResponseMsg, responseFromCache) {
    if (response_in.isReady(clockEdge())) {
        peek(response_in, ResponseMsg) {
            if (in_msg.Type == CoherenceResponseType:Data) {
                trigger(Event:Data, in_msg.addr);
            } else {
                error("Unexpected message type.");
            }
        }
    }
}

in_port(request_in, RequestMsg, requestFromCache) {
    if (request_in.isReady(clockEdge())) {
        peek(request_in, RequestMsg) {
            Entry e := getDirectoryEntry(in_msg.addr);
            if (in_msg.Type == CoherenceRequestType:GetS) {

                trigger(Event:GetS, in_msg.addr);
            } else if (in_msg.Type == CoherenceRequestType:GetM) {
                trigger(Event:GetM, in_msg.addr);
            } else if (in_msg.Type == CoherenceRequestType:PutS) {
                assert(is_valid(e));
                // If there is only a single sharer (i.e., the requestor)
                if (e.Sharers.count() == 1) {
                    assert(e.Sharers.isElement(in_msg.Requestor));
                    trigger(Event:PutSLast, in_msg.addr);
                } else {
                    trigger(Event:PutSNotLast, in_msg.addr);
                }
            } else if (in_msg.Type == CoherenceRequestType:PutM) {
                assert(is_valid(e));
                if (e.Owner.isElement(in_msg.Requestor)) {
                    trigger(Event:PutMOwner, in_msg.addr);
                } else {
                    trigger(Event:PutMNonOwner, in_msg.addr);
                }
            } else {
                error("Unexpected message type.");
            }
        }
    }
}
```

接下来定义动作，首先是向内存发送读写请求。使用刚才定义的特殊端口（port）`memQueue_out`，其中的消息会被转换成普通 gem5 `PacketPtr`，再通过配置中指定的内存端口（port）发送。[配置章节]({{ site.baseurl }}/documentation/learning_gem5/part3/configuration/)会说明连接方法。数据可能来自请求或响应这两个不同的消息缓冲区，因此需要分别定义写入内存的动作。

```cpp
action(sendMemRead, "r", desc="Send a memory read request") {
    peek(request_in, RequestMsg) {
        enqueue(memQueue_out, MemoryMsg, toMemLatency) {
            out_msg.addr := address;
            out_msg.Type := MemoryRequestType:MEMORY_READ;
            out_msg.Sender := in_msg.Requestor;
            out_msg.MessageSize := MessageSizeType:Request_Control;
            out_msg.Len := 0;
        }
    }
}

action(sendDataToMem, "w", desc="Write data to memory") {
    peek(request_in, RequestMsg) {
        DPRINTF(RubySlicc, "Writing memory for %#x\n", address);
        DPRINTF(RubySlicc, "Writing %s\n", in_msg.DataBlk);
        enqueue(memQueue_out, MemoryMsg, toMemLatency) {
            out_msg.addr := address;
            out_msg.Type := MemoryRequestType:MEMORY_WB;
            out_msg.Sender := in_msg.Requestor;
            out_msg.MessageSize := MessageSizeType:Writeback_Data;
            out_msg.DataBlk := in_msg.DataBlk;
            out_msg.Len := 0;
        }
    }
}

action(sendRespDataToMem, "rw", desc="Write data to memory from resp") {
    peek(response_in, ResponseMsg) {
        DPRINTF(RubySlicc, "Writing memory for %#x\n", address);
        DPRINTF(RubySlicc, "Writing %s\n", in_msg.DataBlk);
        enqueue(memQueue_out, MemoryMsg, toMemLatency) {
            out_msg.addr := address;
            out_msg.Type := MemoryRequestType:MEMORY_WB;
            out_msg.Sender := in_msg.Sender;
            out_msg.MessageSize := MessageSizeType:Writeback_Data;
            out_msg.DataBlk := in_msg.DataBlk;
            out_msg.Len := 0;
        }
}
```

这里还展示了另一种 SLICC 调试手段 `DPRINTF`。其用法类似 gem5 的 `DPRINTF`，但本例的 SLICC 接口使用 `RubySlicc` 调试标志。

下面定义更新共享者集合与拥有者的动作。

```cpp
action(addReqToSharers, "aS", desc="Add requestor to sharer list") {
    peek(request_in, RequestMsg) {
        getDirectoryEntry(address).Sharers.add(in_msg.Requestor);
    }
}

action(setOwner, "sO", desc="Set the owner") {
    peek(request_in, RequestMsg) {
        getDirectoryEntry(address).Owner.add(in_msg.Requestor);
    }
}

action(addOwnerToSharers, "oS", desc="Add the owner to sharers") {
    Entry e := getDirectoryEntry(address);
    assert(e.Owner.count() == 1);
    e.Sharers.addNetDest(e.Owner);
}

action(removeReqFromSharers, "rS", desc="Remove requestor from sharers") {
    peek(request_in, RequestMsg) {
        getDirectoryEntry(address).Sharers.remove(in_msg.Requestor);
    }
}

action(clearSharers, "cS", desc="Clear the sharer list") {
    getDirectoryEntry(address).Sharers.clear();
}

action(clearOwner, "cO", desc="Clear the owner") {
    getDirectoryEntry(address).Owner.clear();
}
```

再定义发送失效消息，以及将目录无法独立完成的请求转发到相应缓存（cache）的动作。

```cpp
action(sendInvToSharers, "i", desc="Send invalidate to all sharers") {
    peek(request_in, RequestMsg) {
        enqueue(forward_out, RequestMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceRequestType:Inv;
            out_msg.Requestor := in_msg.Requestor;
            out_msg.Destination := getDirectoryEntry(address).Sharers;
            out_msg.MessageSize := MessageSizeType:Control;
        }
    }
}

action(sendFwdGetS, "fS", desc="Send forward getS to owner") {
    assert(getDirectoryEntry(address).Owner.count() == 1);
    peek(request_in, RequestMsg) {
        enqueue(forward_out, RequestMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceRequestType:GetS;
            out_msg.Requestor := in_msg.Requestor;
            out_msg.Destination := getDirectoryEntry(address).Owner;
            out_msg.MessageSize := MessageSizeType:Control;
        }
    }
}

action(sendFwdGetM, "fM", desc="Send forward getM to owner") {
    assert(getDirectoryEntry(address).Owner.count() == 1);
    peek(request_in, RequestMsg) {
        enqueue(forward_out, RequestMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceRequestType:GetM;
            out_msg.Requestor := in_msg.Requestor;
            out_msg.Destination := getDirectoryEntry(address).Owner;
            out_msg.MessageSize := MessageSizeType:Control;
        }
    }
}
```

目录返回数据时，从特殊缓冲区 `responseFromMemory` 读取内存响应。`MemoryMsg` 定义于 `src/mem/ruby/protocol/RubySlicc_MemControl.sm`。

> **译注**：原文给出的该路径遗漏了 `ruby` 目录。

```cpp
action(sendDataToReq, "d", desc="Send data from memory to requestor. May need to send sharer number, too") {
    peek(memQueue_in, MemoryMsg) {
        enqueue(response_out, ResponseMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceResponseType:Data;
            out_msg.Sender := machineID;
            out_msg.Destination.add(in_msg.OriginalRequestorMachId);
            out_msg.DataBlk := in_msg.DataBlk;
            out_msg.MessageSize := MessageSizeType:Data;
            Entry e := getDirectoryEntry(address);
            // Only need to include acks if we are the owner.
            if (e.Owner.isElement(in_msg.OriginalRequestorMachId)) {
                out_msg.Acks := e.Sharers.count();
            } else {
                out_msg.Acks := 0;
            }
            assert(out_msg.Acks >= 0);
        }
    }
}

action(sendPutAck, "a", desc="Send the put ack") {
    peek(request_in, RequestMsg) {
        enqueue(forward_out, RequestMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceRequestType:PutAck;
            out_msg.Requestor := machineID;
            out_msg.Destination.add(in_msg.Requestor);
            out_msg.MessageSize := MessageSizeType:Control;
        }
    }
}
```

随后是队列管理与停顿动作。

```cpp
action(popResponseQueue, "pR", desc="Pop the response queue") {
    response_in.dequeue(clockEdge());
}

action(popRequestQueue, "pQ", desc="Pop the request queue") {
    request_in.dequeue(clockEdge());
}

action(popMemQueue, "pM", desc="Pop the memory queue") {
    memQueue_in.dequeue(clockEdge());
}

action(stall, "z", desc="Stall the incoming request") {
    // Do nothing.
}
```

最后定义转换。大部分直接来自表 8.2，另外增加的转换用于处理内存响应尚未到达的情况。

```cpp
transition({I, S}, GetS, S_m) {
    sendMemRead;
    addReqToSharers;
    popRequestQueue;
}

transition(I, {PutSNotLast, PutSLast, PutMNonOwner}) {
    sendPutAck;
    popRequestQueue;
}

transition(S_m, MemData, S) {
    sendDataToReq;
    popMemQueue;
}

transition(I, GetM, M_m) {
    sendMemRead;
    setOwner;
    popRequestQueue;
}

transition(M_m, MemData, M) {
    sendDataToReq;
    clearSharers; // NOTE: This isn't *required* in some cases.
    popMemQueue;
}

transition(S, GetM, M_m) {
    sendMemRead;
    removeReqFromSharers;
    sendInvToSharers;
    setOwner;
    popRequestQueue;
}

transition({S, S_D, SS_m, S_m}, {PutSNotLast, PutMNonOwner}) {
    removeReqFromSharers;
    sendPutAck;
    popRequestQueue;
}

transition(S, PutSLast, I) {
    removeReqFromSharers;
    sendPutAck;
    popRequestQueue;
}

transition(M, GetS, S_D) {
    sendFwdGetS;
    addReqToSharers;
    addOwnerToSharers;
    clearOwner;
    popRequestQueue;
}

transition(M, GetM) {
    sendFwdGetM;
    clearOwner;
    setOwner;
    popRequestQueue;
}

transition({M, M_m, MI_m}, {PutSNotLast, PutSLast, PutMNonOwner}) {
    sendPutAck;
    popRequestQueue;
}

transition(M, PutMOwner, MI_m) {
    sendDataToMem;
    clearOwner;
    sendPutAck;
    popRequestQueue;
}

transition(MI_m, MemAck, I) {
    popMemQueue;
}

transition(S_D, {GetS, GetM}) {
    stall;
}

transition(S_D, PutSLast) {
    removeReqFromSharers;
    sendPutAck;
    popRequestQueue;
}

transition(S_D, Data, SS_m) {
    sendRespDataToMem;
    popResponseQueue;
}

transition(SS_m, MemAck, S) {
    popMemQueue;
}

// If we get another request for a block that's waiting on memory,
// stall that request.
transition({MI_m, SS_m, S_m, M_m}, {GetS, GetM}) {
    stall;
}
```

可以[查看完整的 MSI-dir.sm](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/MSI-dir.sm)。

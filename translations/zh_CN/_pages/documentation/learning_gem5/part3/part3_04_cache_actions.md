---
layout: documentation
title: "动作代码块"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/cache-actions/
author: Jason Lowe-Power
---

## 动作代码块

状态机（state machine）的下一部分是动作。它们由[转换代码块]({{ site.baseurl }}/documentation/learning_gem5/part3/cache-transitions/)调用，在状态转换过程中执行。每个动作应保持简短，只完成一项工作，例如“向目录发送消息”或“弹出队首消息”。

先实现向目录发送 GetS 的动作。如果要读取的数据在本地既不是 Modified，也不是 Shared 状态，就需要发送 GetS。动作内自动提供三个变量：`address`、`cache_entry` 和 `tbe`，分别对应传给 `trigger` 的地址、条目和 TBE，类似 `peek` 中自动提供的 `in_msg`。

```cpp
action(sendGetS, 'gS', desc="Send GetS to the directory") {
    enqueue(request_out, RequestMsg, 1) {
        out_msg.addr := address;
        out_msg.Type := CoherenceRequestType:GetS;
        out_msg.Destination.add(mapAddressToMachine(address,
                                MachineType:Directory));
        // See mem/protocol/RubySlicc_Exports.sm for possible sizes.
        out_msg.MessageSize := MessageSizeType:Control;
        // Set that the requestor is this machine so we get the response.
        out_msg.Requestor := machineID;
    }
}
```

动作声明包含简写和描述，它们用于生成 HTML 表格。简写显示在转换单元格中，应尽量短。SLICC 提供特殊标记来表示粗体、上标和空格，以便用简短符号表达动作；其中 `^` 表示上标，`_` 用于空格。点击表格中的动作时会显示完整描述，因此描述可以更长，用来解释具体行为。

> **译注**：原文的粗体标记在页面中显示为一对空引号。SLICC 的 HTML 格式化实现使用反斜杠（`\`）将后一个字符加粗并放大；`^` 切换上标格式，`_` 转为空格。

该动作通过前面声明的 `request_out` 发送消息。`enqueue` 与 `peek` 一样带有代码块，块内自动提供 `out_msg`，用于填写新消息。

`enqueue` 接受消息缓冲区、消息类型和延迟三个参数（parameter）。这里以及本控制器其他位置使用 1 个周期，用来建模缓存（cache）访问延迟，此处对应未命中路径。稍后会看到命中路径也采用类似方式指定延迟。

在 `enqueue` 内填充消息字段。地址取自隐式变量 `address`，消息类型设为 GetS。目的地通过 `mapAddressToMachine` 查找：传入地址与目标机器类型，获得负责该地址的 `MachineID`。`Destination` 是 `NetDest` 位图，因此使用 `Destination.add` 加入目标。

最后指定消息大小，并将本控制器的 `machineID` 设为请求方。这样目录既可以直接响应，也可以转发请求，让另一个缓存（cache）向本控制器返回数据。

> **译注**：原文此处的 `mem/protocol/RubySlicc_Exports.sm` 路径省略了 `ruby`；完整源码路径为 `src/mem/ruby/protocol/RubySlicc_Exports.sm`。

其他 Get 和 Put 请求也可以用相同方式实现。Get 用于请求数据或访问权限；Put 用于降低权限或驱逐本地副本。

```cpp
action(sendGetM, "gM", desc="Send GetM to the directory") {
    enqueue(request_out, RequestMsg, 1) {
        out_msg.addr := address;
        out_msg.Type := CoherenceRequestType:GetM;
        out_msg.Destination.add(mapAddressToMachine(address,
                                MachineType:Directory));
        out_msg.MessageSize := MessageSizeType:Control;
        out_msg.Requestor := machineID;
    }
}

action(sendPutS, "pS", desc="Send PutS to the directory") {
    enqueue(request_out, RequestMsg, 1) {
        out_msg.addr := address;
        out_msg.Type := CoherenceRequestType:PutS;
        out_msg.Destination.add(mapAddressToMachine(address,
                                MachineType:Directory));
        out_msg.MessageSize := MessageSizeType:Control;
        out_msg.Requestor := machineID;
    }
}

action(sendPutM, "pM", desc="Send putM+data to the directory") {
    enqueue(request_out, RequestMsg, 1) {
        out_msg.addr := address;
        out_msg.Type := CoherenceRequestType:PutM;
        out_msg.Destination.add(mapAddressToMachine(address,
                                MachineType:Directory));
        out_msg.DataBlk := cache_entry.DataBlk;
        out_msg.MessageSize := MessageSizeType:Data;
        out_msg.Requestor := machineID;
    }
}
```

接下来实现向其他缓存（cache）发送数据的动作。当目录转发另一个请求方的访问时，需要 `peek` 请求队列，取得原请求方信息。这里与 `in_port` 中的 `peek` 写法相同。在 `peek` 内嵌套 `enqueue`，即可同时使用 `in_msg` 和 `out_msg`，确定数据应发给谁；数据本身则从 `cache_entry` 取得。

```cpp
action(sendCacheDataToReq, "cdR", desc="Send cache data to requestor") {
    assert(is_valid(cache_entry));
    peek(forward_in, RequestMsg) {
        enqueue(response_out, ResponseMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceResponseType:Data;
            out_msg.Destination.add(in_msg.Requestor);
            out_msg.DataBlk := cache_entry.DataBlk;
            out_msg.MessageSize := MessageSizeType:Data;
            out_msg.Sender := machineID;
        }
    }
}
```

然后定义向目录发送数据，以及在失效后向原请求方返回确认的动作。

```cpp
action(sendCacheDataToDir, "cdD", desc="Send the cache data to the dir") {
    enqueue(response_out, ResponseMsg, 1) {
        out_msg.addr := address;
        out_msg.Type := CoherenceResponseType:Data;
        out_msg.Destination.add(mapAddressToMachine(address,
                                MachineType:Directory));
        out_msg.DataBlk := cache_entry.DataBlk;
        out_msg.MessageSize := MessageSizeType:Data;
        out_msg.Sender := machineID;
    }
}

action(sendInvAcktoReq, "iaR", desc="Send inv-ack to requestor") {
    peek(forward_in, RequestMsg) {
        enqueue(response_out, ResponseMsg, 1) {
            out_msg.addr := address;
            out_msg.Type := CoherenceResponseType:InvAck;
            out_msg.Destination.add(in_msg.Requestor);
            out_msg.DataBlk := cache_entry.DataBlk;
            out_msg.MessageSize := MessageSizeType:Control;
            out_msg.Sender := machineID;
        }
    }
}
```

收到其他缓存（cache）的失效确认后，需要减少待收确认数。该动作要求 TBE 有效，并直接修改隐式变量 `tbe`。

这里还引入调试辅助函数 `APPEND_TRANSITION_COMMENT`。它接受字符串或可以转换为字符串的值，例如整数，将其追加到协议（protocol）跟踪（trace）输出中。[调试章节]({{ site.baseurl }}/documentation/learning_gem5/part3/MSIdebugging/)会详细介绍。执行此动作的每一行都会显示剩余确认数，便于观察这部分块状态。

```cpp
action(decrAcks, "da", desc="Decrement the number of acks") {
    assert(is_valid(tbe));
    tbe.AcksOutstanding := tbe.AcksOutstanding - 1;
    APPEND_TRANSITION_COMMENT("Acks: ");
    APPEND_TRANSITION_COMMENT(tbe.AcksOutstanding);
}
```

还需要在收到目录响应时，将其中的确认数量计入 TBE。使用 `peek` 读取响应字段，并更新有效的 TBE。

```cpp
action(storeAcks, "sa", desc="Store the needed acks to the TBE") {
    assert(is_valid(tbe));
    peek(response_in, ResponseMsg) {
        tbe.AcksOutstanding := in_msg.Acks + tbe.AcksOutstanding;
    }
    assert(tbe.AcksOutstanding > 0);
}
```

下一组动作向 CPU 报告命中或未命中请求的完成。它们通知 Ruby 与 gem5 之间的接口 `sequencer`：数据已经可用。存储请求则把数据块交给 sequencer，由它原地更新数据。

```cpp
action(loadHit, "Lh", desc="Load hit") {
    assert(is_valid(cache_entry));
    cacheMemory.setMRU(cache_entry);
    sequencer.readCallback(address, cache_entry.DataBlk, false);
}

action(externalLoadHit, "xLh", desc="External load hit (was a miss)") {
    assert(is_valid(cache_entry));
    peek(response_in, ResponseMsg) {
        cacheMemory.setMRU(cache_entry);
        // Forward the type of machine that responded to this request
        // E.g., another cache or the directory. This is used for tracking
        // statistics.
        sequencer.readCallback(address, cache_entry.DataBlk, true,
                               machineIDToMachineType(in_msg.Sender));
    }
}

action(storeHit, "Sh", desc="Store hit") {
    assert(is_valid(cache_entry));
    cacheMemory.setMRU(cache_entry);
    // The same as the read callback above.
    sequencer.writeCallback(address, cache_entry.DataBlk, false);
}

action(externalStoreHit, "xSh", desc="External store hit (was a miss)") {
    assert(is_valid(cache_entry));
    peek(response_in, ResponseMsg) {
        cacheMemory.setMRU(cache_entry);
        sequencer.writeCallback(address, cache_entry.DataBlk, true,
                               // Note: this could be the last ack.
                               machineIDToMachineType(in_msg.Sender));
    }
}

action(forwardEviction, "e", desc="sends eviction notification to CPU") {
    if (send_evictions) {
        sequencer.evictionCallback(address);
    }
}
```

读写相关动作必须调用 `setMRU`，使替换策略（replacement policy）知道哪些块最近被访问。如果遗漏，替换行为就不正确。

加载与存储分别调用 sequencer 的 `readCallback`、`writeCallback`。本例接口接收地址、数据块、原请求是否未命中的布尔值，以及可选的 `MachineType`。最后一项用于统计数据来源，例如区分缓存（cache）之间传输与从内存返回。

此外还定义向 CPU 通知驱逐的动作。gem5 的乱序（out-of-order）模型需要这种通知，以便在推测性加载提交前对应块被驱逐时取消该加载。是否启用由文件开头的参数（parameter）决定。

接下来是分配和释放条目、TBE 的管理动作。分配条目前，`CacheMemory` 必须有空位。其 `allocate` 方法不会替本控制器创建自定义 `Entry` 的宿主机对象，因此要显式传入 `new Entry`。

这些动作还使用 `set_cache_entry`、`unset_cache_entry` 及对应的 TBE 方法，更新由 `trigger` 传入的隐式变量。例如 `allocateCacheBlock` 分配新块后调用 `set_cache_entry`，使同一转换中后续动作的 `cache_entry` 指向有效条目。

另一个动作把条目中的数据复制到 TBE。这样即使先移除了条目，也能在确认本控制器不再负责该数据之前，继续保存它。

```cpp
action(allocateCacheBlock, "a", desc="Allocate a cache block") {
    assert(is_invalid(cache_entry));
    assert(cacheMemory.cacheAvail(address));
    set_cache_entry(cacheMemory.allocate(address, new Entry));
}

action(deallocateCacheBlock, "d", desc="Deallocate a cache block") {
    assert(is_valid(cache_entry));
    cacheMemory.deallocate(address);
    // clear the cache_entry variable (now it's invalid)
    unset_cache_entry();
}

action(writeDataToCache, "wd", desc="Write data to the cache") {
    peek(response_in, ResponseMsg) {
        assert(is_valid(cache_entry));
        cache_entry.DataBlk := in_msg.DataBlk;
    }
}

action(allocateTBE, "aT", desc="Allocate TBE") {
    assert(is_invalid(tbe));
    TBEs.allocate(address);
    // this updates the tbe variable for other actions
    set_tbe(TBEs[address]);
}

action(deallocateTBE, "dT", desc="Deallocate TBE") {
    assert(is_valid(tbe));
    TBEs.deallocate(address);
    // this makes the tbe variable invalid
    unset_tbe();
}

action(copyDataFromCacheToTBE, "Dct", desc="Copy data from cache to TBE") {
    assert(is_valid(cache_entry));
    assert(is_valid(tbe));
    tbe.DataBlk := cache_entry.DataBlk;
}
```

下一组动作管理消息缓冲区，在消息处理完成后弹出队首。`dequeue` 接受出队时间，用于反映缓冲区操作的时序。原文建议通过延迟出队限制同周期处理同一队列的多条消息。

```cpp
action(popMandatoryQueue, "pQ", desc="Pop the mandatory queue") {
    mandatory_in.dequeue(clockEdge());
}

action(popResponseQueue, "pR", desc="Pop the response queue") {
    response_in.dequeue(clockEdge());
}

action(popForwardQueue, "pF", desc="Pop the forward queue") {
    forward_in.dequeue(clockEdge());
}
```

> **译注**：示例实际传入 `clockEdge()`，而非显式的下一周期；`dequeue` 时间与同周期可处理消息数量的关系取决于消息缓冲区实现及控制器的转换上限，不应仅凭这段代码推断每周期只能处理一条消息。

最后是停顿动作。本例采用 `z_stall`，它是 SLICC 中最简单的停顿方式。动作体为空，并使用这一特殊停顿约定，使当前消息暂时不执行转换。原文指出，这类设计比较简单，但队首阻塞可能连带影响其他本可处理的请求，降低性能。

```cpp
action(stall, "z", desc="Stall the incoming request") {
    // z_stall
}
```

另外两种处理暂时无法执行消息的方式可能改善性能，不过本例不使用它们。第一种是 `recycle`，将队首消息移到队尾，使本队列后续消息或其他队列的消息有机会执行。它往往能显著改善性能。

但 `recycle` 与真实缓存一致性（cache coherence）实现并不十分贴近。Ruby 还提供 `stall_and_wait`：把队首请求移到一个独立结构中，按指定地址保存，通常使用请求地址。当阻塞条件解除后，调用 `wakeUpBuffers(address)` 唤醒等待该地址的所有请求，或调用 `wakeUpAllBuffers()` 唤醒全部等待请求。被唤醒的请求重新放回消息缓冲区，等待后续处理。

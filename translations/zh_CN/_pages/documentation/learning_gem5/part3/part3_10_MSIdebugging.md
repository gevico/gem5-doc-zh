---
layout: documentation
title: "调试 SLICC 协议（protocol）"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/MSIdebugging/
author: Jason Lowe-Power
---

## 调试 SLICC 协议（protocol）

本节记录作者调试前面 MSI 实现时的过程。学会调试一致性协议（protocol）并不容易，最好与有 SLICC 经验的人一起实践。这里通过保留排查过程，让读者尽可能看到错误是如何被发现和解决的。

先介绍一般建议，再说明死锁及协议（protocol）跟踪（trace）的读法，最后按实际调试过程展示错误、尝试和最终修复。后半部分包含一些后来被否定的猜想，请注意区分它们与最终结论。

## 通用调试建议

Ruby 有很多调试标志，其中最有用的是 `ProtocolTrace`。它打印所有控制器的每一次转换，使我们能跟踪（trace）整个缓存（cache）系统的执行过程。后面会给出多个例子。

其他常用标志包括：

RubyGenerated
:   输出 Ruby 自动生成代码中的详细调试信息。

RubyPort/RubySequencer
:   查看消息进入和离开 Ruby 时的细节。

RubyNetwork
:   输出网络消息，包括发送方、接收方及数据内容。数据不匹配时尤其有用。

调试的第一步通常是运行 Ruby 随机测试器。它向系统发出半随机请求，检查返回数据是否正确。为了更容易触发交互，它会让一个控制器读取某个块，同时让另一个控制器写入同一块的其他字节，从而充分覆盖瞬态状态与竞争情况。

随机测试器的配置与普通 CPU 略有不同，因此需要另一版 `MyCacheSystem`。可以下载[系统配置]({{ site.baseurl }}/pages/static/scripts/part3/configs/test_caches.py)和[运行脚本]({{ site.baseurl }}/pages/static/scripts/part3/configs/ruby_test.py)。运行脚本与之前基本相同，但创建的是 `RubyRandomTester`，而不是 CPU。

建议先使用一个“CPU”，将加载次数从默认的 100 逐渐增加到宿主机需要几分钟才能完成的规模。如果没有错误，再增加到两个“CPU”，把加载次数降回 100，然后逐渐增加。最后按目标系统规模继续增加“CPU”数。能连续运行 10—15 分钟，会增加一定信心，但并不证明不存在其他缺陷。

随机测试通过后，再运行实际应用。实际应用仍可能暴露更多错误；如果可以，尽量先用随机测试器定位，因为它通常比完整应用更容易调试。

## 理解协议（protocol）跟踪（trace）

即使经过充分测试，一致性协议（protocol）仍可能有缺陷。有些容易修复，有些则很隐蔽。最棘手的情况之一是死锁：应用完全无法继续前进。类似的问题还有活锁，即系统持续执行某种循环，但程序无法取得有效进展。遇到这两类问题，下一步通常是生成协议（protocol）跟踪（trace），查看内存请求的开始与结束、L1 和目录转换等。不过，即使有这些记录，死锁仍可能很难定位。

先看一小段输出，稍后会回到它的上下文。

```protocoltrace
    ...
    4541   0    L1Cache         Replacement   MI_A>MI_A   [0x4ac0, line 0x4ac0]
    4542   0    L1Cache              PutAck   MI_A>I      [0x4ac0, line 0x4ac0]
    4549   0  Directory              MemAck   MI_M>I      [0x4ac0, line 0x4ac0]
    4641   0        Seq               Begin       >       [0x4aec, line 0x4ac0] LD
    4652   0    L1Cache                Load      I>IS_D   [0x4ac0, line 0x4ac0]
    4657   0  Directory                GetS      I>S_M    [0x4ac0, line 0x4ac0]
    4669   0  Directory             MemData    S_M>S      [0x4ac0, line 0x4ac0]
    4674   0        Seq                Done       >       [0x4aec, line 0x4ac0] 33 cycles
    4674   0    L1Cache       DataDirNoAcks   IS_D>S      [0x4ac0, line 0x4ac0]
    5321   0        Seq               Begin       >       [0x4aec, line 0x4ac0] ST
    5322   0    L1Cache               Store      S>SM_AD  [0x4ac0, line 0x4ac0]
    5327   0  Directory                GetM      S>M_M    [0x4ac0, line 0x4ac0]
```

每行通常包含以下字段：

1. **当前 tick**：打印发生的模拟（simulation）时刻。
2. **机器编号**：打印记录的控制器实例编号。例如四个 L1 的编号为 0—3；若每核一个 L1，可以据此对应核心。
3. **组件**：`Seq` 表示 sequencer，`L1Cache` 表示 L1，`Directory` 表示目录。SLICC 控制器采用 `machine()` 声明中 `MachineType:` 后的名称。
4. **动作或事件**：例如 `Begin` 表示 sequencer 收到新请求，`Done` 表示请求完成，`DataDirNoAcks` 表示触发同名事件。
5. **转换**：例如 `MI_A>MI_A`，格式为 `当前状态>下一状态`；没有状态转换信息时显示 `>`。
6. **地址**：例如 `[0x4ac0, line 0x4ac0]`，包含请求物理地址和块地址。除 sequencer 与 mandatory 队列中的原始请求外，这里的地址通常按块对齐。
7. **可选注释**：例如 `LD`、`ST`、`33 cycles`，补充加载、存储或耗时信息。SLICC 中可用[之前介绍的]({{ site.baseurl }}/documentation/learning_gem5/part3/cache-actions/) `APPEND_TRANSITION_COMMENT` 添加注释。

字段间通常自动插入空格，无需手动添加。不过字段内容过长时，间隔可能消失，或导致对齐偏移。

上面的输出覆盖 tick 4541—5327。记录涉及 `L1Cache-0`（核心 0）与 `Directory-0`（第一个目录银行），以及地址 `0x4ac0` 的多次访问和状态转换。例如在 tick 5322，核心向 `0x4ac0` 执行存储，但该块仍处于此前 tick 4641—4674 的加载所获得的 Shared 状态，需要向目录申请所有权。目录在 tick 5327 收到请求。等待期间，L1 从 `S` 转为 `SM_AD`，表示原来为 Shared、正在转向 Modified、等待确认与数据。

若要增加自己的输出，需要使用 `ProtocolTrace` 标志并按这些字段格式打印。例如在 `src/mem/ruby/system/Sequencer.cc` 搜索 `ProtocolTrace`，就能找到 `Seq Begin` 和 `Seq Done` 的来源。

## 调试 MSI 时遇到的错误

以下保留作者的排查思路与修正过程。

```termout
    gem5.opt: build/MSI/mem/ruby/system/Sequencer.cc:423: void Sequencer::readCallback(Addr, DataBlock&, bool, MachineType, Cycles, Cycles, Cycles): Assertion `m_readRequestTable.count(makeLineAddress(address))' failed.
```

这是一个简单笔误：`externalStoreHit` 中误调用了 `readCallback`，应当调用 `writeCallback`。从简单测试开始很有帮助。

```termout
    gem5.opt: build/MSI/mem/ruby/network/MessageBuffer.cc:220: Tick MessageBuffer::dequeue(Tick, bool): Assertion `isReady(current_time)' failed.
```

在 GDB 中运行 gem5，查看 `L1Cache_Controller::doTransitionWorker`。当前事件为 `L1Cache_Event_PutAck`，状态为 `L1Cache_State_MI_A`，调试器中的下一状态变量尚显示 `L1Cache_State_FIRST`。实际对应的转换是收到 PutAck 后从 `MI_A` 转到 `I`，错误发生在 `popResponseQueue`。

问题在于 PutAck 从转发网络到达，而不是响应网络；这里弹错了队列。

```termout
    panic: Invalid transition
    system.caches.controllers0 time: 3594 addr: 3264 event: DataDirAcks state: IS_D
```

起初我认为不应出现这种情况：需要等待的确认数应该为零，或者数据应来自拥有者。我发现目录的 `sendDataToReq` 总会发送共享者数量，于是猜想：处于 `IS_D` 时不必关心其他共享者，干脆让 `DataDirAcks` 也转到 `S`。这将偏离 Sorin 等人的实现。

但这个猜想是*错误的*，书中的设计没有错。实际上，目录已经将请求方加入共享者列表，不能无条件把共享者数量作为它需要等待的确认数。

最终修复是：目录发回数据前，先判断请求方是否为*拥有者*。只有请求写权限的拥有者才需要携带共享者数量作为确认数；否则将响应中的确认计数设为 0。

```termout
    panic: Invalid transition system.caches.controllers0 time: 5332
    addr: 0x4ac0 event: Inv state: SM\_AD
```

先查看何时会触发 `Inv`：只有收到失效消息时。难道本控制器不该出现在共享者列表里，却仍在其中？

可以结合协议（protocol）跟踪（trace）和文本筛选查看过程。

```sh
build/MSI/gem5.opt --debug-flags=ProtocolTrace configs/learning_gem5/part6/ruby_test.py | grep 0x4ac0
```

```termout
    ...
    4541   0    L1Cache         Replacement   MI_A>MI_A   [0x4ac0, line 0x4ac0]
    4542   0    L1Cache              PutAck   MI_A>I      [0x4ac0, line 0x4ac0]
    4549   0  Directory              MemAck   MI_M>I      [0x4ac0, line 0x4ac0]
    4641   0        Seq               Begin       >       [0x4aec, line 0x4ac0] LD
    4652   0    L1Cache                Load      I>IS_D   [0x4ac0, line 0x4ac0]
    4657   0  Directory                GetS      I>S_M    [0x4ac0, line 0x4ac0]
    4669   0  Directory             MemData    S_M>S      [0x4ac0, line 0x4ac0]
    4674   0        Seq                Done       >       [0x4aec, line 0x4ac0] 33 cycles
    4674   0    L1Cache       DataDirNoAcks   IS_D>S      [0x4ac0, line 0x4ac0]
    5321   0        Seq               Begin       >       [0x4aec, line 0x4ac0] ST
    5322   0    L1Cache               Store      S>SM_AD  [0x4ac0, line 0x4ac0]
    5327   0  Directory                GetM      S>M_M    [0x4ac0, line 0x4ac0]
```

我怀疑共享者列表里有不该保留的成员，因此在 `clearOwner` 和 `setOwner` 中加入防御性断言。

```cpp
action(setOwner, "sO", desc="Set the owner") {
    assert(getDirectoryEntry(address).Sharers.count() == 0);
    peek(request_in, RequestMsg) {
        getDirectoryEntry(address).Owner.add(in_msg.Requestor);
    }
}

action(clearOwner, "cO", desc="Clear the owner") {
    assert(getDirectoryEntry(address).Sharers.count() == 0);
    getDirectoryEntry(address).Owner.clear();
}
```

然后得到：

```termout
    panic: Runtime Error at MSI-dir.sm:301: assert failure.
```

失败发生在 `setOwner`。但此时保留共享者其实是合理的，因为稍后还要统计数量并发给请求方。去掉这个断言后，原问题仍未解决。

目录什么时候发送失效消息？是在 `S` 转向等待内存数据的 Modified 瞬态时。因此需要把请求方自己从失效消息的目的地中移除。当时我还以为应继续保留它在共享者列表中，因为发送确认数时会减一。

后来用多个 CPU 测试才发现，上面两个断言都不正确：收到 GetS，从 `M` 转为 `S_D` 时，会先设置共享者，再清除拥有者。

继续看下一个问题。

```termout
    panic: Deadlock detected: current_time: 56091 last_progress_time: 6090 difference:  50001 processor: 0
```

死锁通常最难调试。真正的原因往往发生在很早之前，需要向前追查许多周期。

查看输出末尾，发现一个地址一直在尝试替换，就从这里开始。输出可能非常大，必要时应保存到文件。

```protocoltrace
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
    56091   0    L1Cache         Replacement   SM_A>SM_A   [0x5ac0, line 0x5ac0]
```

向前查找，在这次替换卡住之前约 50000 个周期，出现了以下记录：

```protocoltrace
    ...
    5592   0    L1Cache               Store      S>SM_AD  [0x5ac0, line 0x5ac0]
    5597   0  Directory                GetM      S>M_M    [0x5ac0, line 0x5ac0]
    ...
    5641   0  Directory             MemData    M_M>M      [0x5ac0, line 0x5ac0]
    ...
    5646   0    L1Cache         DataDirAcks  SM_AD>SM_A   [0x5ac0, line 0x5ac0]
```

这里只有一个 CPU，本不该出现 `DataDirAcks`，说明确认数计算仍不正确。回看上一个问题，我错误地认为应把请求方自己留在共享者列表里，却忘记代码已经不再减一。因此，在收到 `S` 向 `M` 的请求、发送失效消息之前，应先把请求方从共享者列表移除。

修改后，单核 Ruby 测试器完成了测试。接下来增加加载次数，再增加核心数。

把加载次数增到 10000 后，又出现死锁。输出末尾反复出现：

```protocoltrace
    144684   0    L1Cache         Replacement   MI_A>MI_A   [0x5bc0, line 0x5bc0]
    ...
    144685   0  Directory                GetM   MI_M>MI_M   [0x54c0, line 0x54c0]
    ...
    144685   0    L1Cache         Replacement   MI_A>MI_A   [0x5bc0, line 0x5bc0]
    ...
    144686   0  Directory                GetM   MI_M>MI_M   [0x54c0, line 0x54c0]
    ...
    144686   0    L1Cache         Replacement   MI_A>MI_A   [0x5bc0, line 0x5bc0]
    ...
    144687   0  Directory                GetM   MI_M>MI_M   [0x54c0, line 0x54c0]
    ...
```

这看起来像循环依赖。最终发现输入端口（port）的顺序十分关键：目录原先按请求、响应、内存的顺序检查队列，请求队列阻塞后，解除阻塞所需的内存响应也无法处理，形成死锁。应改为内存、响应、请求。对于这个例子，内存响应与其他响应之间没有相互依赖，因此作者认为前两者的次序不影响问题的解决。

接着试两个 CPU，首先遇到 `setState` 中第一个断言失败。

```cpp
void setState(Addr addr, State state) {
    if (directory.isPresent(addr)) {
        if (state == State:M) {
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
```

在断言前加入 `DPRINTF`，同时启用跟踪（trace）。这里必须使用生成的 SLICC 文件所支持的 `RubySlicc` 调试标志。

```cpp
DPRINTF(RubySlicc, "Owner %s\n", getDirectoryEntry(addr).Owner);
```

同时启用 `ProtocolTrace` 与 `RubySlicc` 后，输出如下：

```gem5trace
    118   0  Directory             MemData    M_M>M      [0x400, line 0x400]
    118: system.caches.controllers2: MSI-dir.sm:160: Owner [NetDest (16) 1 0  -  -  - 0  -  -  -  -  -  -  -  -  -  -  -  -  - ]
    118   0  Directory                GetM      M>M      [0x400, line 0x400]
    118: system.caches.controllers2: MSI-dir.sm:160: Owner [NetDest (16) 1 1  -  -  - 0  -  -  -  -  -  -  -  -  -  -  -  -  - ]
```

看来在 `M` 状态处理 GetM 时，必须先清除旧拥有者，再加入新拥有者。另一种办法是在 `setOwner` 中直接替换整个拥有者集合，而不是向现有 `NetDest` 追加成员。

随后出现新错误：

```termout
    panic: Runtime Error at MSI-dir.sm:229: Unexpected message type..
```

使用 `RubyNetwork` 查出触发错误的消息。错误前几行有一条目的地为目录的消息。`NetDest` 是按机器类型分段的位图；当前有两个 CPU，前两个 0 对应它们，另一个 1 对应目录。

```gem5trace
    2285: PerfectSwitch-2: Message: [ResponseMsg: addr = [0x8c0, line 0x8c0] Type = InvAck Sender = L1Cache-1 Destination = [NetDest (16) 0 0  -  -  - 1  -  -  -  -  -  -  -  -  -  -  -  -  - ] DataBlk = [ 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0xb1 0xb2 0xb3 0xb4 0xca 0xcb 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 ] MessageSize = Control Acks = 0 ]
```

消息类型是 `InvAck`，但它不应发给目录。原来目录向 L1 发送 Inv 时错误地设置了请求方。这里必须保留原始请求方，使确认返回给真正申请访问的控制器。FwdGetS/M 中已正确处理，但失效消息遗漏了这一点。

下一个错误：

```termout
    panic: Invalid transition
    system.caches.controllers0 time: 2287 addr: 0x8c0 event: LastInvAck state: SM_AD
```

起初怀疑确认计数错误，也可能是目录需要访问内存，所以数据返回慢于其他缓存（cache）的确认。我曾考虑把目录数据也算作一个待收确认，在数据到达时减一，再据新计数触发事件。

打印每次收到 InvAck 时的计数后，确认了实际原因：其他缓存（cache）的确认先到，而目录尚未告知预期确认总数。

因此应允许计数暂时小于零；目录消息到达后，再把预期总数加上。同时调整“最后一个确认”等事件的触发判断，使其正确处理这种先后顺序。

继续测试，出现了更棘手的数据不匹配。与死锁类似，数据可能早在许多周期前就已损坏，下面输出末尾的地址是排查起点。

```termout
    panic: Action/check failure: proc: 0 address: 19688 data: 0x779e6d0
    byte\_number: 0 m\_value+byte\_number: 53 byte: 0 [19688, value: 53,
    status: Check\_Pending, initiating node: 0, store\_count: 4]Time:
    5843
```

可能仍与确认数有关，虽然我认为未必如此。无论如何，把确认信息加入输出都有帮助，可以使用 `APPEND_TRANSITION_COMMENT`：

```cpp
action(decrAcks, "da", desc="Decrement the number of acks") {
    assert(is_valid(tbe));
    tbe.Acks := tbe.Acks - 1;
    APPEND_TRANSITION_COMMENT("Acks: ");
    APPEND_TRANSITION_COMMENT(tbe.Acks);
}
```

```protocoltrace
    5737   1    L1Cache              InvAck  SM_AD>SM_AD  [0x400, line 0x400] Acks: -1
```

数据问题适合使用 `RubyNetwork`，因为它显示网络各处的数据块内容。上述地址从主存读回时全为 0，但它应该已包含有效数据。向前查找，确实能看到非零值。

```protocoltrace
    5382   1    L1Cache                 Inv      S>I      [0x4cc0, line 0x4cc0]
```

```gem5trace
    5383: PerfectSwitch-1: Message: [ResponseMsg: addr = [0x4cc0, line
    0x4cc0] Type = InvAck Sender = L1Cache-1 Destination = [NetDest (16) 1
    0 - - - 0 - - - - - - - - - - - - - ] DataBlk = [ 0x0 0x0 0x0 0x0 0x0
    0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 0x35 0x36 0x37 0x61 0x6d 0x6e 0x6f 0x70 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 ] MessageSize = Control Acks =
    0 ] ... ... ... 5389 0 Directory MemData M\_M\    >M [0x4cc0, line 0x4cc0]
    5390: PerfectSwitch-2: incoming: 0 5390: PerfectSwitch-2: Message:
    [ResponseMsg: addr = [0x4cc0, line 0x4cc0] Type = Data Sender =
    Directory-0 Destination = [NetDest (16) 1 0 - - - 0 - - - - - - - - -
    - - - - ] DataBlk = [ 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0
    0x0 ] MessageSize = Data Acks = 1 ]
```

看来 `M` 转为 `S` 时没有正确更新内存。进一步使用 `MemoryAccess` 查看主存的实际读写，发现 `sendDataToMem` 从 `request_in` 取数据。这对 PutM 正确，对 Data 响应却不正确，因此必须另外定义一个从响应队列取数据并写入内存的动作。

```termout
    panic: Invalid transition
    system.caches.controllers0 time: 44381 addr: 0x7c0 event: Inv state: SM_AD
```

无效转换通常更容易定位，因为报错直接给出地址，可以沿该地址的记录追查。这里并没有更深的逻辑错误，只是漏写了一个转换，补上即可。

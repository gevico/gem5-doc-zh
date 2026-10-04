---
layout: documentation
title: "SLICC"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/slicc/
author: Jason Lowe-Power
---

# SLICC

SLICC 是一种用于编写缓存一致性（cache coherence）
协议的领域特定语言。SLICC 编译器为不同
控制器生成 C++ 代码，这些控制器可以与 Ruby 的其他部分协同工作。该
编译器还会生成协议的 HTML 规范。HTML
生成默认是关闭的。要启用 HTML 输出，在编译时向 scons 传入
选项 "SLICC_HTML=True"。

### 编译器的输入

SLICC 编译器以指定协议中所涉及控制器的文件
作为输入。.slicc 文件指定所考虑的特定协议
所使用的各个文件。例如，如果
尝试用 SLICC 编写 MI 协议，我们可能使用 MI.slicc
作为指定该协议所需全部文件的文件。编写一个协议所需的
文件包括不同控制器的状态机定义，以及
在这些控制器之间传递的网络消息的定义。

这些文件的语法与 C++ 类似。编译器使用
[PLY（Python Lex-Yacc）](http://www.dabeaz.com/ply/)编写，它解析这些
文件以创建抽象语法树（AST）。随后遍历该 AST
来构建一些内部数据结构。最后编译器再次遍历该树，
输出 C++ 代码。该 AST 表示
状态机内部各种结构的层次关系。
下面我们介绍这些结构。

### 协议状态机

本节我们更仔细地看一个包含
状态机规范的文件里有哪些内容。

#### 指定数据成员

每个状态机都用 SLICC 的 **machine** 数据类型描述。每个
machine 都有若干不同类型的成员。缓存和
目录控制器的 machine 分别包含缓存内存和目录内存
数据成员。我们将使用 src/mem/protocol 中的 MI 协议作为
贯穿示例。因此下面是你可能想开始编写状态机的方式

```
machine(MachineType:L1Cache, "MI Example L1 Cache")
 : Sequencer * sequencer,
   CacheMemory * cacheMemory,
   int cache_response_latency = 12,
   int issue_latency = 2 {
     // Add rest of the stuff
   }
```
为了让控制器能够接收来自系统中不同
实体的消息，machine 拥有若干 **Message
Buffer**。它们充当该 machine 的输入和输出端口。下面是
指定输出端口的示例。

```
 MessageBuffer requestFromCache, network="To", virtual_network="2", ordered="true";
 MessageBuffer responseFromCache, network="To", virtual_network="4", ordered="true";
```

注意 Message Buffer 有一些必须正确指定的属性。
另一个示例，这次是指定输入
端口。

```
 MessageBuffer forwardToCache, network="From", virtual_network="3", ordered="true";
 MessageBuffer responseToCache, network="From", virtual_network="4", ordered="true";
```

接下来，machine 中包含对该 machine 可能到达的**状态**
的声明。在缓存一致性协议中，状态可以有
两种类型 —— 稳定状态与瞬态。如果没有任何活动（例如
来自另一个控制器对该块的请求），
该缓存块会永远保持在该状态，我们就说它处于稳定状态。瞬态
用于在稳定状态之间转换，凡是
两个稳定状态之间的转换无法
以原子方式完成时，就需要它们。下面是一个示例，展示如何声明状态。
SLICC 有一个关键字 **state_declaration**，声明
状态时必须使用它。

```
state_declaration(State, desc="Cache states") {
   I, AccessPermission:Invalid, desc="Not Present/Invalid";
   II, AccessPermission:Busy, desc="Not Present/Invalid, issued PUT";
   M, AccessPermission:Read_Write, desc="Modified";
   MI, AccessPermission:Busy, desc="Modified, issued PUT";
   MII, AccessPermission:Busy, desc="Modified, issued PUTX, received nack";
   IS, AccessPermission:Busy, desc="Issued request for LOAD/IFETCH";
   IM, AccessPermission:Busy, desc="Issued request for STORE/ATOMIC";
}
```

在本例中，状态 I 和 M 是仅有的稳定状态。再次
注意必须为状态指定某些属性。

状态机需要指定它能处理的**事件**，从而
从一个状态转换到另一个状态。SLICC 提供了
关键字 **enumeration**，可用于指定可能的
事件集合。下面用一个例子进一步说明这一点 ——

```
enumeration(Event, desc="Cache events") {
   // From processor
   Load,       desc="Load request from processor";
   Ifetch,     desc="Ifetch request from processor";
   Store,      desc="Store request from processor";
   Data,       desc="Data from network";
   Fwd_GETX,        desc="Forward from network";
   Inv,        desc="Invalidate request from dir";
   Replacement,  desc="Replace a block";
   Writeback_Ack,   desc="Ack from the directory for a writeback";
   Writeback_Nack,   desc="Nack from the directory for a writeback";
}
```

在开发协议机时，我们可能需要定义
表示内存系统中不同实体的结构。
SLICC 为此提供了关键字 **structure**。下面是一个
例子

```
structure(Entry, desc="...", interface="AbstractCacheEntry") {
   State CacheState,        desc="cache state";
   bool Dirty,              desc="Is the data dirty (different than memory)?";
   DataBlock DataBlk,       desc="Data in the block";
}
```

使用 SLICC 结构的妙处在于，它会自动
为你生成各个字段的 get 和 set 函数。它还会
写一个不错的 print 函数，并重载 \<\< 运算符。但
如果你更愿意自己完成一切，可以在
结构声明中使用关键字 **external**。这会
阻止 SLICC 为该结构生成 C++ 代码。

```
structure(TBETable, external="yes") {
   TBE lookup(Address);
   void allocate(Address);
   void deallocate(Address);
   bool isPresent(Address);
}
```

事实上，src/mem/protocol/RubySlicc_\*.sm
文件中存在许多预定义类型。你可以使用它们，或者如果需要新类型，
也可以定义新的。你还可以使用关键字 **interface** 来
利用 C++ 中可用的继承特性。注意目前
SLICC 只支持公有继承。

我们也可以像在 C++ 中那样声明和定义函数。有一些
函数是编译器期望控制器总会定义的。它们包括
- getState()
- setState()

#### Machine 的输入

由于协议是状态机，我们需要指定该 machine 在收到输入时
如何从一个状态转换到另一个状态。如前所述，
每个 machine 都有若干输入和输出端口。对于每个输入
端口，使用 **in_port** 关键字来指定该 machine
在该输入端口上收到消息时的行为。下面的例子
展示声明输入
端口的语法。

```
in_port(mandatoryQueue_in, RubyRequest, mandatoryQueue, desc="...") {
  if (mandatoryQueue_in.isReady()) {
    peek(mandatoryQueue_in, RubyRequest, block_on="LineAddress") {
      Entry cache_entry := getCacheEntry(in_msg.LineAddress);
      if (is_invalid(cache_entry) &&
          cacheMemory.cacheAvail(in_msg.LineAddress) == false ) {
        // make room for the block
        trigger(Event:Replacement, cacheMemory.cacheProbe(in_msg.LineAddress),
                getCacheEntry(cacheMemory.cacheProbe(in_msg.LineAddress)),
                TBEs[cacheMemory.cacheProbe(in_msg.LineAddress)]);
      }
      else {
        trigger(mandatory_request_type_to_event(in_msg.Type), in_msg.LineAddress,
                cache_entry, TBEs[in_msg.LineAddress]);
      }
    }
  }
}
```

如你所见，in_port 接受多个参数。第一个
参数 mandatoryQueue_in 是该文件中使用的 in_port
标识符。下一个参数 RubyRequest 是该输入端口所接收消息的
类型。每个输入端口
都使用一个队列来存储消息，队列名就是
第三个参数。

关键字 **peek** 用于从输入端口的队列中取出消息。使用该关键字
会隐式声明一个变量 **in_msg**，其类型与
输入端口声明中指定的类型相同。该变量
指向队列头部的消息。可以用它访问
消息的字段，如上面的代码所示。

一旦对到来的消息完成了分析，就该使用
该消息采取适当的动作并改变
machine 的状态。这通过关键字 **trigger** 完成。
trigger 函数实际上只用在 SLICC 代码中，并不
出现在生成的代码里。相反，该调用会被转换为
对 **doTransition()** 函数的调用，后者出现在
生成的代码中。doTransition() 函数由 SLICC 为每个状态机
自动生成。trigger 的参数数量取决于
machine 本身。一般而言，trigger 的输入参数是所需处理消息
的类型、该消息所针对的地址，以及该地址对应的
缓存和事务缓冲条目。

**trigger** 还会递增一个计数器，在做出转换之前会检查它。
在一个 ruby 周期内，可以执行的转换数量是有限的。
这样做是为了更贴近基于硬件的状态机。**@TODO：
如果没有更多转换可用会怎样？wakeup
会中止吗？**

#### 动作

本节我们将介绍如何定义状态机
可以执行的动作。当状态机收到某条输入消息并据此
进行状态转换时，就会调用这些动作。下面通过一个例子说明
如何使用关键字 **action**。

```
action(a_issueRequest, "a", desc="Issue a request") {
   enqueue(requestNetwork_out, RequestMsg, latency=issue_latency) {
   out_msg.Address := address;
     out_msg.Type := CoherenceRequestType:GETX;
     out_msg.Requestor := machineID;
     out_msg.Destination.add(map_Address_to_Directory(address));
     out_msg.MessageSize := MessageSizeType:Control;
   }
}
```

第一个输入参数是动作的名称，下一个
参数是用于生成文档的缩写，最后一个是该动作的描述（用于 HTML
文档以及 C++ 代码中的注释）。

每个动作都会被转换为同名的 C++ 函数。生成的
C++ 代码会在函数头部隐式包含最多三个输入参数，
同样取决于 machine。这些
参数是执行该动作所针对的内存地址，以及与该地址相关的
缓存和事务缓冲条目。

接下来值得关注的是 **enqueue** 关键字。该
关键字用于把由该动作生成的一条消息排队到输出端口。该关键字
接受三个输入参数，分别是输出端口名、要排队的消息
类型，以及该消息可以被出队的延迟。
注意如果启用了随机化，指定的延迟会被
忽略。使用该关键字会隐式声明一个变量
out_msg，它由后续语句填充。

#### 转换（Transition）

转换函数是从状态集合与事件集合的笛卡尔积
到状态集合的映射。SLICC 提供了
关键字 **transition** 用于指定状态机的转换函数。下面是一个
例子 ——

```
transition(IM, Data, M) {
   u_writeDataToCache;
   sx_store_hit;
   w_deallocateTBE;
   n_popResponseQueue;
}
```

在本例中，初始状态是 *IM*。如果该状态下发生了
*Data* 类型的事件，那么最终状态是 *M*。在做出
转换之前，状态机可以对其维护的结构执行某些动作。在给定的示例中，
*u_writeDataToCache* 是一个动作。所有这些操作都以
原子方式执行，也就是说，在随该转换指定的动作集合完成之前，
不能再发生其他事件。

为便于使用，可以把事件集合和状态集合作为输入
传给 transition。这些集合的笛卡尔积将映射到同一个
最终状态。注意最终状态不能是集合。如果对于
某个特定事件，最终状态与初始状态相同，则可以
省略最终状态。

```
transition({IS, IM, MI, II}, {Load, Ifetch, Store, Replacement}) {
   z_stall;
}
```

### 特殊函数

#### 停顿/回收/等待输入端口

SLICC 及其生成的状态机内部较复杂的特性之一，是
处理因缓存块处于瞬态而无法处理事件的情况。
处理这种情况有几种可能的方式，每种方案都有
不同的取舍。本小节试图解释这些
差异。后续问题请发邮件到 gem5-user 邮件列表。

##### 停顿输入端口

处理无法处理的事件最简单的方式是直接
停顿输入端口。正确的做法是在转换语句中包含
"z_stall" 动作：

```
transition({IS, IM, MI, II}, {Load, Ifetch, Store, Replacement}) {
   z_stall;
}
```

在内部，SLICC 会为该转换返回 ProtocolStall，并且来自相关联输入端口的后续消息
都不会被处理，直到被停顿的消息被处理为止。不过，其他输入端口
仍会被检查是否有就绪消息并并行处理。虽然
这是一个相对简单的方案，但你可能注意到，停顿同一输入端口上
无关的消息会造成过度且不必要的停顿。

需要注意的一点是**不要**像下面这样把转换语句留空：

```
transition({IS, IM, MI, II}, {Load, Ifetch, Store, Replacement}) {
   // stall the input port by simply not popping the message
}
```

这会让 SLICC 为该转换返回成功，并且 SLICC
会继续反复分析同一个输入端口。结果就是
最终死锁。

##### 回收输入端口

性能更好但更不真实的方案是回收
输入端口上被停顿的消息。做法是使用
"zz_recycleMandatoryQueue"
动作：

```
action(zz_recycleMandatoryQueue, "\z", desc="Send the head of the mandatory queue to the back of the queue.") {
   mandatoryQueue_in.recycle();
}
```
```
transition({IS, IM, MI, II}, {Load, Ifetch, Store, Replacement}) {
   zz_recycleMandatoryQueue;
}
```

该动作的结果是：转换返回 Protocol
Stall，并且问题消息被移动到该 FIFO 输入端口的末尾。因此，
同一输入端口上的其他无关消息可以被
处理。该方案的问题在于，被回收的消息可能
每个周期都被分析和重新分析，直到某个地址改变状态。

##### 停顿并等待输入端口

更好但更复杂的方案是对
问题输入消息执行“停顿并等待”。做法是使用
"z_stallAndWaitMandatoryQueue"
动作：

```
action(z_stallAndWaitMandatoryQueue, "\z", desc="recycle L1 request queue") {
   stall_and_wait(mandatoryQueue_in, address);
}
```
```
transition({IS, IM, IS_I, M_I, SM, SINK_WB_ACK}, {Load, Ifetch, Store, L1_Replacement}) {
   z_stallAndWaitMandatoryQueue;
}
```

该动作的结果是转换返回成功，这没问题，因为 stall_and_wait 会把问题消息
从输入端口移到一个与该输入端口关联的侧表。该消息
在被唤醒之前不会再被分析。在此期间，其他
无关消息将被处理。

停顿并等待的复杂之处在于，被停顿的消息必须
由其他消息/转换显式唤醒。特别是
把一个地址转移到基本状态的转换，应唤醒
可能正在等待该地址的被停顿消息：

```
action(kd_wakeUpDependents, "kd", desc="wake-up dependents") {
   wakeUpBuffers(address);
}
```

```
transition(M_I, WB_Ack, I) {
   s_deallocateTBE;
   o_popIncomingResponseQueue;
   kd_wakeUpDependents;
}
```

替换尤其复杂，因为被停顿的地址
与它们实际等待改变的那个地址并不相同。在这些情况下，
所有等待的消息都必须被唤醒：

```
action(ka_wakeUpAllDependents, "ka", desc="wake-up all dependents") {
   wakeUpAllBuffers();
}
```

```
transition(I, L2_Replacement) {
   rr_deallocateL2CacheBlock;
   ka_wakeUpAllDependents;
}
```

### 其他编译器特性

- SLICC 支持以 **if** 和
**else** 形式出现的条件语句。注意 SLICC 不支持 **else if**。

- 每个函数都有返回类型，返回类型也可以为 void。返回值
不能被忽略。

- SLICC 对指针变量的支持有限。支持 is_valid() 和
is_invalid() 操作，分别用于测试给定
指针“不为 NULL”和“为 NULL”。关键字
**OOD**（表示 Out of Domain）扮演了 C++ 中关键字
NULL 的角色。

- SLICC 不支持 **\!**（非运算符）。

- SLICC 支持静态类型转换。为此提供了关键字
**static_cast**。例如，在
下面的代码片段中，一个 AbstractCacheEntry 类型的变量
被转换为 Entry 类型的变量。

```
   Entry L1Dcache_entry := static_cast(Entry, "pointer", L1DcacheMemory[addr]);
```

### SLICC 内部实现

**C++ 到 Slicc 的接口 —— @note：这些文件各自
做什么/定义什么？？？**

- src/mem/protocol/RubySlicc_interaces.sm
    - RubySlicc_Exports.sm
    - RubySlicc_Defines.sm
    - RubySlicc_Profiler.sm
    - RubySlicc_Types.sm
    - RubySlicc_MemControl.sm
    - RubySlicc_ComponentMapping.sm

**变量赋值**

- 使用 `:=` 运算符赋类成员（例如在 RubySlicc_Types.sm 中
定义的成员）：
    - 会在 SLICC
    文件中提到的名称前自动加上 `m_`。

---
layout: documentation
title: "CHI"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/CHI/
author: Tiago Mück
---

# CHI

CHI ruby 协议提供单个缓存控制器，它可以在缓存层次结构的多个层级复用，并被配置为建模多种 MESI 与 MOESI 缓存一致性（cache coherency）协议的实例。该实现基于 [Arm 的 AMBA 5 CHI 规范](https://developer.arm.com/documentation/ihi0050/D/)，为大型 SoC 设计的空间探索提供了一个可扩展的框架。

- [CHI 概述与术语](#chi-overview)
- [协议概述](#protocol-overview)
- [协议实现](#protocol-implementation)
  - [事务分配](#transaction-allocation)
  - [事务初始化](#transaction-initialization)
  - [事务执行](#transaction-execution)
  - [事务终结](#transaction-finalization)
  - [冒险处理](#hazard-handling)
  - [性能建模](#performance-modeling)
  - [缓存块分配与替换建模](#cache-block-allocation-and-replacement-modeling)
- [支持的 CHI 事务](#supported-chi-transactions)
  - [支持的请求](#supported-requests)
  - [支持的探听](#supported-snoops)
  - [回写与逐出](#writeback-and-evictions)
  - [冒险](#hazards)
  - [其他实现说明](#other-implementations-notes)
  - [协议表](#protocol-table)

## CHI 概述与术语 {#chi-overview}

CHI（Coherent Hub Interface）提供组件体系结构与事务级规范，用于建模 MESI 与 MOESI 缓存一致性。如下图所示，CHI 定义了三种主要组件：

[chi_components]: {{ site.baseurl }}/assets/img/ruby_chi/chi_components.png
![CHI 组件][chi_components]

- 请求节点（request node）发起事务并向内存发送请求。请求节点可以是*全一致性请求节点（fully coherent request node，**RNF**）*，这意味着请求节点在本地缓存数据，并应响应探听请求。
- 互连（ICN）是请求节点的响应者。在协议层面，互连是一个封装系统*全一致性归属节点（fully coherent home node，**HNF**）*的组件。
- *从节点（slave node，**SNF**）*，与内存控制器对接。

HNF 是特定地址范围的一致性点（PoC）与串行化点（PoS）。HNF 负责向 RNF 发出所需的任何探听请求，或向 SNF 发出内存访问请求，以完成一个事务。HNF 还可以封装共享的最后一级缓存，并包含用于定向探听的目录。

[CHI 规范](https://developer.arm.com/documentation/ihi0050/D/)还为非一致性请求者（RNI）以及非一致性地址范围（HNI 和 SNI）定义了特定类型的节点，例如属于 IO 组件的内存范围。在 Ruby 中，IO 访问不经过缓存一致性协议，因此只实现了 CHI 的全一致性节点类型。本文档中我们互换使用 RN / RNF、HN / HNF、SN / SNF 这些术语。我们还使用术语**上游（upstream）**与**下游（downstream）**，分别指内存层次结构中前一（即朝向 cpu）和后一（即朝向内存）层级的组件。

## 协议概述 {#protocol-overview}

CHI 协议的实现主要由两个控制器组成：

- `Memory_Controller`（**src/mem/ruby/protocol/chi/CHI-mem.sm**）实现 CHI 从节点。它从归属节点接收内存读或写请求，并与 gem5 的 classic 内存控制器对接。
- `Cache_Controller`（**src/mem/ruby/protocol/chi/CHI-cache.sm**）通用缓存控制器状态机。

为了支持完全灵活的缓存层次结构，`Cache_Controller` 可以被配置为在请求节点和归属节点中建模任意缓存层级（例如 L1D、私有 L2、共享 L3）。此外它还支持其他 Ruby 协议所不具备的多种特性：

- 可为每种请求类型配置缓存块分配与释放策略。
- 对到来的和发出的请求使用统一或独立的事务缓冲。
- MESI 或 MOESI 运行模式。
- 目录以及缓存标签与数据阵列的停顿。
- 可在请求处理流程的多个步骤注入延迟的参数。这让我们能更精细地校准性能。

该实现定义了以下缓存状态：

- `I`：行为无效
- `SC`：行为共享且干净
- `UC`：行为独占/唯一且干净
- `SD`：行为共享且脏
- `UD`：行为独占/唯一且脏
- `UD_T`：带超时的 `UD`。当 store conditional 失败并导致该行从 I 转换为 UD 时，如果失败次数超过某个阈值（由配置定义），我们将改为转换到 `UD_T`。在 `UD_T` 中，该行在给定周期数内（同样由配置定义）不能被请求者逐出；之后该行进入 UD。这是为了避免某些场景下的活锁。

下图概述了控制器被配置为 L1 缓存时的状态转换：

[sm_l1_cache]: {{ site.baseurl }}/assets/img/ruby_chi/sm_l1_cache.svg
![L1 缓存状态机][sm_l1_cache]

转换上标注了来自 cpu 的到来的请求（或内部生成的请求，例如*替换*）以及由此向下游发出的请求。为简单起见，图中省略了不改变状态的请求（例如缓存命中）以及失效型探听（最终状态总是 `I`）。为简单起见，图中也只展示了 MOESI 协议中典型的状态转换。在 CHI 中，最终状态最终由响应者返回的数据类型决定（例如请求者收到 `ReadShared` 的响应时可能得到 `UD` 或 `UC` 数据）。

下面几张图展示了*中间层级*缓存控制器（例如私有 L2、共享 L3、HNF 等）的转换：

[sm_lx_cache]: {{ site.baseurl }}/assets/img/ruby_chi/sm_lx_cache.svg
![中间层级缓存状态机][sm_lx_cache]

[sm_lx_dir]: {{ site.baseurl }}/assets/img/ruby_chi/sm_lx_dir.svg
![中间层级缓存目录状态][sm_lx_dir]

与前一种情况一样，为简单起见省略了缓存命中。除缓存状态之外，还定义了以下目录状态来跟踪存在于上游缓存中的行：

- `RU`：某个上游请求者以 UC 或 UD 持有该行
- `RSC`：一个或多个上游请求者以 SC 持有该行
- `RSD`：某个上游请求者以 SD 持有该行；其他请求者可能以 SC 持有
- `RUSC`：`RSC` + 当前域仍拥有独占访问权
- `RUSD`：`RSD` + 当前域仍拥有独占访问权

当该行同时存在于本地缓存与上游缓存中时，可能出现以下组合状态：

- `UD_RSC`、`SD_RSC`、`UC_RSC`、`SC_RSC`
- `UD_RU`、`UC_RU`
- `UD_RSD`、`SD_RSD`

`RUSC` 与 `RUSD` 状态（上面的图中已省略）用于跟踪那些控制器仍拥有独占访问权限、但其本地缓存中并不存在对应行的行。这在非包含缓存中是可能的：本地块可以被释放而不反向失效上游副本。

当缓存控制器是 HNF（归属节点）时，状态转换基本上与中间层级缓存相同，区别在于：

- 向下游发送 `ReadNoSnp` 以获取数据，因为唯一的下游组件是 SN（从节点）。
- 在缓存与目录都未命中时，如果启用则使用 DMT（直接内存传输）。
- 在缓存未命中但目录命中时，如果启用则使用 DCT（直接缓存传输）。

关于 DCT 与 DMT 事务的更多信息，见 [CHI 规范](https://developer.arm.com/documentation/ihi0050/D/)的第 1.7 节与 2.3.1 节。DMT 和 DCT 是 CHI 的特性，允许请求的数据源把数据直接发送给原请求者。在 DMT 请求中，SN 直接把数据发送给 RN（而不是先发给 HN，再由 HN 转发给 RN）；而在 DCT 中，HN 请求被探听的某个 RN（被探听者）把该行的副本直接发送给原请求者。启用 DCT 时，HN 还可以请求被探听者把数据同时发送给 HN 和原请求者，这样 HN 也能缓存该数据。这取决于配置参数所定义的分配策略。注意分配策略也会改变缓存状态转换。为简单起见，上图展示的是包含式缓存。

以下是影响协议行为的主要缓存控制器配置参数列表（细节和完整参数列表请参考协议 SLICC 规范）

- `downstream_destinations`：定义向下游发送的请求的目的地，用于构建缓存层次结构。关于如何为每个核心设置带私有 L1I、L1D 和 L2 缓存的系统示例，见 `configs/ruby/CHI.py` 中的 `create_system` 函数。
- `is_HN`：当控制器被用作某个地址范围的归属节点和一致性点时设置。对其他任何缓存层级都必须为 false。
- `enable_DMT` 与 `enable_DCT`：当控制器是归属节点时，为到来的读请求启用直接内存传输和直接缓存传输。
- `allow_SD`：允许共享脏（shared dirty）状态。它在 MOESI 与 MESI 运行模式之间切换。
- `alloc_on_readshared`、`alloc_on_readunique` 和 `alloc_on_readonce`：是否为存储用于响应相应读请求的数据而分配缓存块。
- `alloc_on_writeback`：是否为存储从回写请求接收到的数据而分配缓存块。
- `dealloc_on_unique` 和 `dealloc_on_shared`：如果该行在上游缓存中变为唯一或共享，则释放本地缓存块。
- `dealloc_backinv_unique` 和 `dealloc_backinv_shared`：如果本地缓存块因替换而被释放，是否同时失效上游缓存中该行的唯一或共享副本。
- `number_of_TBEs`、`number_of_snoop_TBEs` 和 `number_of_repl_TBEs`：用于到来的请求、到来的探听以及替换的 TBE 表中的条目数。
- `unify_repl_TBEs`：替换与其触发它的请求使用相同的 TBE 槽位。这种情况下 `number_of_repl_TBEs` 被忽略。

以下参数影响缓存控制器性能：

- `read_hit_latency` 和 `read_miss_latency`：读请求在本地缓存中命中或未命中时的流水线延迟。
- `snoop_latency`：到来的探听的流水线延迟。
- `write_fe_latency` 和 `write_be_latency`：处理写请求的前端与后端流水线延迟。前端延迟作用于发送确认响应与下一个要执行的动作之间。后端延迟作用于请求者在收到确认与发送写数据之间。
- `allocation_latency`：TBE 分配与事务初始化之间的延迟。
- `cache`：附加到该控制器的 `CacheMemory`，包含大小、相联度、标签与数据延迟、bank 数量等参数。

[协议实现](#protocol-implementation)一节概述了协议的实现，而[支持的 CHI 事务](#supported-chi-transactions)一节描述了所实现的 AMBA 5 CHI 规范子集。接下来的几节会引用协议源码中的具体文件，并包含协议的 SLICC 片段。与实际的 SLICC 规范相比，有些片段被略微简化。

## 协议实现 {#protocol-implementation}

下图概述了缓存控制器的实现。

[cache_cntrl_arch]: {{ site.baseurl }}/assets/img/ruby_chi/cache_cntrl_arch.png
![缓存控制器架构][cache_cntrl_arch]

在 Ruby 中，缓存控制器通过用 SLICC 语言定义状态机来实现。状态机中的转换由到达输入队列的消息触发。在我们的具体实现中，为每个 CHI 通道分别定义了到来的和发出的消息队列。启动新事务的到来请求与探听消息都经过同一个*请求分配*过程：我们分配一个事务缓冲条目（TBE），并把该请求或探听移入一个内部队列，其中的事务已准备就绪
可以被发起。如果事务缓冲已满，该请求会被拒绝并回送一条重试消息。

从输入 / rdy 队列出队的消息要执行的动作取决于目标缓存行的状态。如果该行在本地被缓存，其数据状态存储在缓存中；
如果该行存在于任何上游缓存中，其目录状态存储在目录条目中。对于存在未完成请求的行，瞬态保存在 TBE 中，并在事务完成时
复制回缓存和/或目录。下图描述了事务生命周期中的各阶段，以及缓存控制器中主要组件（输入/输出端口、TBETable、Cache、Directory 和 SLICC 状态机）之间的交互。各阶段在后续小节中有更详细的描述。

[transaction_phases]: {{ site.baseurl }}/assets/img/ruby_chi/transaction_phases.png
![事务生命周期][transaction_phases]

### 事务分配 {#transaction-allocation}

下面的代码片段展示了 `reqIn` 端口中到来的请求是如何处理的。`reqIn` 端口接收来自 CHI 请求通道的到来消息：

    in_port(reqInPort, CHIRequestMsg, reqIn) {
      if (reqInPort.isReady(clockEdge())) {
        peek(reqInPort, CHIRequestMsg) {
          if (in_msg.allowRetry) {
            trigger(Event:AllocRequest, in_msg.addr, 
                  getCacheEntry(in_msg.addr), getCurrentActiveTBE(in_msg.addr));
          } else {
            trigger(Event:AllocRequestWithCredit, in_msg.addr,
                  getCacheEntry(in_msg.addr), getCurrentActiveTBE(in_msg.addr));
          }
        }
      }
    }

`allowRetry` 字段表示可以重试的消息。不可重试的请求只由先前收到信用（credit）的请求者发送（见 CHI 规范中的 `RetryAck` 与 `PCrdGrant`）。由 `Event:AllocRequest` 或 `Event:AllocRequestWithCredit` 触发的转换执行单个动作：要么在 TBE 表中为该请求预留空间并把它移入 `reqRdy` 队列，要么发送一条 `RetryAck` 消息）：

    action(AllocateTBE_Request) {
      if (storTBEs.areNSlotsAvailable(1)) {
        // reserve a slot for this request
        storTBEs.incrementReserved();
        // Move request to rdy queue
        peek(reqInPort, CHIRequestMsg) {
          enqueue(reqRdyOutPort, CHIRequestMsg, allocation_latency) {
            out_msg := in_msg;
          }
        }
      } else {
        // we don't have resources to track this request; enqueue a retry
        peek(reqInPort, CHIRequestMsg) {
          enqueue(retryTriggerOutPort, RetryTriggerMsg, 0) {
            out_msg.addr := in_msg.addr;
            out_msg.event := Event:SendRetryAck;
            out_msg.retryDest := in_msg.requestor;
            retryQueue.emplace(in_msg.addr,in_msg.requestor);
          }
        }
      }
      reqInPort.dequeue(clockEdge());
    }

注意我们并不直接从该动作创建并发送 `RetryAck` 消息。相反，我们在内部的 `retryTrigger` 队列中创建一个独立的触发事件。这是必要的，以防止资源停顿中止该动作。下面的[性能建模](#performance-modeling)一节会更详细地说明资源停顿。

来自 `Sequencer` 对象的到来请求（当控制器被用作 L1 缓存时通常连接到 CPU）以及探听请求分别通过 `seqIn` 与 `snpIn` 端口到达，处理方式类似，区别在于：

- 它们不支持重试。如果没有可用的 TBE，就会产生资源停顿，我们会在下一个周期再试。
- 探听从单独的 TBETable 分配 TBE，以避免死锁。

### 事务初始化 {#transaction-initialization}

一旦某个请求分配到 TBE 并被移入 `reqRdy` 队列，就会触发一个事件来发起该事务。我们为每种不同的请求类型触发不同的事件：

    in_port(reqRdyPort, CHIRequestMsg, reqRdy) {
      if (reqRdyPort.isReady(clockEdge())) {
        peek(reqRdyPort, CHIRequestMsg) {
          CacheEntry cache_entry := getCacheEntry(in_msg.addr);
          TBE tbe := getCurrentActiveTBE(in_msg.addr);
          trigger(reqToEvent(in_msg.type), in_msg.addr, cache_entry, tbe);
        }
      }
    }

每个请求都需要根据该行的初始状态执行不同的初始化动作。为了说明该过程，我们以针对处于 `SC_RSC` 状态（本地缓存中共享
干净，上游缓存中共享干净）的某个行的 `ReadShared` 请求为例：

    transition(SC_RSC, ReadShared, BUSY_BLKD) {
      Initiate_Request;
      Initiate_ReadShared_Hit;
      Profile_Hit;
      Pop_ReqRdyQueue;
      ProcessNextState;
    }

- `Initiate_Request` 初始化所分配的 TBE。该动作把分配在本地缓存与目录中的任何状态和数据复制到 TBE。
- `Initiate_ReadShared_Hit` 建立为完成这个特定请求所需执行的动作集合（见下文）。
- `Profile_Hit` 更新缓存统计信息（statistics）。
- `Pop_ReqRdyQueue` 从 `reqRdy` 队列中移除请求消息。
- `ProcessNextState` 执行由 `Initiate_ReadShared_Hit` 定义的下一个动作。

`Initiate_ReadShared_Hit` 定义如下：

    action(Initiate_ReadShared_Hit) {
      tbe.actions.push(Event:TagArrayRead);
      tbe.actions.push(Event:ReadHitPipe);
      tbe.actions.push(Event:DataArrayRead);
      tbe.actions.push(Event:SendCompData);
      tbe.actions.push(Event:WaitCompAck);
      tbe.actions.pushNB(Event:TagArrayWrite);
    }

`tbe.actions` 存储为完成一个动作而需要依次触发的事件列表。在这个特定情况下，`TagArrayRead`、`ReadHitPipe` 和 `DataArrayRead` 引入延迟，以建模缓存
控制器流水线延迟以及读取缓存/目录标签阵列和缓存数据阵列（见[性能建模](#performance-modeling)一节）。`SendCompData` 建立并发送 `ReadShared` 请求的数据响应，`WaitCompAck` 把 TBE 设置为期望来自请求者的完成确认。最后，`TagArrayWrite` 引入更新目录状态以跟踪新共享者的延迟。

### 事务执行 {#transaction-execution}

初始化之后，该行会转换到 `transition(SC_RSC, ReadShared, BUSY_BLKD)` 中所示的 `BUSY_BLKD` 状态。`BUSY_BLKD` 是一个瞬态，表示该行现在有一个未完成事务。在该状态下，事务要么由 `rspIn` 与 `datIn` 端口中到来的响应消息驱动，要么由 `tbe.actions` 中定义的触发事件驱动。

`ProcessNextState` 动作负责检查 `tbe.actions`，并在所有转换到 `BUSY_BLKD` 状态的转换末尾把触发事件消息入队到 `actionTriggers`。`ProcessNextState` 首先检查是否有待处理的响应消息。如果没有待处理消息，它就向 `actionTriggers` 入队一条消息，以触发 `tbe.actions` 头部的事件。如果有待处理响应，则不 `ProcessNextState` 做任何事，因为一旦收到所有预期响应，事务就会继续推进。

待处理响应由 TBE 中的 `expected_req_resp` 与 `expected_snp_resp` 字段跟踪。例如，由 `WaitCompAck` 触发的转换所执行的 `ExpectCompAck` 动作定义如下：

    action(ExpectCompAck) {
      tbe.expected_req_resp.addExpectedRespType(CHIResponseType:CompAck);
      tbe.expected_req_resp.addExpectedCount(1);
    }

这会让事务等待，直到收到 `CompAck` 响应。

有些动作可以在事务有待处理响应时执行。这些动作用 `tbe.actions.pushNB`（即 push / non-blocking，非阻塞推入）入队。在上面的示例中，`tbe.actions.pushNB(Event:TagArrayWrite)` 建模的是在事务等待 `CompAck` 响应期间执行标签写。

### 事务终结 {#transaction-finalization}

当事务没有更多待处理响应且 `tbe.actions` 为空时，事务结束。`ProcessNextState` 检查该条件并向 `actionTriggers` 入队一条“终结器”触发消息。处理该事件时，当前缓存行状态以及共享/所有权信息决定该行的最终稳定状态。如有必要，会在缓存与目录中更新数据和状态信息，并释放 TBE。

### 冒险处理 {#hazard-handling}

每个控制器对每个缓存行只允许一个活跃事务。如果在该缓存行处于瞬态时到来新的请求或探听，就会产生 CHI 标准中所定义的冒险（hazard）。我们按如下方式处理冒险：

**请求冒险：** 如前所述会分配一个 TBE，但新事务的初始化会延迟到当前事务完成、该行回到稳定状态之后。做法是
把请求消息从 `reqRdy` 移到一个单独的*停顿缓冲*。当前事务完成时，所有被停顿的消息都会被加回 `reqRdy`，并按它们原本的到达顺序处理。

**探听冒险：** CHI 规范不允许探听被现有请求停顿。如果某个事务正在等待向下游发出的请求的响应（例如我们发出了 `ReadShared` 并正在等待
数据响应），我们必须接受并处理该探听。只有当该请求已被响应者接受、并保证会完成时（例如一个 `ReadShared` 数据尚未到达，但已通过 `RespSepData` 响应确认），探听才可以被停顿。为了区分这些情况，我们使用 `BUSY_INTR` 瞬态。

`BUSY_INTR` 表示该事务可以被探听中断。当针对处于该状态的行的探听到达时，会如前所述分配一个探听 TBE，并根据当前活跃的 TBE 初始化其状态。该探听 TBE 随后成为当前活跃的 TBE。探听引起的任何缓存状态以及共享/所有权变化都会在释放该探听之前复制回原 TBE。当针对处于 `BUSY_BLKD` 状态的行的探听到达时，我们会停顿该探听，直到当前事务结束或转换到 `BUSY_INTR`。

### 性能建模 {#performance-modeling}

如前所述，缓存行状态在事务初始化时立即可知，缓存行可以在没有任何延迟的情况下读写。这使实现协议的功能
部分更容易。为了建模时序，我们使用显式动作来给事务引入延迟。例如，在 `ReadShared` 代码片段中：

    action(Initiate_ReadShared_Hit) {
      tbe.actions.push(Event:TagArrayRead);
      tbe.actions.push(Event:ReadHitPipe);
      tbe.actions.push(Event:DataArrayRead);
      tbe.actions.push(Event:SendCompData);
      tbe.actions.push(Event:WaitCompAck);
      tbe.actions.pushNB(Event:TagArrayWrite);
    }

`TagArrayRead`、`ReadHitPipe`、`DataArrayRead` 和 `TagArrayWrite` 没有任何功能意义。它们的存在是为了引入真实缓存控制器流水线中会有的延迟，在这里即：标签读延迟、命中流水线延迟、数据阵列读延迟和标签更新延迟。这些动作引入的延迟由配置参数定义。

除显式添加的延迟之外，SLICC 还有*资源停顿*的概念，用于建模资源竞争。对于在一次转换中执行的一组动作，SLICC 编译器会自动生成
代码来检查这些动作所需的全部资源是否可用。如果任何资源不可用，就会产生资源停顿，该转换不会被执行。导致资源停顿的消息会留在输入队列中，协议会在下一个周期再次尝试触发该转换。

SLICC 编译器以不同方式检测资源：

1. 隐式检测。输出端口就是这种情况。如果某个动作入队了新消息，输出端口的可用性会被自动检查。
2. 向动作添加 `check_allocate` 语句。
3. 用资源类型对该转换做注解。

我们用 (2) 来检查 TBE 的可用性。见下面的片段：

    action(AllocateTBE_Snoop) {
      // No retry for snoop requests; just create resource stall
      check_allocate(storSnpTBEs);
      ...
    }

这通知 SLICC 编译器：在执行任何包含 `AllocateTBE_Snoop` 动作的转换之前，检查 `storSnpTBEs` 结构是否有可用的 TBE 槽位。

下面的片段是 (3) 的示例：

    transition({BUSY_INTR,BUSY_BLKD}, DataArrayWrite) {DataArrayWrite} {
      ...
    }

`DataArrayWrite` 注解通知 SLICC 编译器检查 `DataArrayWrite` 资源类型是否可用。这些注解中使用的*资源请求类型*必须由协议显式定义，以及如何检查它们。在我们的协议中，我们定义了以下类型来检查缓存标签与数据阵列中 bank 的可用性：

    enumeration(RequestType) {
      TagArrayRead;
      TagArrayWrite;
      DataArrayRead;
      DataArrayWrite;
    }

    void recordRequestType(RequestType request_type, Addr addr) {
      if (request_type == RequestType:DataArrayRead) {
        cache.recordRequestType(CacheRequestType:DataArrayRead, addr);
      }
      ...
    }

    bool checkResourceAvailable(RequestType request_type, Addr addr) {
      if (request_type == RequestType:DataArrayRead) {
        return cache.checkResourceAvailable(CacheResourceType:DataArray, addr);
      }
      ...
    }

当我们在事务上使用注解时，SLICC 编译器要求实现 `checkResourceAvailable` 与 `recordRequestType`。

### 缓存块分配与替换建模 {#cache-block-allocation-and-replacement-modeling}

考虑下面针对 ReadShared 未命中的事务初始化代码：

    action(Initiate_ReadShared_Miss) {
      tbe.actions.push(Event:ReadMissPipe);
      tbe.actions.push(Event:TagArrayRead);
      tbe.actions.push(Event:SendReadShared);
      tbe.actions.push(Event:SendCompData);
      tbe.actions.push(Event:WaitCompAck);
      tbe.actions.push(Event:CheckCacheFill);
      tbe.actions.push(Event:TagArrayWrite);
    }

所有因探听或向下游发出的请求而修改某个缓存行或收到该缓存行数据的事务，都使用 `CheckCacheFill` 动作触发事件。该事件触发一个转换，执行以下动作：

- 检查是否需要把当前缓存行数据存入本地缓存。
- 检查我们是否已为该行分配了缓存块。如果没有，则尝试分配一个块。如果块不可用，则选出一个牺牲块用于替换。
- 建模缓存填充的延迟。

执行替换时，会初始化一个新事务来跟踪向下游发出的任何 WriteBack 或 Evict 请求，和/或用于反向失效的探听（如果缓存控制器被配置为
强制包含性）。取决于配置参数，用于替换的 TBE 要么使用专用 TBETable 中的资源，要么复用触发该替换的 TBE 的资源。两种情况
下，触发替换的事务都不会等待替换过程完成就结束。

注意 `CheckCacheFill` 实际上并不把数据写入缓存块。它只确保在需要时分配了缓存块、触发替换，并建模缓存填充延迟。如前所述，TBE 数据会在事务终结期间按需复制到缓存。

## 支持的 CHI 事务 {#supported-chi-transactions}

所有事务均按 [AMBA5 CHI Issue D 规范](https://developer.arm.com/documentation/ihi0050/D/)所述实现。接下来的几节会更详细地解释公开文档未固定的、与本实现相关的选择。

### 支持的请求 {#supported-requests}

支持以下到来的请求：

- `ReadShared`
- `ReadNotSharedDirty`
- `ReadUnique`
- `CleanUnique`
- `ReadOnce`
- `WriteUniquePtl` 和 `WriteUniqueFull`

收到任何请求时，都会在事务初始化期间评估包含性（clusivity）配置参数，并在为该请求分配的事务缓冲条目中设置 `doCacheFill` 与 `dataToBeInvalid` 标志。`doCacheFill` 表示我们应把该行的任何有效副本保留在本地缓存中；`dataToBeInvalid` 表示我们在完成事务时必须使本地副本失效。

收到 `ReadShared` 或 `ReadUnique` 时，如果数据以所需状态存在于本地缓存（例如 `ReadUnique` 需要 `UC` 或 `UD`），就向请求者发送 `CompData` 响应。响应类型取决于 `dataToBeInvalid` 的值。

- 如果 `dataToBeInvalid==true`
  - 唯一和/或脏状态总会被传播
  - 对于 `ReadNotSharedDirty`，如果本地状态是 `SD` 且该行通过 `WriteCleanFull` 回写，则总是发送 `CompData_SC`
- 否则：
  - 响应 `ReadUnique` 时：传播脏状态，即 `CompData_UD` 或 `CompData_UC`。
  - 响应 `ReadShared` 或 `ReadNotSharedDirty` 时：发送 `CompData_SC`。如果设置了 `fwd_unique_on_readshared` 配置参数，当该行没有其他共享者时，`ReadShared` 会按 `ReadUnique` 处理。

收到 `ReadOnce` 时，如果数据存在于本地缓存，则总是发送 `CompData_I`。`WriteUniquePtl` 的处理见下文。

如果缓存未命中，根据 `doCacheFill` 与 `dataToBeInvalid==false` 的组合情况，以及是否启用 DCT 或 DMT，可能执行多个动作：

- `ReadShared` / `ReadNotSharedDirty`：
  - 如果目录状态是 `RSD` 或 `RU`：
    - 如果禁用 DCT：向所有者发送 `SnpShared`；把该行缓存在本地（如果 `doCacheFill`）并向请求者发送响应。
    - 如果启用 DCT：向所有者发送 `SnpSharedFwd`；如果 `doCacheFill==true`，则设置 `retToSrc` 字段，以便该行可以缓存在本地。
  - 如果目录状态是 `RSC`：
    - 如果禁用 DCT：向其中一个共享者发送 `SnpOnce`；把该行缓存在本地（如果 `doCacheFill`）并向
        请求者发送响应。
    - 如果启用 DCT：向其中一个共享者发送 `SnpSharedFwd`；如果 `doCacheFill==true`，则设置 `retToSrc` 字段，以便该行可以缓存在本地。
  - 否则：发出 `ReadShared` / `ReadNotSharedDirty` 或 `ReadNoSnp`（如果是 HNF）。在 HNF 配置中，如果启用 DMT，则 `ReadNoSnp` 以 DMT 发出。
  - 对于 `ReadNotSharedDirty`，改为发送 `SnpNotSharedDirty` 和 `SnpNotSharedDirtyFwd`。
- `ReadUnique`：
  - 如果目录状态是 `RU,RUSD,RUSC`：
    - 如果禁用 DCT 或包含性为包含式：向所有者发送 `SnpUnique`；把该行缓存在本地（如果 `doCacheFill `）并向请求者发送响应。
    - 如果启用 DCT 且包含性为排他式：向所有者发送 `SnpUniqueFwd`。
  - 如果目录状态是 `RSC`/`RSD`：
    - 发送带 `retToSrc=true` 的 `SnpUnique` 以使共享者失效并获取脏行（在 `RSD` 情况下）
    - 如果不是 HNF：向下游发送 `CleanUnique` 以获得唯一权限。
  - 否则：发出 `ReadUnique` 或 `ReadNoSnp`（如果是 HNF）。在 HNF 配置中，如果启用 DMT，则 `ReadNoSnp` 以 DMT 发出。
  - 对于 `RUSC` 和 `RSC`，如果有多个共享者，只选择一个共享者作为上述探听的目标。其他共享者通过带 `retToSrc=false` 的 `SnpUnique` 失效。
- `ReadOnce`：
  - 如果存在目录条目：
    - 如果禁用 DCT：向其中一个共享者发送 `SnpOnce`；把收到的数据响应发送给请求者。
    - 如果启用 DCT：向其中一个共享者发送 `SnpOnceFwd`。
  - 否则：发出 `ReadOnce` 或 `ReadNoSnp`（如果是 HNF）。在 HNF 配置中，如果启用 DMT，则 `ReadNoSnp` 以 DMT 发出。
- `CleanUnique`：
  - 向除原请求者之外的所有共享者/所有者发送 `SnpCleanInvalid`。
  - 如果不是 HNF：向下游发送 `CleanUnique` 以获得唯一权限。
  - 如果有脏行，且请求者持有干净行，并且 `doCacheFill==false`：用 `WriteCleanFull` 回写该行。
- `WriteUniquePtl`/`WriteUniqueFull`：
  - 如果数据以 UC 或 UD 状态存在于本地缓存：
    - 如果存在任何共享者，发出 `SnpCleanInvalid`。
    - 在本地缓存中执行写。
  - 如果本地没有 UC/UD 数据：
    - 如果是 HNF：
      - 如果存在任何共享者，发出 `SnpCleanInvalid`。
      - 把收到的任何探听响应数据与 WriteUnique 数据合并。
      - 如果拥有完整行且设置了 `doCacheFill`，把该行缓存在本地，否则回写到内存（`WriteNoSnp` 或 `WriteNoSnpPtl`）。
    - 如果不是 HNF：
      - 把 `WriteUniquePtl` 以及收到的任何数据转发给下游缓存。
      - 处理该请求期间，到来的探听会使任何本地缓存的数据失效。

### 支持的探听 {#supported-snoops}

缓存控制器发出并接受以下探听：

- `SnpShared` 和 `SnpSharedFwd`
- `SnpNotSharedDirty` 和 `SnpNotSharedDirtyFwd`
- `SnpUnique` 和 `SnpUniqueFwd`
- `SnpCleanInvalid`
- `SnpOnce` 和 `SnpOnceFwd`

探听响应按规范中定义的该行当前状态生成。数据是否随探听响应返回取决于数据状态以及探听者设置的 `retToSrc` 值。如果设置了 `retToSrc`，探听响应总是包含数据。

- `SnpShared` / `SnpNotSharedDirty`：
  - 如果该行是脏、唯一或 `retToSrc`，被探听者总是返回数据。
  - 如果探听者需要缓存该行，则设置 `retToSrc`。
  - 被探听者的最终状态总是共享干净。
- `SnpUnique`：
  - 如果该行是脏、唯一或 `retToSrc`，被探听者总是返回数据。
  - 如果探听者需要缓存该行，则设置 `retToSrc`。
  - 被探听者的最终状态总是无效。
- `SnpCleanInvalid`：
  - 与 *SnpUnique* 相同，只是如果该行是唯一且干净的，则不返回数据。
- `SnpSharedFwd`：
  - 如果探听者需要缓存该行，则设置 `retToSrc`。
  - 如果该行是脏的，则以脏状态转发
  - 被探听者的最终状态总是共享干净
- `SnpNotSharedDirtyFwd`：
  - 如果探听者需要缓存该行，则设置 `retToSrc`。
  - 如果该行在被探听者处是脏的，则总是返回数据；该行总是以干净状态转发。
  - 被探听者的最终状态总是共享干净。
- `SnpUniqueFwd`：
  - 与 SnpUnique 相同，只是数据从不返回给探听者（如规范所定义）
- `SnpOnce`：
  - 总是以 `retToSrc=true` 生成，被探听者总是返回数据。
  - 在任何状态（无效除外）都可接受。被探听者的最终状态不变。
- `SnpOnceFwd`：
  - 与 SnpOnce 相同，只是数据从不返回给探听者。

如果被探听者在任何状态下有共享者，同一请求会被向上游发送给所有共享者。对于 SnpSharedFwd/SnpNotSharedDirtyFwd 与 SnpUniqueFwd，分别发送 SnpShared/SnpNotSharedFwd 或 SnpUnique。对于收到的 SnpOnce，只有当该行不存在于本地时才会向上游发送 SnpOnce。在本实现中，拥有该行的上游缓存总会有一个目录条目。*探听永远不会发送给不持有该行的缓存*。

### 回写与逐出 {#writeback-and-evictions}

当某个缓存行因容量原因需要被逐出时，控制器会在内部触发一次回写（*当前不支持缓存维护操作*）。关于替换的更多信息见[缓存块分配与替换建模](#cache-block-allocation-and-replacement-modeling)一节。这些内部事件根据控制器的配置参数生成：

- `GlobalEviction`：从当前缓存及所有上游缓存中逐出该行。当设置了 `dealloc_backinv_unique` 或 `dealloc_backinv_shared` 参数时适用。
- `LocalEviction`：逐出该行而不反向失效上游缓存。

首先我们释放本地缓存块（这样导致逐出的请求就能分配新的块并完成）。对于 GlobalEviction，会向所有上游缓存发送 `SnpCleanInvalid`。一旦收到所有探听响应（可能带脏数据），就执行 LocalEviction。LocalEviction 通过如下发出相应请求来完成：

- `WriteBackFull`，如果该行是脏的
- `WriteEvictFull`，如果该行是唯一且干净的
- `WriteCleanFull`，如果该行是脏的，但存在干净的共享者
- `Evict`，如果该行是共享且干净的

对于 HNF 配置，行为略有不同：改为向 SNF 发送 `WriteNoSnp` 而不是 `WriteBackFull`，并且如果该行是干净的，则不发出任何请求。

下游缓存按如下方式处理 `WriteBack*` 与 `Evict` 请求：

- `WriteBackFull` / `WriteEvictFull` / `WriteCleanFull`：
  - 如果 `alloc_on_writeback`，可能需要分配一个缓存块。如果没有空闲块，就会为目标缓存组中的一个缓存行触发 LocalEviction。牺牲行由 `cache` 参数所指对象实现的替换策略选出（可以单独配置）。
  - 向请求者发送 `CompDBIDResp`。
  - 一旦收到数据，就更新本地缓存并把请求者从目录中移除（如果是 `WriteBackFull` / `WriteEvictFull`）。
- `Evict`：
  - 把请求者从目录中移除，并用 `Comp\_I` 回复。

### 冒险 {#hazards}

对当前存在未完成事务的行的请求总会被停顿，直到该事务完成。在存在未完成请求时收到的探听按规范中的要求
处理：

- 对于未完成的 `CleanUnique`：
  - 立即发送探听响应，并相应地改变当前行状态。
  - 注意我们没有建模 CHI 规范中的 **UCE** 与 **UDP** 状态。如果在请求者等待 `CleanUnique` 响应期间该行被失效，它会立即接着发出 `ReadUnique`。
- 对于尚未通过 `CompDBIDResp` 确认的未完成 `WriteBackFull`/`WriteEvictFull`/`WriteCleanFull`；或在收到 `Comp_I` 之前的 Evict：
  - 立即发送探听响应，并相应地改变当前行状态。
  - 将被回写的行状态将是探听后的状态。
- 如果当前事务正在等待来自上游缓存的探听响应时收到探听，则该到来的探听会被停顿，直到收到来自上游的所有待处理响应并发出任何后续请求。这可能发生在以下场景：
  - 全局替换期间
  - 已被接受、需要探听上游缓存的 `ReadUnique` 期间

在存在未完成事务时可能收到多个探听。在本实现中，`SnpShared` 或 `SnpSharedFwd` 之后可能跟着 `SnpUnique` 或 `SnpCleanInvalid`。不过，不可能出现来自下游缓存的并发探听。

到来的请求和探听都需要分配 TBE。为了防止事务缓冲已满时发生死锁，使用单独的缓冲来分配探听 TBE。探听不允许重试，因此如果探听 TBE 表已满，snpIn 端口中的消息会被停顿，可能造成互连中探听通道的严重拥塞。

### 其他实现说明 {#other-implementations-notes}

- 如果 HNF 使用 DMT，并且设置了 `enable_DMT_early_dealloc` 配置参数，它会发送 `ReadNoSnpSep` 而不是 `ReadNoSnp`。这使 HNF 能更早地释放 TBE。
- 未实现 Order 位字段，因此除了 `ReadNoSnpSep` 之外从不使用 `ReadReceipt` 响应。在需要请求排序时，Ruby 通过在请求者处串行化请求来强制排序。在缓存控制器处，对同一行的请求按到达顺序处理。对不同行的请求可以以任意顺序处理，不过鉴于有可用资源，它们通常也按到达顺序处理。
- 未实现独占访问和原子请求。Ruby 在 Sequencer 中有自己的全局监视器来管理独占加载和存储。原子操作也由 Ruby 处理，在协议层面它们只需要 `ReadUnique`。
- 当规范中标注 `CompAck` 响应为可选时，我们总是发送它。请求者在终结事务并释放资源之前总是等待 `CompAck`（无论是必需还是可选）。
- 仅对 `WriteUnique` 请求分别使用 `Comp` 与 `DBIDresp`。`DBIDresp` 在收到所有探听响应之后发送；`Comp` 在 `DBIDresp` 之后、并计入前端写延迟（`write_fe_latency`）后发送。
- 未实现内存属性字段。
- 未实现 `DoNotGoToSD` 字段。
- 未实现 `CBusy`。
- 从不使用 `WriteDataCancel` 响应。
- 未实现错误处理。
- 未实现缓存暂存（cache stashing）。
- 未实现原子事务。
- 未实现 DMV 事务。
- 下面协议表中未列出的任何请求在本实现中都不受支持。

### 协议表 {#protocol-table}

[点击此处]({{ site.baseurl }}/assets/img/ruby_chi/protocol_table.htm)

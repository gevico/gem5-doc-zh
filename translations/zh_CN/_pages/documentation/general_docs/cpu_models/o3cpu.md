---
layout: documentation
title: 乱序（out-of-order）CPU 模型
doc: gem5 文档
parent: cpu_models
permalink: /documentation//general_docs/cpu_models/O3CPU
---

# **O3CPU**

目录

 1. [流水线级](##Pipeline-stages)
 2. [Execute-in-execute 模型](##Execute-in-execute-model)
 3. [模板策略（Template Policies）](##Template-Policies)
 4. [指令集架构（ISA）无关性](##ISA-independence)
 5. [与 ThreadContext 的交互](##Interaction-with-ThreadContext**)

O3CPU 是我们为 v2.0 版本推出的新详细模型。它是一个大致基于 Alpha 21264 的乱序（out-of-order）CPU 模型。本页将概述 O3CPU 模型、流水线级以及流水线资源。我们已努力让代码有良好的文档，因此关于 O3CPU 各个部分如何工作的准确细节，请直接浏览代码。


## **流水线级**
* 取指（Fetch）
  
     每个周期取指，并根据所选策略选择从哪个线程取指。这一级是 DynInst 首次被创建的地方。它还负责分支预测。
    
* 译码（Decode）
  
  每个周期译码指令。它还负责提前解析与 PC 相关的无条件分支。

* 重命名（Rename）
  
  使用带空闲列表的物理寄存器堆对指令进行重命名。如果没有足够的寄存器可供重命名，或者后端资源已满，它就会停顿。它还在此时处理任何串行化指令，让它们在重命名阶段停顿，直到后端排空。

* 发射/执行/写回（Issue/Execute/Writeback）
  
  我们的模拟器模型在调用指令的 execute() 函数时同时处理执行和写回，因此我们把这三级合并为一级。这一级（IEW）负责把指令分派到指令队列、通知指令队列发射指令，以及执行和写回指令。

* 提交（Commit）
  
   每个周期提交指令，处理指令可能引发的任何故障（fault）。它还负责在分支预测错误时重定向前端。


## **Execute-in-execute 模型**

对于 O3CPU，我们努力让它具有很高的时序准确性。为此，我们采用了一个真正在流水线的执行级执行指令的模型。大多数模拟器模型会在流水线的开始或结束处执行指令；SimpleScalar 和我们旧的详细 CPU 模型都在流水线开始处执行指令，然后把它交给时序后端。这会带来两个潜在问题：第一，时序后端中的错误可能不会体现在程序结果中。第二，由于在流水线开始处执行，所有指令都按序执行，乱序加载之间的交互就丢失了。我们的模型能够避免这些缺陷，并提供准确的时序模型。

## **模板策略（Template Policies）**

O3CPU 大量使用模板策略，以在不使用虚函数的情况下获得一定程度的 polymorphism。它用模板策略向 O3CPU 内几乎所有的类传入一个 "Impl"。该 Impl 中定义了流水线的所有重要类，例如具体的 Fetch 类、Decode 类、具体的 DynInst 类型、CPU 类等。它让任何以它为模板参数的类都能获得 Impl 中定义的任何类的完整类型信息。通过获得完整类型信息，就不再需要通常用于提供 polymorphism 的传统虚函数/基类。主要缺点是 CPU 必须在编译期完全定义，而且模板化的类需要手动实例化。示例 Impl 类见 `src/cpu/o3/impl.hh ` 和 `src/cpu/o3/cpu_policy.hh`。

## **指令集架构（ISA）无关性**

O3CPU 在设计时力求把依赖指令集架构（ISA）的代码与不依赖指令集架构的代码分开。流水线级和资源基本都是指令集架构无关的，更底层的 CPU 代码也是如此。依赖指令集架构的代码实现指令集架构特有的函数。例如，AlphaO3CPU 实现 Alpha 特有的函数，例如从错误中断返回的硬件操作（hwrei()）或读取中断标志。更底层的 CPU（即 FullO3CPU）负责协调所有流水线级并处理其他与指令集架构无关的动作。我们希望这种分离能让未来实现新指令集架构更容易，因为有望只需重新定义高层级的类。

## **与 ThreadContext 的交互**

[ThreadContext](/documentation/general_docs/cpu_models/execution_basics) 为外部对象提供了访问 CPU 内线程状态的接口。不过，由于 O3CPU 是乱序 CPU，这一点会稍微复杂化。虽然任一周期下的体系结构状态都有明确定义，但若该体系结构状态被修改会发生什么并没有明确定义。因此，读取 ThreadContext 并不费力，但写入 ThreadContext 并改变寄存器状态需要 CPU 清空整条流水线。这是因为可能存在依赖被修改寄存器的在途指令，而这些指令是否应看到该寄存器更新并不明确。因此，对 ThreadContext 的访问有可能导致 CPU 模拟（simulation）变慢。

## **后端流水线**
### 计算指令
计算指令更简单，因为它们不访问内存，也不与 LSQ 交互。下面给出高层级的调用链
（只列出重要函数）以及各函数功能的说明。

```cpp
Rename::tick()->Rename::RenameInsts()
IEW::tick()->IEW::dispatchInsts()
IEW::tick()->InstructionQueue::scheduleReadyInsts()
IEW::tick()->IEW::executeInsts()
IEW::tick()->IEW::writebackInsts()
Commit::tick()->Commit::commitInsts()->Commit::commitHead()
```

- 重命名（`Rename::renameInsts()`）。
  顾名思义，这里对寄存器进行重命名，并把指令
  推入 IEW 级。它会检查 IQ/LSQ 能否容纳这条新
  指令。
- 分派（`IEW::dispatchInsts()`）。
  该函数把重命名后的指令插入 IQ 和 LSQ。
- 调度（`InstructionQueue::scheduleReadyInsts()`）
  IQ 在就绪列表（ready list）中管理就绪指令（操作数已就绪），
  并把它们调度到可用的 FU。FU 的延迟在这里设置，
  当 FU 完成时指令被送往执行。
- 执行（`IEW::executeInsts()`）。
  这里调用计算指令的 `execute()` 函数，并把它
  送往提交。请注意 `execute()` 会把结果写入目标
  寄存器。
- 写回（`IEW::writebackInsts()`）。
  这里调用 `InstructionQueue::wakeDependents()`。依赖
  该指令的指令会被加入就绪列表以便调度。
- 提交（`Commit::commitInsts()`）。
  一旦指令到达 ROB 的头部，它就会被提交并从 ROB
  中释放。

### 加载指令
加载指令在执行之前与计算指令走相同的路径。

```cpp
IEW::tick()->IEW::executeInsts()
  ->LSQUnit::executeLoad()
    ->StaticInst::initiateAcc()
      ->LSQ::pushRequest()
        ->LSQUnit::read()
          ->LSQRequest::buildPackets()
          ->LSQRequest::sendPacketToCache()
    ->LSQUnit::checkViolation()
DcachePort::recvTimingResp()->LSQRequest::recvTimingResp()
  ->LSQUnit::completeDataAccess()
    ->LSQUnit::writeback()
      ->StaticInst::completeAcc()
      ->IEW::instToCommit()
IEW::tick()->IEW::writebackInsts()
```

- `LSQUnit::executeLoad()` 会通过调用指令的 `initiateAcc()` 函数来发起该访问。通过执行上下文接口，
  `initiateAcc()` 会调用 `initiateMemRead()`，最终被导向 `LSQ::pushRequest()`。
- `LSQ::pushRequest()` 会分配一个 `LSQRequest` 来跟踪所有状态，并
  开始地址转换。转换完成后，它会
  记录虚拟地址并调用 `LSQUnit::read()`。
- `LSQUnit::read()` 会检查该加载是否与之前的任何存储
  存在别名。
  - 如果可以转发，它就会为下一个
    周期调度 `WritebackEvent`。
  - 如果存在别名但无法转发，它会调用
  `InstructionQueue::rescheduleMemInst()` 和 `LSQReuqest::discard()`。
  - 否则，它把数据包发送到缓存。
- `LSQUnit::writeback()` 会调用 `StaticInst::completeAcc()`，
  后者把加载到的值写入目标寄存器。该
  指令随后被推入提交队列。接着 `IEW::writebackInsts()`
  会把它标记为已完成并唤醒其依赖者。从这里开始，它
  与计算指令走相同的路径。

### 存储指令
存储指令与加载指令类似，但只在提交之后才
写回缓存。

```cpp
IEW::tick()->IEW::executeInsts()
  ->LSQUnit::executeStore()
    ->StaticInst::initiateAcc()
      ->LSQ::pushRequest()
        ->LSQUnit::write()
    ->LSQUnit::checkViolation()
Commit::tick()->Commit::commitInsts()->Commit::commitHead()
IEW::tick()->LSQUnit::commitStores()
IEW::tick()->LSQUnit::writebackStores()
  ->LSQRequest::buildPackets()
  ->LSQRequest::sendPacketToCache()
  ->LSQUnit::storePostSend()
DcachePort::recvTimingResp()->LSQRequest::recvTimingResp()
  ->LSQUnit::completeDataAccess()
    ->LSQUnit::completeStore()
```

- 与 `LSQUnit::read()` 不同，`LSQUnit::write()` 只复制存储
  数据，而不把数据包发送到缓存，因为该存储尚未提交。
- 存储提交之后，`LSQUnit::commitStores()` 会把 SQ
  条目标记为 `canWB`，从而让 `LSQUnit::writebackStores()` 把
  该存储请求发送到缓存。
- 最后，当响应返回时，`LSQUnit::completeStore()` 会
  释放 SQ 条目。

### 分支误预测

分支误预测在 `IEW::executeInsts()` 中处理。它会
通知提交级开始清空 ROB 中所有位于误预测分支
之后的指令。

```cpp
IEW::tick()->IEW::executeInsts()->IEW::squashDueToBranch()
```

### 内存顺序误预测

`InstructionQueue` 有一个 `MemDepUnit` 来跟踪内存顺序依赖。
如果 MemDepUnit 指出存在依赖，IQ 就不会调度该指令。

在 `LSQUnit::read()` 中，LSQ 会搜索可能存在别名的存储，并在可能时
进行转发。否则，该加载被阻塞，并重新调度到
阻塞它的存储完成时执行（通过通知 MemDepUnit）。

`LSQUnit::executeLoad/Store()` 都会调用 `LSQUnit::checkViolation()`
在 LQ 中搜索可能的误预测。如果找到，它会设置
`LSQUnit::memDepViolator`，随后 `IEW::executeInsts()` 会启动
清空这些误预测的指令。

```cpp
IEW::tick()->IEW::executeInsts()
  ->LSQUnit::executeLoad()
    ->StaticInst::initiateAcc()
    ->LSQUnit::checkViolation()
  ->IEW::squashDueToMemOrder()
```

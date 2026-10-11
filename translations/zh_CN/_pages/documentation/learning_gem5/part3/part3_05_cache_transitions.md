---
layout: documentation
title: "状态转换代码块"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/cache-transitions/
author: Jason Lowe-Power
---

## 状态转换代码块

现在来到状态机（state machine）文件的最后一部分：定义各状态之间的转换，以及转换过程中执行的动作。

本教程按文件顺序逐节展开，但实际编写缓存一致性（cache coherence）协议（protocol）时，往往需要在各部分之间来回修改。例如写转换时发现缺少动作，或者需要增加瞬态状态，都是正常的开发过程。

转换块包含两部分：首行指定起始状态、触发事件以及可选的结束状态；块内按顺序列出动作。例如，MSI 中在 Invalid 状态收到 Load 的转换如下：

```cpp
transition(I, Load, IS_D) {
    allocateCacheBlock;
    allocateTBE;
    sendGetS;
    popMandatoryQueue;
}
```

`transition` 的参数（parameter）表示：起始状态为 `I`、事件为 `Load` 时，转到 `IS_D`，即从无效状态转向共享状态，等待数据。这直接对应 Sorin 等人书中的表 8.3。

块内先分配条目。`allocateCacheBlock` 会设置隐式的条目变量，使后续动作能够使用新条目。然后分配 TBE，用于保存尚未完成操作的信息；其他转换中还可用它跟踪待收确认。接着向目录发送 GetS，最后从 mandatory 队列弹出原始请求，因为该队列中的请求已经交给后续处理流程。

```cpp
transition(IS_D, {Load, Store, Replacement, Inv}) {
    stall;
}
```

这里采用另一种写法。根据表 8.3，处于 `IS_D` 时收到加载、存储、替换或失效事件，都应停顿。将多个事件放入花括号，就能共用一个转换声明。结束状态也可以省略，此时状态保持不变。上例表示：“若块处于 `IS_D`，遇到这四类事件就停顿，继续保持当前状态。”起始状态也能使用花括号列出多个值，后面的示例会用到。

以下是实现 MSI L1 缓存（cache）所需的其他转换：

```cpp
transition(IS_D, {DataDirNoAcks, DataOwner}, S) {
    writeDataToCache;
    deallocateTBE;
    externalLoadHit;
    popResponseQueue;
}

transition({IM_AD, IM_A}, {Load, Store, Replacement, FwdGetS, FwdGetM}) {
    stall;
}

transition({IM_AD, SM_AD}, {DataDirNoAcks, DataOwner}, M) {
    writeDataToCache;
    deallocateTBE;
    externalStoreHit;
    popResponseQueue;
}

transition(IM_AD, DataDirAcks, IM_A) {
    writeDataToCache;
    storeAcks;
    popResponseQueue;
}

transition({IM_AD, IM_A, SM_AD, SM_A}, InvAck) {
    decrAcks;
    popResponseQueue;
}

transition({IM_A, SM_A}, LastInvAck, M) {
    deallocateTBE;
    externalStoreHit;
    popResponseQueue;
}

transition({S, SM_AD, SM_A, M}, Load) {
    loadHit;
    popMandatoryQueue;
}

transition(S, Store, SM_AD) {
    allocateTBE;
    sendGetM;
    popMandatoryQueue;
}

transition(S, Replacement, SI_A) {
    sendPutS;
    forwardEviction;
}

transition(S, Inv, I) {
    sendInvAcktoReq;
    deallocateCacheBlock;
    forwardEviction;
    popForwardQueue;
}

transition({SM_AD, SM_A}, {Store, Replacement, FwdGetS, FwdGetM}) {
    stall;
}

transition(SM_AD, Inv, IM_AD) {
    sendInvAcktoReq;
    forwardEviction;
    popForwardQueue;
}

transition(SM_AD, DataDirAcks, SM_A) {
    writeDataToCache;
    storeAcks;
    popResponseQueue;
}

transition(M, Store) {
    storeHit;
    popMandatoryQueue;
}

transition(M, Replacement, MI_A) {
    sendPutM;
    forwardEviction;
}

transition(M, FwdGetS, S) {
    sendCacheDataToReq;
    sendCacheDataToDir;
    popForwardQueue;
}

transition(M, FwdGetM, I) {
    sendCacheDataToReq;
    deallocateCacheBlock;
    popForwardQueue;
}

transition({MI_A, SI_A, II_A}, {Load, Store, Replacement}) {
    stall;
}

transition(MI_A, FwdGetS, SI_A) {
    sendCacheDataToReq;
    sendCacheDataToDir;
    popForwardQueue;
}

transition(MI_A, FwdGetM, II_A) {
    sendCacheDataToReq;
    popForwardQueue;
}

transition({MI_A, SI_A, II_A}, PutAck, I) {
    deallocateCacheBlock;
    popForwardQueue;
}

transition(SI_A, Inv, II_A) {
    sendInvAcktoReq;
    popForwardQueue;
}
```

可以[查看完整的 MSI-cache.sm](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/MSI-cache.sm)。

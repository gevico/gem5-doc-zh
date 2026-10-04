---
layout: documentation
title: "替换策略（replacement policy）"
doc: gem5 文档
parent: memory_system
permalink: /documentation/general_docs/memory_system/replacement_policies/
author: Jason Lowe-Power
---

# 替换策略（Replacement Policy）

Gem5 实现了多种替换策略（replacement policy）。每种策略都使用其
特有的替换数据，在发生逐出时确定要替换的牺牲块（victim）。

所有替换策略都优先逐出无效块。

一种替换策略由 reset()、touch()、invalidate() 和
getVictim() 方法组成。它们各自以不同方式处理替换数据。

-   reset() 用于初始化替换数据（即使之有效）。
    它只应在条目插入时被调用，并且在失效之前不得再次调用。
    对某个条目的第一次 touch 必须始终是
    reset()。
-   touch() 用于访问替换数据，因此
    应在条目被访问时调用。它会更新替换数据。
-   invalidate() 在条目失效时被调用，可能是
    由于一致性处理导致的。它让该条目在下次寻找牺牲块时尽可能
    容易被逐出。条目不必在 reset() 之前失效。模拟（simulation）
    开始时，所有条目都是无效的。
-   getVictim() 在发生未命中、必须进行逐出时
    被调用。它在所有替换候选者中搜索替换数据
    最差的条目，通常优先逐出无效条目。

下面简要介绍 Gem5 中实现的替换策略。如需更多信息，可以研究
[缓存替换策略
维基百科页面（Cache Replacement Policies Wikipedia page）](https://en.wikipedia.org/wiki/Cache_replacement_policies)或相应的论文。

随机（Random）
------
最简单的替换策略；它不需要替换数据，因为
它在候选者中随机选择牺牲块。

最近最少使用（LRU） {#least_recently_used_lru}
-------------------------
它的替换数据由最后一次访问的时间戳组成，牺牲块
据此选出：时间戳越旧，对应条目越可能
被选为牺牲块。

树形伪最近最少使用（TreePLRU） {#tree_pseudo_least_recently_used_treeplru}
------------------------------------------
LRU 的一种变体，它使用二叉树，通过 1 位指针来记录
各条目的最近使用情况。

双峰插入策略（BIP） {#bimodal_insertion_policy_bip}
------------------------------
[双峰插入策略（Bimodal Insertion Policy）]与 LRU 类似，但块
有一个以 MRU 位置插入的概率，由双峰
节流参数（btp）控制。btp 越高，新块
以 MRU 位置插入的可能性就越大。

LRU 插入策略（LIP） {#lru_insertion_policy_lip}
--------------------------
[LRU 插入策略（LRU Insertion Policy）][双峰插入策略（Bimodal Insertion Policy）]是一种 LRU
替换策略，但它不以最近的
访问时间戳插入块，而是把块插入为 LRU 条目。对该块的后续
访问会像 LRU 一样把其时间戳更新为 MRU 时间。
它也可以看作一种 BIP，其中把新块
插入为最近最常使用的概率为 0%。

最近最常使用（MRU） {#most_recently_used_mru}
------------------------
最近最常使用（Most Recently Used）策略按条目的
新旧程度来选择牺牲块，不过与 LRU 相反，条目越新，
越可能被选为牺牲块。

最少使用频率（LFU） {#least_frequently_used_lfu}
---------------------------
牺牲块根据引用频率来选择。引用次数最少的
条目会被逐出，无论它被访问过多少次，也无论
距上次访问过去了多久。

先进先出（FIFO） {#first_in_first_out_fifo}
--------------------------
牺牲块根据插入时间戳来选择。如果不存在无效
条目，则逐出最旧的那个，无论它
被访问过多少次。

第二次机会（Second-Chance） {#second_chance}
-------------
[第二次机会（Second-Chance）]替换策略与 FIFO 类似，但
条目在被逐出前会获得第二次机会。如果某个条目
本应是下一个被逐出的对象，但它的第二次机会位
被置位，则该位会被清除，该条目被重新插入到
FIFO 的末尾。发生未命中后，插入的条目的第二次机会位
被清除。

最近未使用（NRU） {#not_recently_used_nru}
-----------------------
最近未使用（Not Recently Used，NRU）是 LRU 的一种近似，它使用单个
位来判断某个块在近期还是
远期会被再次引用。如果该位为 1，说明它很可能不会很快被引用，
因此被选为替换牺牲块。当一个块被逐出时，
其所有同组替换候选者的再引用位
都会递增。

重参考间隔预测（RRIP） {#re_reference_interval_prediction_rrip}
---------------------------------------
[重参考间隔预测（Re-Reference Interval Prediction，RRIP）]是 NRU 的扩展，它
使用再引用预测值来判断块在
近期是否会被复用。RRPV 的值越高，
该块距其下次访问的时间就越远。按原始
论文的说法，这种 RRIP 实现也称为静态 RRIP（SRRIP），
因为它总是以相同的 RRPV 插入块。

双峰重参考间隔预测（BRRIP） {#bimodal_re_reference_interval_prediction_brrip}
------------------------------------------------
[双峰重参考间隔预测
（BRRIP）][重参考间隔预测（Re-Reference Interval Prediction，RRIP）]是
RRIP 的扩展，它有一定概率不把块插入为
LRU，这与双峰插入策略相同。该概率由
双峰节流参数（btp）控制。

  [第二次机会（Second-Chance）]: https://apps.dtic.mil/docs/citations/AD0687552
  [重参考间隔预测（Re-Reference Interval Prediction，RRIP）]: https://dl.acm.org/citation.cfm?id=1815971
  [缓存替换策略维基百科页面（Cache Replacement Policies Wikipedia page）]: https://en.wikipedia.org/wiki/Cache_replacement_policies
  [双峰插入策略（Bimodal Insertion Policy）]: https://dl.acm.org/citation.cfm?id=1250709

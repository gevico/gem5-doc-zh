---
layout: documentation
title: "索引策略（indexing policy）"
doc: gem5 文档
parent: memory_system
permalink: /documentation/general_docs/memory_system/indexing_policies/
author: Jason Lowe-Power
---

# 索引策略（Indexing Policy）

索引策略（indexing policy）根据块的地址确定它所映射到的位置。

索引策略最重要的方法是 getPossibleEntries()
和 regenerateAddr()：

-   getPossibleEntries() 确定给定地址可以映射到的
    条目列表。
-   regenerateAddr() 利用条目中存储的地址信息
    来确定其完整的原始地址。

关于缓存索引策略的更多信息，请参阅
维基百科上关于[放置策略（Placement Policies）](https://en.wikipedia.org/wiki/Cache_Placement_Policies)和
[相联度（Associativity）](https://en.wikipedia.org/wiki/CPU_cache#Associativity%7C)的文章。

组相联（Set Associative） {#set_associative}
---------------
组相联索引策略是表状
结构的标准做法，它可以进一步分为直接映射（或 1 路
组相联）、组相联和全相联（N 路
组相联，其中 N 为表条目数）。

组相联缓存可以看作一种偏斜相联（skewed associative）缓存，只是其
偏斜函数对每一路都映射到相同的值。

偏斜相联（Skewed Associative） {#skewed_associative}
------------------
偏斜相联索引策略基于
哈希函数进行可变映射，因此值 x 可以根据
所用的路映射到不同的组。Gem5 按
[“Skewed-Associative
Caches”，来自 Seznec 等人](https://www.researchgate.net/publication/220758754_Skewed-associative_Caches)的描述实现偏斜缓存。

注意，已实现的哈希函数数量有限，因此如果路数超过该数量，
就会使用一个次优的自动生成哈希函数。

---
layout: documentation
title: Ruby 随机测试器（Ruby random tester）
doc: gem5 文档
parent: directed_testers
permalink: /documentation/general_docs/debugging_and_testing/directed_testers/ruby_random_tester/
author: Bobby R. Bruce
---

# Ruby 随机测试器（Ruby random tester）

缓存一致性（cache coherence）协议通常有若干种不同的状态
机（state machine），每种状态机又有若干不同的状态。例如，
`MESI CMP` 目录协议有四种不同的状态机（`L1`、`L2`、
`directory`、`dma`）。测试这样一个协议的功能正确性是一项
艰巨的任务。gem5 提供了一个用于测试一致性
协议的随机测试器。它称为 Ruby Random Tester。与该
测试器相关的源文件位于目录 `src/cpu/testers/rubytest` 中。文件
`configs/examples/ruby_random_test.py` 用于配置和执行
该测试。例如，可以用以下命令测试某个
协议：

```bash
./build/NULL/gem5.fast ./configs/example/ruby_random_test.py
```

注意：自 gem5 v24.1 起，如果使用 ALL 构建，上述命令将无法工作。

虽然可以为随机测试器指定许多不同的选项，但其中有
一些值得注意。

|参数               |说明                                                        |
|:-----------------|:-----------------------------------------------------------------|
|`-n`、`--num-cpus`|向内存系统注入加载/存储请求的 cpu 数量。                          |
|`--num-dirs`      |系统中的目录控制器数量。                                          |
|`-m`、`--maxtick` |要模拟的周期数。                                                  |
|`-l`、`--checks`  |要执行的加载次数。                                                |
|`--random_seed`   |随机数发生器初始化所用的种子。                                    |

用随机测试器测试一致性协议是一项繁琐的工作，需要耐心。
首先，用待测试的协议构建 gem5。然后，如上所述运行
ruby 随机测试器。起初应以单个处理器和少量加载来运行测试器。
你很可能会遇到问题。使用调试标志获取系统中发生事件的跟踪（trace）。
你可能会发现 `ProtocolTrace` 标志特别有用。随着这些问题被
修正，继续增加加载次数，例如每次增加 10 倍，
直到可以执行一百万到一千万次加载。一旦它在
单个处理器上可以工作，就需要对两个
处理器系统采用类似的流程，然后是更大的系统。

已有一些用于[验证一致性协议](
https://doi.org/10.1145/248621.248624)的理论方法，但 gem5 目前不包含任何
基于这些方法的测试器。

---
layout: documentation
title: "MSI 缓存一致性（cache coherence）协议（protocol）示例"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/cache-intro/
author: Jason Lowe-Power
---

## MSI 缓存一致性（cache coherence）协议（protocol）示例

实现之前，需要充分理解缓存一致性（cache coherence）。本节主要参考 Daniel J. Sorin、Mark D. Hill 和 David A. Wood 的 *A Primer on Memory Consistency and Cache Coherence*。该书于 2011 年作为 Synthesis Lectures on Computer Architecture 系列的一部分出版（[DOI:10.2200/S00346ED1V01Y201104CAC016](https://doi.org/10.2200/S00346ED1V01Y201104CAC016)）。如果尚不熟悉这一主题，建议先阅读该书。

本章实现 MSI 协议（protocol）。它有三个稳定状态：Modified，允许读写；Shared，只允许读取；Invalid，没有访问权限。本例采用三跳目录协议（protocol），允许缓存（cache）之间直接传送数据，无需由目录中转。详细定义见该书第 8.2 节，第 141—149 页。实现时可打印这一节，便于随时对照。

也可以通过[此链接下载第二版](https://link.springer.com/content/pdf/10.1007/978-3-031-01764-3.pdf)。

## 编写协议（protocol）的第一步

先创建 `src/learning_gem5/MSI_protocol` 目录。与其他 gem5 源码目录一样，需要一个文件告知 SCons 应构建哪些内容。这里使用 `SConsopts`，而不是 `SConscript`：前者在后者之前处理，以便提前登记 SLICC 构建所需的信息。

创建 `SConsopts`，写入：

```python
Import('*')

main.Append(ALL_PROTOCOLS=['MSI'])

main.Append(PROTOCOL_DIRS=[Dir('.')])
```

这个文件完成两件事。首先注册名称 `'MSI'`，SCons 因而会寻找 `MSI.slicc`，由它列出全部状态机（state machine）和辅助文件。写完各个状态机（state machine）后，再创建这个文件。其次，告知 SCons 在当前目录寻找要交给 SLICC 编译器的文件。

可以[查看 SConsopts 文件](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/SConsopts)。

### 编写状态机（state machine）文件

接下来，也是实现工作中最主要的部分，是编写状态机（state machine）文件。通常包括以下内容：

参数（parameter）
:   将导出到 SLICC 生成的 SimObject 中的参数（parameter）。

所需结构与函数的声明
:   声明状态、事件和其他所需结构。

输入端口（port）代码块
:   检查 `in_port` 消息缓冲区中的消息，决定触发哪个事件。

动作
:   执行单项操作的简单代码块，例如发送消息。状态转换时会执行这些动作。

转换
:   根据起始状态与事件，指定执行的动作以及最终状态。这是状态机（state machine）定义的核心。

后续各节将逐一说明这些组成部分的写法。

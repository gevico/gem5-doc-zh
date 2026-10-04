---
layout: documentation
title: gem5-resources
doc: gem5 文档
parent: gem5-apis
permalink: /documentation/general_docs/gem5-apis/
authors: Bobby R. Bruce
---

关于所有被标记为 API 的方法和变量的完整文档，请
查阅我们的 [Doxygen 模块页面](
http://doxygen.gem5.org/release/v20-1-0-0/modules.html)。

# gem5 API

为了提升产品稳定性，gem5 开发团队正在逐步把 gem5 中的方法和变量标记为 API；开发者若要修改这些内容，需要经历特定的流程。我们设立 gem5 API 的目标，是为用户提供一个稳定的接口来构建 gem5 模型、扩展 gem5 代码库，并保证这些 API 不会在两次 gem5 发布之间发生突变。

## gem5 API 是如何记录的？

我们使用 [Doxygen 文档生成工具](
https://www.doxygen.nl/index.html)来记录 gem5 API。这意味着你可以在源码层面以及通过我们的[基于 Web 的文档](
http://doxygen.gem5.org)看到被标记的 API。我们使用 Doxygen 的 `@ingroup` 标签来把某个方法/变量标记为 gem5 API 的一部分。我们把 API 划分为 `api_simobject`、`api_ports` 等子域，不过所有 gem5 API 都带有前缀 `api_`。例如，我们按如下方式标记 SimObject 的 `params()`
函数：

```cpp
/**
* @return This function returns the cached copy of the object parameters.
*
* @ingroup api_simobject
*/
const Params *params() const { return _params; }
```

通过 Doxygen 的自动生成，gem5 API 的列表可在
[Doxygen 模块页面](http://doxygen.gem5.org/release/current/modules.html)找到。
在本例中，SimObject API 的完整列表记录在
[SimObject API 页面](
http://doxygen.gem5.org/release/current/group__api__simobject.html)。不同 API 组的
定义可在
[`src/doxygen/group_definitions.hh`](
https://github.com/gem5/gem5/blob/stable/src/doxygen/group_definitions.hh)中找到。

### 给开发者的说明

如果开发者希望把新的方法/变量标记为 gem5 API 的一部分，
应当征求 gem5 社区的意见。API 的意图是在一段时间内保持不变。为了避免 gem5 项目被“过多的 API”拖累，
我们强烈建议希望扩展 API 的人向
gem5 开发团队说明该 API 的价值所在。
[gem5 Discussion 页面](https://github.com/orgs/gem5/discussions/categories/gem5-dev)
是进行这类沟通的良好渠道。

## API 可以如何变更？

我们不保证 gem5 API 永远不会随时间变化。gem5 是一个
持续开发中的产品，必须适应
计算机体系结构研究社区的需求。不过我们保证 API
的变更会遵循以下严格规则。

1. 当某个 API 方法或变量被修改时，新的 API 会与旧 API 并存，
旧 API 会被标记为已废弃（deprecated），但仍然可用。

2. 旧的、已废弃的 API 会在两个 gem5 大版本周期内继续存在，之后才从代码库中彻底移除；不过 gem5 开发者也可以选择让
某个已废弃的 API 在代码库中保留更久。例如，如果某个 API 在 gem5 21.0 中被标记为
已废弃，它在 gem5 21.1 中仍然存在（仍标记为已废弃）。
它可能在 gem5 21.2 中被彻底移除，不过这由
gem5 开发者自行决定。

3. 已废弃的 gem5 C++ API 会使用 C++ 的 deprecated
属性（`[[deprecated(<msg>)]]`）标记。使用已废弃的 C++ API 时，编译期会给出
警告，指明应改用哪个 API。已废弃的 gem5 Python 参数 API 则用我们[定制的
`DeprecatedParam` 类](
https://github.com/gem5/gem5/blob/bd13e8e206e6c86581cf9afa904ef1060351a4b0/src/python/m5/params.py#L2166)包装。
用该类包装的 Python 参数在被使用时会产生警告，并
指明应改用哪个 API。

### 给开发者的说明

在对 gem5 API 做任何修改之前，应咨询 [gem5-dev 邮件列表](
/ask-a-question/)。无论出于何种原因修改 API，
都**会**比其他改动受到更严格的审查。开发者应当
准备好说明为什么该 API 必须变更。我们强烈建议先讨论 API 变更，否则它可能在代码评审中被拒绝。

在创建新 API 时，必须把旧 API 标记为已废弃，并让新
API 与旧 API 并存。**维护旧的、已废弃的 API 而不删除它至关重要**。

举一个例子，请看以下代码：

```cpp
/**
 * @ingroup api_bitfield
 */
inline uint64_t
mask(int first, int last)
{
    return mbits((uint64_t)-1LL, first, last);
}
```

这个函数是 gem5 bitfield API 的一部分。它是一个基本的掩码函数，
接收 MSB（first）和 LSB（last）来生成 64 位值。
我们假设有一个充分理由说明该函数应被替换为接收 MSB（first）和掩码长度
的版本。

首先，旧 API 需要被保留（即不做改动）并打上
`[[deprecated(<msg>)]]` 标记。消息（`<msg>`）应说明应改用哪个新 API，
并且应移除原来的 API 标记。然后创建新 API 并打上标记。因此，沿用我们的示例：

```cpp
[[deprecated("Use mask_length instead.")]]
inline uint64_t
mask(int first, int last)
{
    return mbits((uint64_t)-1LL, first, last);
}

/**
 * @ingroup api_bitfield
 */
inline uint64_t
mask_length(int first, int length)
{
    return mbits((uint64_t)-1LL, first, first + length);
}
```

这里创建了一个新函数 `mask_length`。它已通过 Doxygen
正确打上标记。旧 API `mask` 仍然存在，但加上了
`[[deprecated]]` 注解。所提供的消息说明了替代它的 API。

随后开发者需要把代码库中所有对 `mask` 的使用替换为
`mask_length`。如果使用了 `mask`，编译期会给出警告，
说明它已废弃，并提示 "Use mask\_length instead."。

有时可能需要修改与已标记 API 相关的 Python API 接口。例如，看下面的代码：

```python
class TLBCoalescer(ClockedObject):
    type = 'TLBCoalescer'
    cxx_class = 'TLBCoalescer'
    cxx_header = 'gpu-compute/tlb_coalescer.hh'

    ...

    slave    = VectorResponsePort("Port on side closer to CPU/CU")
    master   = VectorRequestPort("Port on side closer to memory")

   ...
```

在[近期的修订](
https://github.com/gem5/gem5/tree/392c1ced53827198652f5eda58e1874246b024f4)中，
`master` 与 `slave` 这两个术语已被替换。不过 `slave` 和
`master` 用语被广泛使用，以至于我们视其为旧 API 的一部分。因此我们希望在安全地废弃该 API 的同时，
把 `master` 和 `slave` 改为 `cpu_side_ports` 和 `mem_side_ports`。为此，
我们会保留 `master` 和 `slave` 变量，但使用我们的
[`DeprecatedParam` 类](
https://github.com/gem5/gem5/blob/bd13e8e206e6c86581cf9afa904ef1060351a4b0/src/python/m5/params.py#L2166)
在这两个已废弃变量被使用时产生警告。沿用我们的示例，会得到以下代码：

```python
class TLBCoalescer(ClockedObject):
    type = 'TLBCoalescer'
    cxx_class = 'TLBCoalescer'
    cxx_header = 'gpu-compute/tlb_coalescer.hh'

    ...

    cpu_side_ports = VectorResponsePort("Port on side closer to CPU/CU")
    slave    = DeprecatedParam(cpu_side_ports,
                        '`slave` is now called `cpu_side_ports`')
    mem_side_ports = VectorRequestPort("Port on side closer to memory")
    master   = DeprecatedParam(mem_side_ports,
                        '`master` is now called `mem_side_ports`')

   ...
```

注意这里使用了 `DeprecatedParam`，它既通过重定向到 `mem_side_ports` 和 `cpu_side_ports` 确保 `master` 和 `slave`
仍然可用，也提供了说明该 API 为何被废弃的注释。当 `master` 或 `slave` 被使用时，
这会以警告形式显示给用户。

与对 gem5 源码的所有改动一样，这些改动必须经过
我们的 Gerrit 代码评审系统，然后才能合并到 `develop` 分支，
最终作为某次 gem5 发布的一部分进入 `stable` 分支。
按照我们的 API 政策，这些已废弃的 API 必须以
标记为已废弃的状态存在两个 gem5 大版本周期。此后它们
可以被移除，不过开发者并没有必须移除的义务。

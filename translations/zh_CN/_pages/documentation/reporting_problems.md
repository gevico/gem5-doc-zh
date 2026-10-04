---
layout: page
title: 问题报告
parent: documentation
permalink: documentation/reporting_problems/
author: Bobby R. Bruce
---

[gem5 社区](/ask-a-question)中的许多人都乐于在有人遇到问题或某些东西无法正常工作时提供帮助。不过请
记住，参与 gem5 工作的人还有其他事务，因此我们希望
在报告问题之前，用户能先花一些精力尝试自行解决，
或者至少收集足够的信息以便他人帮助解决
问题。

下面我们给出一些关于报告问题的一般性建议。

## 报告问题之前

报告问题之前最重要的事情，是尽可能充分地调查
该问题。这可能会让你直接找到解决方案，
或者让你能向 gem5 社区提供关于该问题的更多信息。下面是我们建议你在报告
问题之前执行的一系列步骤/检查：

1. 请检查是否已有类似问题在我们的某个
[渠道](/ask-a-question)上提出过（也请查阅存档）。

2. 确保你编译和运行的是最新版本的 [gem5](
https://github.com/gem5/gem5)。该问题可能已经被解决。

3. 检查[当前正在我们的 GitHub 系统上评审的改动](
https://github.com/gem5/gem5/pulls/)。你的问题可能已经有修复方案
正在被合并到项目中。

4. 确保你使用的是 `gem5.opt` 或 `gem5.debug`，而不是 `gem5.fast`。
`gem5.fast` 二进制程序为了速度编译掉了断言检查，因此在 `gem5.fast` 上导致崩溃或错误的
问题，在 `gem5.opt` 或 `gem5.debug` 上可能会表现为信息更丰富的断言失败。

5. 如果看来合适，请启用一些调试标志（例如通过命令行
`--debug-flags=Foo`）。关于调试标志的更多信息，请查阅我们的
[调试教程](/documentation/learning_gem5/part2/debugging)。

6. 如果你的问题出现在 C++ 侧，不要害怕用 GDB 调试。

# 报告问题

当你认为自己已经收集到关于该问题的足够信息后，
就可以报告它了。

* 如果你有理由认为这是一个缺陷，请在 gem5 的 [GitHub issues](https://github.com/gem5/gem5/issues) 上报告。
**请附上任何有助于他人在自己的系统上复现该缺陷的信息**。包括所使用的命令行参数、任何
相关系统信息（至少要说明你使用的是什么操作系统，以及
你是如何编译 gem5 的？）、收到的错误信息、程序输出、栈回溯
等。

* 如果你选择在 [gem5 Discussions 页面](
https://github.com/orgs/gem5/discussions)上提问，请提供任何
可能有帮助的信息。如果你对问题原因有自己的推测，请告诉我们，但也要包含足够的
基本信息，以便他人判断你的推测是否正确。


# 解决问题

如果你已经解决了自己报告的问题，请把解决方案作为后续回复告知社区
（在对应的 GitHub issue 或 discussion 中）。如果你
修复了一个缺陷，我们希望你能把修复提交到 gem5
源码。具体做法请参阅我们的[贡献新手指南](/contributing)。

如果你发现的问题在于某篇 gem5 文档/教程的内容有误，
请考虑提交改动。关于如何为 gem5 网站做贡献的
更多信息，请查阅我们的 [README](
https://github.com/gem5/website/blob/stable/README.md)。

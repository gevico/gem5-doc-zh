---
layout: documentation
title: 基于调试器的调试（debugger-based debugging）
doc: gem5 文档
parent: debugging
permalink: /documentation/general_docs/debugging_and_testing/debugging/debugger_based_debugging
author: Bobby R. Bruce
---

# 基于调试器的调试（debugger-based debugging）

如果仅靠跟踪（trace）还不够，你就需要用调试器（例如 gdb）详细查看 gem5 在做什么。走到这一步时，你一定要使用
`gem5.debug` 二进制程序。理想情况下，查看跟踪至少应该让你把出问题的周期范围
缩小。达到该目标最快的方法是使用
`DebugEvent`：它会被放入 gem5 的事件队列，并在到达指定周期时向进程发送 `SIGTRAP`
信号，从而强制进入调试器。要让这一点生效，你需要在调试器下启动 gem5，
或者让调试器附加到 gem5 进程上。

在调用 gem5 时，你可以用
`--debug-break=100` 参数创建一个或多个 DebugEvent。你也可以在
调试器提示符下用 `schedBreak()` 函数创建新的 DebugEvent。下面的示例
会话演示了这两种方式：

```
% gdb m5/build/ALL/gem5.debug
GNU gdb 6.1
Copyright 2002 Free Software Foundation, Inc.
[...]
(gdb) run --debug-break=2000 configs/run.py
Starting program: /z/stever/bk/m5/build/ALL/gem5.debug --debug-break=2000 configs/run.py
M5 Simulator System
[...]
warn: Entering event queue @ 0.  Starting simulation...

Program received signal SIGTRAP, Trace/breakpoint trap.
0xffffe002 in ?? ()
(gdb) p curTick
$1 = 2000
(gdb) c
Continuing.

(gdb) call schedBreak(3000)
(gdb) c
Continuing.

Program received signal SIGTRAP, Trace/breakpoint trap.
0xffffe002 in ?? ()
(gdb) p _curTick
$3 = 3000
(gdb)
```

gem5 包含若干专门为从调试器调用而设计的函数（例如使用 gdb 的 `call` 命令，如上面的 `schedBreak()` 示例）。
其中许多是用于显示模拟器内部数据结构的 "dump" 函数。
例如，`eventq_dump()` 会显示主事件队列上已调度的事件。大多数其他 dump 函数
与特定对象关联，例如详细 CPU 模型中的指令队列和 ROB。它们包括：

|函数                                        |作用                                                     |
|:-------------------------------------------|:--------------------------------------------------------|
|`schedBreak(<tick>)`                        |调度一个在 `<tick>` 时发生的 `SIGTRAP`                   |
|`setDebugFlag("<flag>")`                    |从调试器中启用某个调试标志                               |
|`clearDebugFlag("<flag>")`                  |从调试器中禁用某个调试标志                               |
|`eventqDump()`                              |打印事件队列上的所有事件                                 |
|`takeCheckpoint(<tick>)`                    |在周期 `<tick>` 创建检查点（checkpoint）                 |
|`SimObject::find("system.qualified.name")`  |返回指向指定名称对象的指针                               |

<!---
The following has been commented out as the link the classic
memory system has yet to be migrated over to the website.

Additional gdb-accessible features for debugging coherence protocols in the
classic memory system are documented [here]{
http://gem5.org/Classic_Memory_System#Debugging}.
-->

## 用 PDB 调试 Python

你可以像调试其他 Python
脚本一样，用 [Python 调试器（PDB）](
https://docs.python.org/3/library/pdb.html)调试配置脚本。你可以在配置脚本执行之前进入 PDB，
方法是给 gem5 二进制程序加上 `--pdb` 参数。另一种做法是在配置脚本中
你想进入调试器的位置加入下面这一行：

```python
import pdb; pdb.set_trace()
```

注意，`src` 下的 Python 文件会被编译进 gem5 二进制程序，因此如果你在这些
文件中加入这一行（或做其他修改），必须重新构建二进制程序。或者，你可以把
`M5_OVERRIDE_PY_SOURCE` 环境变量设为 "true"（见 `src/python/importer.py`）。

关于使用 PDB 的更多细节，请参见[PDB 官方文档](
https://docs.python.org/3/library/pdb.html)。

## 使用 Valgrind

Valgrind 是一个动态分析工具，主要用途是对目标
应用程序进行性能分析、检测运行时错误的来源，以及检测内存
泄漏。

要让 Valgrind 能工作，目标 gem5 二进制程序必须在编译时
包含调试信息。因此必须使用 `gem5.debug` 二进制程序。由于
Valgrind 与 tcmalloc 配合使用时存在困难，`gem5.debug`
必须使用 `--without-tcmalloc` 选项编译：

```bash
scons --without-tcmalloc build/ALL/gem5.debug
```

要用 Valgrind 运行检查，请执行：

```bash
valgrind --leak-check=yes --suppressions=util/valgrind-suppressions build/ALL/gem5.debug {gem5 arguments}
```

上面的命令会运行 gem5，并做两件事：

1. 如果出现运行时错误，给出栈回溯。
2. 给出关于潜在内存泄漏的信息。

`util/valgrind-suppressions` 文件包含一组由 Valgrind
报告、但 gem5 开发者认为不构成问题的警告。
**已知 Valgrind 会给出误报。当这些误报被发现时，应更新
`util/valgrind-suppressions`**。关于抑制 Valgrind 警告的更多信息见 [Valgrind 用户手册](
http://valgrind.org/docs/manual/manual-core.html#manual-core.suppress)。

如果出现运行时错误，Valgrind 会返回类似以下的输出
（摘自 [Valgrind 快速入门指南](
http://valgrind.org/docs/manual/quick-start.html)）：

```txt
==19182== Invalid write of size 4
==19182==    at 0x804838F: f (example.c:6)
==19182==    by 0x80483AB: main (example.c:11)
```

在该输出中：

* 19182 是进程 ID
* `Invalid write` 是错误类型。
* 该错误下方是栈回溯。在本例中，泄漏发生在
`example.c` 的第 6 行。该行位于函数 `f` 中，而 `f` 由
第 11 行的 `main` 方法调用（同样在 `example.c` 中）。
* `0x804838F` 是代码地址。通常不重要。

Valgrind 还可能返回关于内存泄漏的警告，例如：

```txt
==19182== 40 bytes in 1 blocks are definitely lost in loss record 1 of 1
==19182==    at 0x1B8FF5CD: malloc (vg_replace_malloc.c:130)
==19182==    by 0x8048385: f (a.c:5)
==19182==    by 0x80483AB: main (a.c:11)
```

栈回溯会告诉你内存泄漏发生在哪里。如果 Valgrind
指出某个内存块 "definitely lost"，那就是内存泄漏。不过，如果 Valgrind 指出某个块
"probably lost"，则说明 Valgrind 有理由认为存在内存泄漏，但也可能并非如此（这通常意味着
代码在指针上做了复杂操作）。

如果 Valgrind 返回的输出难以确定根本原因，
可以尝试用 `--track-origins=yes` 运行 Valgrind。这会增加执行
时间，但会提供更多信息。

更高级的特性请查阅 [Valgrind 用户手册](https://valgrind.org/docs/manual/manual.html)。

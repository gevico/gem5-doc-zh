---
layout: documentation
title: 基于跟踪的调试（trace-based debugging）
doc: gem5 文档
parent: debugging
permalink: /documentation/general_docs/debugging_and_testing/debugging/trace_based_debugging
author: Bobby R. Bruce
---

# 基于跟踪的调试（trace-based debugging）

## 简介

最简单的调试方法是让 gem5 打印出它正在做什么的跟踪（trace）。模拟器（simulator）中包含许多 DPRINTF 语句，用于打印描述潜在有趣事件的跟踪消息。
每个 DPRINTF 都关联一个
调试标志（例如 `Bus`、`Cache`、`Ethernet`、`Disk` 等）。要打开
某个标志的消息，使用 `--debug-flags` 命令行参数。
可以通过给出字符串列表来指定多个标志，例如：

```
build/<ISA>/gem5.opt --debug-flags=Bus,Cache configs/examples/fs.py
```

这会打开一组与指令执行相关的调试标志，但不包含
Tick（时序）信息。当你想比较两次运行中相同指令以不同速率执行的情况时，
这很有用。

注意 gem5.fast 二进制程序不支持跟踪；它比 gem5.opt 更快的原因之一，
就是 DPRINTF 代码被编译掉了。

`--debug-flags` 命令行选项应放在 gem5 可执行文件之后、
但在模拟脚本之前。这是因为调试标志由
gem5 本身处理，而命令行选项位于模拟脚本之前还是之后，
决定它们是给 gem5 的还是给脚本的。

```
Debugging Options
-----------------
--debug-break=TIME[,TIME]
                        Tick to create a breakpoint
--debug-help            Print help on debug flags
--debug-flags=FLAG[,FLAG]
                        Sets the flags for debug output (-FLAG disables a
                        flag)
--debug-start=TIME      Start debug output at TIME (must be in ticks)
--debug-file=FILE       Sets the output file for debug [Default: cout]
--debug-ignore=EXPR     Ignore EXPR sim objects
```

完整的调试/跟踪标志列表可以通过带
`--debug-help` 选项运行 gem5 查看。

如果你发现感兴趣的事件没有被跟踪，可以自行添加
DPRINTF。你只需把 `DebugFlag()`
命令添加到任意 SConscript 文件（最好是最接近你使用该新标志位置的那个）即可添加新的调试标志。如果你在某个 C++ 源文件中使用了某个调试标志，
就需要在该文件中包含头文件 `debug/<name of debug flag>.hh`。

对于更复杂的缺陷，跟踪可以用于识别
模拟中需要更深入调查的位置。`--debug-break`
选项让你可以在调试器下重新运行模拟，并在跟踪所标识的
特定 tick 处停止。你也可以从调试器内部调度断点
以及启用或禁用调试标志。更多信息见
基于调试器的调试页面。

### Exec 调试标志

`Exec` 复合调试标志非常有用，因为它会打开 gem5 中的指令
跟踪。它让模拟器在每条指令执行完成时打印其反汇编版本，
同时打印其他有用信息，例如
时间、pc、如果是内存指令则打印地址等。通过这些单项信息可以由 Exec 所控制的基础调试标志分别开启和关闭。例如，你可以通过关闭
ExecSymbol 标志来禁用用函数符号名替代绝对 PC 地址（如果有的话）的做法
（例如 `--debug-flags=Exec,-ExecSymbol`）。

如果某个看似无害的改动导致 gem5 不再正确工作，
你可以用 `src/util` 目录中的 tracediff 脚本比较改动前后的跟踪输出。
该脚本中的注释说明了如何使用它。

### 减小跟踪文件大小

跟踪文件可能很快变得非常大，但它们压缩效果也很好
（例如约 90%）。如果你希望让 gem5 输出压缩后的跟踪，只需
在输出文件名后加上 `.gz` 扩展名。例如
`--debug-file=trace.out` 会像平常一样生成未压缩文件，而
`--debug-file=trace.out.gz` 会生成 gzip 压缩文件。你可以用
zcat 程序和管道来处理输出。vim 编辑器也能在内存中
解压 gzip 压缩文件。

## tracediff 与 rundiff 工具

`tracediff` 和 `rundiff` 工具可以简单地对两股 gem5
跟踪数据做差分，以找出任何差异。它对于调试回归测试为何失败、查明你的小改动为何似乎导致了
某些无关的执行问题，或比较 CPU 模型的执行，都非常方便。

这两个工具都在 `util` 目录中。`rundiff` 是一个简单的
类 diff 程序。与常规 diff 不同，该脚本在比较输入之前不会读取
全部输入，因此可以用于从其他程序（例如 gem5 跟踪）通过管道传入的很长的输出。`tracediff` 是
`rundiff` 的前端，提供了一种简便方式来运行两份相似的 gem5 并对其输出做差分。它接受一条内嵌
备选值的公共 gem5 命令行，并在不同的子目录中执行两条备选命令，输出通过管道送入 rundiff。

脚本参数的处理方式统一如下：

* 如果参数不包含 '|' 字符，它会被追加到两条
  命令行上。
* 如果参数中包含 '|" 字符，'|' 两侧的文本
  会分别被追加到对应的命令行上。注意你必须给该
  参数加引号，或用反斜杠转义 '|'，以免 shell 认为你在
  使用管道，或在它周围加上引号。
* 含 '#' 字符的参数会在这些字符处被切分，把备选项（'|'）
  作为独立词处理，然后再粘回单个
  参数（去掉 '#'）。（灵感大致来自 C 预处理器的 '##' 记号
  粘贴运算符。）

换句话说，这些参数看起来应像你想运行的命令行，
只是用 '|' 列出两次运行中你希望有所不同的那些部分的备选值。

例如：

```
 % tracediff gem5.opt --opt1 '--opt2|--opt3' --opt4
# would compare these two runs:
gem5.opt --opt1 --opt2 --opt4
gem5.opt --opt1 --opt3 --opt4

% tracediff 'path1|path2#/m5.opt' --opt1 --opt2
# would compare these two runs:
path1/gem5.opt --opt1 --opt2
path2/gem5.opt --opt1 --opt2
```

如果你只想给其中一次运行添加参数，只需写一个 '|'，并让文本只出现在
一侧（`--onlyOn1|`）。也可以对多个参数一起这样做
（`|-a -b -c` 只给第二次运行添加三个参数）。

tracediff 的 `-n` 参数让你可以预览生成的两条命令行
而不实际运行它们。

要让 tracediff 有用，必须启用一些跟踪标志。与 tracediff 配合使用最常见的
跟踪标志是 `--debug-flags=Exec,-ExecTicks`，它会
从每条跟踪中移除时间戳，从而适合在存在轻微
时序差异时做差分。

当某个 CPU 模型失败而另一个没有失败时，tracediff 也可用于比较它们。
在这种情况下，最好在问题
发生之前创建检查点（只要创建一批检查点、找出
会失败的那个即可）。如果故障发生在内核代码中，使用
`-ExecUser` 调试标志；反之，如果发生在用户代码中，则试用
`-ExecKernel` 调试标志，以在跟踪中隔离出用户代码。然后你就可以
比较跟踪，看执行在何处出现分歧。

### 跨机器比较跟踪

有时 gem5 的执行在不同环境之间会出现难以解释的差异，
而你想用 rundiff 帮助定位它们的分歧点。与其
尝试在同一台机器上复现那些环境，你可以把 netcat
与 rundiff 结合使用，比较运行在不同系统上、通过网络连接的 gem5 实例的跟踪。

首先，在一台机器上启动 rundiff，配置为把本地 gem5 实例的跟踪
输出与 netcat "服务器"的输出做比较。
由于网络很可能成为瓶颈，我们会压缩跨 netcat 传输的跟踪，
这意味着需要在数据到达时解压它。例如（随意选用端口号 33335）：

```
util/rundiff 'gem5.opt --debug-flag=Exec <gem5 args> |' 'nc -d -l 33335 | gunzip -c |' >& tracediff.out &
```

现在到第二台机器上，在那里启动一份 gem5，并把其
压缩后的跟踪输出发送到第一台机器上运行的 netcat 实例。
例如：

```
gem5.opt --debug-flag=Exec <gem5 args> |& gzip -c |& nc <hostname> 33335
```

## 内部 Exec 跟踪实现（InstTracer）

上面的“基于跟踪的调试”一节介绍了如何使用 `Exec`
跟踪标志在每条指令完成时打印其信息。该
功能实际上由一个 `InstTracer` 对象实现，它在指令执行时收集
指令信息。这些对象可以替换，不同的对象可以对所收集的信息
做不同的事情。例如，`IntelTrace` 对象会以另一种格式打印跟踪，
该格式与某个外部工具兼容。这些对象
也可以做的不只是打印跟踪。`NativeTrace` 对象会逐条指令地通过 socket 把体系结构状态信息发送给
statetrace 工具（下文介绍）以校验执行。`InstTracer` 对象
是 `SimObject`，被赋给每个 CPU 的 `tracer` 参数。如果你
想安装不同的 tracer，只需把它赋给所关注 CPU 上的该参数即可。

在编写自己的 `InstTracer` 时，你至少要写两个不同的
类：一个继承自 `InstTracer`，一个继承自
`InstRecord`。`InstTracer` 类的主要职责是生成
与特定指令关联的 `InstRecord` 对象。通过
继承 `InstTracer`，你将能够返回自己专门的
`InstRecord` 版本，而真正完成大部分工作的正是该类。

`InstRecord` 类有许多字段，用于保存有关某条指令
历史的信息。例如，`InstRecord` 记录指令的
PC、如果访问内存则记录所用地址、它产生的 "data" 值
（不处理多个数据值）等。`InstRecord` 函数
还有一个指向 `ThreadContext` 的指针，可用于读出
体系结构状态。当指令执行完成时，会调用
`InstRecord` 的 `dump()` 虚函数来处理该记录。对于
默认的 `InstTracer`，这里就是打印指令的汇编语言
形式等内容的地方，也就是你开启 `Exec` 时看到的输出。对于
`NativeTrace`，这里则是收集体系结构状态以发送给
statetrace 的地方。

### 使用第三方反汇编器反汇编指令

大多数 gem5 tracer（继承上面提到的 InstTracer）会打印/导出
动态指令流以及其他信息（例如目标
寄存器值）。反汇编是通过查询被跟踪的指令
（StaticInst）即时生成的。
每个 StaticInst 都应定义一个 generateDisassembly 方法，它返回
指令助记符（操作码 + 操作数列表）字符串。

自 gem5 v23.1 起，可以为每个 InstTracer 挂接不同的反汇编器。
反汇编器必须实现 src/sim/insttracer.hh 中定义的
InstDisassembler 接口。

默认会使用原生反汇编器（依赖 generateDisassembly）。
要用自定义反汇编器（假设名为 MyDisassembler）替换它，
只需在配置文件中加入：

```
cpu.tracer.disassembler = MyDisassembler()
```

#### Capstone 反汇编器

gem5 v23.1 引入了[与 Capstone 反汇编器的集成](https://github.com/gem5/gem5/pull/494)。
[Capstone](http://www.capstone-engine.org/) 是一个开源反汇编器，已被
其他项目（例如 QEMU）使用。

要用 capstone 支持编译 gem5，必须先安装 capstone。
然后需要在配置脚本中实例化 capstone 反汇编器。在撰写本文时，
只实现了 Arm 版本的反汇编器。
因此需要加入脚本的行应为（假设是 Arm
模拟）：

```
cpu.tracer.disassembler = ArmCapstoneDisassembler()
```

## 与真实机器比较跟踪

statetrace 工具与 gem5 并行运行，把工作负载（workload）在
真实机器上的执行与在 gem5 中的执行进行比较。在模拟器和真实系统中，
工作负载被允许一次执行一条指令。每条
指令之后，收集并比较体系结构状态，报告任何差异。
让它正确设置并产出有用的结果可能有些棘手
（下文有描述），但它是一个极其宝贵的调试工具，因为它往往能
快速精确定位问题究竟来自哪里，很可能为每个缺陷省下
许多小时痛苦的调试。

### 原生跟踪（Native Trace）

在 gem5 中，需要把 NativeTrace `InstTracer` 对象（上文已描述）安装到
将要运行所关注工作负载的 CPU 上。执行
开始时，该 tracer 会等待 statetrace 工具连接到它。
随后，每条指令执行之后，它使用 `InstRecord` 对象中的 `ThreadContext` 指针
从当前正在运行的进程收集体系结构状态。它还会读取 statetrace 通过二者建立的连接收集到的
体系结构状态。两种状态版本会被
比较，报告任何有意义的差异。状态的具体构成
以及应如何比较，与指令集架构（ISA）高度相关，因此每种指令集架构
都定义了自己的 NativeTrace 版本。这些专门的类可以处理
寄存器可能变为未定义时的预期差异，或者
执行因某种原因跳步的情况。

### statetrace 工具

statetrace 工具位于 util 目录，负责
在真实机器上运行工作负载。它使用 Linux 内核提供的 ptrace 机制
对目标进程单步执行并访问其状态。
它使用 scons，但独立于 gem5 其余部分所用的 scons。要
构建适合特定指令集架构的 statetrace，使用
`build/${ARCH}/statetrace` 目标，其中 `${ARCH}` 替换为所关注的指令集架构。
目前 `${ARCH}` 可识别的取值为 `amd64`、`arm`、`i686`
和 `sparc`。你可以用 CXX scons
参数覆盖任何指令集架构所用的编译器，用 `${ARCH}CXX` 覆盖特定指令集架构所用的编译器。例如，
要构建 arm 版本的 statetrace，可以运行：

```
cd util/statetrace
scons ARMCXX=arm-softfloat-linux-gnueabi-g++ build/arm/statetrace
```

statetrace 接受四个标志：`-h` 打印帮助，`--host` 指定 gem5
监听的 ip 和端口，`-i` 打印初始栈帧上的内容，
`-nt` 禁用跟踪。`-nt` 通常与 `-i` 搭配使用，以在不运行进程的情况下获取
其初始栈的信息。命令行选项的结束以两个短横线标记。接着放入你
希望 statetrace 运行的命令行。

程序名和参数的确切文本很重要，因为它们会被
传到进程的栈上。较长的值在栈上占用更多空间，从而把其他项挤到
不同地址，使 statetrace 塞满大量不重要的差异。例如，如果你需要在 gem5 的子目录中运行
位于你主目录下的程序，而你运行了这个
命令：

```
statetrace -- ~/gem5/my_benchmark arg1 arg2
```

你还必须在 gem5 中把 arg0 覆盖为 `~/gem5/my_benchmark`。

### 调优

statetrace 是一个很敏感的系统，被模拟执行与真实执行之间的任何细微差异都可能产生
大量虚假差异。为了从 statetrace 获得有用信息，你需要
调整真实系统和 gem5，使一切都完全对齐。我通常
创建一个补丁，包含我为 statetrace 对 gem5 所做的所有修改。这样我就能在
发现问题并修复时轻松移除或重新应用它们。Mercurial 队列很适合
管理该补丁以及我的修复补丁。以下是你可能需要
修正的差异的不完整列表。

地址随机化：为提高安全性，Linux 会随机化进程的地址
空间，移动其栈和堆区域。这让
攻击者更难预测内存的样子，但也彻底破坏了 statetrace。要禁用它，把 `0` 
写入 `/proc/sys/kernel/randomize_va_space`。你几乎肯定需要 root
权限才能这样做。

argv 值：务必确保 gem5 中与真实系统上程序的每个参数文本_完全_相同。这包括 arg0，即程序名。

文件块大小：Glibc 使用与文件关联的块大小来决定如何
缓冲它。不同的行为会打乱执行并导致
statetrace 无法工作。你可以修改 gem5 在
`src/sim/syscall_emul.hh` 中 `convertStatBuf` 和 `convertStat64Buf` 函数里报告的块大小。

初始栈内容：取决于你的 Linux 版本，初始栈的内容
可能不同。你可以使用 `-i` 和 `-nt` 选项打印
真实机器上初始栈的内容。statetrace 会尝试
解释初始栈，以便你更容易看清其中的内容。你需要
调整 gem5 建立栈的方式，使其与你的真实系统匹配。这段代码
通常位于相应 arch 目录下名为 `process.cc` 的文件中。
gem5 的代码经过精心构造，尽可能与 Linux 一样地建立栈，但底层机制可能会变化。
此外，Linux 会在初始栈上放置一组辅助向量。它们是
类型、值对，让内核能在进程启动时向其提供额外信息。Linux 时不时会引入新类型的
辅助向量并加入栈中。你可能需要深入 Linux
源码并仿真任何新增条目。

### 注意事项

由于 statetrace 对执行的任何变化都非常敏感，它不能
用于行为不太可预测的程序。例如，如果某个程序从 `/dev/random` 读入一个随机值并在计算中使用它
（更糟的是在控制流中使用），那么该程序就不能使用。不那么
明显的是，如果程序依赖不可预测的系统时间，它
也不能使用。一般来说，许多基准测试（benchmark）都力求高度
确定性，以便生成可复现的数据。这使它们能与 statetrace 良好配合。

statetrace 不能在操作系统层面使用，至少有两个主要原因。
第一，目前没有、在可预见的将来也不会有用于对操作系统单步执行的系统
被实现。第二，真实操作系统不是确定性的。来自硬件设备的中断
几乎肯定会在不可预测的时刻到来，某些设备会返回
不可预测的数据，而 gem5 在固件和其他实现细节不再被抽象掉的那个层面
与系统行为完全一致的可能性要低得多。其次，在
系统层面相关的状态量通常比用户层面更大，在像 `x86` 这样复杂的
指令集架构中尤其如此。收集、比较和传输所有这些额外状态
会显著影响性能。

并非所有 ptrace 的实现都能真正正常工作。例如，我上次把 statetrace 与 `ARM` 一起使用时，
某些函数会调用内核建立的一块内存区域，其中包含内核特有的
各种操作实现。Ptrace 依赖软件断点，其工作方式是把程序中的下一条指令
替换为会触发陷阱的指令。由于
那块内存区域真正属于内核，ptrace 无法修改它
来安装断点。该进程“逃出”了单步执行，很快运行到结束，
使 gem5 一直等待一个永远不会到来的更新。

statetrace 无法跟踪对内存的修改。由于内存非常大，
而且没有便利的方式检测对它的修改，statetrace 只
跟踪基于寄存器的体系结构状态。如果一条指令正确地改变了寄存器，
却把错误的值存到内存和/或错误的地址，这个问题可能要到很多条指令之后才会被检测到。
幸运的是，这类错误只是例外。

要把执行与真实机器做比较，理想情况下你需要有一台真实的机器
可用。不过，在像 qemu 这样的模拟器里运行 statetrace 仍然完全可行。
这会稍慢一些，而且是把执行与模拟器而非真实硬件做比较，但它仍能帮助识别
缺陷。

### 指令集架构支持

目前 `SPARC`、`ARM` 和 `x86` 支持状态比较。ARM 的支持目前
最为成熟：它只通过连接发送存在差异的状态，
从而提升性能，并且只在差异开始或停止时打印，从而减少输出并提高可读性。这些特性计划
移植到其他指令集架构。希望那段代码能被抽出来放入
基础 `NativeTrace` 类，以便所有指令集架构都能方便地使用。

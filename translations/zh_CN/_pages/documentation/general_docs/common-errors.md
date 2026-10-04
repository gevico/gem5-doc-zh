---
layout: documentation
title: gem5 中常见的错误
doc: gem5 文档
parent: common-errors
permalink: /documentation/general_docs/common-errors/
---

以下是用户在使用 gem5 时常遇到的一些问题，以及如何修复它们的信息。

## 构建错误

如果你的 gem5 编译失败并出现以下信息：

```txt
[    LINK]  -> ALL/gem5.opt
collect2: fatal error: ld terminated with signal 9 [Killed]
compilation terminated.
scons: *** [build/ALL/gem5.opt] Error 1
scons: building terminated because of errors.
```

这表示你的机器在尝试构建
gem5 时内存耗尽，并因此杀掉了该进程。
如果出现这种情况，请尝试用更少的线程编译 gem5，因为这样会消耗
更少的内存。
如果系统中有其他进程占用大量内存，请尝试在内存更充裕时
构建 gem5。

## 段错误

段错误（segfault）可能发生，并在终端输出如下内容：

```bash
gem5 has encountered a segmentation fault!

— BEGIN LIBC BACKTRACE —
gem5/build/X86/gem5.opt(_Z15print_backtracev+0x2c)[0x55ead536d5bc]
gem5/build/X86/gem5.opt(+0x1030b8f)[0x55ead537fb8f]
/lib/x86_64-linux-gnu/libpthread.so.0(+0x128a0)[0x7f50fb78b8a0]
/lib/x86_64-linux-gnu/libgcc_s.so.1(_Unwind_Resume+0xcf)[0x7f50fa12ad9f]
gem5/build/X86/gem5.opt(_ZN6X86ISA7Decoder10decodeInstENS_11ExtMachInstE+0x5d19e)[0x55ead4e5ea8e]
gem5/build/X86/gem5.opt(_ZN6X86ISA7Decoder6decodeENS_11ExtMachInstEm+0x244)[0x55ead4dc74a4]
gem5/build/X86/gem5.opt(_ZN6X86ISA7Decoder6decodeERNS_7PCStateE+0x22b)[0x55ead4dc779b]
gem5/build/X86/gem5.opt(_ZN12DefaultFetchI9O3CPUImplE5fetchERb+0x942)[0x55ead54695f2]
gem5/build/X86/gem5.opt(_ZN12DefaultFetchI9O3CPUImplE4tickEv+0xd3)[0x55ead546a7b3]
gem5/build/X86/gem5.opt(_ZN9FullO3CPUI9O3CPUImplE4tickEv+0x12b)[0x55ead5448e3b]
gem5/build/X86/gem5.opt(_ZN10EventQueue10serviceOneEv+0xa5)[0x55ead5375a95]
gem5/build/X86/gem5.opt(_Z9doSimLoopP10EventQueue+0x87)[0x55ead539a7b7]
gem5/build/X86/gem5.opt(_Z8simulatem+0xcba)[0x55ead539b80a]
gem5/build/X86/gem5.opt(+0x11d3431)[0x55ead5522431]
gem5/build/X86/gem5.opt(+0x6df0b4)[0x55ead4a2e0b4]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalFrameEx+0x64d7)[0x7f50fba38c47]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalCodeEx+0x7d8)[0x7f50fbb77908]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalFrameEx+0x5bf6)[0x7f50fba38366]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalCodeEx+0x7d8)[0x7f50fbb77908]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalCode+0x19)[0x7f50fba325d9]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalFrameEx+0x6ac0)[0x7f50fba39230]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalCodeEx+0x7d8)[0x7f50fbb77908]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalFrameEx+0x5bf6)[0x7f50fba38366]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalCodeEx+0x7d8)[0x7f50fbb77908]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyEval_EvalCode+0x19)[0x7f50fba325d9]
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0(PyRun_StringFlags+0x76)[0x7f50fbae26f6]
gem5/build/X86/gem5.opt(_Z6m5MainiPPc+0x83)[0x55ead537e823]
gem5/build/X86/gem5.opt(main+0x38)[0x55ead48d5068]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0xe7)[0x7f50f9d4ab97]
gem5/build/X86/gem5.opt(_start+0x2a)[0x55ead48fd37a]
— END LIBC BACKTRACE —
```

需要注意的是，要确认自己遇到的是段错误，请向上滚动到回溯输出之上，确认已输出 `gem5 has encountered a segmentation fault!` 这一行。
这类错误的原因通常是你的 C++ 文件中存在错误，导致访问了错误的地址。
在 gem5 中调试段错误的最好方式是使用 gdb，我们[在此处](https://www.gem5.org/documentation/general_docs/debugging_and_testing/debugging/debugger_based_debugging)提供了相关文档。

## Fatal

致命错误（fatal）通常发生在模拟配置无效、gem5 模拟器（simulator）无法处理时。
致命错误之前会先输出该错误来自哪个文件，这通常是判断去哪里查找问题根源的良好线索。
例如，在下面的错误中，`gem5/src/cpu/base.cc` 就是调试该错误的好起点。

```bash
build/ALL/cpu/base.cc:186: fatal: Number of processes (cpu.workload) (0) assigned to the CPU does not equal number of threads (1).
```

这类错误涵盖的情况包括文件类型错误、传给 gem5 的值无效，或者端口未连接等等，仅举几例。
它应该能让你对当前问题有更多了解；但如果信息仍不够，使用 gem5 中的一些[调试技术](https://www.gem5.org/documentation/general_docs/debugging_and_testing/debugging/trace_based_debugging)（例如 gdb 或调试标志）可能会有所帮助。


## Panic

如果遇到 panic 错误，通常表明 gem5 自身出了问题。
gem5 中较常见的 panic 错误包括使用了无法识别的值，或者使用了尚未实现的功能。
要调试这类错误，你可以先查看生成该错误的文件，
终端中 panic 错误之前会指明该文件。
例如，在下面的错误中，最好从 `gem5/src/sim/mem_pool.cc`
开始查看：

```bash
build/ARM/sim/mem_pool.cc:45: panic: assert(_totalPages > 0) failed
```

这应该能让你对当前问题有更多了解；不过与上面的致命错误类似，
如果信息仍不够，使用 gem5 中的一些[调试技术](https://www.gem5.org/documentation/general_docs/debugging_and_testing/debugging/trace_based_debugging)可能会有所帮助。

## Python 脚本错误

对于任何类型的 Python 错误（例如 AttributeError 或 OSError），最好从错误信息下方开始查看，那里应该能看到跟踪输出。
第一个文件和行号应指明错误发生的位置。
例如，在下面的错误中，你应先查看 `build/ARM/python/m5/SimObject.py(908)`；如果信息仍不够，再看 `configs/example/gem5_library/arm-ubuntu-run.py(70)`。

```bash
AttributeError: Class PrivateL1PrivateL2CacheHierarchy has no parameter l1_size

At:
  build/ARM/python/m5/SimObject.py(908): __setattr__
  configs/example/gem5_library/arm-ubuntu-run.py(70): <module>
  build/ARM/python/m5/main.py(597): main
```

同样，如果你收到如下所示的 traceback 错误，也需要查看输出的最底部，以了解应从何处开始调试。在这个 IOError 示例中，你应首先查看 `gem5/configs/common/SysPaths.py`

```bash
Traceback (most recent call last):
File "<string>", line 1, in <module>
File "/opt/gem5/src/python/m5/main.py", line 389, in main
exec filecode in scope
File "./configs/example/fs.py", line 327, in <module>
test_sys = build_test_system(np)
File "./configs/example/fs.py", line 96, in build_test_system
options.ruby, cmdline=cmdline)
File "/opt/gem5/configs/common/FSConfig.py", line 580, in
makeLinuxX86System
makeX86System(mem_mode, numCPUs, mdesc, self, Ruby)
File "/opt/gem5/configs/common/FSConfig.py", line 506, in makeX86System
disk2.childImage(disk('linux-bigswap2.img'))
File "/opt/gem5/configs/common/SysPaths.py", line 45, in disk
return searchpath(disk.path, filename)
File "/opt/gem5/configs/common/SysPaths.py", line 41, in searchpath
raise IOError, "Can't find file '%s' on path." % filename
IOError: Can't find file 'linux-bigswap2.img' on path.
```

查看该文件应该能提供更多有助于调试的信息；不过如果这还不够，你可以查看[此处](https://www.gem5.org/documentation/general_docs/debugging_and_testing/debugging/trace_based_debugging)，启用基于跟踪（trace）的调试以获取更多信息。

## PreCommit

如果你在向 develop 分支推送代码时遇到错误，一个可能的原因是你没有通过 gem5 在提交任何改动前所要求的 precommit 检查。
如果你在 Gerrit 中看到 verified 检查上有以下错误，可以查看测试输出的日志。

```bash
Kokoro presubmit build finished with status: FAILURE
```

如果这些日志中包含类似下面的行，你需要确认你的改动符合 gem5 的编码风格。

```bash
trim trailing whitespace.................................................Failed
```

为了确保你的代码通过这些检查，你应当安装并针对改动运行 precommit。
可以用下面的命令安装。

```bash
pip install pre-commit
pre-commit install
```

另外，你也可以改为运行 `util/pre-commit-install.sh` 来完成设置。
此后，只要你使用 `git commit`，pre-commit 就会运行。
不过，如果你已经提交了这些文件，也可以手动检查 pre-commit 是否仍能通过：用 `pre-commit run --files <files to format>` 检查特定文件，用 `pre-commit run --all-files` 测试整个目录，或用 `pre-commit run <hook_id>` 运行单个钩子。
运行这些命令时，pre-commit 既会检测任何风格问题，也会自动为你重新格式化文件。

## Change-ID

如果你在让持续集成测试于 GitHub 上通过时遇到问题，可能是你忘记在提交信息中添加 Change-Id。
虽然我们已经从 Gerrit 迁移出来，但仍然要求添加 Change-Id。
要修正提交并让我们的所有检查通过，你必须从 Gerrit 安装提交信息钩子。
可以用下面的命令安装并更新你的提交。

```bash
n f=.git/hooks/commit-msg ; mkdir -p  ;  curl -Lo  https://gerrit-review.googlesource.com/tools/hooks/commit-msg ; chmod +x
git commit --amend --no-edit
```

如果你想了解提交信息钩子的更多信息，请阅读[此处](https://gerrit-review.googlesource.com/Documentation/cmd-hook-commit-msg.html)；如果想进一步了解 Change-Id，请看[此处](https://gerrit-review.googlesource.com/Documentation/user-changeid.html)

## 其他问题

如果你在使用 gem5 时仍持续遇到错误，欢迎[寻求帮助](/ask-a-question)。
此外，如果其他渠道未能涵盖你所需的全部信息，你可以在[此处](https://www.gem5.org/documentation/reporting_problems/)找到关于如何报告可能需要修复的错误的信息。

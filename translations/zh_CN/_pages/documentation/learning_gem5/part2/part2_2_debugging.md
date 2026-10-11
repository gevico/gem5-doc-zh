---
layout: documentation
title: "调试 gem5"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/debugging/
author: Jason Lowe-Power
---

调试 gem5
==============

[上一章]({{ site.baseurl }}/documentation/learning_gem5/part2/helloobject/)创建了一个简单 SimObject。本章将把直接写入 `stdout` 的语句替换为 gem5 的调试输出。

gem5 通过*调试标志（debug flag）*支持类似 `printf` 的跟踪（trace）和调试。每个组件可以包含大量调试输出语句，而无需同时启用全部输出。运行时，在命令行中选择需要的标志即可。

使用调试标志（debug flag）
-----------------

例如，运行第一部分的 `simple.py` 并启用 `DRAM`，可得到下面的输出。注意，这会产生*大量*控制台信息，原文示例约为 7 MB。

```
    build/ALL/gem5.opt --debug-flags=DRAM configs/learning_gem5/part1/simple.py | head -n 50
```

    gem5 Simulator System.  http://gem5.org
    DRAM device capacity (gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  3 2017 16:03:38
    gem5 started Jan  3 2017 16:09:53
    gem5 executing on chinook, pid 19223
    command line: build/X86/gem5.opt --debug-flags=DRAM configs/learning_gem5/part1/simple.py

    Global frequency set at 1000000000000 ticks per second
          0: system.mem_ctrl: Memory capacity 536870912 (536870912) bytes
          0: system.mem_ctrl: Row buffer size 8192 bytes with 128 columns per row buffer
          0: system.remote_gdb.listener: listening for remote gdb #0 on port 7000
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
          0: system.mem_ctrl: recvTimingReq: request ReadReq addr 400 size 8
          0: system.mem_ctrl: Read queue limit 32, current size 0, entries needed 1
          0: system.mem_ctrl: Address: 400 Rank 0 Bank 0 Row 0
          0: system.mem_ctrl: Read queue limit 32, current size 0, entries needed 1
          0: system.mem_ctrl: Adding to read queue
          0: system.mem_ctrl: Request scheduled immediately
          0: system.mem_ctrl: Single request, going to a free rank
          0: system.mem_ctrl: Timing access to addr 400, rank/bank/row 0 0 0
          0: system.mem_ctrl: Activate at tick 0
          0: system.mem_ctrl: Activate bank 0, rank 0 at tick 0, now got 1 active
          0: system.mem_ctrl: Access to 400, ready at 46250 bus busy until 46250.
      46250: system.mem_ctrl: processRespondEvent(): Some req has reached its readyTime
      46250: system.mem_ctrl: number of read entries for rank 0 is 0
      46250: system.mem_ctrl: Responding to Address 400..   46250: system.mem_ctrl: Done
      77000: system.mem_ctrl: recvTimingReq: request ReadReq addr 400 size 8
      77000: system.mem_ctrl: Read queue limit 32, current size 0, entries needed 1
      77000: system.mem_ctrl: Address: 400 Rank 0 Bank 0 Row 0
      77000: system.mem_ctrl: Read queue limit 32, current size 0, entries needed 1
      77000: system.mem_ctrl: Adding to read queue
      77000: system.mem_ctrl: Request scheduled immediately
      77000: system.mem_ctrl: Single request, going to a free rank
      77000: system.mem_ctrl: Timing access to addr 400, rank/bank/row 0 0 0
      77000: system.mem_ctrl: Access to 400, ready at 101750 bus busy until 101750.
     101750: system.mem_ctrl: processRespondEvent(): Some req has reached its readyTime
     101750: system.mem_ctrl: number of read entries for rank 0 is 0
     101750: system.mem_ctrl: Responding to Address 400..  101750: system.mem_ctrl: Done
     132000: system.mem_ctrl: recvTimingReq: request ReadReq addr 400 size 8
     132000: system.mem_ctrl: Read queue limit 32, current size 0, entries needed 1
     132000: system.mem_ctrl: Address: 400 Rank 0 Bank 0 Row 0
     132000: system.mem_ctrl: Read queue limit 32, current size 0, entries needed 1
     132000: system.mem_ctrl: Adding to read queue
     132000: system.mem_ctrl: Request scheduled immediately
     132000: system.mem_ctrl: Single request, going to a free rank
     132000: system.mem_ctrl: Timing access to addr 400, rank/bank/row 0 0 0
     132000: system.mem_ctrl: Access to 400, ready at 156750 bus busy until 156750.
     156750: system.mem_ctrl: processRespondEvent(): Some req has reached its readyTime
     156750: system.mem_ctrl: number of read entries for rank 0 is 0

如果希望根据 CPU 正在执行的具体指令进行调试，可以使用 `Exec`，它会显示被模拟 CPU 执行每条指令的详细信息。

```
    build/ALL/gem5.opt --debug-flags=Exec configs/learning_gem5/part1/simple.py | head -n 50
```

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  3 2017 16:03:38
    gem5 started Jan  3 2017 16:11:47
    gem5 executing on chinook, pid 19234
    command line: build/X86/gem5.opt --debug-flags=Exec configs/learning_gem5/part1/simple.py

    Global frequency set at 1000000000000 ticks per second
          0: system.remote_gdb.listener: listening for remote gdb #0 on port 7000
    warn: ClockedObject: More than one power state change request encountered within the same simulation tick
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
      77000: system.cpu T0 : @_start    : xor   rbp, rbp
      77000: system.cpu T0 : @_start.0  :   XOR_R_R : xor   rbp, rbp, rbp : IntAlu :  D=0x0000000000000000
     132000: system.cpu T0 : @_start+3    : mov r9, rdx
     132000: system.cpu T0 : @_start+3.0  :   MOV_R_R : mov   r9, r9, rdx : IntAlu :  D=0x0000000000000000
     187000: system.cpu T0 : @_start+6    : pop rsi
     187000: system.cpu T0 : @_start+6.0  :   POP_R : ld   t1, SS:[rsp] : MemRead :  D=0x0000000000000001 A=0x7fffffffee30
     250000: system.cpu T0 : @_start+6.1  :   POP_R : addi   rsp, rsp, 0x8 : IntAlu :  D=0x00007fffffffee38
     250000: system.cpu T0 : @_start+6.2  :   POP_R : mov   rsi, rsi, t1 : IntAlu :  D=0x0000000000000001
     360000: system.cpu T0 : @_start+7    : mov rdx, rsp
     360000: system.cpu T0 : @_start+7.0  :   MOV_R_R : mov   rdx, rdx, rsp : IntAlu :  D=0x00007fffffffee38
     415000: system.cpu T0 : @_start+10    : and    rax, 0xfffffffffffffff0
     415000: system.cpu T0 : @_start+10.0  :   AND_R_I : limm   t1, 0xfffffffffffffff0 : IntAlu :  D=0xfffffffffffffff0
     415000: system.cpu T0 : @_start+10.1  :   AND_R_I : and   rsp, rsp, t1 : IntAlu :  D=0x0000000000000000
     470000: system.cpu T0 : @_start+14    : push   rax
     470000: system.cpu T0 : @_start+14.0  :   PUSH_R : st   rax, SS:[rsp + 0xfffffffffffffff8] : MemWrite :  D=0x0000000000000000 A=0x7fffffffee28
     491000: system.cpu T0 : @_start+14.1  :   PUSH_R : subi   rsp, rsp, 0x8 : IntAlu :  D=0x00007fffffffee28
     546000: system.cpu T0 : @_start+15    : push   rsp
     546000: system.cpu T0 : @_start+15.0  :   PUSH_R : st   rsp, SS:[rsp + 0xfffffffffffffff8] : MemWrite :  D=0x00007fffffffee28 A=0x7fffffffee20
     567000: system.cpu T0 : @_start+15.1  :   PUSH_R : subi   rsp, rsp, 0x8 : IntAlu :  D=0x00007fffffffee20
     622000: system.cpu T0 : @_start+16    : mov    r15, 0x40a060
     622000: system.cpu T0 : @_start+16.0  :   MOV_R_I : limm   r8, 0x40a060 : IntAlu :  D=0x000000000040a060
     732000: system.cpu T0 : @_start+23    : mov    rdi, 0x409ff0
     732000: system.cpu T0 : @_start+23.0  :   MOV_R_I : limm   rcx, 0x409ff0 : IntAlu :  D=0x0000000000409ff0
     842000: system.cpu T0 : @_start+30    : mov    rdi, 0x400274
     842000: system.cpu T0 : @_start+30.0  :   MOV_R_I : limm   rdi, 0x400274 : IntAlu :  D=0x0000000000400274
     952000: system.cpu T0 : @_start+37    : call   0x9846
     952000: system.cpu T0 : @_start+37.0  :   CALL_NEAR_I : limm   t1, 0x9846 : IntAlu :  D=0x0000000000009846
     952000: system.cpu T0 : @_start+37.1  :   CALL_NEAR_I : rdip   t7, %ctrl153,  : IntAlu :  D=0x00000000004001ba
     952000: system.cpu T0 : @_start+37.2  :   CALL_NEAR_I : st   t7, SS:[rsp + 0xfffffffffffffff8] : MemWrite :  D=0x00000000004001ba A=0x7fffffffee18
     973000: system.cpu T0 : @_start+37.3  :   CALL_NEAR_I : subi   rsp, rsp, 0x8 : IntAlu :  D=0x00007fffffffee18
     973000: system.cpu T0 : @_start+37.4  :   CALL_NEAR_I : wrip   , t7, t1 : IntAlu :
    1042000: system.cpu T0 : @__libc_start_main    : push   r15
    1042000: system.cpu T0 : @__libc_start_main.0  :   PUSH_R : st   r15, SS:[rsp + 0xfffffffffffffff8] : MemWrite :  D=0x0000000000000000 A=0x7fffffffee10
    1063000: system.cpu T0 : @__libc_start_main.1  :   PUSH_R : subi   rsp, rsp, 0x8 : IntAlu :  D=0x00007fffffffee10
    1118000: system.cpu T0 : @__libc_start_main+2    : movsxd   rax, rsi
    1118000: system.cpu T0 : @__libc_start_main+2.0  :   MOVSXD_R_R : sexti   rax, rsi, 0x1f : IntAlu :  D=0x0000000000000001
    1173000: system.cpu T0 : @__libc_start_main+5    : mov  r15, r9
    1173000: system.cpu T0 : @__libc_start_main+5.0  :   MOV_R_R : mov   r15, r15, r9 : IntAlu :  D=0x0000000000000000
    1228000: system.cpu T0 : @__libc_start_main+8    : push r14

实际上，`Exec` 是多个调试标志（debug flag）的组合。使用 `--debug-help` 可以查看这种组合关系以及全部可用标志：

```
    build/ALL/gem5.opt --debug-help
```

    Base Flags:
        Activity: None
        AddrRanges: None
        Annotate: State machine annotation debugging
        AnnotateQ: State machine annotation queue debugging
        AnnotateVerbose: Dump all state machine annotation details
        BaseXBar: None
        Branch: None
        Bridge: None
        CCRegs: None
        CMOS: Accesses to CMOS devices
        Cache: None
        CacheComp: None
        CachePort: None
        CacheRepl: None
        CacheTags: None
        CacheVerbose: None
        Checker: None
        Checkpoint: None
        ClockDomain: None
    ...
    Compound Flags:
        All: Controls all debug flags. It should not be used within C++ code.
            All Base Flags
        AnnotateAll: All Annotation flags
            Annotate, AnnotateQ, AnnotateVerbose
        CacheAll: None
            Cache, CacheComp, CachePort, CacheRepl, CacheVerbose, HWPrefetch
        DiskImageAll: None
            DiskImageRead, DiskImageWrite
    ...
    XBar: None
        BaseXBar, CoherentXBar, NoncoherentXBar, SnoopFilter

添加新的调试标志（debug flag）
-----------------------

[上一章]({{ site.baseurl }}/documentation/learning_gem5/part2/helloobject/)使用 `std::cout` 打印信息。虽然 gem5 中可以使用普通 C/C++ I/O，但不推荐这样做。下面改用 gem5 自身的调试设施。

首先在包含 HelloObject 源码的目录所对应的 `SConscript` 中声明新标志：

```python
DebugFlag('HelloExample')
```

这会声明 `HelloExample`，供 SimObject 内的调试语句使用。

> **译注：** 原文写作 `src/learning_gem5/SConscript`，但上一章的示例位于 `src/learning_gem5/part2/`，本章末尾引用的文件也在该子目录中。按教程目录编写时，应修改 `src/learning_gem5/part2/SConscript`。

声明后，构建系统会在 `debug` 目录中自动生成头文件，文件名及大小写与标志名一致。使用该标志的源码必须包含这个生成的头文件。在 `hello_object.cc` 中添加：

```cpp
#include "base/trace.hh"
#include "debug/HelloExample.hh"
```

然后把 `std::cout` 替换为：

```cpp
DPRINTF(HelloExample, "Created the hello object\n");
```

`DPRINTF` 是一个 C++ 宏，第一个实参是在 `SConscript` 中声明的调试标志（debug flag）。由于已经声明了 `HelloExample`，现在可以使用它。其余部分为可变实参，与传给 `printf` 的内容相同。

重新编译，再启用 `HelloExample` 运行：

```
scons build/ALL/gem5.opt
build/ALL/gem5.opt --debug-flags=HelloExample configs/learning_gem5/part2/run_hello.py
```

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  4 2017 09:40:10
    gem5 started Jan  4 2017 09:41:01
    gem5 executing on chinook, pid 29078
    command line: build/X86/gem5.opt --debug-flags=HelloExample configs/learning_gem5/part2/run_hello.py

    Global frequency set at 1000000000000 ticks per second
          0: hello: Created the hello object
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Exiting @ tick 18446744073709551615 because simulate() limit reached

更新后的 [SConscript](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part2/SConscript) 与 [hello object 代码](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part2/hello_object.cc) 可通过对应链接查看。

调试输出
------------

每次实际执行 `DPRINTF` 时，默认向 `stdout` 输出三部分内容：首先是当前 tick，其次是调用它的 SimObject 名称，最后是格式字符串及实参生成的消息。

对象名称通常来自 Python 配置文件中的变量名，但准确地说，以 SimObject 的 `name()` 返回值为准。

可以用 `--debug-file` 控制输出位置。调试输出默认写到 `stdout`，也可以重定向到文件。文件路径相对于 gem5 的主输出目录，而非当前工作目录。

使用 DPRINTF 之外的函数
----------------------------------

`DPRINTF` 最常用，但 gem5 还提供了适用于特定情形的其他调试函数，详见 [reference documentation](http://doxygen.gem5.org/release/current/base_2trace_8hh.html)。

> 原文还提到不接受调试标志实参的输出宏。

> **译注：** 原文该段含有损坏的 `:cppDDUMP`、`:cppDPRINTF`、`:cppDPRINTFR` 引用，并未列清具体名称。当前接口中的 `DPRINTFN`、`DPRINTFNR` 不接受单独的调试标志，适合与相应的带标志宏对照；不要据此误认为 `DPRINTF` 本身不需要标志。

这些调试输出设施只在 `opt` 或 `debug` 构建中启用；其他构建模式将相应宏替换为空操作。因此，要使用调试标志（debug flag），必须运行 `gem5.opt` 或 `gem5.debug`。

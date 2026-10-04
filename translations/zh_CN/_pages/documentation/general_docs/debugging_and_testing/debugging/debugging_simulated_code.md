---
layout: documentation
title: 调试被模拟的代码
doc: gem5 文档
parent: debugging
permalink: /documentation/general_docs/debugging_and_testing/debugging/debugging_simulated_code
author: Bobby R. Bruce
---

# 调试被模拟的代码

gem5 内置支持 gdb 的远程调试器接口。如果你有兴趣监视
被模拟机器上代码的行为（FS 模式下是内核，SE 模式下是程序），
你可以在宿主机（host）平台上启动 gdb，让它与
被模拟的 gem5 系统通信，就像在与一台真实机器/进程通信一样（而且更好，
因为 gem5 的执行是确定性的，并且 gem5 的远程调试器接口保证不会扰动
被模拟系统上的执行）。

如果你模拟的系统使用的指令集架构（ISA）与你运行所在的宿主机不同，
就需要一个跨体系结构的 gdb；相关说明见下文。
如果你模拟的是宿主机的原生指令集架构，很可能直接使用
预装的原生 gdb 即可。

运行 gem5 时，每个 CPU 都会在一个 TCP
端口上监听远程调试连接。分配的第一个端口一般是 7000，如果该端口已被占用，
则会尝试下一个端口。

要附加远程调试器，需要有内核副本
和源码副本。此外，要查看内核的调用栈，你必须确保 Linux
在构建时启用了必要的调试配置参数。要运行
远程调试器，请执行以下操作（假设 host=localhost、port=7000）：

```
gdb-multiarch <path-to-linux>/vmlinux
GNU gdb (Ubuntu 8.2-0ubuntu1~18.04) 8.2
Copyright (C) 2018 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

(gdb) target remote <host>:<port>
```

gem5 模拟器（simulator）此时已经在运行，target remote 命令会连接到
这个已在运行的模拟器，并在执行过程中把它停下来。你可以
设置断点，并用调试器调试内核。也可以用
远程调试器调试控制台代码。其设置
类似，但具体做法留待日后补充。

如果你同时使用远程调试器和模拟器上的调试器，
可以通过在主调试器中执行 `call debugger()` 来触发远程调试器。
在此之前，你需要确定要调试哪个 CPU（CPU id），并把 `current_debugger` 设为该 `cpuid`。
如果只有一个 CPU，那就是 `cpuid 0`；但如果有多个
CPU，你需要把 CPU id 与远程 gdb 会话对应的端口号
对应起来。例如，根据下面 gem5 的示例输出，
为 cpu 3 调用内核调试器要求内核调试器监听在端口 7001。

```
%./build/<ISA>/gem5.debug configs/example/fs.py
...
making dual system
Global frequency set at 1000000000000 ticks per second
Listening for testsys connection on port 3456
Listening for drivesys connection on port 3457
0: testsys.remote_gdb.listener: listening for remote gdb #0 on port 7002
0: testsys.remote_gdb.listener: listening for remote gdb #1 on port 7003
0: testsys.remote_gdb.listener: listening for remote gdb #2 on port 7000
0: testsys.remote_gdb.listener: listening for remote gdb #3 on port 7001
0: drivesys.remote_gdb.listener: listening for remote gdb #4 on port 7004
0: drivesys.remote_gdb.listener: listening for remote gdb #5 on port 7005
0: drivesys.remote_gdb.listener: listening for remote gdb #6 on port 7006
0: drivesys.remote_gdb.listener: listening for remote gdb #7 on port 7007
```

## 获取跨体系结构的 gdb

要让远程调试器与 gem5 配合使用，最重要的一点是你要有
针对所模拟目标系统编译的 gdb。
推荐的做法是安装 gdb-multiarch 包，
它提供一个可用于多种指令集架构（arch）的 gdb 二进制程序

```
% sudo apt-get update -y
% sudo apt-get install -y gdb-multiarch
```

另一种做法是在
宿主机上编译非原生体系结构的 gdb。只需在编译 gdb 时
给 configure 加上 `--target=` 选项。你也可以从交叉编译器中获得预编译的
调试器。关于包含调试器的部分交叉编译器链接，参见 Download。

```
% wget http://ftp.gnu.org/gnu/gdb/<gdb-version>.tar.gz
% tar xfz <gdb-version>.tar.gz
% cd <gdb-version>
% ./configure --target=<isa>
<configure output....>
% make
<make output...this may take a while>
```

最终得到 gdb/gdb，可用于远程调试。

## 各目标的专项说明

### ARM 目标

如果你打算调试 ARM 内核，需要一个相当新的 gdb
版本（7.1 或更高）。此外，你必须像下面这样手动指定
`tspecs`（端口号可能不同）。`tspec` 文件
可在 gdb 源代码中找到：

```
set remote Z-packet on
set tdesc filename path/to/features/arm-with-neon.xml
symbol-file <path to vmlinux used for gem5>
target remote <ip addr of host running gem5 or if local host 127.0.0.1>:7000
```

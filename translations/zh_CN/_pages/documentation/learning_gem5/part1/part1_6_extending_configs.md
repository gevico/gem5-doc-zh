---
layout: documentation
title: Extending gem5 for ARM
doc: 学习 gem5
parent: part1
permalink: /documentation/learning_gem5/part1/extending_configs
author: Julian T. Angeles, Thomas E. Hansen
---

为 ARM 扩展 gem5
======================

本章假定你已经用 gem5 构建了一个基本的 x86 系统，并创建了一个简单的配置脚本。

下载 ARM 二进制程序
------------------------

我们先下载一些 ARM 基准测试（benchmark）二进制程序。从
gem5 文件夹的根目录开始：

```
mkdir -p cpu_tests/benchmarks/bin/arm
cd cpu_tests/benchmarks/bin/arm
wget dist.gem5.org/dist/v22-0/test-progs/cpu-tests/bin/arm/Bubblesort
wget dist.gem5.org/dist/v22-0/test-progs/cpu-tests/bin/arm/FloatMM
```

我们将用它们进一步测试我们的 ARM 系统。

构建 gem5 以运行 ARM 二进制程序
---------------------------------

正如我们最初构建基本 x86 系统时所做的，我们运行
同样的命令，只是这次希望它用
默认的 ARM 配置来编译。为此，我们只需把 x86 替换为 ARM：

```
scons build/ARM/gem5.opt -j 20
```

编译完成后，你应该在 `build/ARM/gem5.opt` 得到一个可用的 gem5 可执行文件。

修改 simple.py 以运行 ARM 二进制程序
---------------------------------------

在用我们的新系统运行任何 ARM 二进制程序之前，我们必须
对 simple.py 做一处小调整。

如果你还记得，我们创建简单配置脚本时曾指出，
对于 x86 之外的任何指令集架构，我们都不必把 PIO 和中断端口连接到
内存总线。因此我们把这三行去掉：

```
system.cpu.createInterruptController()
#system.cpu.interrupts[0].pio = system.membus.mem_side_ports
#system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
#system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports
```

你可以像上面那样删除或注释掉它们。接下来把
processes 命令设为我们的某个 ARM 基准测试二进制程序：

```
process.cmd = ['cpu_tests/benchmarks/bin/arm/Bubblesort']
```

如果你想和之前一样测试一个简单的 hello 程序，只需
把 x86 替换为 arm：

```
process.cmd = ['tests/test-progs/hello/bin/arm/linux/hello']
```

运行 gem5
------------

像之前一样运行它即可，只是把 X86 替换为 ARM：

```
build/ARM/gem5.opt configs/tutorial/simple.py
```

如果你把进程设为 Bubblesort 基准测试，你的
输出应如下所示：

```
gem5 Simulator System.  http://gem5.org
gem5 is copyrighted software; use the --copyright option for details.

gem5 compiled Oct  3 2019 16:02:35
gem5 started Oct  6 2019 13:22:25
gem5 executing on amarillo, pid 77129
command line: build/ARM/gem5.opt configs/tutorial/simple.py

Global frequency set at 1000000000000 ticks per second
warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
0: system.remote_gdb: listening for remote gdb on port 7002
Beginning simulation!
info: Entering event queue @ 0.  Starting simulation...
info: Increasing stack size by one page.
warn: readlink() called on '/proc/self/exe' may yield unexpected results in various settings.
      Returning '/home/jtoya/gem5/cpu_tests/benchmarks/bin/arm/Bubblesort'
-50000
Exiting @ tick 258647411000 because exiting with last active thread context
```

ARM 全系统模拟
--------------------------
要运行 ARM FS 模拟，需要对配置做一些改动。

如果你还没做，请从 gem5 仓库的根目录用以下命令 `cd` 进入
`util/term/` 目录：

```bash
$ cd util/term/
```

然后通过运行以下命令编译 `m5term` 二进制程序：

```bash
$ make
```

gem5 仓库附带示例系统配置与设置。它们
可以在 `configs/example/arm/` 目录中找到。

[此处](https://www.gem5.org/documentation/general_docs/fullsystem/guest_binaries)提供了一组
全系统 Linux 镜像文件。把它们保存到一个目录中，并记住该目录的路径。例如，你可以
把它们存放在

```
/path/to/user/gem5/fs_images/
```

在本示例的其余部分，我们假定 `fs_images` 目录中包含解压后的 FS 镜像。

镜像下载完成后，在终端中执行以下命令：

```bash
$ export IMG_ROOT=/absolute/path/to/fs_images/<image-directory-name>
```

把 "\<image-directory-name\>" 替换为从所下载镜像文件中解压出的
目录名，不要带尖括号。

现在我们准备好运行 ARM FS 模拟了。在 gem5
仓库的根目录运行：

```bash
$ ./build/ARM/gem5.opt configs/example/arm/fs_bigLITTLE.py \
    --caches \
    --bootloader="$IMG_ROOT/binaries/<bootloader-name>" \
    --kernel="$IMG_ROOT/binaries/<kernel-name>" \
    --disk="$IMG_ROOT/disks/<disk-image-name>" \
    --bootscript=path/to/bootscript.rcS
```

把尖括号中的内容替换为相应的目录或文件名，
不要带尖括号。

随后你可以在另一个终端窗口中运行以下命令
附加到该模拟：

```bash
$ ./util/term/m5term 3456
```

`fs_bigLITTLE.py` 脚本所支持内容的完整细节可以通过
运行以下命令获得：

```bash
$ ./build/ARM/gem5.opt configs/example/arm/fs_bigLITTLE.py --help
```

> **关于 FS 模拟的一点补充：**
>
> 注意 FS 模拟耗时很长；长到“加载内核要 1 小时”的程度！有一些方法可以“快进”模拟，然后在
> 关注的时刻恢复详细模拟，但这些超出了本章的
> 范围。

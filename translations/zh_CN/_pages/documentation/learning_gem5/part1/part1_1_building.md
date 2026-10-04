---
layout: documentation
title: Building gem5
doc: 学习 gem5
parent: part1
permalink: /documentation/learning_gem5/part1/building/
author: Jason Lowe-Power
---

构建 gem5
=============

本章介绍如何搭建 gem5 开发环境并构建 gem5 的细节。

如果你有预构建的二进制程序
-----------------------------

如果你使用预构建的二进制程序运行 gem5，可以跳过本节。
预构建的二进制程序使用 ALL 构建，可用于运行所有指令集架构和所有 Ruby 一致性协议。

gem5 的依赖要求
---------------------

更多细节见 [gem5 依赖要求](http://www.gem5.org/documentation/general_docs/building#dependencies)。

在 Ubuntu 上，可以用以下命令安装所有必需的依赖项。具体要求详述如下。

```bash
sudo apt install build-essential git m4 scons zlib1g zlib1g-dev libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev python-dev python
```

1. git（[Git](https://git-scm.com/)）：
    ：   gem5 项目使用 [Git](https://git-scm.com/) 进行版本
        控制。[Git](https://git-scm.com/) 是一个分布式版本
        控制系统。关于
        [Git](https://git-scm.com/) 的更多信息可以通过该链接找到。
        大多数平台上 Git 应当默认已安装。不过，
        在 Ubuntu 上安装 Git 使用

    ```bash
    sudo apt install git
    ```

2. gcc 10+
    ：   你可能需要用环境变量指向
        非默认版本的 gcc。

        在 Ubuntu 上，可以用以下命令安装开发环境

        ```bash
        sudo apt install build-essential
        ```

       **我们支持 GCC 10 到 GCC 13 的版本**

3.  [SCons 3.0+](http://www.scons.org/)
    ：   gem5 使用 SCons 作为其构建环境。SCons 像是加强版的 make，
        用 Python 脚本处理构建过程的所有方面。这带来了非常灵活（虽然可能较慢）的构建系统。

        在 Ubuntu 上获取 SCons 使用

    ```bash
    sudo apt install scons
    ```

4.  Python 3.6+
    ：   gem5 依赖 Python 开发库。在 Ubuntu 上安装
        它们使用

    ```bash
    sudo apt install python3-dev
    ```

5.  [protobuf](https://developers.google.com/protocol-buffers/) 2.1+（**可选**）
    ：   “Protocol buffers 是一种语言中立、平台中立、
        可扩展的结构化数据序列化机制。”在 gem5 中，
        [protobuf](https://developers.google.com/protocol-buffers/)
        库用于跟踪（trace）的生成与回放。
        [protobuf](https://developers.google.com/protocol-buffers/) 
        不是必需的包，除非你打算用它做跟踪的
        生成与回放。

    ```bash
    sudo apt install libprotobuf-dev protobuf-compiler libgoogle-perftools-dev
    ```

6. [Boost](https://www.boost.org/)（**可选**）
    ：   Boost 库是一组通用 C++ 库。如果你希望使用 SystemC 实现，
        它是必需的依赖项。
        ```
        sudo apt install libboost-all-dev
        ```

获取代码
----------------

切换到你想下载 gem5 源码的目录。然后
用 `git clone` 命令克隆仓库。

```bash
git clone https://github.com/gem5/gem5
```

现在你可以切换到 `gem5` 目录，其中包含所有 gem5
代码。

你的第一次 gem5 构建
---------------------

我们先构建一个基本的 x86 系统。自 gem5 v22.1 起，
你可以编译包含所有指令集架构的 ALL 构建。自 gem5 v24.1 起，
ALL 构建还包含所有 Ruby 缓存一致性协议。如果你使用
ruby-intro-chapter，这一点很重要。

要构建 gem5，我们将使用 SCons。SCons 使用 SConstruct 文件
（`gem5/SConstruct`）设置若干变量，然后在每个子目录中使用
SConscript 文件查找并编译所有
gem5 源码。

SCons 在第一次执行时会自动创建 `gem5/build` 目录。
在该目录中你会找到 SCons、编译器等生成的文件。
你用来编译 gem5 的每一组选项（指令集架构与缓存一致性协议）
都会有一个单独的目录。

`build_opts` 目录中有若干默认编译选项。这些文件指定了
构建 gem5 所使用的、取非默认值的参数。我们将使用 ALL 默认值。
你可以查看文件
`build_opts/ALL` 中取非默认值的（kconfig）设置。
对于 gem5 <= 23.0，你也可以在命令行指定这些选项以
覆盖任何默认值。对于 gem5 >= 23.1，你可以使用 setconfig、menuconfig 或 guiconfig 之类的 kconfig 工具，在
已有的构建目录中修改这些设置。

```bash
python3 `which scons` build/ALL/gem5.opt -j9
```

> **gem5 二进制程序类型**
>
> gem5 中的 SCons 脚本目前有三种可以构建的
> 二进制程序：debug、opt 和 fast。这些名称
> 大多不言自明，但下面会详细说明。
>
> debug
> ：   不带优化、带调试符号构建。当你用调试器调试、
>     而 opt 版 gem5 中你需要的变量被优化掉时，该二进制程序很有用。
>     与其他二进制程序相比，以 debug 运行较慢。
>
> opt
> ：   该二进制程序在开启大多数优化（例如 -O3）的情况下构建，
>     但包含调试符号。它比
>     debug 快得多，但仍包含足够的调试信息，能调试大多数问题。
>
> fast
> ：   在开启所有优化（在支持的平台上包括链接时优化）
>     且不带调试符号的情况下构建。此外，
>     所有断言都被移除，但 panic 和 fatal 仍然保留。
>     fast 是性能最高的二进制程序，也比
>     opt 小得多。不过，只有当你认为自己的代码不太可能有重大缺陷时，
>     fast 才合适。
>
>传给 SCons 的主要参数是你要构建的目标，
`build/ALL/gem5.opt`。在本例中我们构建 gem5.opt（一个
带调试符号的优化二进制程序）。我们希望在
build/ALL 目录中构建 gem5。由于该目录目前不存在，SCons
会在 `build_opts` 中查找 ALL 构建的参数。（注意：
我这里用 -j9 是为了在我机器的 8 个核心上跑 9 个构建任务。你应当为你的机器选择
合适的数量，通常是核心数 +1。）

输出应类似下面这样（针对 gem5 >= 24.1）：

```txt
    scons: Reading SConscript files ...
    Mkdir("/local.chinook/gem5/gem5-tutorial/gem5/build/ALL/gem5.build")
    Checking for linker -Wl,--as-needed support... (cached) yes
    Checking for compiler -gz support... (cached) yes
    Checking for linker -gz support... (cached) yes
    Info: Using Python config: python3-config
    Checking for C header file Python.h... (cached) yes
    Checking Python version... (cached) 3.12.3
    Checking for accept(0,0,0) in C++ library None... (cached) yes
    Checking for zlibVersion() in C++ library z... (cached) yes
    Checking for C library tcmalloc_minimal... (cached) yes
    Building in /home/bees/gem5-4th-worktree/build/ALL
    "build_tools/kconfig_base.py" "/home/bees/gem5-4th-worktree/build/ALL/gem5.build/Kconfig" "/home/bees/gem5-4th-worktree/src/Kconfig" 
    Checking for C header file fenv.h... (cached) yes
    Checking for C header file png.h... (cached) yes
    Checking for clock_nanosleep(0,0,NULL,NULL) in C library None... (cached) yes
    Checking for C header file valgrind/valgrind.h... (cached) yes
    Checking for pkg-config package hdf5-serial... (cached) yes
    Checking for H5Fcreate("", 0, 0, 0) in C library hdf5... (cached) yes
    Checking for H5::H5File("", 0) in C++ library hdf5_cpp... (cached) yes
    Checking for pkg-config package protobuf... (cached) yes
    Checking for shm_open("/test", 0, 0) in C library None... (cached) yes
    Checking for backtrace_symbols_fd((void *)1, 0, 0) in C library None... (cached) yes
    Checking size of struct kvm_xsave ... (cached) yes
    Checking for C header file capstone/capstone.h... (cached) yes
    Checking for C header file linux/kvm.h... (cached) yes
    Checking for timer_create(CLOCK_MONOTONIC, NULL, NULL) in C library None... (cached) yes
    Checking for member exclude_host in struct perf_event_attr...(cached) yes
    Checking for C header file linux/if_tun.h... (cached) yes 
    Checking whether __i386__ is declared... (cached) no
    Checking whether __x86_64__ is declared... (cached) yes
    Checking for compiler -Wno-self-assign-overloaded support... (cached) yes
    Checking for linker -Wno-free-nonheap-object support... (cached) yes
    BUILD_TLM not set, not building CHI-TLM integration

    scons: done reading SConscript files.
    scons: Building targets ...
    [     CXX] ALL/base/Graphics.py.cc -> .o
    [    LINK]  -> ALL/gem5py_m5
    [     CXX] src/base/atomicio.cc -> ALL/base/atomicio.o
    [     CXX] src/base/bitfield.cc -> ALL/base/bitfield.o

     ....
     .... <lots of output>
     ....
 [SO Param] m5.objects.Uart, Uart8250 -> ALL/params/Uart8250.hh
 [     CXX] ALL/python/_m5/param_SimpleUart.cc -> .o
 [     CXX] ALL/enums/TerminalDump.cc -> .o
 [     CXX] ALL/python/_m5/param_Uart8250.cc -> .o
 [     CXX] src/dev/serial/serial.cc -> ALL/dev/serial/serial.o
 [     CXX] src/dev/serial/simple.cc -> ALL/dev/serial/simple.o
 [     CXX] src/dev/serial/terminal.cc -> ALL/dev/serial/terminal.o
 [     CXX] src/dev/serial/uart.cc -> ALL/dev/serial/uart.o
 [     CXX] src/dev/serial/uart8250.cc -> ALL/dev/serial/uart8250.o
 [     CXX] ALL/debug/Terminal.cc -> .o
 [     CXX] ALL/debug/TerminalVerbose.cc -> .o
 [     CXX] ALL/debug/Uart.cc -> .o
 [     CXX] ALL/python/m5/defines.py.cc -> .o
 [     CXX] ALL/python/m5/info.py.cc -> .o
 [     CXX] src/base/date.cc -> ALL/base/date.o
 [    LINK]  -> ALL/gem5.opt
scons: done building targets.
```

编译完成后，你应该在 `build/ALL/gem5.opt` 得到一个可用的 gem5 可执行文件。编译可能耗时很长，
往往要 15 分钟以上，尤其是在 AFS 或 NFS 之类的远程
文件系统上编译时。

常见错误
-------------

### gcc 版本不对

```txt
    Error: gcc version 5 or newer required.
           Installed version: 4.4.7
```

更新你的环境变量，使其指向正确的 gcc 版本，或者
安装更新版本的 gcc。见
building-requirements-section。

### Python 不在默认位置

如果你使用非默认版本的 Python（例如在默认版本是 2.5 时使用
3.6），用 SCons 构建 gem5 时可能会出现问题。
RHEL6 版本的 SCons 对 Python 位置使用了硬编码路径，从
而导致该问题。gem5 在这种情况下常常能成功构建，但可能
无法运行。下面是运行 gem5 时可能看到的一种错误。

```txt
    Traceback (most recent call last):
      File "........../gem5-stable/src/python/importer.py", line 93, in <module>
        sys.meta_path.append(importer)
    TypeError: 'dict' object is not callable
```

要解决这个问题，你可以通过运行 `` python3 `which scons` build/ALL/gem5.opt ``（而不是
`scons build/ALL/gem5.opt`）来强制 SCons 使用你环境中的 Python
版本。

### 未安装 M4 宏处理器

如果未安装 M4 宏处理器，你会看到类似这样的错误：

```txt
    ...
    Checking for member exclude_host in struct perf_event_attr...yes
    Error: Can't find version of M4 macro processor.  Please install M4 and try again.
```

仅安装 M4 宏包可能无法解决该问题。你可能
还需要安装所有 `autoconf` 工具。在 Ubuntu 上，可以用
以下命令。

```bash
sudo apt-get install automake
```

### Protobuf 3.12.3 问题

用 protobuf 编译 gem5 可能导致以下错误，

```txt
In file included from build/X86/cpu/trace/trace_cpu.hh:53,
                 from build/X86/cpu/trace/trace_cpu.cc:38:
build/X86/proto/inst_dep_record.pb.h:49:51: error: 'AuxiliaryParseTableField' in namespace 'google::protobuf::internal' does not name a type; did you mean 'AuxillaryParseTableField'?
   49 |   static const ::PROTOBUF_NAMESPACE_ID::internal::AuxiliaryParseTableField aux[]
```

该问题的根本原因在此讨论：[https://gem5.atlassian.net/browse/GEM5-1032]。

要解决该问题，你可能需要更新 ProtocolBuffer 的版本，

```bash
sudo apt update
sudo apt install libprotobuf-dev protobuf-compiler libgoogle-perftools-dev
```

之后，在重新编译 gem5 **之前**，你可能需要清理 gem5 构建文件夹，

```bash
python3 `which scons` --clean --no-cache        # cleaning the build folder
python3 `which scons` build/ALL/gem5.opt -j 9   # re-compiling gem5
```

如果问题仍然存在，在再次编译 gem5 **之前**，你可能需要彻底删除 gem5 构建文件夹，

```bash
rm -rf build/                                   # completely removing the gem5 build folder
python3 `which scons` build/ALL/gem5.opt -j 9   # re-compiling gem5
```

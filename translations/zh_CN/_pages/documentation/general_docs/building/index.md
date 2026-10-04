---
layout: documentation
title: 构建 gem5
doc: gem5 文档
parent: building_extras
permalink: /documentation/general_docs/building
authors: Bobby R. Bruce
---

# 构建 gem5

## 受支持的操作系统与环境

gem5 在设计时以 Linux 环境为目标。我们定期在 **Ubuntu 22.04** 和 **Ubuntu 24.04** 上进行测试，以确保 gem5 在这些环境中运作良好。不过，**只要安装了正确的依赖项，任何基于 Linux 的操作系统都应该可用**。我们确保 gem5 既能用 gcc 也能用 clang 编译（编译器版本信息见下方[依赖项](#dependencies)）。

自 gem5 21.0 起，**我们只支持用 Python 3.6+ 构建和运行 gem5**。gem5 20.0 是最后一个支持 Python 2 的 gem5 版本。

如果无法在合适的操作系统/环境中运行 gem5，我们提供了预先准备的 [Docker](https://www.docker.com/) 镜像，可用于编译和运行 gem5。更多信息见下文的 [Docker](#docker) 章节。

## 依赖项 {#dependencies}

* **git** ：gem5 使用 git 进行版本控制。
* **gcc**：使用 gcc 编译 gem5。**必须使用 10 或更高版本**。我们
支持到 gcc 13 版本。
* **Clang**：也可以使用 Clang。目前我们支持 Clang 7 到
Clang 16（含）。
* **SCons** ：gem5 使用 SCons 作为构建环境。必须使用 SCons 3.0 或更高版本。
* **Python 3.6+** ：gem5 依赖 Python 开发库。gem5 可以在使用 Python 3.6+ 的环境中
编译和运行。
* **protobuf 2.1+**（可选）：protobuf 库用于跟踪（trace）
的生成与回放。
* **Boost**（可选）：Boost 库是一组通用 C++
库。如果你希望使用 SystemC 实现，它是必需的依赖项。

### 在 Ubuntu 24.04 上配置环境（gem5 >= v24.0）

如果在 Ubuntu 24.04 或相关 Linux 发行版上编译 gem5，可以用 APT
安装所有这些依赖项：

```bash
sudo apt install build-essential scons python3-dev git pre-commit zlib1g zlib1g-dev \
    libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev \
    libboost-all-dev  libhdf5-serial-dev python3-pydot python3-venv python3-tk mypy \
    m4 libcapstone-dev libpng-dev libelf-dev pkg-config wget cmake doxygen clang-format
```

### 在 Ubuntu 22.04 上配置环境（gem5 >= v21.1）

如果在 Ubuntu 22.04 或相关 Linux 发行版上编译 gem5，可以用 APT
安装所有这些依赖项：

```bash
sudo apt install build-essential git m4 scons zlib1g zlib1g-dev \
    libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev \
    python3-dev libboost-all-dev pkg-config python3-tk clang-format-15
```

你可能需要把 `clang-format-15` 配置为系统默认的
`clang-format`。

```bash
# Configure clang-format-15 and git-clang-format-15 as the system defaults.
sudo update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-15 150 \
        --slave /usr/bin/clang-format-diff clang-format-diff /usr/bin/clang-format-diff-15 \
        --slave /usr/bin/git-clang-format git-clang-format /usr/bin/git-clang-format-15

# [Optional] Add other alternative versions, and select version 15 as the default version.
sudo update-alternatives --config clang-format
```

### 在 Ubuntu 20.04 上配置环境（gem5 >= v21.0）

如果在 Ubuntu 20.04 或相关 Linux 发行版上编译 gem5，可以用 APT
安装所有这些依赖项：

```bash
sudo apt install build-essential git m4 scons zlib1g zlib1g-dev \
    libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev \
    python3-dev python-is-python3 libboost-all-dev pkg-config gcc-10 g++-10 \
    python3-tk clang-format-18
```

你可能需要把 `clang-format-18` 配置为系统默认的
`clang-format`。

```bash
# Configure clang-format-18 and git-clang-format-18 as the system defaults.
sudo update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-18 180 \
        --slave /usr/bin/clang-format-diff clang-format-diff /usr/bin/clang-format-diff-18 \
        --slave /usr/bin/git-clang-format git-clang-format /usr/bin/git-clang-format-18

# [Optional] Add other alternative versions, and select version 18 as the default version.
sudo update-alternatives --config clang-format
```

### Docker {#docker}

对于难以搭建 gem5 构建与运行环境的用户，我们提供
以下 Docker 镜像：

Ubuntu 24.04，包含所有可选依赖项：
[ghcr.io/gem5/ubuntu-24.04_all-dependencies:v24-0](
https://ghcr.io/gem5/ubuntu-24.04_all-dependencies:v24-0)
（[源 Dockerfile](https://github.com/gem5/gem5/blob/v24.0.0.0/util/dockerfiles/ubuntu-24.04_all-dependencies/Dockerfile)）。

Ubuntu 24.04，包含最少依赖项：
[ghcr.io/gem5/ubuntu-24.04_min-dependencies:v24-0](
https://ghcr.io/gem5/ubuntu-24.04_min-dependencies:v24-0)
（[源 Dockerfile](https://github.com/gem5/gem5/blob/v24.0.0.0/util/dockerfiles/ubuntu-24.04_min-dependencies/Dockerfile)）。

Ubuntu 22.04，包含所有可选依赖项：
[ghcr.io/gem5/ubuntu-22.04_all-dependencies:v23-0](
https://ghcr.io/gem5/ubuntu-22.04_all-dependencies:v23-0)（[源 Dockerfile](
https://github.com/gem5/gem5/blob/v23.0.1.0/util/dockerfiles/ubuntu-22.04_all-dependencies/Dockerfile)）。

Ubuntu 20.04，包含所有可选依赖项：
[ghcr.io/gem5/ubuntu-20.04_all-dependencies:v23-0](
https://ghcr.io/gem5/ubuntu-20.04_all-dependencies:v23-0)（[源 Dockerfile](
https://github.com/gem5/gem5/blob/v23.0.1.0/util/dockerfiles/ubuntu-20.04_all-dependencies/Dockerfile)）。

Ubuntu 18.04，包含所有可选依赖项：
[ghcr.io/gem5/ubuntu-18.04_all-dependencies:v23-0](
https://ghcr.io/gem5/ubuntu-18.04_all-dependencies:v23-0)（[源 Dockerfile](
https://github.com/gem5/gem5/blob/v23.0.1.0/util/dockerfiles/ubuntu-18.04_all-dependencies/Dockerfile)）。

获取 docker 镜像：

```bash
docker pull <image>
```

例如，获取包含所有可选依赖项的 Ubuntu 20.04：

```bash
docker pull ghcr.io/gem5/ubuntu-20.04_all-dependencies:v23-0
```

然后，要在此环境中工作，我们建议使用：

```bash
docker run -u $UID:$GID --volume <gem5 directory>:/gem5 --rm -it <image>
```

其中 `<gem5 directory>` 是 gem5 在你文件系统中的完整路径，
`<image>` 是所拉取的镜像（例如
ghcr.io/gem5/ubuntu-22.04_all-dependencies:v23-0`）。

在此环境中，你就可以从 `/gem5`
目录构建和运行 gem5。

## 获取代码

```bash
git clone https://github.com/gem5/gem5
```

## 使用 SCons 构建

gem5 的构建系统基于 SCons，这是一个用
Python 实现的开源构建系统。关于 scons 的更多信息见 <http://www.scons.org>。
主 scons 文件名为 SConstruct，位于源码
树的根目录。其他 scons 文件名为 SConscript，散布在
整棵树中，通常靠近它们所关联的文件。

在 gem5 目录的根下，可以用 SCons 构建 gem5：

```bash
scons build/{ISA}/gem5.{variant} -j {cpus}
```

其中 `{ISA}` 是目标（客户机）指令集架构（ISA），
`{variant}` 指定编译设置。就大多数用途而言，
`opt` 是很好的编译目标。`-j` 选项是可选的，用于
并行编译，其中 `{cpus}` 指定线程数。从零开始的单线程编译在某些系统上
可能需要长达 2 小时。因此我们强烈建议在可能的情况下分配更多线程。
不过，编译 gem5 对计算和内存消耗都很大，增加
线程数也会增加内存占用。如果使用内存较少的机器，
建议使用较少的线程（例如 `-j 1` 或 `-j 2`）。

有效的指令集架构（ISA）为：

* ALL - 推荐，因为自 gem5 v24.1 起它包含所有指令集架构和所有 Ruby 协议
* ARM
* NULL
* MIPS
* POWER
* RISCV
* SPARC
* X86

有效的构建变体为：

* **debug** 关闭了优化。这可以确保变量不会被
优化掉、函数不会被意外内联、控制流不会
以出人意料的方式运行。这使得该版本更易于在
gdb 之类的工具中使用，但由于没有优化，它明显比其他版本慢。
在使用 gdb、valgrind 之类的工具且不希望任何细节被掩盖时应选择它，
否则更推荐使用经过更多优化的版本。
* **opt** 开启了优化，并保留断言和 DPRINTF 等调试功能。
这在模拟速度和出问题时了解内部情况之间取得了良好平衡。
它在大多数情况下是最佳选择。
* **fast** 开启了优化并编译掉了调试功能。这在性能上
可谓用尽一切手段，但代价是失去了运行时错误检查和开启调试输出的能力。
如果你非常有把握一切都正确运行，并希望从模拟器
获得峰值性能，推荐使用该版本。

这些版本总结如下表。

|构建变体|优化|运行时调试支持|
|-------------|-------------|--------------------------|
|**debug**    |             |X                         |
|**opt**      |X            |X                         |
|**fast**     |X            |                          |

例如，用 4 个线程以 `opt` 构建包含所有指令集架构的 gem5：

```bash
scons build/ALL/gem5.opt -j 4
```

此外，用户还可以使用 "gprof" 和 "pperf" 构建选项来
启用性能分析：

* **gprof** 允许 gem5 配合 gprof 性能分析工具使用。可以通过
使用 `--gprof` 选项编译来启用。例如
`scons build/ALL/gem5.debug --gprof`。
* **pprof** 允许 gem5 配合 pprof 性能分析工具使用。可以通过
使用 `--pprof` 选项编译来启用。例如
`scons build/ALL/gem5.debug --pprof`。

## 使用 Kconfig 构建

请参见[此处](https://www.gem5.org/documentation/general_docs/kconfig_build_system/)

## 使用

编译完成后，可以用以下方式运行 gem5：

```console
./build/{ISA}/gem5.{variant} [gem5 options] {simulation script} [script options]
```

如果你使用的是预编译的二进制程序，可以用以下命令运行 gem5：

```console
gem5 [gem5 options] {simulation script} [script options]
```

使用 `--help` 选项运行会显示所有可用选项：

```txt
Usage
=====
  gem5.opt [gem5 options] script.py [script options]

gem5 is copyrighted software; use the --copyright option for details.

Options
=======
--help, -h              show this help message and exit
--build-info, -B        Show build information
--copyright, -C         Show full copyright information
--readme, -R            Show the readme
--outdir=DIR, -d DIR    Set the output directory to DIR [Default: m5out]
--redirect-stdout, -r   Redirect stdout (& stderr, without -e) to file
--redirect-stderr, -e   Redirect stderr to file
--silent-redirect       Suppress printing a message when redirecting stdout or
                        stderr
--stdout-file=FILE      Filename for -r redirection [Default: simout.txt]
--stderr-file=FILE      Filename for -e redirection [Default: simerr.txt]
--listener-mode={on,off,auto}
                        Port (e.g., gdb) listener mode (auto: Enable if
                        running interactively) [Default: auto]
--allow-remote-connections
                        Port listeners will accept connections from anywhere
                        (0.0.0.0). Default is only localhost.
--interactive, -i       Invoke the interactive interpreter after running the
                        script
--pdb                   Invoke the python debugger before running the script
--path=PATH[:PATH], -p PATH[:PATH]
                        Prepend PATH to the system path when invoking the
                        script
--quiet, -q             Reduce verbosity
--verbose, -v           Increase verbosity
-m mod                  run library module as a script (terminates option
                        list)
-c cmd                  program passed in as string (terminates option list)
-P                      Don't prepend the script directory to the system path.
                        Mimics Python 3's `-P` option.
-s                      IGNORED, only for compatibility with python. don'tadd
                        user site directory to sys.path; also PYTHONNOUSERSITE

Statistics Options
------------------
--stats-file=FILE       Sets the output file for statistics [Default:
                        stats.txt]
--stats-help            Display documentation for available stat visitors

Configuration Options
---------------------
--dump-config=FILE      Dump configuration output file [Default: config.ini]
--json-config=FILE      Create JSON output of the configuration [Default:
                        config.json]
--dot-config=FILE       Create DOT & pdf outputs of the configuration
                        [Default: config.dot]
--dot-dvfs-config=FILE  Create DOT & pdf outputs of the DVFS configuration
                        [Default: none]

Debugging Options
-----------------
--debug-break=TICK[,TICK]
                        Create breakpoint(s) at TICK(s) (kills process if no
                        debugger attached)
--debug-help            Print help on debug flags
--debug-flags=FLAG[,FLAG]
                        Sets the flags for debug output (-FLAG disables a
                        flag)
--debug-start=TICK      Start debug output at TICK
--debug-end=TICK        End debug output at TICK
--debug-file=FILE       Sets the output file for debug. Append '.gz' to the
                        name for it to be compressed automatically [Default:
                        cout]
--debug-activate=EXPR[,EXPR]
                        Activate EXPR sim objects
--debug-ignore=EXPR     Ignore EXPR sim objects
--remote-gdb-port=REMOTE_GDB_PORT
                        Remote gdb base port (set to 0 to disable listening)

Help Options
------------
--list-sim-objects      List all built-in SimObjects, their params and default
                        values
```

## 使用 EXTRAS

可以把 [EXTRAS]({{ site.baseurl }}/documentation/general_docs/building/EXTRAS) 这个 scons 变量设置为以冒号分隔的路径列表，从而把这些
额外目录中的源文件也编入 gem5。EXTRAS 是一种
便捷方式，让你能在 gem5 代码库之上进行构建，而不把新源码
与上游源码混在一起。这样你就可以按需独立于主代码库
管理自己的新代码。

---
layout: documentation
title: "使用默认配置脚本"
doc: 学习 gem5
parent: part1
permalink: /documentation/learning_gem5/part1/example_configs/
author: Jason Lowe-Power
---

gem5 v24.1：使用标准库配置脚本
=================================================================

gem5 标准库的引入改变了配置脚本的编写方式。下方 v21.0 小节提到的许多旧脚本已被弃用，取而代之的是 `configs/example/gem5_library` 中的标准库配置脚本。

目录结构简要如下：

```txt
gem5_library
    |
    |- caches       #contains a configuration script for the octopi cache
    |
    |- checkpoints  #scripts for taking and restoring from checkpoints
    |
    |- dramsys      #scripts for using gem5 with dramsys
    |
    |- looppoints   #scripts for taking and restoring from looppoints
    |
    |- multisim     #scripts for launching multiple simulations at once using multisim
    |
    |- spatter_gen  #scripts for SpatterGen
    |
    |- (various example configuration scripts not sorted into a subdirectory)

```

直接放在 `gem5_library` 目录下的示例，与前几章的脚本类似，但覆盖更多指令集架构（ISA）、板卡（board）和工作负载（workload）组合。源码见[此处](https://github.com/gem5/gem5/tree/stable/configs/example/gem5_library)。

gem5 v21.0：使用默认配置脚本
=======================================

本节介绍 gem5 自带的默认配置脚本及其重要选项。这些脚本可以帮助你快速开始使用 gem5，但常见误区是在尚未理解系统模型时就直接使用它们。进行计算机体系结构（architecture）研究时，必须充分了解自己实际模拟的系统。

前几章从零编写了配置脚本，这种方式能够精确控制每个系统参数（parameter），非常灵活。不过，全系统（full-system）ARM 或 x86 等系统的配置相当复杂，因此开发者提供了很多脚本，帮助用户完成初始搭建。

> **译注：** 以下目录、命令、默认值和输出对应历史版本。学习旧脚本的配置逻辑仍然有用，但不要据此假定当前版本仍在相同路径提供这些脚本。

目录结构概览
---------------------------------

gem5 的配置文件位于 `configs/`，目录结构如下：

    configs/boot:
    bbench-gb.rcS  bbench-ics.rcS  hack_back_ckpt.rcS  halt.sh

    configs/common:
    Benchmarks.py   Caches.py  cpu2000.py    FileSystemConfig.py  GPUTLBConfig.py   HMC.py       MemConfig.py   Options.py     Simulation.py
    CacheConfig.py  cores      CpuConfig.py  FSConfig.py          GPUTLBOptions.py  __init__.py  ObjectList.py  SimpleOpts.py  SysPaths.py

    configs/dist:
    sw.py

    configs/dram:
    lat_mem_rd.py  low_power_sweep.py  sweep.py

    configs/example:
    apu_se.py  etrace_replay.py  garnet_synth_traffic.py  hmctest.py    hsaTopology.py  memtest.py  read_config.py  ruby_direct_test.py      ruby_mem_test.py     sc_main.py
    arm        fs.py             hmc_hello.py             hmc_tgen.cfg  memcheck.py     noc_config  riscv           ruby_gpu_random_test.py  ruby_random_test.py  se.py

    configs/learning_gem5:
    part1  part2  part3  README

    configs/network:
    __init__.py  Network.py

    configs/nvm:
    sweep_hybrid.py  sweep.py

    configs/ruby:
    AMD_Base_Constructor.py  CHI.py        Garnet_standalone.py  __init__.py              MESI_Three_Level.py  MI_example.py      MOESI_CMP_directory.py  MOESI_hammer.py
    CHI_config.py            CntrlBase.py  GPU_VIPER.py          MESI_Three_Level_HTM.py  MESI_Two_Level.py    MOESI_AMD_Base.py  MOESI_CMP_token.py      Ruby.py

    configs/splash2:
    cluster.py  run.py

    configs/topologies:
    BaseTopology.py  Cluster.py  CrossbarGarnet.py  Crossbar.py  CustomMesh.py  __init__.py  MeshDirCorners_XY.py  Mesh_westfirst.py  Mesh_XY.py  Pt2Pt.py

各目录的用途如下。

**boot/**
:   包含全系统（full-system）模式使用的 rcS 文件。Linux 启动后，模拟器（simulator）加载这些文件，再由 shell 执行。大部分用于控制基准测试（benchmark）的运行，也有 `hack_back_ckpt.rcS` 这样的辅助脚本。全系统（full-system）章节会进一步介绍。

**common/**
:   包含创建系统所需的辅助脚本和函数。例如，`Caches.py` 与前几章编写的 `caches.py`、`caches_opts.py` 类似。

    `Options.py` 定义 CPU 数量、系统时钟等大量命令行选项。想知道某项配置是否已经有对应选项，可以先查看这里。

    `CacheConfig.py` 提供 Classic 内存系统（memory system）的缓存（cache）配置选项及函数。

    `MemConfig.py` 提供配置内存系统（memory system）的辅助函数。

    `FSConfig.py` 提供为多种系统建立全系统（full-system）模拟（simulation）所需的函数，相关章节会进一步说明。

    `Simulation.py` 包含配置和运行 gem5 的辅助函数，其中大量代码负责保存、恢复检查点（checkpoint）。`example/` 中的示例通过这些函数执行模拟（simulation）。虽然该文件较复杂，但也带来了很大的运行控制灵活性。

**dram/**
:   包含测试 DRAM 的脚本。

**example/**
:   包含可直接运行的示例配置，尤其是 `se.py`、`fs.py`，下一节将进一步介绍。这里也有其他实用配置脚本。

**learning_gem5/**
:   包含《学习 gem5》中出现的全部配置脚本。

**network/**
:   包含 HeteroGarnet 网络配置脚本。

**nvm/**
:   包含使用 NVM 接口的示例脚本。

**ruby/**
:   包含 Ruby 及其缓存一致性（cache coherence）协议（protocol）的配置脚本，详见 Ruby 章节。

**splash2/**
:   包含运行 SPLASH-2 基准测试（benchmark）套件的脚本，并提供部分系统配置选项。

**topologies/**
:   包含创建 Ruby 缓存（cache）层次结构时可用的网络拓扑实现，详见 Ruby 章节。

使用 `se.py` 和 `fs.py`
-------------------------

下面介绍这两个脚本共有的一些命令行选项。全系统（full-system）模式的具体运行方法见对应章节。

本节的大多数选项在 `Options.py` 的 `addCommonOptions` 函数中注册。这里并未覆盖全部选项；完整列表可以通过 `--help` 查看，也可以阅读脚本源码。

先不指定其他系统配置选项，运行 Hello world：

```
build/X86/gem5.opt configs/example/se.py --cmd=tests/test-progs/hello/bin/x86/linux/hello
```

输出如下：

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 version 21.0.0.0
    gem5 compiled May 17 2021 18:05:59
    gem5 started May 18 2021 00:33:42
    gem5 executing on amarillo, pid 85168
    command line: build/X86/gem5.opt configs/example/se.py --cmd=tests/test-progs/hello/bin/x86/linux/hello

    Global frequency set at 1000000000000 ticks per second
    warn: No dot file generated. Please install pydot to generate the dot file and pdf.
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb: listening for remote gdb on port 7005
    **** REAL SIMULATION ****
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 5943000 because exiting with last active thread context

然而，这次运行还不能提供所需的详细时序数据。脚本默认使用 atomic CPU 和 atomic 内存访问。查看 `m5out/config.ini` 即可确认；原文示例中第 51 行附近的 CPU 配置如下：

    [system.cpu]
    type=X86AtomicSimpleCPU
    children=interrupts isa mmu power_state tracer workload
    branchPred=Null
    checker=Null
    clk_domain=system.cpu_clk_domain
    cpu_id=0
    do_checkpoint_insts=true
    do_statistics_insts=true

要真正以 timing 模式运行，需要指定 CPU 类型。同时也可以设置 L1 缓存（cache）的容量：

```
build/X86/gem5.opt configs/example/se.py --cmd=tests/test-progs/hello/bin/x86/linux/hello --cpu-type=TimingSimpleCPU --l1d_size=64kB --l1i_size=16kB
```

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 version 21.0.0.0
    gem5 compiled May 17 2021 18:05:59
    gem5 started May 18 2021 00:36:10
    gem5 executing on amarillo, pid 85269
    command line: build/X86/gem5.opt configs/example/se.py --cmd=tests/test-progs/hello/bin/x86/linux/hello --cpu-type=TimingSimpleCPU --l1d_size=64kB --l1i_size=16kB

    Global frequency set at 1000000000000 ticks per second
    warn: No dot file generated. Please install pydot to generate the dot file and pdf.
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb: listening for remote gdb on port 7005
    **** REAL SIMULATION ****
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 454646000 because exiting with last active thread context

现在检查 `config.ini`，确认选项是否传递到了最终系统。如果在 `m5out/config.ini` 中搜索 `cache`，会发现根本没有创建缓存（cache）！原因是只设置了容量，却没有要求系统启用缓存（cache）。正确命令应为：

```
build/X86/gem5.opt configs/example/se.py --cmd=tests/test-progs/hello/bin/x86/linux/hello --cpu-type=TimingSimpleCPU --l1d_size=64kB --l1i_size=16kB --caches
```

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 version 21.0.0.0
    gem5 compiled May 17 2021 18:05:59
    gem5 started May 18 2021 00:37:03
    gem5 executing on amarillo, pid 85560
    command line: build/X86/gem5.opt configs/example/se.py --cmd=tests/test-progs/hello/bin/x86/linux/hello --cpu-type=TimingSimpleCPU --l1d_size=64kB --l1i_size=16kB --caches

    Global frequency set at 1000000000000 ticks per second
    warn: No dot file generated. Please install pydot to generate the dot file and pdf.
    warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
    0: system.remote_gdb: listening for remote gdb on port 7005
    **** REAL SIMULATION ****
    info: Entering event queue @ 0.  Starting simulation...
    Hello world!
    Exiting @ tick 31680000 because exiting with last active thread context

最后一行显示，被模拟程序的执行时间从 454646000 tick 降至 31680000 tick。这表明缓存（cache）很可能已经启用，但仍应检查 `config.ini` 确认：

    [system.cpu.dcache]
    type=Cache
    children=power_state replacement_policy tags
    addr_ranges=0:18446744073709551615
    assoc=2
    clk_domain=system.cpu_clk_domain
    clusivity=mostly_incl
    compressor=Null
    data_latency=2
    demand_mshr_reserve=1
    eventq_index=0
    is_read_only=false
    max_miss_count=0
    move_contractions=true
    mshrs=4
    power_model=
    power_state=system.cpu.dcache.power_state
    prefetch_on_access=false
    prefetcher=Null
    replace_expansions=true
    replacement_policy=system.cpu.dcache.replacement_policy
    response_latency=2
    sequential_access=false
    size=65536
    system=system
    tag_latency=2
    tags=system.cpu.dcache.tags
    tgts_per_mshr=20
    warmup_percentage=0
    write_allocator=Null
    write_buffers=8
    writeback_clean=false
    cpu_side=system.cpu.dcache_port
    mem_side=system.membus.cpu_side_ports[2]

`se.py` 与 `fs.py` 的常用选项
---------------------------------------

运行下面的命令可以列出所有选项：

```
build/X86/gem5.opt configs/example/se.py --help
```

其中一些重要选项如下：

- `--cpu-type=CPU_TYPE`：选择 CPU 类型。这一参数（parameter）应始终明确设置；默认 atomic 类型不进行详细时序模拟（simulation）。
- `--sys-clock=SYS_CLOCK`：设置按系统速度运行的模块所使用的顶层时钟。
- `--cpu-clock=CPU_CLOCK`：设置按 CPU 速度运行的模块所用的时钟，独立于上述系统时钟。
- `--mem-type=MEM_TYPE`：选择内存类型，包括各种 DDR 内存和 Ruby 内存控制器。
- `--caches`：启用 Classic 缓存（cache）。
- `--l2cache`：使用 Classic 时启用 L2 缓存（cache）。
- `--ruby`：使用 Ruby 进行缓存（cache）系统建模。
- `-m TICKS, --abs-max-tick=TICKS`：运行到指定的绝对 tick，其中包含从检查点（checkpoint）恢复的既有时间。适合限制模拟（simulation）的时间范围。
- `-I MAXINSTS, --maxinsts=MAXINSTS`：设置要模拟的指令数量，默认不以此限制结束。适合在执行一定数量指令后停止。
- `-c CMD, --cmd=CMD`：指定 SE 模式要运行的二进制程序。
- `-o OPTIONS, --options=OPTIONS`：给被模拟程序传递选项和实参，整个字符串需要用双引号包围。既可以传位置实参，也可以传 `--whatever` 这样的选项。
- `--output=OUTPUT`：将被模拟应用程序的标准输出重定向到文件。若要重定向的是 gem5 自身的输出，则应把相应参数（parameter）放在配置脚本名之前。
- `--errout=ERROUT`：将被模拟程序的标准错误输出重定向到文件，用法类似上一项。

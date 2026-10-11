---
layout: documentation
title: "理解 gem5 的统计信息与输出"
doc: 学习 gem5
parent: part1
permalink: /documentation/learning_gem5/part1/gem5_stats/
author: Jason Lowe-Power
---

理解 gem5 的统计信息与输出
========================================

除配置脚本自行打印的信息外，运行 gem5 后还会在 `m5out` 目录下生成三个文件：

**config.ini**
:   列出本次模拟（simulation）创建的全部 SimObject 及其参数（parameter）值。

**config.json**
:   内容与 `config.ini` 相同，但采用 JSON 格式。

**stats.txt**
:   以文本形式记录本次模拟（simulation）注册的全部 gem5 统计信息。

config.ini
----------

该文件是确认实际模拟了什么系统的权威依据。每个 SimObject 的全部参数（parameter）都会列在这里，无论它是在配置脚本中显式设置的，还是使用了默认值。

下面摘自运行[简单配置脚本一章]({{ site.baseurl }}/documentation/learning_gem5/part1/simple_config/)中的 `simple.py` 后生成的 `config.ini`。

    [root]
    type=Root
    children=system
    eventq_index=0
    full_system=false
    sim_quantum=0
    time_sync_enable=false
    time_sync_period=100000000000
    time_sync_spin_threshold=100000000

    [system]
    type=System
    children=clk_domain cpu dvfs_handler mem_ctrl membus
    boot_osflags=a
    cache_line_size=64
    clk_domain=system.clk_domain
    default_p_state=UNDEFINED
    eventq_index=0
    exit_on_work_items=false
    init_param=0
    kernel=
    kernel_addr_check=true
    kernel_extras=
    kvm_vm=Null
    load_addr_mask=18446744073709551615
    load_offset=0
    mem_mode=timing

    ...

    [system.membus]
    type=CoherentXBar
    children=snoop_filter
    clk_domain=system.clk_domain
    default_p_state=UNDEFINED
    eventq_index=0
    forward_latency=4
    frontend_latency=3
    p_state_clk_gate_bins=20
    p_state_clk_gate_max=1000000000000
    p_state_clk_gate_min=1000
    point_of_coherency=true
    point_of_unification=true
    power_model=
    response_latency=2
    snoop_filter=system.membus.snoop_filter
    snoop_response_latency=4
    system=system
    use_default_range=false
    width=16
    master=system.cpu.interrupts.pio system.cpu.interrupts.int_slave system.mem_ctrl.port
    slave=system.cpu.icache_port system.cpu.dcache_port system.cpu.interrupts.int_master system.system_port

    [system.membus.snoop_filter]
    type=SnoopFilter
    eventq_index=0
    lookup_latency=1
    max_capacity=8388608
    system=system

每个 SimObject 的描述都以方括号包围的对象名称开头，例如 `[system.membus]`；名称来自配置文件中建立的对象层次关系。

接下来列出该 SimObject 的每个参数（parameter）及其值，包括未在配置文件中显式设置的项。例如，脚本将时钟域（clock domain）的频率设为 1 GHz，对应此例中的 1000 tick 周期；但没有指定缓存（cache）行大小，`system` 对象使用的值是 64 字节。

`config.ini` 能帮助你确认实际模拟的系统是否符合预期。gem5 中有多种设置与覆盖默认值的方法，因此应始终检查该文件，核实配置脚本中的设定是否真正传递到了实例化的 SimObject。这是一项很有价值的基本检查。

stats.txt
---------

gem5 提供灵活的统计机制，详见[统计信息文档]({{ site.baseurl }}/documentation/general_docs/statistics/)。每个 SimObject 实例都有自己的统计信息。模拟（simulation）结束时，或执行特定的统计导出命令时，所有 SimObject 的当前统计状态都会写入文件。

文件首先包含整体执行情况：

    ---------- Begin Simulation Statistics ----------
    simSeconds                                   0.000057                       # Number of seconds simulated (Second)
    simTicks                                     57467000                       # Number of ticks simulated (Tick)
    finalTick                                    57467000                       # Number of ticks from beginning of simulation (restored from checkpoints and never reset) (Tick)
    simFreq                                  1000000000000                       # The number of ticks per simulated second ((Tick/Second))
    hostSeconds                                      0.03                       # Real time elapsed on the host (Second)
    hostTickRate                               2295882330                       # The number of ticks simulated per host second (ticks/s) ((Tick/Second))
    hostMemory                                     665792                       # Number of bytes of host memory used (Byte)
    simInsts                                         6225                       # Number of instructions simulated (Count)
    simOps                                          11204                       # Number of ops (including micro ops) simulated (Count)
    hostInstRate                                   247382                       # Simulator instruction rate (inst/s) ((Count/Second))
    hostOpRate                                     445086                       # Simulator op (including micro ops) rate (op/s) ((Count/Second))

    ---------- Begin Simulation Statistics ----------
    simSeconds                                   0.000490                       # Number of seconds simulated (Second)
    simTicks                                    490394000                       # Number of ticks simulated (Tick)
    finalTick                                   490394000                       # Number of ticks from beginning of simulation (restored from checkpoints and never reset) (Tick)
    simFreq                                  1000000000000                       # The number of ticks per simulated second ((Tick/Second))
    hostSeconds                                      0.03                       # Real time elapsed on the host (Second)
    hostTickRate                              15979964060                       # The number of ticks simulated per host second (ticks/s) ((Tick/Second))
    hostMemory                                     657488                       # Number of bytes of host memory used (Byte)
    simInsts                                         6225                       # Number of instructions simulated (Count)
    simOps                                          11204                       # Number of ops (including micro ops) simulated (Count)
    hostInstRate                                   202054                       # Simulator instruction rate (inst/s) ((Count/Second))
    hostOpRate                                     363571                       # Simulator op (including micro ops) rate (op/s) ((Count/Second))

每段统计输出以 `---------- Begin Simulation Statistics ----------` 开头。如果运行期间多次导出统计信息，一个文件中就会出现多个这样的区段；长时间运行应用程序或从检查点（checkpoint）恢复时，经常会出现这种情况。

每项统计包含名称（第一列）、数值（第二列），以及 `#` 后的说明（最后一列）；说明后还列出单位。

大多数统计项的含义可以从说明直接理解。几个重要指标是总模拟（simulation）时间、CPU 已提交的指令数，以及反映 gem5 自身运行速度的宿主指令处理速率。

> **译注：统计项命名。** 原文正文使用旧名称 `sim_seconds`、`sim_insts`、`host_inst_rate`，而上面的示例输出分别使用 `simSeconds`、`simInsts`、`hostInstRate`。分析结果时应以实际运行版本生成的名称和单位为准。被模拟程序的时间与 gem5 在宿主机上消耗的时间是不同的量。

随后输出各个 SimObject 的统计信息。例如，CPU 的统计包含系统调用次数，以及缓存（cache）系统、地址转换后备缓冲器（TLB）等信息：

    system.clk_domain.clock                          1000                       # Clock period in ticks (Tick)
    system.clk_domain.voltage_domain.voltage            1                       # Voltage in Volts (Volt)
    system.cpu.numCycles                            57467                       # Number of cpu cycles simulated (Cycle)
    system.cpu.numWorkItemsStarted                      0                       # Number of work items this cpu started (Count)
    system.cpu.numWorkItemsCompleted                    0                       # Number of work items this cpu completed (Count)
    system.cpu.dcache.demandHits::cpu.data           1941                       # number of demand (read+write) hits (Count)
    system.cpu.dcache.demandHits::total              1941                       # number of demand (read+write) hits (Count)
    system.cpu.dcache.overallHits::cpu.data          1941                       # number of overall hits (Count)
    system.cpu.dcache.overallHits::total             1941                       # number of overall hits (Count)
    system.cpu.dcache.demandMisses::cpu.data          133                       # number of demand (read+write) misses (Count)
    system.cpu.dcache.demandMisses::total             133                       # number of demand (read+write) misses (Count)
    system.cpu.dcache.overallMisses::cpu.data          133                       # number of overall misses (Count)
    system.cpu.dcache.overallMisses::total            133                       # number of overall misses (Count)
    system.cpu.dcache.demandMissLatency::cpu.data     14301000                       # number of demand (read+write) miss ticks (Tick)
    system.cpu.dcache.demandMissLatency::total     14301000                       # number of demand (read+write) miss ticks (Tick)
    system.cpu.dcache.overallMissLatency::cpu.data     14301000                       # number of overall miss ticks (Tick)
    system.cpu.dcache.overallMissLatency::total     14301000                       # number of overall miss ticks (Tick)
    system.cpu.dcache.demandAccesses::cpu.data         2074                       # number of demand (read+write) accesses (Count)
    system.cpu.dcache.demandAccesses::total          2074                       # number of demand (read+write) accesses (Count)
    system.cpu.dcache.overallAccesses::cpu.data         2074                       # number of overall (read+write) accesses (Count)
    system.cpu.dcache.overallAccesses::total         2074                       # number of overall (read+write) accesses (Count)
    system.cpu.dcache.demandMissRate::cpu.data     0.064127                       # miss rate for demand accesses (Ratio)
    system.cpu.dcache.demandMissRate::total      0.064127                       # miss rate for demand accesses (Ratio)
    system.cpu.dcache.overallMissRate::cpu.data     0.064127                       # miss rate for overall accesses (Ratio)
    system.cpu.dcache.overallMissRate::total     0.064127                       # miss rate for overall accesses (Ratio)
    system.cpu.dcache.demandAvgMissLatency::cpu.data 107526.315789                       # average overall miss latency ((Cycle/Count))
    system.cpu.dcache.demandAvgMissLatency::total 107526.315789                       # average overall miss latency ((Cycle/Count))
    system.cpu.dcache.overallAvgMissLatency::cpu.data 107526.315789                       # average overall miss latency ((Cycle/Count))
    system.cpu.dcache.overallAvgMissLatency::total 107526.315789                       # average overall miss latency ((Cycle/Count))
    ...
    system.cpu.mmu.dtb.rdAccesses                    1123                       # TLB accesses on read requests (Count)
    system.cpu.mmu.dtb.wrAccesses                     953                       # TLB accesses on write requests (Count)
    system.cpu.mmu.dtb.rdMisses                        11                       # TLB misses on read requests (Count)
    system.cpu.mmu.dtb.wrMisses                         9                       # TLB misses on write requests (Count)
    system.cpu.mmu.dtb.walker.power_state.pwrStateResidencyTicks::UNDEFINED     57467000                       # Cumulative time (in ticks) in various power states (Tick)
    system.cpu.mmu.itb.rdAccesses                       0                       # TLB accesses on read requests (Count)
    system.cpu.mmu.itb.wrAccesses                    7940                       # TLB accesses on write requests (Count)
    system.cpu.mmu.itb.rdMisses                         0                       # TLB misses on read requests (Count)
    system.cpu.mmu.itb.wrMisses                        37                       # TLB misses on write requests (Count)
    system.cpu.mmu.itb.walker.power_state.pwrStateResidencyTicks::UNDEFINED     57467000                       # Cumulative time (in ticks) in various power states (Tick)
    system.cpu.power_state.pwrStateResidencyTicks::ON     57467000                       # Cumulative time (in ticks) in various power states (Tick)
    system.cpu.thread_0.numInsts                        0                       # Number of Instructions committed (Count)
    system.cpu.thread_0.numOps                          0                       # Number of Ops committed (Count)
    system.cpu.thread_0.numMemRefs                      0                       # Number of Memory References (Count)
    system.cpu.workload.numSyscalls                    11                       # Number of system calls (Count)

文件后面还有内存控制器的统计信息，例如各组件读取的字节数及平均带宽：

    system.mem_ctrl.bytesReadWrQ                        0                       # Total number of bytes read from write queue (Byte)
    system.mem_ctrl.bytesReadSys                    23168                       # Total read bytes from the system interface side (Byte)
    system.mem_ctrl.bytesWrittenSys                     0                       # Total written bytes from the system interface side (Byte)
    system.mem_ctrl.avgRdBWSys               403153113.96105593                       # Average system read bandwidth in Byte/s ((Byte/Second))
    system.mem_ctrl.avgWrBWSys                 0.00000000                       # Average system write bandwidth in Byte/s ((Byte/Second))
    system.mem_ctrl.totGap                       57336000                       # Total gap between requests (Tick)
    system.mem_ctrl.avgGap                      158386.74                       # Average gap between requests ((Tick/Count))
    system.mem_ctrl.requestorReadBytes::cpu.inst        14656                       # Per-requestor bytes read from memory (Byte)
    system.mem_ctrl.requestorReadBytes::cpu.data         8512                       # Per-requestor bytes read from memory (Byte)
    system.mem_ctrl.requestorReadRate::cpu.inst 255033323.472601681948                       # Per-requestor bytes read from memory rate ((Byte/Second))
    system.mem_ctrl.requestorReadRate::cpu.data 148119790.488454252481                       # Per-requestor bytes read from memory rate ((Byte/Second))
    system.mem_ctrl.requestorReadAccesses::cpu.inst          229                       # Per-requestor read serviced memory accesses (Count)
    system.mem_ctrl.requestorReadAccesses::cpu.data          133                       # Per-requestor read serviced memory accesses (Count)
    system.mem_ctrl.requestorReadTotalLat::cpu.inst      6234000                       # Per-requestor read total memory access latency (Tick)
    system.mem_ctrl.requestorReadTotalLat::cpu.data      4141000                       # Per-requestor read total memory access latency (Tick)
    system.mem_ctrl.requestorReadAvgLat::cpu.inst     27222.71                       # Per-requestor read average memory access latency ((Tick/Count))
    system.mem_ctrl.requestorReadAvgLat::cpu.data     31135.34                       # Per-requestor read average memory access latency ((Tick/Count))
    system.mem_ctrl.dram.bytesRead::cpu.inst        14656                       # Number of bytes read from this memory (Byte)
    system.mem_ctrl.dram.bytesRead::cpu.data         8512                       # Number of bytes read from this memory (Byte)
    system.mem_ctrl.dram.bytesRead::total           23168                       # Number of bytes read from this memory (Byte)
    system.mem_ctrl.dram.bytesInstRead::cpu.inst        14656                       # Number of instructions bytes read from this memory (Byte)
    system.mem_ctrl.dram.bytesInstRead::total        14656                       # Number of instructions bytes read from this memory (Byte)
    system.mem_ctrl.dram.numReads::cpu.inst           229                       # Number of read requests responded to by this memory (Count)
    system.mem_ctrl.dram.numReads::cpu.data           133                       # Number of read requests responded to by this memory (Count)
    system.mem_ctrl.dram.numReads::total              362                       # Number of read requests responded to by this memory (Count)
    system.mem_ctrl.dram.bwRead::cpu.inst       255033323                       # Total read bandwidth from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwRead::cpu.data       148119790                       # Total read bandwidth from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwRead::total          403153114                       # Total read bandwidth from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwInstRead::cpu.inst    255033323                       # Instruction read bandwidth from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwInstRead::total      255033323                       # Instruction read bandwidth from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwTotal::cpu.inst      255033323                       # Total bandwidth to/from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwTotal::cpu.data      148119790                       # Total bandwidth to/from this memory ((Byte/Second))
    system.mem_ctrl.dram.bwTotal::total         403153114                       # Total bandwidth to/from this memory ((Byte/Second))
    system.mem_ctrl.dram.readBursts                   362                       # Number of DRAM read bursts (Count)
    system.mem_ctrl.dram.writeBursts                    0                       # Number of DRAM write bursts (Count)

---
layout: documentation
title: 跟踪（trace）CPU 模型
parent: cpu_models
doc: gem5 文档
permalink: /documentation/general_docs/cpu_models/TraceCPU
---
# **TraceCPU**
 目录


1. [概述](##Overveiw)


 1. [弹性跟踪（elastic trace）生成](##Elastic-Trace-Generation)
       1. [脚本与选项](##Scripts-and-options)
       2. [跟踪文件格式](###Trace-file-formats)





 2. [用 Trace CPU 回放](#replay-with-trace-cpu)
       1. [脚本与选项](##Scripts-and-options)




## **概述**
Trace CPU 模型用于回放弹性跟踪（elastic trace），这些跟踪由挂载在 O3 CPU 模型上的 Elastic Trace Probe 生成，带有依赖与时序标注。Trace CPU 模型的关注点是以快速且合理精确的方式探索内存系统（缓存层次结构、互连与主存）的性能，而不是使用详细但缓慢的 O3 CPU 模型。这些跟踪是为在 SE 和 FS 模式下模拟的单线程基准测试（benchmark）开发的。通过把 Trace CPU 与 classic 内存系统对接，并改变缓存设计参数和 DRAM 内存类型，它们已针对 15 个对内存敏感的 SPEC 2006 基准测试以及少量 HPC 代理应用进行了相关性验证。一般而言，弹性跟踪可以移植到其他模拟环境中。

 **论文**：

[Exploring System Performance using Elastic Traces: Fast, Accurate and Portable"](https://ieeexplore.ieee.org/document/7818336) Radhika Jagtap, Stephan Diestelhorst, Andreas Hansson, Matthias Jung and Norbert Wehn SAMOS 2016

**跟踪生成与回放方法**

![方法框图：使用 O3 CPU 生成弹性跟踪并用 Trace CPU 回放
](/assets/img/Etrace_methodology.jpg)

## **弹性跟踪（elastic trace）生成**
Elastic Trace Probe Listener 监听插入 O3 CPU 流水线各级的 Probe Point。它监视每条指令，通过记录数据写后读（Read-After-Write）依赖以及加载与存储之间的顺序依赖来构建依赖图。它把指令取指请求跟踪和弹性数据内存请求跟踪写成两个独立的文件，如下所示。

![弹性跟踪文件生成](/assets/img/Etraces_output.jpg)

### **跟踪文件格式**

弹性数据内存跟踪和取指请求跟踪都使用 google protobuf 编码。

##### **protobuf 格式的弹性跟踪字段**

字段    | 说明
-------------- | -------------
required uint64 seq_num &nbsp;   | 用作追踪依赖的 id 的指令编号
required RecordType type &nbsp;    | RecordType 枚举的取值有：INVALID、LOAD、STORE、COMP
optional uint64 p_addr &nbsp; 	| 如果指令是加载/存储，则为物理内存地址
optional uint32 size &nbsp; 	| 如果指令是加载/存储，则为数据的字节大小
optional uint32 flags &nbsp; 	| 	该访问的标志或属性，例如 Uncacheable
required uint64 rob_dep &nbsp;  |   所依赖的、存在顺序（ROB）依赖的过去指令编号
required uint64 comp_delay &nbsp;       |	最后一个依赖完成到该指令执行之间的执行延迟 &nbsp;
repeated uint64 reg_dep &nbsp;              | 所依赖的、存在 RAW 数据依赖的过去指令编号
optional uint32 weight &nbsp; | 	用于补偿被过滤掉的已提交指令
optional uint64 pc &nbsp; | 指令地址，即程序计数器
optional uint64 v_addr &nbsp; | 	如果指令是加载/存储，则为虚拟内存地址
optional uint32 asid &nbsp; | 地址空间 ID

`util/decode_inst_dep_trace.py` 中有一个 Python 解码脚本，可以把跟踪输出为 ASCII 格式。

**ASCII 格式的跟踪示例**

    1,356521,COMP,8500::

    2,35656,1,COMP,0:,1:

    3,35660,1,LOAD,1748752,4,74,500:,2:

    4,35660,1,COMP,0:,3:

    5,35664,1,COMP,3000::,4

    6,35666,1,STORE,1748752,4,74,1000:,3:,4,5

    7,35666,1,COMP,3000::,4

    8,35670,1,STORE,1748748,4,74,0:,6,3:,7

    9,35670,1,COMP,500::,7

指令取指跟踪中的每条记录包含以下字段。

字段    | 说明
-------------- | -------------
required uint64 tick &nbsp;   |	该访问的时间戳
required uint32 cmd	&nbsp;    | 读或写（此处总是读）
required uint64 addr &nbsp;	| 物理内存地址
required uint32 size &nbsp;	| 数据的字节大小
optional uint32 flags &nbsp;	| 该访问的标志或属性
optional uint64 pkt_id &nbsp;  |   该访问的 id
optional uint64 pc  &nbsp;     |	指令地址，即程序计数器



`util/decode_packet_trace.py` 中的 Python 解码脚本可用于把跟踪输出为 ASCII 格式。


**编译依赖**：

你需要安装 google protocol buffer，因为跟踪是用它记录的。

```sh

sudo apt-get install protobuf-compiler
sudo apt-get install libprotobuf-dev

```

### **脚本与选项**
#### SE 模式
```
build/ARM/gem5.opt configs/example/arm/etrace_se.py \
    --inst-trace-file fetchtrace.proto.gz \
    --data-trace-file deptrace.proto.gz \
    [WORKLOAD]
```
#### FS 模式
为你的关注区域创建检查点（checkpoint），然后使用 O3 CPU 模型并启用跟踪，从该检查点恢复。
```
# Checkpoint generation
# NOTE: fs.py is deprecated and will be removed. Do not rely too much on it
build/ARM/gem5.opt --outdir=m5out/bbench \
    ./configs/deprecated/example/fs.py [fs.py options] \
    --benchmark bbench-ics
```
```
# Checkpoint restore
# NOTE: fs.py is deprecated and will be removed. Do not rely too much on it
build/ARM/gem5.opt --outdir=m5out/bbench/capture_10M \
    ./configs/deprecated/example/fs.py [fs.py options] \
    --cpu-type=arm_detailed --caches \
    --elastic-trace-en --data-trace-file=deptrace.proto.gz --inst-trace-file=fetchtrace.proto.gz \
    --mem-type=SimpleMemory \
    --checkpoint-dir=m5out/bbench -r 0 --benchmark bbench-ics -I 10000000
```

## **用 Trace CPU 回放**

上面生成的执行跟踪随后由 Trace CPU 消费，如下图所示。

![Trace_cpu_top_level](/assets/img/Trace_cpu_top_level.jpg)

Trace CPU 模型继承自 Base CPU，并与数据与指令 L1 缓存对接。下面给出 Trace CPU 的框图，说明其主要逻辑与控制块。

![Trace_CPU_details](/assets/img/Trace_cpu_detail.jpg)

### **脚本与选项**

* examples 文件夹中的跟踪回放脚本可用于回放 SE 和 FS 生成的跟踪
    * `build/ARM/gem5.opt [gem5.opt options] -d bzip_10Minsts_replay configs/example/etrace_replay.py [options] --caches --data-trace-file=bzip_10Minsts/deptrace.proto.gz --inst-trace-file=bzip_10Minsts/fetchtrace.proto.gz --mem-size=4GB`






字段    | 说明
-------------- | -------------
required uint64 seq_num    |	该访问的时间戳
required RecordType type    | 读或写（此处总是读）
optional uint64 p_addr	| 如果指令是加载/存储，则为物理内存地址
optional uint32 size	| 如果指令是加载/存储，则为数据的字节大小
optional uint32 flags	| 该访问的标志或属性，例如 Uncacheable
required uint64 rob_dep | 所依赖的、存在顺序（ROB）依赖的过去指令编号
required uint64 comp_delay | 最后一个依赖完成到该指令执行之间的执行延迟
repeated uint64 reg_dep | 所依赖的、存在 RAW 数据依赖的过去指令编号
optional uint32 weight | 用于补偿被过滤掉的已提交指令
optional uint64 pc	| 指令地址，即程序计数器
optional uint64 v_addr | 如果指令是加载/存储，则为虚拟内存地址
optional uint32 asid |	地址空间 ID

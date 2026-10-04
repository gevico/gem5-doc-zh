---
layout: documentation
title: 检查点（checkpoint）
doc: gem5 文档
parent: checkpoints
permalink: /documentation/general_docs/checkpoints/
---

# 检查点（checkpoint）

检查点（checkpoint）本质上是模拟（simulation）的快照。当你的模拟耗时极长时（几乎总是如此），你会希望使用检查点，这样之后可以用 DerivO3CPU 从该检查点恢复。

## 创建

首先，你需要创建一个检查点。每个检查点都会保存在一个名为 'cpt.TICKNUMBER' 的新目录中，其中 TICKNUMBER 指创建该检查点时的 tick 值。创建检查点有几种方式：

* 启动 gem5 模拟器（simulator）后，执行命令 m5 checkpoint。你可以用 m5term 手动执行该命令，也可以把它写进运行脚本，在 Linux 内核启动完成后自动执行。
* 有一条伪指令可用于创建检查点。例如，你可以在应用程序中加入该伪指令，使应用到达某个状态时创建检查点。
* 可以把 **-****-take-checkpoints** 选项传给 python 脚本（fs.py、ruby_fs.py），以便定期导出检查点。**-****-checkpoint-at-end** 选项可用于在模拟结束时创建检查点。这些选项请查看文件 **configs/common/Options.py**。

在使用 Ruby 内存模型创建检查点时，必须使用 MOESI hammer 协议。这是因为要正确地检查点化内存状态，需要把缓存刷写到内存。目前只有 MOESI hammer 协议支持该刷写操作。

## 恢复

从检查点恢复通常可以在命令行中轻松完成，例如：

```console
  build/ALL/gem5.debug configs/example/fs.py -r N
  OR
  build/ALL/gem5.debug configs/example/fs.py --checkpoint-restore=N
```

数字 N 是表示检查点编号的整数，通常从 1 开始，递增到 2、3、4……

默认情况下，gem5 假定使用 Atomic CPU 恢复检查点。如果该检查点是用 Timing / Detailed / Inorder CPU 记录的，这可能无法工作。可以在命令行中指定 <br /> **-****-restore-with-cpu \<CPU Type\>** 选项。随后将使用该选项提供的 CPU 类型从检查点恢复。

## 详细示例：Parsec

下面我们将描述如何为 PARSEC 基准测试（benchmark）套件的工作负载（workload）创建检查点。不过，对于 PARSEC 之外的
其他工作负载，也可以采用类似流程。以下是创建检查点的高层步骤：

1. 为每个工作负载标注关注区域（Region of Interest）的起止，以及程序中工作单元的起止。
2. 在关注区域开始时创建检查点。
3. 在关注区域内模拟整个程序，并定期创建检查点。
4. 分析定期检查点对应的统计信息（statistics），选出程序执行中最有意思的部分。
5. 在到达程序最有趣的部分之前，为 Ruby 生成预热缓存跟踪，并创建最终检查点。
在接下来的各节中，我们会更详细地解释上述每一步。

### 标注工作负载

标注有两个用途：界定程序中初始化部分之后的范围，以及定义每个工作负载中的逻辑工作单元。

PARSEC 基准测试套件中的工作负载已经带有标注，标出了程序初始化部分与结束部分之外的起止位置。我们只需使用 gem5 特有的标注来标记关注区域的开始。关注区域（ROI）的开始由 **m5_roi_begin()** 标记，ROI 的结束由 **m5_roi_end()** 标记。

由于模拟时间很长，并非总能模拟整个程序。此外，与单线程程序不同，在多线程工作负载中模拟给定数量的指令并不是模拟程序一部分的正确方式，因为可能存在在同步变量上自旋的指令。因此，在每个工作负载中定义语义上有意义的逻辑工作单元非常重要。在多线程工作负载中模拟给定数量的工作单元，是在考虑到同步变量自旋指令问题的情况下模拟部分工作负载的合理方式。

# 切换/快进

## 采样

采样（在功能模型与详细模型之间切换）可以通过你的 Python 脚本实现。在脚本中，你可以指示模拟器在两套 CPU 之间切换。为此，在脚本中设置一个由 (oldCPU, newCPU) 元组构成的列表。如果你希望同时切换多个 CPU，可以把它们都加入该列表。例如：

```python
run_cpu1 = SimpleCPU()
switch_cpu1 = DetailedCPU(switched_out=True)
run_cpu2 = SimpleCPU()
switch_cpu2 = FooCPU(switched_out=True)
switch_cpu_list = [(run_cpu1,switch_cpu1),(run_cpu2,switch_cpu2)]
```

注意，不会立即运行的 CPU 应设置参数 "switched_out=True"。这会使这些 CPU 不把自己加入要运行的 CPU 列表；它们会在你切入时被加入。

为了让 gem5 实例化你的所有 CPU，你必须让将被切入的 CPU 成为配置层次结构中某个对象的子对象。遗憾的是，目前某些配置限制迫使被切换的 CPU 必须放在 System 对象之外。Root 对象是放置 CPU 的次优便利位置，如下所示：

```python
m5.simulate(500)  # simulate for 500 cycles
m5.switchCpus(switch_cpu_list)
m5.simulate(500)  # simulate another 500 cycles after switching
```

注意，由于被切出的 CPU 中可能存在未完成状态，gem5 可能需要在切换 CPU 之前再模拟几个周期。

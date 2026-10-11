---
layout: documentation
title: "ARM DVFS 支持"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/arm_dvfs_support/
author: Thomas E. Hansen
---

ARM DVFS 建模
==================

与大多数现代 CPU 一样，ARM CPU 支持动态电压与频率调整（DVFS）。gem5 可以对其建模，例如观察调整后功率消耗的变化。DVFS 建模依赖时钟驱动对象的两个组成部分：电压域和时钟域（clock domain）。本章介绍它们，并展示如何加入已有的模拟（simulation）。

电压域
---------------

电压域规定 CPU 可使用的电压值。在本章的全系统（full-system）配置中，如果没有显式指定电压，就使用默认的 1.0 V，使不关注电压的用户无需额外配置。

创建 `VoltageDomain` 时，可以通过 `voltage` 关键字参数（parameter）传入单个值或一个列表。若只指定一个电压值而提供多个频率，该电压适用于所有频率；若指定多个电压值，数量必须与对应时钟域（clock domain）的频率档位数一致，并按*降序*排列。本例按整个处理器插槽设置电压域。因此，若希望 big.LITTLE 等配置中的不同处理器采用不同电压域，需要确保 big 与 LITTLE 集群属于不同插槽，检查集群对应的 `socket_id`。

可以通过两种方式为已有 CPU 配置加入电压域：修改 `configs/example/arm/fs_bigLITTLE.py`，增加命令行选项；或者定义自有类。前者更灵活，后者更直接。

1. 使用命令行选项最为灵活。在文件中找到 `addOptions`，加入选项及相应帮助说明。下面的示例同时支持一个或多个电压值：

   ```python
   def addOptions(parser):
       [...]
       parser.add_argument("--big-cpu-voltage", nargs="+", default="1.0V",
                           help="Big CPU voltage(s).")
       return parser
   ```

   运行时可以这样指定电压：

   ```
   --big-cpu-voltage <val1>V [<val2>V [<val3>V [...]]]
   ```

   在 `build` 中通过 `options.big_cpu_voltage` 读取。`nargs="+"` 表示至少提供一个值。使用示例如下：

   ```python
   def build(options):
       [...]
       # big cluster
       if options.big_cpus > 0:
           system.bigCluster = big_model(system, options.big_cpus,
                                         options.big_cpu_clock,
                                         options.big_cpu_voltage)
       [...]
   ```

   为 LITTLE CPU 设置电压时，也可以添加类似选项并修改 `build`。这种方式便于指定和调整电压；不足之处是选项较多，且部分为列表，会使启动模拟器（simulator）的命令较长。

2. 另一种方式是创建 `CpuCluster` 的子类，与现有的 `BigCluster`、`LittleCluster` 类似。在子类构造函数中，除了指定 CPU 类型，还定义电压列表，并通过 `cpu_voltage` 关键字参数（parameter）传给父类构造函数。为 `BigCluster` 添加电压的示例如下：

   ```python
   class VDBigCluster(devices.CpuCluster):
       def __init__(self, system, num_cpus, cpu_clock=None, cpu_voltage=None):
           # use the same CPU as the stock BigCluster
           abstract_cpu = ObjectList.cpu_list.get("O3_ARM_v7a_3")
           # voltage value(s)
           my_voltages = [ '1.0V', '0.75V', '0.51V']

           super(VDBigCluster, self).__init__(
               cpu_voltage=my_voltages,
               system=system,
               num_cpus=num_cpus,
               cpu_type=abstract_cpu,
               l1i_type=devices.L1I,
               l1d_type=devices.L1D,
               wcache_type=devices.WalkCache,
               l2_type=devices.L2
           )
   ```

   同理，可以定义 `VDLittleCluster` 为 LITTLE 集群设置电压。

   定义子类后，还需要在 `cpu_types` 字典中加入条目，以字符串名称为键，以一对类为值，例如：

   ```python
   cpu_types = {
       [...]
       "vd-timing" : (VDBigCluster, VDLittleCluster)
   }
   ```

   随后在启动命令中加入以下选项，使用这些配置了电压域的 CPU：

   ```
   --cpu-type vd-timing
   ```

   这种方式下，每次更改电压都需要修改相应子类，或者添加新子类和 `cpu_types` 条目，因此灵活性低于命令行选项方式。

时钟域（clock domain）
-------------

电压域与时钟域（clock domain）配合使用。如前所述，若未自定义电压，本例的所有频率档位均使用 1.0 V。

### 时钟域（clock domain）的类型

`src/sim/clock_domain.hh` 定义了三类相关对象：

- `ClockDomain`：为归属于同一时钟域（clock domain）的时钟驱动对象提供时钟。时钟域（clock domain）又归属于电压域，并支持由源域和派生域构成的层级结构。
- `SrcClockDomain`：连接到可调节的时钟源，维护时钟周期，提供设置和读取时钟的方法，并保存管理器所需的配置参数（parameter），包括各性能级别的频率、域编号和当前性能级别。软件请求的一个性能级别对应一个可用的频率工作点。
- `DerivedClockDomain`：连接到父时钟域（clock domain），父域可以是 `SrcClockDomain` 或另一个 `DerivedClockDomain`。它维护分频系数，并提供读取时钟的方法。

为已有模拟（simulation）添加时钟域（clock domain）
----------------------------------------------

本节继续使用 `configs/example/arm/fs_bigLITTLE.py` 和 `configs/example/arm/devices.py`。

时钟频率也可以指定为单个值或列表。若同时提供频率列表和多值电压列表，两者长度必须一致，频率也必须按*降序*排列。随附脚本的 `--{big,little}-cpu-clock` 选项只支持单个值。扩展现有选项以支持多个值最简单，也最灵活；同样也可以通过子类实现。

> **译注**：频率与电压列表必须等长的要求，针对多值电压列表；如前文所述，单个电压值也可用于多个频率档位。

1. 在 `fs_bigLITTLE.py` 的 `addOptions` 中找到添加 CPU 时钟选项的 `parser.add_argument`，将 `type=str` 改为 `nargs="+"`：

   ```python
   def addOptions(parser):
       [...]
       parser.add_argument("--big-cpu-clock", nargs="+", default="2GHz",
                           help="Big CPU clock frequency.")
       parser.add_argument("--little-cpu-clock", nargs="+", default="1GHz",
                           help="Little CPU clock frequency.")
       [...]
   ```

   然后像电压选项一样指定多个频率：

   ```
   --{big,little}-cpu-clock <val1>GHz [<val2>MHz [<val3>MHz [...]]]
   ```

   由于修改的是已有选项，`build` 中已经将其值传递给相应的构造函数，不需要额外修改。

2. 使用子类的过程与添加电压域类似，只是改为定义频率列表，并在调用父类构造函数时使用 `cpu_clock`：

   ```python
   class CDBigCluster(devices.CpuCluster):
       def __init__(self, system, num_cpus, cpu_clock=None, cpu_voltage=None):
           # use the same CPU as the stock BigCluster
           abstract_cpu = ObjectList.cpu_list.get("O3_ARM_v7a_3")
           # clock value(s)
           my_freqs = [ '1510MHz', '1000MHz', '667MHz']

           super(VDBigCluster, self).__init__(
               cpu_clock=my_freqs,
               system=system,
               num_cpus=num_cpus,
               cpu_type=abstract_cpu,
               l1i_type=devices.L1I,
               l1d_type=devices.L1D,
               wcache_type=devices.WalkCache,
               l2_type=devices.L2
           )
   ```

   可以与前面的电压域示例合并，同时为集群指定电压和频率档位。

   同样，需要为希望使用的每种 CPU 类型定义相应类，并在 `cpu_types` 字典中设置名称与 CPU 类对的映射。这种方法具有与电压域子类方案相同的限制，修改起来不如命令行选项灵活。

确保 DomainID 有效
-------------------------------------

无论采用哪种方式，还需要修改 `configs/example/arm/devices.py`。

找到 CPU 集群类中用 `SrcClockDomain` 初始化 `self.clk_domain` 的位置。该对象带有域编号；如果像原始配置那样未设置，就使用默认的 `-1`。应改为显式指定有效编号：

```python
[...]
self.clk_domain = SrcClockDomain(clock=cpu_clock,
                                 voltage_domain=self.voltage_domain,
                                 domain_id=system.numCpuClusters())
[...]
```

这里使用 `system.numCpuClusters()`，因为每个集群对应一个时钟域（clock domain）：第一个集群为 0，第二个为 1，依此类推。

> **译注**：原文在此将类名写成 `CpuClusters`；前文与相关脚本通常使用 `CpuCluster`，应以实际文件为准。

如果不设置编号，在运行支持 DVFS 的模拟（simulation）时，内部检查会发现默认值无效，并报错：

```
fatal: fatal condition domain_id == SrcClockDomain::emptyDomainID occurred:
DVFS: Controlled domain system.bigCluster.clk_domain needs to have a properly
assigned ID.
```

DVFS 管理器
----------------

配置电压域和时钟域（clock domain）后，模拟（simulation）可能已经能运行，但输出中可能出现以下警告：

```
warn: Existing EnergyCtrl, but no enabled DVFSHandler found.
```

原因是尚未提供供系统调节工作点的 `DVFSHandler`。最简单的处理方式是在 `configs/example/arm/fs_bigLITTLE.py` 中再加入一个命令行选项。

在 `addOptions` 中加入：

```python
def addOptions(parser):
    [...]
    parser.add_argument("--dvfs", action="store_true",
                        help="Enable the DVFS Handler.")
    return parser
```

然后在 `build` 中加入：

```python
def build(options):
    [...]
    if options.dvfs:
        system.dvfs_handler.domains = [system.bigCluster.clk_domain,
                                       system.littleCluster.clk_domain]
        system.dvfs_handler.enable = options.dvfs

    return root
```

完成后，在启动命令中使用 `--dvfs` 即可启用 DVFS 支持，并按需要指定 big 与 LITTLE 集群各自的电压、频率工作点。

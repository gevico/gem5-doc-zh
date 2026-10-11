---
layout: documentation
title: "ARM 功耗建模"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/arm_power_modelling/
author: Thomas E. Hansen
---

ARM 功耗建模
===================

gem5 可以对模拟（simulation）过程中的功率与能耗进行建模和监测。方法是使用 `MathExprPowerModel`，将 gem5 已有的统计数据代入数学表达式，计算功率。本章介绍功耗建模所需的组成部分，以及如何将其加入已有的 ARM 模拟（simulation）。

本章以 `configs/example/arm` 中的 `fs_power.py` 为例，也介绍如何扩展该脚本或其他脚本。

注意，本章示例的功耗模型（power model）要求使用较详细的 `timing` CPU 配置。

关于 gem5 功耗建模的整体设计，以及它与模拟器（simulator）其他部分的交互，可以参考 Sascha Bischoff 在 2017 年 ARM Research Summit 上的[演讲](https://youtu.be/3gWyUWHxVj4)。

运行时的电源状态
--------------------

功耗模型（power model）通过两个表达式，分别计算某一电源状态下的功率组成。`src/sim/PowerState.py` 定义了以下电源状态：

- `UNDEFINED`：无效状态，无法获取由电源状态派生的信息。这是默认状态。
- `ON`：逻辑模块正在运行，会根据处理活动消耗动态能量和漏电能量。
- `CLK_GATED`：模块内部的时钟电路被门控，以降低动态能耗；模块仍然供电，因此仍有漏电能耗。
- `SRAM_RETENTION`：逻辑模块中的 SRAM 进入数据保持状态，进一步降低漏电能耗。
- `OFF`：逻辑模块被电源门控，在该模型中不消耗能量。

除 `UNDEFINED` 外，每种状态都通过 `PowerModel` 类的 `pm` 字段对应一个功耗模型（power model）。`pm` 是包含四个元素的列表，顺序如下：

0. `ON`
1. `CLK_GATED`
2. `SRAM_RETENTION`
3. `OFF`

四个条目不必采用四种不同的功耗模型（power model）。随附的 `fs_power.py` 为 `ON` 使用一种模型，其余状态使用同一种模型。

功率的类型
-----------------

gem5 模拟器（simulator）区分两类功率：

- **静态功率**：与系统活动无关的功率消耗。
- **动态功率**：由各种活动产生的功率消耗。

每个功耗模型（power model）都必须提供两类功率的计算表达式。如果不需要考虑静态功率，或它在该模型中无关紧要，可以简单地写成 `st = "0"`。

MathExprPowerModel
-------------------

`fs_power.py` 中的功耗模型（power model）继承 `MathExprPowerModel`。它以字符串形式的数学表达式描述功率计算方式，通常同时引用统计项和温度等自动变量，例如：

```python
class CpuPowerOn(MathExprPowerModel):
    def __init__(self, cpu_path, **kwargs):
        super(CpuPowerOn, self).__init__(**kwargs)
        # 2A per IPC, 3pA per cache miss
        # and then convert to Watt
        self.dyn = "voltage * (2 * {}.ipc + 3 * 0.000000001 * " \
                   "{}.dcache.overall_misses / sim_seconds)".format(cpu_path,
                                                                    cpu_path)
        self.st = "4 * temp"
```

以上示例取自 `fs_power.py`。

自动变量 `voltage` 和 `temp` 不需要对象路径；组件专属的统计项，例如 CPU 每周期指令数 `ipc`，则需要完整路径。该文件的 `main` 函数中调用 CPU 对象的 `path()`，获取它在系统中的路径，例如 `system.bigCluster.cpus0`。这个方法由 `SimObject` 提供，因此其他派生对象也能使用，后面的 L2 缓存（cache）对象就采用了相同方法。

注意表达式将 `dcache.overall_misses` 除以 `sim_seconds`，使按访问次数累积的量转换为单位时间的量，并结合系数与电压得到瓦特。这里建立的是*功率*模型，即单位时间的能量消耗，而不是能量模型。虽然日常表述中经常混用这两个词，在功率与能耗模拟（simulation）中必须严格区分。

> **译注**：此处保留原始示例公式。其注释中的 `3pA` 与代码里的 `3 * 0.000000001` 并不一致；未命中次数除以时间后的系数还需要与其量纲相匹配。该示例用于展示表达式写法，不能直接当作经过硬件校准的功率估计。

扩展已有模拟（simulation）
--------------------------------

`fs_power.py` 导入并修改 `fs_bigLITTLE.py` 的配置。在此过程中，脚本遍历 SimObject 的后代对象，为它们设置功耗模型（power model）。扩展已有模拟（simulation）时，可以定义如下辅助函数：

```python
def _apply_pm(simobj, power_model, so_class=None):
    for desc in simobj.descendants():
        if so_class is not None and not isinstance(desc, so_class):
            continue

        desc.power_state.default_state = "ON"
        desc.power_model = power_model(desc.path())
```

该函数接收一个 SimObject、一个功耗模型（power model）类，以及可选的对象类型。指定类型后，仅为属于该类型的后代对象应用模型；不指定则应用到所有后代对象。

无论是否采用辅助函数，都需要先定义功耗模型（power model）。可以遵循 `fs_power.py` 的模式：

0. 为关心的各个电源状态定义继承 `MathExprPowerModel` 的类，包含 `dyn` 和 `st` 字段，分别以字符串描述该状态下动态功率与静态功率的计算方法。构造函数接收对象路径，通过 `format` 将路径填入表达式，并将其他关键字参数（parameter）传给父类构造函数。
1. 定义继承 `PowerModel` 的汇总类。其 `pm` 字段包含四个元素，`pm[0]` 对应 `ON`，`pm[1]` 对应 `CLK_GATED`，其后依次对应另外两种状态。构造函数接收要传给各状态模型的路径，并把其他关键字参数（parameter）传给父类。
2. 定义好辅助函数与模型类后，扩展 `build` 函数应用它们。也可以在 `addOptions` 中增加命令行选项，控制是否启用这些模型。

> **实现示例：**
>
> ```python
> class CpuPowerOn(MathExprPowerModel):
>     def __init__(self, cpu_path, **kwargs):
>         super(CpuPowerOn, self).__init__(**kwargs)
>         self.dyn = "voltage * 2 * {}.ipc".format(cpu_path)
>         self.st = "4 * temp"
>
>
> class CpuPowerClkGated(MathExprPowerModel):
>     def __init__(self, cpu_path, **kwargs):
>         super(CpuPowerOn, self).__init__(**kwargs)
>         self.dyn = "voltage / sim_seconds"
>         self.st = "4 * temp"
>
>
> class CpuPowerOff(MathExprPowerModel):
>     dyn = "0"
>     st = "0"
>
>
> class CpuPowerModel(PowerModel):
>     def __init__(self, cpu_path, **kwargs):
>         super(CpuPowerModel, self).__init__(**kwargs)
>         self.pm = [
>             CpuPowerOn(cpu_path),       # ON
>             CpuPowerClkGated(cpu_path), # CLK_GATED
>             CpuPowerOff(),              # SRAM_RETENTION
>             CpuPowerOff(),              # OFF
>         ]
>
> [...]
>
> def addOptions(parser):
>     [...]
>     parser.add_argument("--power-models", action="store_true",
>                         help="Add power models to the simulated system. "
>                              "Requires using the 'timing' CPU."
>     return parser
>
>
> def build(options):
>     root = Root(full_system=True)
>     [...]
>     if options.power_models:
>         if options.cpu_type != "timing":
>             m5.fatal("The power models require the 'timing' CPUs.")
>
>         _apply_pm(root.system.bigCluster.cpus, CpuPowerModel
>                   so_class=m5.objects.BaseCpu)
>         _apply_pm(root.system.littleCluster.cpus, CpuPowerModel)
>
>     return root
>
> [...]
> ```

> **译注**：以上示例按原文保留，但并非可直接运行的完整脚本：`CpuPowerClkGated` 中的 `super` 应引用本类；`parser.add_argument` 缺少右括号；调用 `_apply_pm` 时 `CpuPowerModel` 后缺少逗号，`BaseCpu` 的大小写也应按实际 API 核对（通常为 `BaseCPU`）。此外，辅助函数要求输入具有 `descendants()` 的 SimObject，若传入的是 `cpus` 列表，应逐个处理其中的对象。

统计项名称
----------

表达式中的统计项名称通常与模拟（simulation）结束后 `m5out/stats.txt` 中的名称一致，但存在例外：

- CPU 时钟在 `stats.txt` 中显示为 `clk_domain.clock`，功耗模型（power model）中访问时使用的是 `clock_period`，*不是* `clock`。

统计输出间隔
-------------------

本例按每秒模拟（simulation）时间向 `stats.txt` 输出一次统计数据。调用 `m5.stats.periodicStatDump` 可以调整这一间隔；它接受的单位是模拟（simulation）中的 tick，而不是秒。可以用 `m5.ticks.fromSeconds` 转换。

> **译注**：原文将每秒输出一次称为 gem5 的默认行为；周期性输出实际取决于配置脚本是否安排了统计事件。此外，此处所谓“frequency”选项的数值含义是输出*间隔*，单位为秒，并非以 Hz 表示的频率。

下图取自 [Sascha Bischoff 的演讲](https://youtu.be/3gWyUWHxVj4)第 16 页，比较了 1 秒与 1 毫秒采样间隔对结果分辨率的影响。

![1 秒与 1 毫秒采样间隔的功率曲线对比]({{ site.baseurl }}/pages/static/figures/empowering_the_masses_slide16.png)

输出间隔直接决定根据 `stats.txt` 绘图时可获得的时间分辨率，也影响文件大小。从每秒输出一次改为每毫秒一次，可能使文件增大数百倍，因此需要按需求选择间隔。

在 `fs_power.py` 中可以这样设置：

```python
[...]

def addOptions(parser):
    [...]
    parser.add_argument("--stat-freq", type=float, default=1.0,
                        help="Frequency (in seconds) to dump stats to the "
                             "'stats.txt' file. Supports scientific notation, "
                             "e.g. '1.0E-3' for milliseconds.")
    return parser

[...]

def main():
    [...]
    m5.stats.periodicStatDump(m5.ticks.fromSeconds(options.stat_freq))
    bL.run()

[...]
```

运行时通过以下选项指定间隔：

```
--stat-freq <val>
```

常见问题
---------------

使用 `fs_power.py` 时，可能遇到以下错误：

- `fatal: statistic '' (160) was not properly initialized by a regStats() function`
- `fatal: Failed to evaluate power expressions: [...]`

原文写作时，这些问题与 gem5 统计框架的重构有关。更新当时的源代码并重新构建可以解决；若不能更新，则需要以下两组补丁：

1. [https://gem5-review.googlesource.com/c/public/gem5/+/26643](https://gem5-review.googlesource.com/c/public/gem5/+/26643)
2. [https://gem5-review.googlesource.com/c/public/gem5/+/26785](https://gem5-review.googlesource.com/c/public/gem5/+/26785)

可按照各链接中的下载说明检出并应用补丁。对于较新版本，应先检查具体的统计项名称与表达式，不能仅凭相同错误信息判断仍需应用这些历史补丁。

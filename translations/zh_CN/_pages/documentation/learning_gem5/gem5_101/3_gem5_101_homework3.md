---
layout: documentation
title: "作业 3"
doc: 学习 gem5
parent: gem5_101
permalink: /documentation/learning_gem5/gem5_101/homework-3
authors:
---

# CS 752 作业 3：高级计算机体系结构（architecture）I（2015 年秋季，唯一班级）

**截止日期：9 月 29 日，星期二，下午 1 点。**

**独立完成，不接受迟交。**

本作业通过流水线 CPU 实验，先用简单时序 CPU 分析程序的指令组成，再用流水线顺序（in-order）CPU 研究不同阶段的延迟和带宽对性能的影响。还会学习用于实验控制的伪指令。作业基于 *Computer Architecture: A Quantitative Approach* 第三版练习 3.6。

> **译注**：这是 2015 年的历史作业。以下 m5ops 头文件位置与 Makefile 构建方法属于旧版 gem5；较新版本应参照对应版本的 m5ops 文档。课程日期和提交方式按原文保留。

----

## 实验步骤

### 1. 运行 DAXPY

DAXPY，即双精度 `aX + Y`，是矩阵和向量计算中的常见操作。以下为 C++11 实现。

```cpp
  #include <cstdio>
  #include <random>

  int main()
  {
    const int N = 1000;
    double X[N], Y[N], alpha = 0.5;
    std::random_device rd; std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(1, 2);
    for (int i = 0; i < N; ++i)
    {
      X[i] = dis(gen);
      Y[i] = dis(gen);
    }

    // Start of daxpy loop
    for (int i = 0; i < N; ++i)
    {
      Y[i] = alpha * X[i] + Y[i];
    }
    // End of daxpy loop

    double sum = 0;
    for (int i = 0; i < N; ++i)
    {
      sum += Y[i];
    }
    printf("%lf\n", sum);
    return 0;
  }
```

将程序静态编译，并使用 `TimingSimpleCPU` 运行。编译时使用 `-O2`，以避免原课程版本中尚未实现的 x87 指令。报告各操作类别的指令分布，可以在 `stats.txt` 中搜索 `op_class`。

### 2. 只统计核心计算区间

使用 GCC 的 `-S` 和 `-O2` 生成汇编。除了真正计算 `aX + Y` 的循环外，向量 `X`、`Y` 的生成、对 `Y` 求和及输出等指令也会被模拟（simulation）。作者生成的汇编约有 350 行，而 DAXPY 主循环只占约 10—15 行。

评估设计时，通常只关心最重要代码区间的统计信息。可以在程序中加入标记，让模拟器（simulator）在指定位置创建检查点（checkpoint）、输出或清零统计项。

修改第一步的程序，在 DAXPY 循环前后各调用一次 `m5_dump_reset_stats()`，输出并清零统计数据。原版本的声明位于仓库（repository）的 `util/m5/m5op.h`；延迟与周期两个实参都可设为 0。

为提供实现，进入 `util/m5`，如下修改 `Makefile.x86`：

```
  diff --git a/util/m5/Makefile.x86 b/util/m5/Makefile.x86
  --- a/util/m5/Makefile.x86
  +++ b/util/m5/Makefile.x86
  [=@@=] -31,7 +31,7 @@
   AS=as
   LD=ld

  -CFLAGS=-O2 -DM5OP_ADDR=0xFFFF0000
  +CFLAGS=-O2
   OBJS=m5.o m5op_x86.o

   all: m5
```

运行 `make -f Makefile.x86`，得到 `m5op_x86.o`，再将其与 DAXPY 程序链接。重新使用 `TimingSimpleCPU` 运行，`stats.txt` 应包含三组统计数据。报告三个区间的指令类别分布，并提供从第一次调用 `m5_dump_reset_stats()` 到第二次调用之间、包含 DAXPY 主循环的汇编片段。

### 3. 研究浮点功能单元

gem5 支持原子、时序、乱序（out-of-order）、顺序（in-order）和 KVM 等 CPU 模型或运行方式。这里比较简单时序 CPU 与 Minor：前者不采用流水线，同一时刻只处理一条指令，算术指令按简单时序执行，内存访问可能耗费多个周期；Minor 使用流水线，包含 `fetch1`、`fetch2`、`decode` 和 `execute` 阶段。

> **译注**：原文将类名误写为 `SimpleTimingCPU`，实际为 `TimingSimpleCPU`；此处的单周期描述是作业采用的简化模型说明。

阅读 `src/cpu/minor/MinorCPU.py`。功能单元类 `MinorFU` 包含 `opLat` 与 `issueLat`，根据注释理解它们的含义，并查看 `MinorDefaultFUPool` 中实例化的各类功能单元。

假设 `FloatSimdFU` 的 `issueLat` 和 `opLat` 均可取 1—6 个周期，且两者之和始终为 7。每减少一个周期的 `opLat`，就必须增加一个周期的 `issueLat`。你会选择哪种设计？使用前面标记区间的统计结果提供证据。

原文在 `<$urlbase}html/cpu.py>` 提供扩展 MinorCPU 的骨架文件，但 wiki 变量未展开。可恢复的历史地址为 `https://pages.cs.wisc.edu/~david/courses/cs752/Fall2015/html/cpu.py`；翻译时该资源返回 HTTP 403，无法验证内容。若取得骨架文件，需调整配置脚本以使用它，并为下一步继续修改。

### 4. 比较整数与浮点延迟优化

默认 MinorCPU 有两个普通整数功能单元，此处忽略乘除法单元。假设初始设计中整数操作延迟为 2 个周期，浮点操作为 4 个周期，新设计只能将其中一类的延迟减半。应选择哪类？用模拟（simulation）统计数据支持结论。

## 提交内容

原课程要求发送邮件给 David Wood 教授 <david@cs.wisc.edu> 和 Nilay Vaish <nilay@cs.wisc.edu>，主题为 `CS752 Homework3`。

1. 写明姓名和学号，以下文件打包为 zip 附件。
2. `daxpy.cpp`，包含第二步要求的 `m5_dump_reset_stats()`；以及 `daxpy.s`，包含要求的汇编片段。
3. 所有实验的 `stats.txt` 和 `config.ini`。
4. 约 200 词的报告，回答上述问题。

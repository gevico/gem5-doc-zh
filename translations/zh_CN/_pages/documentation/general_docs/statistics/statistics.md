---
layout: documentation
title: 统计信息（statistics）
parent: statistics
doc: gem5 文档
permalink: /documentation/general_docs/statistics/
---

# Stats 包（stats package）
目前 stats 包的设计思路是：只有一个名为 Stat 的基类，它仅仅是通往该统计项其他所有可能重要方面的钩子。因此，这个 Stat 基类带有虚函数，用于为所有统计项命名、设置精度、设置标志以及初始化大小。对于所有基于 Vector 的统计项，在使用之前进行初始化非常重要，这样才能完成相应的存储分配。对于其他所有统计项，命名和标志设置也很重要，但对二进制程序的正确执行来说没那么关键。代码中的做法是有一个 regStats() 阶段，在此期间所有统计项都可以被注册到统计数据库中并完成初始化。

因此，要添加你自己的统计项，只需把它们加入相应类的数据成员列表，并确保在该类的 regStats 函数中对它们进行初始化/注册。

下面是各种初始化函数的列表。注意它们都返回 Stat& 引用，因此可以用看起来简洁的方式把它们串起来调用。

* init（参数各不相同）//对于不同类型的统计项有所不同。
   * Average：没有 init()
   * Vector：init(size_t) //指明 vector 的大小
   * AverageVector：init(size_t) //指明 vector 的大小
   * Vector2d：init(size_t x, size_t y) //行、列
   * Distribution：init(min, max, bkt) //min 指最小值，max 指最大值，bkt 指每个 bucket 的大小。换句话说，如果 min=0、max=15、bkt=8，那么 0-7 会进入 bucket 0，8-15 会进入 bucket 1。
   * StandardDeviation：没有 init()
   * AverageDeviation：没有 init()
   * VectorDistribution：init(size, min, max, bkt) //size 指 vector 的大小，其余与 Distribution 相同。
   * VectorStandardDeviation：init(size) //size 指 vector 的大小
   * VectorAverageDeviation：init(size) //size 指 vector 的大小
   * Formula：没有 init()
* name(const std::string name) //统计项的名称
* desc(const std::string desc) //统计项的简要描述
* precision(int p) //p 指小数点后保留多少位。p=0 会强制取整为整数。
* prereq(const Stat &prereq) //表示除非 prereq 的值非零，否则不打印该统计项。（例如若缓存访问次数为 0，就不打印缓存未命中、命中等等。）
* subname(int index, const std::string subname) //用于基于 Vector 的统计项，为 vector 的每个索引给出子名称。
* subdesc(int index, const std::string subname) //同样用于基于 Vector 的统计项，为每个索引给出子描述。对于二维 Vector，subname 作用于每一行（x）。y 方向可以用 Vector2d 的成员函数 ysubname 命名，细节见代码。

flags(FormatFlags f) //这些是可以传给统计项的各种标志，下面会说明。

* none —— 无特殊格式
* total —— 用于基于 Vector 的统计项，如果设置了该标志，会在末尾打印 Vector 的总计（对于那些支持该功能的统计项）。
* pdf —— 会打印某个统计项的概率分布
* nozero —— 如果统计项的值为零，则不打印
* nonan —— 如果统计项是 Not a Number（nan），则不打印。
* cdf —— 会打印某个统计项的累积分布

下面是一个如何初始化 VectorDistribution 的示例：

```
    vector_dist.init(4,0,5,2)
        .name("Dummy Vector Dist")
        .desc("there are 4 distributions with buckets 0-1, 2-3, 4-5")
        .flags(nonan | pdf)
        ;
```
# 统计项类型 #
## Scalar ##
最基本的统计项是 Scalar。它体现的是基本计数功能。它是一个模板化统计项，接受两个参数：类型和 bin。默认类型是 Counter，默认 bin 是 NoBin（即该统计项不做分箱）。它的用法很直接：要赋值，只需写 foo = 10;；要递增，就像其他任何类型一样使用 ++ 或 +=。
## Average ##
这是一个“特殊用途”统计项，用于计算某个量在模拟（simulation）周期数上的平均值。用示例解释最清楚。如果你想知道整个模拟过程中加载存储队列的平均占用，你需要每个周期累加 LSQ 中的指令数，最后再除以周期数。对于该统计项来说，可能有很多周期 LSQ 占用没有变化。因此你可以使用这个统计项，只在 LSQ 占用发生变化时才显式更新它。对于没有变化的周期，统计项会自行处理。该统计项可以做分箱，它的模板化方式与 Stat 相同。
## Vector ##
Vector 就像它名字所说的那样，是模板参数中类型 T 的一个 vector。它也可以做分箱。Vector 最自然的用法是跟踪某些跨 SMT 线程数量的统计量。大小为 n 的 Vector 只需声明 `Vector<> foo;`，之后再把它的大小初始化为 n。此时就可以像访问普通 vector 或数组那样访问 foo，例如 `foo[7]++`。
## AverageVector ##
AverageVector 就是由 Average 组成的 Vector。
## Vector2d ##
Vector2d 是二维 vector。它可以在 x 和 y 两个方向命名，不过主名称是沿 x 维度给出的。要在 y 维度命名，使用只有 Vector2d 才有的特殊 ysubname 函数。
## Distribution ##
它本质上是一个 Vector，但有细微差别。在 Vector 中，索引对应该 bucket 所关注的项；而在 Distribution 中，你可以把不同的关注范围映射到一个 bucket。基本上，如果你把 Distribution 的 init 的 bkt 参数设为 1，那你不如直接用 Vector。
## StandardDeviation ##
该统计项计算模拟（simulation）周期数上的标准差。它与 Average 类似，内置了一些行为，但需要每个周期都更新。
## AverageDeviation ##
该统计项也计算标准差，但与 Average 类似，不需要每个周期都更新。它会自行处理没有变化的周期。
## VectorDistribution ##
它就是由 Distribution 组成的 vector。
## VectorStandardDeviation ##
它就是由 StandardDeviation 组成的 vector。
## VectorAverageDeviation ##
它就是由 AverageDeviation 组成的 vector。
## Histogram ##
该统计项把每个采样值放入可配置数量个 bin 中的一个。所有 bin 构成一个连续区间，且长度相等。如果某个采样值无法放入现有的任一 bin，bin 的长度会被动态扩展。
## SparseHistogram ##
该统计项与 Histogram 类似，只是它只能对自然数采样。例如 SparseHistogram 适合统计对内存地址的访问次数。
## Formula ##
这是一个 Formula 统计项，用于任何需要在模拟结束时进行计算的东西，例如某个速率。定义一个 Formula 的示例如下：

```
    Formula foo = bar + 10 / num;
```

Formula 有一些微妙之处。如果 bar 和 num 都是统计项（包括 Formula 类型），就没有问题。如果 bar 或 num 是普通变量，则必须用 constant(bar) 加以限定。这本质上就是类型转换。如果你想使用 bar 或 num 在定义时刻的值，就使用 constant()。如果你想使用 bar 或 num 在公式被计算时（即模拟结束时）的值，就把 num 定义为 Scalar。如果 num 是 Vector，则用 sum(num) 来计算它在公式中的和。把普通变量转换为 Scalar 的 "scalar(num)" 操作已不复存在。

---
layout: documentation
title: 统计信息 API（statistics API）
parent: statistics
doc: gem5 文档
permalink: /documentation/general_docs/statistics/api
---

# 统计信息 API

## 目录
1. [通用统计函数](#general-statistics-functions)
2. [Stats::Group —— 统计信息容器](#stats_group-statistics-container)
3. [统计标志](#stats-flags)
4. [统计类](#statistics-classes)
5. [附录：迁移到新的统计信息跟踪方式](#appendix_migrating-to-the-new-style-of-tracking-statistics)

---

## 通用统计函数

| 函数签名                                            | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`void Stats::dump()`                                 | 把所有统计信息导出到已注册的输出，例如 stats.txt。                     |
|`void Stats::reset()`                                | 重置统计信息。                                                         |

---

## Stats::Group —— 统计信息容器 {#stats_group-statistics-container}
通常，统计对象可以作为类变量放在任何 `SimObject` 中。
不过，[最近的一次更新](https://gem5-review.googlesource.com/c/public/gem5/+/19368)
处理了 gem5 中 `SimObject` 的层次结构特性，
这进而使各对象的统计信息也具有层次性。
该更新引入了 `Stats::Group` 类，它是一个统计信息容器，
并且能感知 `SimObject` 的层次结构。
理想情况下，该容器应包含某个 `SimObject` 中的所有统计信息。

**注意**：如果你决定在 `SimObject` 内部使用 `Stats::Group` 结构体，
通常有两种做法：
- 使用 `Stats::Group(Stats::Group &parent, const std::string &name)` 构造函数创建子组。当你希望同一统计结构有多个实例时，这很有用。
- 使用 `Stats::Group(Stats::Group &parent)` 构造函数，它会把当前组的统计信息合并（即添加）到父组。因此，添加到当前组的统计信息，其行为就像是被直接添加到父组一样。

### Stats::Group 宏
##### `#define ADD_STAT(n, ...) n(this, # n, __VA_ARGS__)`
用于向统计组添加统计项的便利宏。

该宏用于在 Group 构造函数的初始化
列表中向 Stats::Group 添加统计项。该宏
会自动把该统计项赋给当前组，并给它一个与类中
相同的名称。例如：
```
struct MyStats : public Stats::Group
{
    Stats::Scalar scalar0;
    Stats::Scalar scalar1;

    MyStats(Stats::Group *parent)
        : Stats::Group(parent),
          ADD_STAT(scalar0, "Description of scalar0"),       // equivalent to scalar0(this, "scalar0", "Description of scalar0"), where scalar0 has the follwing constructor
                                                             // Stats::Scalar(Group *parent = nullptr, const char *name = nullptr, const char *desc = nullptr)
          scalar1(this, "scalar1", "Description of scalar1")
     {
     }
};
```


### Stats::Group 函数
##### `Group(Group *parent, const char *name = nullptr)`
构造一个新的统计组。

该构造函数接受两个参数：父组和名称。通常
应指定父组。不过有些特殊情况父组可以为
null。其中一种特殊情况是 Python 代码
对组父对象进行延迟绑定的 SimObject。

如果 name 参数为 NULL，该组会被合并到
父组中，而不是创建子组。属于已合并组的统计信息，
其行为就像被直接添加到父组一样。

##### `virtual void regStats()`
用于设置统计参数的回调。

该回调通常用于复杂统计项（例如
分布），它们除名称和描述之外还需要参数。在
统计对象无法于构造函数中初始化的情况下（例如跟踪
总线主设备的统计信息，只有在整个
系统实例化完成后才能被发现），也会用到它。统计项的名称和描述
通常应在构造函数中通过 `ADD_STAT` 宏设置。

##### `virtual void resetStats()`
用于重置统计信息的回调。

##### `virtual void preDumpStats()`
统计信息导出之前的回调。需要在统计框架
已实现能力之外做额外计算的对象可以覆盖它。

##### `void addStat(Stats::Info *info)`
把一个统计项注册到该组。该方法通常在
统计项被实例化时自动调用。

##### `const std::map<std::string, Group *> &getStatGroups() const`
获取与该对象关联的所有子组。

##### `const std::vector<Info *> &getStats() const`
获取与该对象关联的所有统计信息。

##### `void addStatGroup(const char *name, Group *block)`
把一个统计块添加为该块的子块。

该方法只能从 Group 构造函数或
regStats 中调用。通常只有在 Python 中建立 SimObject 层次结构时
才会显式调用它。

##### `const Info * resolveStat(std::string name) const`
在该组内按名称解析一个统计项。

该方法会遍历该组及各个子组中的统计项，
返回与所给名称匹配的统计项的指针。输入名称
必须相对于该组的名称。

例如，如果该组是 `SimObject
system.bigCluster.cpus`，而我们想要统计项
`system.bigCluster.cpus.ipc`，那么输入参数应为
字符串 "ipc"。

---

## 统计标志

| 标志             | 说明                                                           |
|------------------|----------------------------------------------------------------|
| `Stats::none`    | 不额外打印任何内容。                                           |
| `Stats::total`   | 打印总计。                                                     |
| `Stats::pdf`     | 打印该条目占总量的百分比。                                     |
| `Stats::cdf`     | 打印到该条目为止的累积百分比。                                 |
| `Stats::dist`    | 打印分布。                                                     |
| `Stats::nozero`  | 若为零则不打印。                                               |
| `Stats::nonan`   | 若为 NAN 则不打印                                              |
| `Stats::oneline` | 把所有值打印在一行上。只对 histogram 有用。                    |

注意：尽管 `Stats::init` 和 `Stats::display` 标志是存在的，但
不允许用户设置这两个标志。

---

## 统计类 {#statistics-classes}

| 类名                                                | 说明                                                                    |
|-----------------------------------------------------|-------------------------------------------------------------------------|
| [`Stats::Scalar`](#statsscalar)                     | 简单的标量统计。                                                        |
| [`Stats::Average`](#statsaverage)                   | 计算某个值每 TICK 平均值的统计。                                        |
| [`Stats::Value`](#statsvalue)                       | 与 Stats::Scalar 类似。                                                 |
| [`Stats::Vector`](#statsvector)                     | 标量统计的 vector。                                                     |
| [`Stats::AverageVector`](#statsaveragevector)       | 平均值统计的 vector。                                                   |
| [`Stats::Vector2d`](#statsvector2d)                 | 标量统计的二维 vector。                                                 |
| [`Stats::Distribution`](#statsdistribution)         | 简单的分布统计（带有便利的 min、max、sum 等）。                         |
| [`Stats::Histogram`](#statshistogram)               | 简单的直方图统计（记录等分连续区间的频次）。                            |
| [`Stats::SparseHistogram`](#statssparsehistogram)   | 记录一组离散值的频次 / 直方图。                                         |
| [`Stats::StandardDeviation`](#statsstandarddeviation)| 计算所有样本的均值与方差。                                             |
| [`Stats::AverageDeviation`](#statsaveragedeviation) | 计算样本每 tick 的均值与方差。                                          |
| [`Stats::VectorDistribution`](#statsvectordistribution)| 分布的 vector。                                                       |
| [`Stats::VectorStandardDeviation`](#statsvectorstandarddeviation)| 标准差统计的 vector。                                      |
| [`Stats::VectorAverageDeviation`](#statsvectoraveragedeviation)| 平均偏差统计的 vector。                                      |
| [`Stats::Formula`](#statsformula)                   | 记录涉及多个统计对象算术运算的统计。                                    |

**注意：** `Stats::Average` 只计算某个标量在已模拟 tick 数上的平均值。
若要计算量 A 相对量 B 的平均值，可以使用 `Stats::Formula`。
例如，
```C++
Stats::Scalar totalReadLatency;
Stats::Scalar numReads;
Stats::Formula averageReadLatency = totalReadLatency/numReads;
```

### 通用统计函数

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`StatClass name(const std::string &name)`            | 设置统计名称，并把该统计项标记为需打印                                 |
|`StatClass desc(const std::string &_desc)`           | 设置该统计项的描述                                                     |
|`StatClass precision(int _precision)`                | 设置该统计项的精度                                                     |
|`StatClass flags(Flags _flags)`                      | 设置标志                                                               |
|`StatClass prereq(const Stat &prereq)`               | 设置前置统计项                                                         |

### `Stats::Scalar`
存储一个有符号整数统计量。

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`void operator++()`                                  | 把该统计项加 1 // 前置 ++，例如 `++scalar`                             |
|`void operator--()`                                  | 把该统计项减 1 // 前置 --                                              |
|`void operator++(int)`                               | 把该统计项加 1 // 后置 ++，例如 `scalar++`                             |
|`void operator--(int)`                               | 把该统计项减 1 // 后置 --                                              |
|`template <typename U> void operator=(const U &v)`   | 把标量设为给定值                                                       |
|`template <typename U> void operator+=(const U &v)`  | 把该统计项增加给定值                                                   |
|`template <typename U> void operator-=(const U &v)`  | 把该统计项减少给定值                                                   |
|`size_type size()`                                   | 返回 1                                                                 |
|`Counter value()`                                    | 以整数形式返回该统计项的当前值                                         |
|`Counter value() const`                              | 以整数形式返回该统计项的当前值                                         |
|`Result result()`                                    | 以 `double` 形式返回该统计项的当前值                                   |
|`Result total()`                                     | 以 `double` 形式返回该统计项的当前值                                   |
|`bool zero()`                                        | 若该统计项等于零返回 `true`，否则返回 `false`                          |
|`void reset()`                                       | 把该统计项重置为 0                                                     |

### `Stats::Average`
存储量 A 在已模拟 tick 数上的平均值。
量 A 在其最近一次更新之后、下一次更新之前，在所有 tick 上保持相同的值。
**注意：** 当用户调用 `Stats::reset()` 时，已模拟 tick 数会被重置。

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`void set(Counter val)`                              | 把量 A 设为给定值                                                      |
|`void inc(Counter val)`                              | 把量 A 增加给定值                                                      |
|`void dec(Counter val)`                              | 把量 A 减少给定值                                                      |
|`Counter value()`                                    | 以整数形式返回 A 的当前值                                              |
|`Result result()`                                    | 以 `double` 形式返回当前平均值                                         |
|`bool zero()`                                        | 若平均值等于零返回 `true`，否则返回 `false`                            |
|`void reset(Info \*info)`                            | 保留 A 的当前值，不计入当前 tick 之前的 A 值                            |

### `Stats::Value`
存储一个有符号整数统计量，它可以是整数，也可以是调用某个函数或对象方法得到的整数。

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`Counter value()`                                    | 以整数形式返回值                                                       |
|`Result result() const`                              | 以 double 形式返回值                                                   |
|`Result total() const`                               | 以 double 形式返回值                                                   |
|`size_type size() const`                             | 返回 1                                                                 |
|`bool zero() const`                                  | 若该值为零返回 `true`，否则返回 `false`                                |


### `Stats::Vector`
存储一个标量统计数组，其中 vector 的每个元素都具有与 `Stats::Scalar` 类似的函数签名。

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`Derived & init(size_type size)`                     | 把 vector 初始化为给定大小（若试图调整已初始化 vector 的大小则抛出错误）|
|`Derived & subname(off_type index, const std::string &name)`| 为给定索引处的统计项添加名称                                   |
|`Derived & subdesc(off_type index, const std::string &desc)`| 为给定索引处的统计项添加描述                                   |
|`void value(VCounter &vec) const`                    | 把统计 vector 复制到给定的整数 vector                                  |
|`void result(VResult &vec) const`                    | 把统计 vector 复制到给定的 double vector                               |
|`Result total() const`                               | 以 double 形式返回 vector 中所有统计项的和                             |
|`size_type size() const`                             | 返回 vector 的大小                                                     |
|`bool zero() const`                                  | 若 vector 中每个统计项都为 0 返回 `true`，否则返回 `false`             |
|`operator[](off_type index)`                         | 取得给定索引处统计项的引用，例如 `vecStats[1]+=9`                      |

### `Stats::AverageVector`
存储一个平均统计数组，其中 vector 的每个元素都具有与 `Stats::Average` 类似的函数签名。

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`Derived & init(size_type size)`                     | 把 vector 初始化为给定大小（若试图调整已初始化 vector 的大小则抛出错误）|
|`Derived & subname(off_type index, const std::string &name)`| 为给定索引处的统计项添加名称                                   |
|`Derived & subdesc(off_type index, const std::string &desc)`| 为给定索引处的统计项添加描述                                   |
|`void value(VCounter &vec) const`                    | 把统计 vector 复制到给定的整数 vector                                  |
|`void result(VResult &vec) const`                    | 把统计 vector 复制到给定的 double vector                               |
|`Result total() const`                               | 以 double 形式返回 vector 中所有统计项的和                             |
|`size_type size() const`                             | 返回 vector 的大小                                                     |
|`bool zero() const`                                  | 若 vector 中每个统计项都为 0 返回 `true`，否则返回 `false`             |
|`operator[](off_type index)`                         | 取得给定索引处统计项的引用，例如 `avgStats[1].set(9)`                  |

### `Stats::Vector2d`
存储一个标量统计的二维数组，其中数组的每个元素都具有与 `Stats::Scalar` 类似的函数签名。
该数据结构假定第二维索引相同的所有元素具有相同的名称。

| 函数签名                                             | 说明                                                                   |
|-----------------------------------------------------|------------------------------------------------------------------------|
|`Derived & init(size_type _x, size_type _y)`         | 把 vector 初始化为给定大小（若试图调整已初始化 vector 的大小则抛出错误）|
|`Derived & ysubname(off_type index, const std::string &subname)` | 把 `subname` 设为第二维为 `index` 的元素的统计名称|
|`Derived & ysubnames(const char **names)`            | 与上面的 `ysubname()` 类似，但为第二维的所有索引设置名称             |
|`std::string ysubname(off_type i) const`             | 返回第二维为 `i` 的元素的统计名称                                    |
|`size_type size() const`                             | 返回数组中元素的数量                                                  |
|`bool zero()`                                        | 若第 0 行第 0 列的元素等于 0 返回 `true`，否则返回 `false`             |
|`Result total()`                                     | 以 double 形式返回所有元素的和
|`void reset()`                                       | 把数组中每个元素设为 0                                               |
|`operator[](off_type index)`                         | 取得给定索引处统计项的引用，例如 `vecStats[1][2]+=9`                  |

### `Stats::Distribution`
存储某个量的分布。
该分布的统计信息包括：
  - 被采样的最小/最大值
  - 小于/大于所指定 min 与 max 的值的数量
  - 所有样本的和
  - 样本的均值、几何平均值与标准差
  - 在 [`min`, `max`] 范围内按 `(max-min)/bucket_size` 等分为若干个 bucket 的直方图，其中 `min`/`max`/`bucket_size` 是 init() 函数的输入。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`Distribution & init(Counter min, Counter max, Counter bkt)` | 初始化该分布，其中 `min` 是该分布直方图所跟踪的最小值，`max` 是该分布直方图所跟踪的最小值，`bkt` 是每个 bucket 中值的数量 |
|`void sample(Counter val, int number)`                       | 把 `val` 加入该分布 `number` 次                                        |
|`size_type size() const`                                     | 返回该分布中 bucket 的数量                                             |
|`bool zero() const`                                          | 若样本数为零返回 `true`，否则返回 `false`                              |
|`void reset(Info *info)`                                     | 丢弃所有样本                                                           |
|`add(DistBase &)`                                            | 合并来自另一个带 `DistBase` 的 `Stats` 类（例如 `Stats::Histogram`）的样本|

### `Stats::Histogram`
在给定 bucket 数量的情况下存储某个量的直方图。
所有 bucket 大小相等。
与 `Stats::Distribution` 只跟踪特定范围内样本的直方图不同，`Stats::Histogram` 在其直方图中跟踪所有样本。
另外，`Stats::Distribution` 以每个 bucket 中值的数量为参数，而 `Stats::Histogram` 唯一的参数是 bucket 数量。
当新样本落在所有 bucket 当前范围之外时，bucket 会被调整大小。
大致做法是不断合并相邻的两个 bucket，直到新样本落入其中一个 bucket 内。

除直方图本身之外，该分布的统计信息还包括：
  - 被采样的最小/最大值
  - 所有样本的和
  - 样本的均值、几何平均值与标准差

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`Histogram & init(size_type size)`                           | 初始化直方图，把 bucket 数量设为 `size`                                |
|`void sample(Counter val, int number)`                       | 把 `val` 加入该直方图 `number` 次                                      |
|`void add(HistStor *)`                                       | 把另一个直方图合并到该直方图                                           |
|`size_type size() const `                                    | 返回 bucket 的数量                                                     |
|`bool zero() const`                                          | 若样本数为零返回 `true`，否则返回 `false`                              |
|`void reset(Info *info)`                                     | 丢弃所有样本                                                           |

### `Stats::SparseHistogram`
在给定一组整数值的情况下存储某个量的直方图。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`template <typename U> void sample(const U &v, int n = 1)`   | 把 `v` 加入该直方图 `n` 次                                             |
|`size_type size() const `                                    | 返回条目数量                                                           |
|`bool zero() const`                                          | 若样本数为零返回 `true`，否则返回 `false`                              |
|`void reset()`                                               | 丢弃所有样本                                                           |

### `Stats::StandardDeviation`
跟踪一个样本的标准差。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`void sample(Counter val, int number)`                       | 把 `val` 加入该分布 `number` 次                                        |
|`size_type size() const`                                     | 返回 1                                                                 |
|`bool zeros() const`                                         | 丢弃所有样本                                                           |
|`add(DistBase &)`                                            | 合并来自另一个带 `DistBase` 的 `Stats` 类（例如 `Stats::Distribution`）的样本|

### `Stats::AverageDeviation`
跟踪一个样本的平均偏差。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`void sample(Counter val, int number)`                       | 把 `val` 加入该分布 `number` 次                                        |
|`size_type size() const`                                     | 返回 1                                                                 |
|`bool zeros() const`                                         | 丢弃所有样本                                                           |
|`add(DistBase &)`                                            | 合并来自另一个带 `DistBase` 的 `Stats` 类（例如 `Stats::Distribution`）的样本|

### `Stats::VectorDistribution`
存储一个分布的 vector，其中 vector 的每个元素都具有与 `Stats::Distribution` 类似的函数签名。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`VectorDistribution & init(size_type size, Counter min, Counter max, Counter bkt)` | 初始化由 `size` 个分布组成的 vector，其中 `min` 是各分布直方图所跟踪的最小值，`max` 是各分布直方图所跟踪的最小值，`bkt` 是各分布每个 bucket 中值的数量 |
|`Derived & subname(off_type index, const std::string &name)` | 为给定索引处的统计项添加名称                                           |
|`Derived & subdesc(off_type index, const std::string &desc)` | 为给定索引处的统计项添加描述                                           |
|`size_type size() const`                                     | 返回 vector 中元素的数量                                               |
|`bool zero() const`                                          | 若每个分布都只有 0 个样本返回 `true`，否则返回 `false`                 |
|`operator[](off_type index)`                                 | 取得给定索引处分布的引用，例如 `dists[1].sample(2,3)`                  |

### `Stats::VectorStandardDeviation`
存储一个标准差的 vector，其中 vector 的每个元素都具有与 `Stats::StandardDeviation` 类似的函数签名。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`VectorStandardDeviation & init(size_type size)`             | 初始化由 `size` 个标准差组成的 vector                                  |
|`Derived & subname(off_type index, const std::string &name)`| 为给定索引处的统计项添加名称                                           |
|`Derived & subdesc(off_type index, const std::string &desc)`| 为给定索引处的统计项添加描述                                           |
|`size_type size() const`                                     | 返回 vector 中元素的数量                                               |
|`bool zero() const`                                          | 若每个分布都只有 0 个样本返回 `true`，否则返回 `false`                 |
|`operator[](off_type index)`                                 | 取得给定索引处标准差的引用，例如 `dists[1].sample(2,3)`                |

### `Stats::VectorAverageDeviation`
存储一个平均偏差的 vector，其中 vector 的每个元素都具有与 `Stats::AverageDeviation` 类似的函数签名。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`VectorAverageDeviation & init(size_type size)`              | 初始化由 `size` 个平均偏差组成的 vector                                |
|`Derived & subname(off_type index, const std::string &name)`| 为给定索引处的统计项添加名称                                           |
|`Derived & subdesc(off_type index, const std::string &desc)`| 为给定索引处的统计项添加描述                                           |
|`size_type size() const`                                     | 返回 vector 中元素的数量                                               |
|`bool zero() const`                                          | 若每个分布都只有 0 个样本返回 `true`，否则返回 `false`                 |
|`operator[](off_type index)`                                 | 取得给定索引处平均偏差的引用，例如 `dists[1].sample(2,3)`              |

### `Stats::Formula`
存储以一系列对 `Stats` 对象的算术运算为结果的统计项。
注意在以下函数中，`Temp` 可以是任何持有统计信息的 `Stats` 类（包括 vector 统计）、一个公式，或一个数字（例如 `int`、`double`、`1.2`）。

| 函数签名                                                     | 说明                                                                   |
|-------------------------------------------------------------|------------------------------------------------------------------------|
|`const Formula &operator=(const Temp &r)`                    | 把一个未初始化的 `Stats::Formula` 赋给给定的根                          |
|`const Formula &operator=(const T &v)`                       | 把该公式赋为某个统计项、另一个公式或一个数字                           |
|`const Formula &operator+=(Temp r)`                          | 向当前公式加上某个统计项、另一个公式或一个数字                         |
|`const Formula &operator/=(Temp r)`                          | 把当前公式除以某个统计项、另一个公式或一个数字                         |
|`void result(VResult &vec) const`                            | 把公式的求值结果赋给给定的 vector；如果该公式*没有* vector 分量（公式中没有任何变量是 vector），则 vector 大小为 1 |
|`Result total() const`                                       | 以 double 形式返回 `Stats::Formula` 的求值结果；如果该公式确实有 vector 分量（公式中有一个变量是 vector），则通过把 vector 设为其中所有元素之和，把该 vector 转换为标量 |
|`size_type size() const`                                     | 若根元素不是 vector 则返回 1，否则返回 vector 的大小                   |
|`bool zero()`                                                | 若 `result()` 中所有元素都为 0 返回 `true`，否则返回 `false`           |

使用 `Stats::Formula` 的示例，
```C++
Stats::Scalar totalReadLatency;
Stats::Scalar numReads;
Stats::Formula averageReadLatency = totalReadLatency/numReads;
```

---

## 附录. 迁移到新的统计信息跟踪方式 {#appendix_migrating-to-the-new-style-of-tracking-statistics}

### 一种新的统计信息跟踪方式
gem5 的统计信息过去是扁平结构，无法感知 `SimObject`（通常包含统计对象）的层次结构。
这导致不同统计项可能同名，更重要的是，操作 gem5 统计信息结构并不容易。
此外，gem5 过去没有提供把一组统计对象归入不同组的机制，而这对于维护大量统计对象很重要。

[最近的一次提交](https://gem5-review.googlesource.com/c/public/gem5/+/19368)引入了 `Stats::Group`，这是一个用于容纳某个对象全部统计信息的结构。
该新结构提供了一种显式方式来反映 `SimObject` 的层次特性；
`Stats::Group` 还让维护大量需要归入不同集合的 `Stats` 对象变得更明确、更容易，因为你可以在一个 `SimObject` 中创建多个 `Stats::Group` 并把它们合并到该 `SimObject`，而 `SimObject` 本身也是一个能感知其子 `Stats::Group` 的 `Stats::Group`。

总体而言，这是朝着更结构化的 `Stats` 格式迈出的一步，它应当有助于操作 gem5 中统计信息的整体结构，例如筛选统计信息，以及把 `Stats` 输出为 JSON、XML 之类更标准的格式，而这些格式在多种编程语言中都有大量受支持的库。

### 迁移到新的统计信息跟踪方式

*注意*：强烈鼓励迁移到新方式；不过，旧式统计信息（即扁平结构的那套）仍然受支持。

本指南广泛介绍如何迁移到新的 gem5 统计信息跟踪方式，并指出一些展示具体做法的实例。

#### `ADD_STAT`
`ADD_STAT` 是一个宏，定义为
```C++
#define ADD_STAT(n, ...) n(this, # n, __VA_ARGS__)
```
该宏用于在 `Stats::Group` 构造函数中初始化一个 `Stats` 对象。
换句话说，`ADD_STAT` 是调用 `Stats` 对象构造函数的别名。
例如，`ADD_STAT(stat_name, stat_desc)` 等同于，
```
  stat_name.parent = the `Stats::Group` where stat_name is defined
  stat_name.name = "stat_name"
  stat_name.desc = "stat_desc"
```
这适用于大多数 `Stats` 数据类型，但有一个例外：对于 `Stats::Formula`，宏 `ADD_STAT` 可以接受一个指定公式的可选参数。
例如，`ADD_STAT(ips, "Instructions per Second", n_instructions/sim_seconds)`。


`ADD_STAT` 的一个用例示例（本节中我们称其为“**示例 1**”）。
该示例也可作为构造 `Stats::Group` 结构体的模板。
```C++
    protected:
        // Defining the a stat group
        struct StatGroup : public Stats::Group
        {
            StatGroup(Stats::Group *parent); // constructor
            Stats::Histogram histogram;
            Stats::Scalar scalar;
            Stats::Formula formula;
        } stats;

    // Defining the declared constructor
    StatGroup::StatGroup(Stats::Group *parent)
      : Stats::Group(parent),                           // initilizing the base class
        ADD_STAT(histogram, "A useful histogram"),
        scalar(this, "scalar", "A number"),             // this is the same as ADD_STAT(scalar, "A number")
        ADD_STAT(formula, "A formula", scalar1/scalar2)
    {
        histogram
          .init(num_bins);
        scalar
          .init(0)
          .flags(condition ? 1 : 0);
    }
```

#### 迁移到新方式
以下是把统计信息转换为新方式的具体示例：[此处](https://gem5-review.googlesource.com/c/public/gem5/+/19370)、[此处](https://gem5-review.googlesource.com/c/public/gem5/+/19371)和[此处](https://gem5-review.googlesource.com/c/public/gem5/+/32794)。

把统计信息迁移到新方式涉及：
  - 创建一个 `Stats::Group` 结构体，并把所有统计变量移入其中。该结构体的作用域应为 `protected`。统计变量的声明通常在头文件中。
  - 去掉 `regStats()`，并把统计变量的初始化移到 `Stats::Group` 构造函数中，如**示例 1**所示。
  - 在头文件和 cpp 文件中，所有统计变量都应以新建的 `Stats::Group` 名称为前缀，因为这些统计项现在位于 `Stats::Group` 结构体之下。
  - 更新类构造函数以初始化 `Stats::Group` 变量。通常是在构造函数中加入 `stats(this)`，假定该变量名为 `stats`。

一些示例，
  - `Stats::Group` 声明的示例见[此处](https://github.com/gem5/gem5/blob/v20.0.0.3/src/cpu/testers/traffic_gen/base.hh#L194)。
注意所有类型以 `Stats::` 开头的变量都已移入该结构体。
  - 使用 `ADD_STAT` 的 `Stats::Group` 构造函数示例见[此处](https://github.com/gem5/gem5/blob/v20.0.0.3/src/cpu/testers/traffic_gen/base.cc#L332)。
  - 如果某个统计变量需要除 `name` 和 `description` 之外的额外初始化，可以参照[这个示例](https://github.com/gem5/gem5/blob/v20.0.0.3/src/mem/comm_monitor.cc#L105)。

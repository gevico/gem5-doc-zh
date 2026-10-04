---
layout: documentation
title: 构建 EXTRAS
doc: gem5 文档
parent: building_extras
permalink: /documentation/general_docs/building/EXTRAS
authors: Jason Lowe-Power
---

# 构建 EXTRAS
`EXTRAS` 这个 SCons 选项让你可以在不把文件加入 gem5 源码树的情况下为 gem5 添加功能。具体来说，它允许你指定一个或多个目录，这些目录会被编入 gem5，就好像它们出现在 gem5 源码树的 'src' 部分一样，而不需要把代码实际放在 'src' 下。它的用途是让用户把 gem5 未随其分发、或无法随其分发的额外功能（通常是额外的 SimObject 类）编入进来。这对维护不适合并入 gem5 源码树的本地代码，或因许可不兼容而无法并入的第三方代码很有用。由于 EXTRAS 的位置与 gem5 仓库完全无关，你也可以把代码放在其他版本控制系统下。

EXTRAS 功能的主要缺点是：它本身只支持向 gem5 添加代码，而不支持修改任何 gem5 基础代码。

EXTRAS 功能的一个用途是支持 EIO 跟踪（trace）。EIO 的跟踪读取器采用 SimpleScalar 许可，由于该许可与 gem5 的 BSD 许可不兼容，读取这些跟踪的代码未包含在 gem5 发行版中。EIO 代码改为通过一个单独的 "encumbered" [仓库](https://github.com/gem5/gem5)分发。

下面的示例展示如何编译 EIO 代码。通过添加或修改 extras 路径，也可以编入其他任何合适的额外代码。要使用 EXTRAS 编入代码，只需执行：

```js
 scons EXTRAS=/path/to/encumbered build/<ISA>/gem5.opt
```

在该目录的根下应有一个 SConscript，其中使用 M5 其余部分所用的 ```Source()``` 和 ```SimObject()``` scons 函数来编译相应的源码并添加所需的 SimObject。如果你想添加多个目录，可以把 EXTRAS 设置为以冒号分隔的路径列表。

注意 EXTRAS 是一个“粘性”参数：一旦向 scons 提供过一次值，只要你没有覆盖它，该值就会被后续针对同一构建目录（此处为 ```build/<ISA>```）的 scons 调用复用。因此，你只需在第一次构建某个特定配置时指定 EXTRAS，或者在想要覆盖此前指定的值时再指定。
要用 EXTRAS 运行回归测试，可执行类似如下命令：
```js
 ./util/regress --scons-opts = "EXTRAS=/path/to/encumbered" -j 2 quick
```

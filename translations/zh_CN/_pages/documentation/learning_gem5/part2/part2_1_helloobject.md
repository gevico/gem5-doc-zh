---
layout: documentation
title: "创建一个非常简单的 SimObject"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/helloobject/
author: Jason Lowe-Power
---

创建一个非常简单的 SimObject
==================================

**注意：** gem5 已有名为 `SimpleObject` 的 SimObject。再次定义同名类型会引发难以理解的编译错误。

gem5 中几乎所有对象都继承自 `SimObject` 基类。它提供对象的主要公共接口，并封装 C++ 对象，使其能够从 Python 配置脚本中访问。

SimObject 可以有许多由 Python 配置文件设置的参数（parameter）。除整数、浮点数等简单类型外，其他 SimObject 也可以作为参数（parameter），从而构建类似真实机器的复杂系统层次结构。

本章将创建一个输出 “HelloWorld” 的简单 SimObject，介绍创建过程以及所有 SimObject 必需的基础代码，并编写一个实例化它的 Python 脚本。

后续几章将在此基础上加入[调试支持]({{ site.baseurl }}/documentation/learning_gem5/part2/debugging/)、[动态事件]({{ site.baseurl }}/documentation/learning_gem5/part2/events/)和[参数（parameter）]({{ site.baseurl }}/documentation/learning_gem5/part2/parameters/)。

> **使用 Git 分支**
>
> 通常应为每项新增功能建立独立的 Git 分支。修改 gem5 或添加功能前，先创建用于保存变更的分支。分支的详细用法可查阅 Git book。
>
> ```
> git checkout -b hello-simobject
> ```

第一步：为新 SimObject 创建 Python 类
----------------------------------------------------

每个 SimObject 都有一个关联的 Python 类，用于描述能够通过配置文件控制的参数（parameter）。这个简单示例暂不需要参数（parameter），因此只需声明新类，指定其类型名称以及声明 C++ 类的头文件。

在 `src/learning_gem5/part2` 中创建 `HelloObject.py`。如果已经克隆 gem5 仓库（repository），会发现 `src/learning_gem5/part2` 和 `configs/learning_gem5/part2` 已提供完成后的教程文件。可以先把这些示例移到其他位置，或在确认不需要保留后删除，再跟着本教程编写。

```python
from m5.params import *
from m5.SimObject import SimObject

class HelloObject(SimObject):
    type = 'HelloObject'
    cxx_header = "learning_gem5/part2/hello_object.hh"
    cxx_class = "gem5::HelloObject"
```

[//]: # 完整文件见原文对应示例。
[//]: # [here](/_static/scripts/part2/helloobject/HelloObject.py)

`type` 通常与 Python 类名一致。原文将其描述为所包装的 C++ 类型名称；常规情况下只有特殊需求才会让两者不同。

`cxx_header` 指定声明 C++ 类的头文件。通常使用小写字母和下划线组成的 SimObject 名称，但这只是惯例，也可以指定其他文件。

`cxx_class` 指定实际 C++ 类的限定名称。本例通过它表明新类位于 `gem5` 命名空间；gem5 代码中的大多数 SimObject 都在这一命名空间中。

第二步：用 C++ 实现 SimObject
---------------------------------------

在 `src/learning_gem5/part2/` 中创建 `hello_object.hh` 和 `hello_object.cc`，实现 `HelloObject`。

先编写头文件。gem5 通常使用根据目录和文件名组成的 `#ifndef/#endif` 保护宏，避免头文件重复包含。SimObject 应声明在 `namespace gem5` 中。

这里只需声明类。`HelloObject` 必须继承 C++ 的 `SimObject`；实际项目中，新类通常继承其某个子类，而不是直接继承 `SimObject`。

`SimObject` 定义了许多虚函数，但没有纯虚函数，因此最简单的派生类只需实现构造函数。

SimObject 的构造函数接受参数（parameter）对象。构建系统根据前面的 Python 类自动生成这个对象的类型，并由 SimObject 名称推导类型名；对 `HelloObject` 而言，就是 `HelloObjectParams`。

头文件如下：

```cpp
#ifndef __LEARNING_GEM5_HELLO_OBJECT_HH__
#define __LEARNING_GEM5_HELLO_OBJECT_HH__

#include "params/HelloObject.hh"
#include "sim/sim_object.hh"

namespace gem5
{

class HelloObject : public SimObject
{
  public:
    HelloObject(const HelloObjectParams &p);
};

} // namespace gem5

#endif // __LEARNING_GEM5_HELLO_OBJECT_HH__
```

[//]: # 完整文件见原文对应示例。
[//]: # [here](/_pages/static/scripts/part2/helloobject/hello_object.hh).

接着编写 `.cc` 文件中的构造函数：将参数（parameter）对象传给父类 `SimObject`，再输出 “Hello world!”。

正常情况下，不应在 gem5 中直接使用 `std::cout`，而应使用调试标志。[下一章]({{ site.baseurl }}/documentation/learning_gem5/part2/debugging/)将进行替换；这里只为简化示例而使用它。

```cpp
#include "learning_gem5/part2/hello_object.hh"

#include <iostream>

namespace gem5
{

HelloObject::HelloObject(const HelloObjectParams &params) :
    SimObject(params)
{
    std::cout << "Hello World! From a SimObject!" << std::endl;
}

} // namespace gem5
```

**注意：** 如果 SimObject 构造函数遵循以下签名：

```cpp
Foo(const FooParams &)
```

构建系统会自动定义 `FooParams::create()`，负责调用构造函数并返回 SimObject 实例。大多数 SimObject 都采用此模式。如果不符合这一模式，可查阅 [gem5 SimObject documentation](https://doxygen.gem5.org/release/current/classgem5_1_1SimObject.html#details)，了解如何手工实现 `create()`。

> **译注：** 原文此处保留了“需要实现两个函数”的旧说法，但后面的说明已明确指出 `create()` 会自动生成。按照本例的标准构造函数签名，只需手写构造函数。

[//]: # 完整文件见原文对应示例。
[//]: # [here](/_pages/static/scripts/part2/helloobject/hello_object.cc).

第三步：注册 SimObject 与 C++ 文件
-------------------------------------------

要让构建系统编译 C++ 文件并解析 Python 文件，必须注册它们。gem5 使用 SCons，因此在 SimObject 源码目录中创建 `SConscript` 即可；若已有该文件，就向其中添加下面的声明。

`SConscript` 本身是普通 Python 文件，可以编写任意 Python 代码。gem5 利用这一能力为 SimObject 自动生成代码，并编译 SLICC、指令集架构（ISA）描述语言等领域专用语言。

导入构建环境后，`SConscript` 中便可使用构建系统提供的函数。为了编译新的对象，在 `src/learning_gem5/part2/SConscript` 中声明 SimObject 和 `.cc` 文件：

```python
Import('*')

SimObject('HelloObject.py', sim_objects=['HelloObject'])
Source('hello_object.cc')
```

[//]: # 完整文件见原文对应示例。
[//]: # [here](/_pages/static/scripts/part2/helloobject/SConscript).

第四步：重新构建 gem5
-----------------------

重新构建 gem5，即可编译并链接新文件。下面使用 x86 构建；由于这个对象不依赖任何特定指令集架构（ISA），其他受支持的构建也可以使用。

```
scons build/ALL/gem5.opt
```

第五步：编写使用新 SimObject 的配置脚本
-----------------------------------------------------------

对象已经实现并编译到 gem5 中。现在在 `configs/learning_gem5/part2` 中创建或修改 `run_hello.py`，实例化该对象。它十分简单，不需要 `System`、CPU 或缓存（cache），只需要所有 gem5 实例都必需的 `Root` 对象。

先导入 `m5` 及已编译的对象：

```python
import m5
from m5.objects import *
```

再实例化 `Root`：

```python
root = Root(full_system = False)
```

然后调用 Python 构造函数创建 `HelloObject`，后文再介绍如何通过构造函数传入参数（parameter）。同时必须把它挂到 `Root` 的对象层次结构下；只有属于这一层次结构的 SimObject 才会在 C++ 中实例化。

```python
root.hello = HelloObject()
```

最后调用 `m5.instantiate`，并运行模拟（simulation）：

```python
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print('Exiting @ tick {} because {}'
      .format(m5.curTick(), exit_event.getCause()))
```

[//]: # 完整文件见原文对应示例。
[//]: # [here](/_pages/static/scripts/part2/helloobject/run_hello.py).

每次修改 `src/` 中的文件后，都要重新构建 gem5。运行配置脚本的命令见下面输出的 `command line:` 一行。

注意，如果 `src/learning_gem5/part2` 中已包含后续“为 SimObject 添加参数（parameter）以及更多事件”一章的 `goodbye_object` 版本代码，当前 `run_hello.py` 可能因版本不匹配而出错。应先保存现有文件，并恢复成本章对应的示例版本，再运行。

```
    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled May  4 2016 11:37:41
    gem5 started May  4 2016 11:44:28
    gem5 executing on mustardseed.cs.wisc.edu, pid 22480
    command line: build/X86/gem5.opt configs/learning_gem5/part2/run_hello.py

    Global frequency set at 1000000000000 ticks per second
    Hello World! From a SimObject!
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    Exiting @ tick 18446744073709551615 because simulate() limit reached
```

至此，你已经编写了第一个 SimObject。后续章节将在此基础上扩展，探索它能够实现的功能。

---
layout: documentation
title: "为 SimObject 添加参数（parameter）与更多事件"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/parameters/
author: Jason Lowe-Power
---

为 SimObject 添加参数（parameter）以及更多事件
===============================================

gem5 Python 接口的一项强大能力，是把配置参数（parameter）从 Python 传入 C++ 对象。本章在[前面创建的 HelloObject]({{ site.baseurl }}/documentation/learning_gem5/part2/helloobject/)基础上，介绍几类 SimObject 参数（parameter）及其用法。

> **译注：版本一致性。** 原文混用了不同阶段的示例：部分构造函数定义接受 `const HelloObjectParams &`，头文件却仍声明指针形式；`EventWrapper` 的写法与前一章的 `EventFunctionWrapper` 也不一致。代码按原文保留，用于说明参数（parameter）传递原理；实际编译时必须统一构造函数签名、事件类型与 `gem5` 命名空间，并按所用版本处理自动生成的 `create()`。

简单参数（parameter）
-----------------

首先让 `HelloObject` 的事件延迟和触发次数可配置。在 `src/learning_gem5/part2/HelloObject.py` 的类定义中，加入使用 `Param` 类型的声明。

下面的 `time_to_wait` 是 `Latency` 类型，`number_of_fires` 是整数类型：

```python
class HelloObject(SimObject):
    type = 'HelloObject'
    cxx_header = "learning_gem5/part2/hello_object.hh"

    time_to_wait = Param.Latency("Time before firing the event")
    number_of_fires = Param.Int(1, "Number of times to fire the event before "
                                   "goodbye")
```

`Param.<TypeName>` 声明类型为 `TypeName` 的参数（parameter）。常见类型有 `Int`、`Float` 等，它们的使用方式类似普通 Python 类。

每项声明接受一个或两个实参。提供两个时，第一个为*默认值*。例如，如果实例化 `HelloObject` 时不指定 `number_of_fires`，就会采用默认值 1。

第二个实参是简短说明，必须是 Python 字符串。如果只提供一个实参，那么它就是说明，如 `time_to_wait` 所示，此时没有默认值。

gem5 也支持多种专用类型。例如，`Latency` 接受表示时间的字符串，并转换为模拟器（simulator）的 **tick**。默认每个 tick 为 1 ps，即每秒 10^12 tick（1 THz），所以 `"1ns"` 会转换为 1000。其他便利类型还包括 `Percent`、`Cycles`、`MemorySize` 等。

在 Python SimObject 文件中声明后，还需在 C++ 构造函数中取得这些值：

```cpp
HelloObject::HelloObject(const HelloObjectParams &params) :
    SimObject(params),
    event(*this),
    myName(params.name),
    latency(params.time_to_wait),
    timesLeft(params.number_of_fires)
{
    DPRINTF(Hello, "Created the hello object with the name %s\n", myName);
}
```

这里使用传入值初始化 `latency` 和 `timesLeft`，同时把参数（parameter）对象的 `name` 保存为成员 `myName`，供后面使用。每个 `params` 实例都具有来自 Python 对象实例化过程的名称。

保存名称只是演示如何使用 `params`。实际上，所有 SimObject 都有 `name()` 函数，因此无需额外存储名称。

在 `HelloObject` 类中添加对应成员：

```cpp
class HelloObject : public SimObject
{
  private:
    void processEvent();

    EventWrapper event;

    const std::string myName;

    const Tick latency;

    int timesLeft;

  public:
    HelloObject(HelloObjectParams *p);

    void startup() override;
};
```

此时直接运行，会得到以下错误：

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  4 2017 14:46:36
    gem5 started Jan  4 2017 14:46:52
    gem5 executing on chinook, pid 3422
    command line: build/X86/gem5.opt --debug-flags=Hello configs/learning_gem5/part2/run_hello.py

    Global frequency set at 1000000000000 ticks per second
    fatal: hello.time_to_wait without default or user set value

原因是 `time_to_wait` 没有默认值。需要在 `run_hello.py` 中显式设置：

```python
root.hello = HelloObject(time_to_wait = '2us')
```

也可以在创建对象后，通过成员赋值设置它。两种方式完全等价，因为直到调用 `m5.instantiate()` 才会创建 C++ 对象。

```python
root.hello = HelloObject()
root.hello.time_to_wait = '2us'
```

启用示例的调试标志后，输出如下：

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  4 2017 14:46:36
    gem5 started Jan  4 2017 14:50:08
    gem5 executing on chinook, pid 3455
    command line: build/X86/gem5.opt --debug-flags=Hello configs/learning_gem5/part2/run_hello.py

    Global frequency set at 1000000000000 ticks per second
          0: hello: Created the hello object with the name hello
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    2000000: hello: Hello world! Processing the event! 0 left
    2000000: hello: Done firing!
    Exiting @ tick 18446744073709551615 because simulate() limit reached

还可以修改脚本中的触发次数，让事件执行多次。

把其他 SimObject 作为参数（parameter）
------------------------------

SimObject 也可以接受另一个 SimObject。为此创建 `GoodbyeObject`，提供向其他对象说 “Goodbye” 的函数。为了使示例更有意义，它包含用于写入消息的缓冲区，并限制写入带宽。

先在 `SConscript` 中声明新对象：

```python
Import('*')

SimObject('HelloObject.py', sim_objects=['HelloObject', 'GoodbyeObject'])
Source('hello_object.cc')
Source('goodbye_object.cc')

DebugFlag('Hello')
```

更新后的文件见[此处]({{ site.baseurl }}/pages/static/scripts/part2/parameters/SConscript)。

然后添加 Python 声明。由于 `GoodbyeObject` 与 `HelloObject` 密切相关，可以将它们放在同一个 `HelloObject.py` 中。

它有两个带默认值的参数（parameter）：`MemorySize` 类型的缓冲区容量，以及控制填充速度的 `write_bandwidth`。缓冲区填满后，模拟（simulation）退出。

```python
class GoodbyeObject(SimObject):
    type = 'GoodbyeObject'
    cxx_header = "learning_gem5/part2/goodbye_object.hh"
    cxx_class = "gem5::GoodbyeObject"

    buffer_size = Param.MemorySize('1kB',
                                   "Size of buffer to fill with goodbye")
    write_bandwidth = Param.MemoryBandwidth('100MB/s', "Bandwidth to fill "
                                            "the buffer")
```

更新后的 `HelloObject.py` 见[此处]({{ site.baseurl }}/pages/static/scripts/part2/parameters/HelloObject.py)。

接着实现 `GoodbyeObject`：

```cpp
#ifndef __LEARNING_GEM5_GOODBYE_OBJECT_HH__
#define __LEARNING_GEM5_GOODBYE_OBJECT_HH__

#include <string>

#include "params/GoodbyeObject.hh"
#include "sim/sim_object.hh"

class GoodbyeObject : public SimObject
{
  private:
    void processEvent();

    /**
     * Fills the buffer for one iteration. If the buffer isn't full, this
     * function will enqueue another event to continue filling.
     */
    void fillBuffer();

    EventWrapper<GoodbyeObject, &GoodbyeObject::processEvent> event;

    /// The bytes processed per tick.
    float bandwidth;

    /// The size of the buffer we are going to fill.
    int bufferSize;

    /// The buffer we are putting our message in.
    char *buffer;

    /// The message to put into the buffer.
    std::string message;

    /// The amount of the buffer we've used so far.
    int bufferUsed;

  public:
    GoodbyeObject(GoodbyeObjectParams *p);
    ~GoodbyeObject();

    /**
     * Called by an outside object. Starts off the events to fill the buffer
     * with a goodbye message.
     *
     * @param name the name of the object we are saying goodbye to.
     */
    void sayGoodbye(std::string name);
};

#endif // __LEARNING_GEM5_GOODBYE_OBJECT_HH__
```

```cpp
#include "learning_gem5/part2/goodbye_object.hh"

#include "base/trace.hh"
#include "debug/Hello.hh"
#include "sim/sim_exit.hh"

GoodbyeObject::GoodbyeObject(const GoodbyeObjectParams &params) :
    SimObject(params), event(*this), bandwidth(params.write_bandwidth),
    bufferSize(params.buffer_size), buffer(nullptr), bufferUsed(0)
{
    buffer = new char[bufferSize];
    DPRINTF(Hello, "Created the goodbye object\n");
}

GoodbyeObject::~GoodbyeObject()
{
    delete[] buffer;
}

void
GoodbyeObject::processEvent()
{
    DPRINTF(Hello, "Processing the event!\n");
    fillBuffer();
}

void
GoodbyeObject::sayGoodbye(std::string other_name)
{
    DPRINTF(Hello, "Saying goodbye to %s\n", other_name);

    message = "Goodbye " + other_name + "!! ";

    fillBuffer();
}

void
GoodbyeObject::fillBuffer()
{
    // There better be a message
    assert(message.length() > 0);

    // Copy from the message to the buffer per byte.
    int bytes_copied = 0;
    for (auto it = message.begin();
         it < message.end() && bufferUsed < bufferSize - 1;
         it++, bufferUsed++, bytes_copied++) {
        // Copy the character into the buffer
        buffer[bufferUsed] = *it;
    }

    if (bufferUsed < bufferSize - 1) {
        // Wait for the next copy for as long as it would have taken
        DPRINTF(Hello, "Scheduling another fillBuffer in %d ticks\n",
                bandwidth * bytes_copied);
        schedule(event, curTick() + bandwidth * bytes_copied);
    } else {
        DPRINTF(Hello, "Goodbye done copying!\n");
        // Be sure to take into account the time for the last bytes
        exitSimLoop(buffer, 0, curTick() + bandwidth * bytes_copied);
    }
}
```

[头文件]({{ site.baseurl }}/pages/static/scripts/part2/parameters/goodbye_object.hh)与[实现文件]({{ site.baseurl }}/pages/static/scripts/part2/parameters/goodbye_object.cc)均可下载。

其对外接口 `sayGoodbye` 接受一个字符串。调用时先生成消息并保存到成员变量，再开始填充缓冲区。

为了模拟有限带宽，每次写入一段消息后，都等待完成这次写入所需的时间；这个等待过程用一个事件实现。

因为声明使用了 `MemoryBandwidth` 类型，传入 C++ 的 `bandwidth` 已自动换算为**每字节所需的 tick 数**。因此，写入延迟等于该值乘以要写入的字节数。

缓冲区填满时，调用 `exitSimLoop` 结束模拟（simulation）。这里使用的三个实参分别为返回 Python 配置脚本的消息（通过 `exit_event.getCause()` 取得）、退出码，以及退出时刻。

### 将 GoodbyeObject 传给 HelloObject

在 `HelloObject` 中声明一个 `GoodbyeObject` 类型的参数（parameter），只需将 SimObject 类名作为 `Param` 的 `TypeName`。与普通类型一样，可以提供默认值，也可以不提供。

```python
class HelloObject(SimObject):
    type = 'HelloObject'
    cxx_header = "learning_gem5/part2/hello_object.hh"

    time_to_wait = Param.Latency("Time before firing the event")
    number_of_fires = Param.Int(1, "Number of times to fire the event before "
                                   "goodbye")

    goodbye_object = Param.GoodbyeObject("A goodbye object")
```

更新后的 `HelloObject.py` 见[此处]({{ site.baseurl }}/pages/static/scripts/part2/parameters/HelloObject.py)。

然后在 C++ 的 `HelloObject` 中保存对 `GoodbyeObject` 的引用。不要忘记在 `hello_object.hh` 顶部包含 `goodbye_object.hh`。

```cpp
#include <string>

#include "learning_gem5/part2/goodbye_object.hh"
#include "params/HelloObject.hh"
#include "sim/sim_object.hh"

class HelloObject : public SimObject
{
  private:
    void processEvent();

    EventWrapper event;

    /// Pointer to the corresponding GoodbyeObject. Set via Python
    GoodbyeObject* goodbye;

    /// The name of this object in the Python config file
    const std::string myName;

    /// Latency between calling the event (in ticks)
    const Tick latency;

    /// Number of times left to fire the event before goodbye
    int timesLeft;

  public:
    HelloObject(const HelloObjectParams &p);

    void startup() override;
};
```

更新构造函数与事件处理函数，并检查 `goodbye` 指针是否有效。Python 中特殊的 `NULL` SimObject 可以用来传递空指针，但本例不支持这种情况，因此应触发 panic。

```cpp
#include "learning_gem5/part2/hello_object.hh"

#include "debug/Hello.hh"

HelloObject::HelloObject(HelloObjectParams &params) :
    SimObject(params),
    event(*this),
    goodbye(params.goodbye_object),
    myName(params.name),
    latency(params.time_to_wait),
    timesLeft(params.number_of_fires)
{
    DPRINTF(Hello, "Created the hello object with the name %s\n", myName);
    panic_if(!goodbye, "HelloObject must have a non-null GoodbyeObject");
}
```

处理完指定次数的事件后，调用 `GoodbyeObject::sayGoodbye`：

```cpp
void
HelloObject::processEvent()
{
    timesLeft--;
    DPRINTF(Hello, "Hello world! Processing the event! %d left\n", timesLeft);

    if (timesLeft <= 0) {
        DPRINTF(Hello, "Done firing!\n");
        goodbye->sayGoodbye(myName);
    } else {
        schedule(event, curTick() + latency);
    }
}
```

更新后的[头文件]({{ site.baseurl }}/pages/static/scripts/part2/parameters/hello_object.hh)和[实现文件]({{ site.baseurl }}/pages/static/scripts/part2/parameters/hello_object.cc)见对应链接。

### 更新配置脚本

最后把 `GoodbyeObject` 加入配置。创建 `hello_goodbye.py`，同时实例化两个对象。例如：

```python
import m5
from m5.objects import *

root = Root(full_system = False)

root.hello = HelloObject(time_to_wait = '2us', number_of_fires = 5)
root.hello.goodbye_object = GoodbyeObject(buffer_size='100B')

m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
```

完整脚本可从[此处]({{ site.baseurl }}/pages/static/scripts/part2/parameters/hello_goodbye.py)下载。

运行后输出如下：

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  4 2017 15:17:14
    gem5 started Jan  4 2017 15:18:41
    gem5 executing on chinook, pid 3838
    command line: build/X86/gem5.opt --debug-flags=Hello configs/learning_gem5/part2/hello_goodbye.py

    Global frequency set at 1000000000000 ticks per second
          0: hello.goodbye_object: Created the goodbye object
          0: hello: Created the hello object
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
    2000000: hello: Hello world! Processing the event! 4 left
    4000000: hello: Hello world! Processing the event! 3 left
    6000000: hello: Hello world! Processing the event! 2 left
    8000000: hello: Hello world! Processing the event! 1 left
    10000000: hello: Hello world! Processing the event! 0 left
    10000000: hello: Done firing!
    10000000: hello.goodbye_object: Saying goodbye to hello
    10000000: hello.goodbye_object: Scheduling another fillBuffer in 152592 ticks
    10152592: hello.goodbye_object: Processing the event!
    10152592: hello.goodbye_object: Scheduling another fillBuffer in 152592 ticks
    10305184: hello.goodbye_object: Processing the event!
    10305184: hello.goodbye_object: Scheduling another fillBuffer in 152592 ticks
    10457776: hello.goodbye_object: Processing the event!
    10457776: hello.goodbye_object: Scheduling another fillBuffer in 152592 ticks
    10610368: hello.goodbye_object: Processing the event!
    10610368: hello.goodbye_object: Scheduling another fillBuffer in 152592 ticks
    10762960: hello.goodbye_object: Processing the event!
    10762960: hello.goodbye_object: Scheduling another fillBuffer in 152592 ticks
    10915552: hello.goodbye_object: Processing the event!
    10915552: hello.goodbye_object: Goodbye done copying!
    Exiting @ tick 10944163 because Goodbye hello!! Goodbye hello!! Goodbye hello!! Goodbye hello!! Goodbye hello!! Goodbye hello!! Goo

可以修改两个 SimObject 的参数（parameter），观察总模拟（simulation）时间如何变化，例如上述输出中的 `Exiting @ tick 10944163`。进行这类实验时，可以关闭调试标志，减少终端输出。

接下来的章节会创建更复杂、更实用的 SimObject，最终实现一个用于单处理器的简单阻塞式缓存（cache）。

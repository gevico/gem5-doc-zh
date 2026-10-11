---
layout: documentation
title: "事件驱动（event-driven）编程"
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/events/
author: Jason Lowe-Power
---

事件驱动（event-driven）编程
========================

gem5 是事件驱动（event-driven）模拟器（simulator）。本章以[前面创建的 HelloObject]({{ site.baseurl }}/documentation/learning_gem5/part2/helloobject/)为基础，介绍如何创建和调度事件。

创建简单的事件回调
--------------------------------

在 gem5 的事件驱动（event-driven）模型中，每个事件都有一个回调函数，负责*处理*事件。一般可以通过继承 `Event` 实现；对于简单事件，gem5 还提供了包装器。

在 `HelloObject` 头文件中声明 `processEvent()`，让它在事件每次触发时执行。该函数必须无实参、无返回值。

再添加一个事件实例。这里使用 `EventFunctionWrapper`，包装符合上述签名的可调用对象。同时声明稍后解释的 `startup()`：

```cpp
class HelloObject : public SimObject
{
  private:
    void processEvent();

    EventFunctionWrapper event;

  public:
    HelloObject(const HelloObjectParams &p);

    void startup() override;
};
```

然后在 `HelloObject` 构造函数中初始化事件。`EventFunctionWrapper` 接受两个主要实参：要执行的函数和事件名称。名称通常使用所属 SimObject 的名称；输出事件名时会自动追加 `.wrapped_function_event`。

第一个实参类型为 `std::function<void(void)>`。通常使用简单的 lambda 调用成员函数，也可以使用其他符合签名的函数。下面用 `[this]` 捕获当前实例，以便调用它的成员函数：

```cpp
HelloObject::HelloObject(const HelloObjectParams &params) :
    SimObject(params), event([this]{processEvent();}, name())
{
    DPRINTF(HelloExample, "Created the hello object\n");
}
```

还需实现事件处理函数。这里仅在启用调试输出时打印消息：

```cpp
void
HelloObject::processEvent()
{
    DPRINTF(HelloExample, "Hello world! Processing the event!\n");
}
```

调度事件
-----------------

事件必须先被*调度*，才会得到处理。`schedule` 函数把一个 `Event` 安排在未来的某个时刻；事件驱动（event-driven）模拟（simulation）不允许事件在过去执行。

首次调度放在 `HelloObject::startup()` 中。SimObject 可以在这里安排内部事件。只有首次启动模拟（simulation），即从 Python 配置文件调用 `simulate()` 时，才会执行 `startup()`。

```cpp
void
HelloObject::startup()
{
    schedule(event, 100);
}
```

这里把事件安排在 tick 100。通常应在 `curTick()` 基础上加一个时间偏移；此例知道 `startup()` 在时间 0 被调用，因此可以直接使用绝对 tick 值。

启用 `HelloExample` 后，输出如下：

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  4 2017 11:01:46
    gem5 started Jan  4 2017 13:41:38
    gem5 executing on chinook, pid 1834
    command line: build/X86/gem5.opt --debug-flags=Hello configs/learning_gem5/part2/run_hello.py

    Global frequency set at 1000000000000 ticks per second
          0: hello: Created the hello object
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
        100: hello: Hello world! Processing the event!
    Exiting @ tick 18446744073709551615 because simulate() limit reached

进一步调度事件
---------------------

还可以在事件处理过程中调度后续事件。下面为 `HelloObject` 添加延迟和触发次数两个成员变量。[下一章]({{ site.baseurl }}/documentation/learning_gem5/part2/parameters/)会把它们开放为可从 Python 配置的参数（parameter）。

在类声明中添加：

```cpp
class HelloObject : public SimObject
{
  private:
    void processEvent();

    EventFunctionWrapper event;

    const Tick latency;

    int timesLeft;

  public:
    HelloObject(const HelloObjectParams &p);

    void startup() override;
};
```

在构造函数中为 `latency` 和 `timesLeft` 设置初值：

```cpp
HelloObject::HelloObject(const HelloObjectParams &params) :
    SimObject(params), event([this]{processEvent();}, name()),
    latency(100), timesLeft(10)
{
    DPRINTF(HelloExample, "Created the hello object\n");
}
```

最后更新 `startup()` 与 `processEvent()`：

```cpp
void
HelloObject::startup()
{
    schedule(event, latency);
}

void
HelloObject::processEvent()
{
    timesLeft--;
    DPRINTF(HelloExample, "Hello world! Processing the event! %d left\n", timesLeft);

    if (timesLeft <= 0) {
        DPRINTF(HelloExample, "Done firing!\n");
    } else {
        schedule(event, curTick() + latency);
    }
}
```

现在事件应触发 10 次，最后一次发生在 tick 1000。输出如下：

> **译注：** 原文称“模拟在 1000 tick 后结束”，但这个示例只停止安排新事件，并没有显式调用退出函数。应区分最后一个自定义事件的时刻与 `m5.simulate()` 最终返回时报告的 tick；后者以所用版本和运行限制为准。

    gem5 Simulator System.  http://gem5.org
    gem5 is copyrighted software; use the --copyright option for details.

    gem5 compiled Jan  4 2017 13:53:35
    gem5 started Jan  4 2017 13:54:11
    gem5 executing on chinook, pid 2326
    command line: build/X86/gem5.opt --debug-flags=Hello configs/learning_gem5/part2/run_hello.py

    Global frequency set at 1000000000000 ticks per second
          0: hello: Created the hello object
    Beginning simulation!
    info: Entering event queue @ 0.  Starting simulation...
        100: hello: Hello world! Processing the event! 9 left
        200: hello: Hello world! Processing the event! 8 left
        300: hello: Hello world! Processing the event! 7 left
        400: hello: Hello world! Processing the event! 6 left
        500: hello: Hello world! Processing the event! 5 left
        600: hello: Hello world! Processing the event! 4 left
        700: hello: Hello world! Processing the event! 3 left
        800: hello: Hello world! Processing the event! 2 left
        900: hello: Hello world! Processing the event! 1 left
       1000: hello: Hello world! Processing the event! 0 left
       1000: hello: Done firing!
    Exiting @ tick 18446744073709551615 because simulate() limit reached

更新后的[头文件]({{ site.baseurl }}/pages/static/scripts/part2/events/hello_object.hh)与[实现文件]({{ site.baseurl }}/pages/static/scripts/part2/events/hello_object.cc)可以通过对应链接查看。

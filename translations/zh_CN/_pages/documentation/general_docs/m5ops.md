---
layout: documentation
title: M5ops
doc: gem5 文档
parent: m5ops
permalink: /documentation/general_docs/m5ops/
---

# M5ops

本页介绍可在 M5 中用于执行检查点（checkpoint）等操作的特殊操作码。m5 实用程序（在我们的磁盘镜像中以及 util/m5/* 中）在命令行上提供了其中部分功能。在很多情况下，最好把该操作直接插入到你关心的应用程序源码中。你应该能够链接相应的 libm5.a 文件，而 m5ops.h 头文件中包含所有函数的原型。
关于使用 M5ops 的教程是 gem5 2022 Bootcamp 的一部分。该活动的录像见[此处](https://youtu.be/TeHKMVOWUAY)。

## 构建 M5 与 libm5

要为你的目标指令集架构（ISA）构建 m5 和 libm5.a，请在 util/m5/ 目录中运行以下命令。

```bash
scons build/{TARGET_ISA}/out/m5
```

目标指令集架构（ISA）列表如下。

* x86
* arm (arm-linux-gnueabihf-gcc)
* thumb (arm-linux-gnueabihf-gcc)
* sparc (sparc64-linux-gnu-gcc)
* arm64 (aarch64-linux-gnu-gcc)
* riscv (riscv64-unknown-linux-gnu-gcc)

注意，如果你在 x86 系统上为其他指令集架构构建，需要安装交叉编译器。交叉编译器的名称列在上表各项的括号中。

更多细节请参见 [util/m5/README.md](https://github.com/gem5/gem5/blob/stable/util/m5/README.md)。

## m5 实用程序（FS 模式）

m5 实用程序（见 util/m5/）可以在 FS 模式下用于发出特殊指令，以触发模拟（simulation）特有的功能。它目前提供以下选项：

* initparam：已废弃，仅为兼容旧二进制程序而保留
* exit [delay]：在 delay 纳秒后停止模拟。
* resetstats [delay [period]]：在 delay 纳秒后重置模拟统计信息（statistics）；此后每 period 纳秒重复一次。
* dumpstats [delay [period]]：在 delay 纳秒后把模拟统计信息保存到文件；此后每 period 纳秒重复一次。
* dumpresetstats [delay [period]]：等同于 dumpstats; resetstats
* checkpoint [delay [period]]：在 delay 纳秒后创建检查点（checkpoint）；此后每 period 纳秒重复一次。
* readfile：打印由配置参数 system.readfile 指定的文件。rcS 文件正是以此方式被复制到模拟环境中的。
* debugbreak：在模拟器中调用 debug_break()（使模拟器收到 SIGTRAP 信号，在用 GDB 调试时很有用）。
* switchcpu：引发一个类型为 "switch cpu" 的退出事件，使 Python 可以在需要时切换到另一个 CPU 模型。
* workbegin：引发一个类型为 "workbegin" 的退出事件，可用于标记 ROI 的开始。
* workend：引发一个类型为 "workend" 的退出事件，可用于标记 ROI 的结束。

## 其他 M5 操作

以下是其他在命令行形式下用处不大的 M5 操作。

* quiesce：取消调度 CPU 的 tick() 调用，直到某个异步事件（中断）将其唤醒
* quiesceNS：同上，但如果在此之前未被唤醒，则在若干纳秒后自动唤醒
* quiesceCycles：同上，但使用 CPU 周期数而不是纳秒
* quisceTIme：CPU 被置为静止状态的时间长度
* addsymbol：向模拟器的符号表添加一个符号。例如在内核模块被加载时

## 在 Java 代码中使用 gem5 操作

这些操作也可以在 Java 代码中使用。它们允许像下面这样在 Java 程序内部调用 gem5 操作：

```python
import jni.gem5Op;

public  class HelloWorld {

   public static void main(String[] args) {
       gem5Op gem5 = new gem5Op();
       System.out.println("Rpns0:" + gem5.rpns());
       System.out.println("Rpns1:" + gem5.rpns());
   }

   static {
       System.loadLibrary("gem5OpJni");
   }
}
```

构建时需要确保 classpath 中包含 gem5OpJni.jar：

```javascript
javac -classpath $CLASSPATH:/path/to/gem5OpJni.jar HelloWorld.java
```

运行时需要确保同时设置了 java 路径和库路径：

```javascript
java -classpath $CLASSPATH:/path/to/gem5OpJni.jar -Djava.library.path=/path/to/libgem5OpJni.so HelloWorld
```

## 在 Fortran 代码中使用 gem5 操作

gem5 的特殊操作码（伪指令）可以与 Fortran 程序配合使用。在 Fortran 代码中，可以调用那些会触发特殊操作码的 C 函数。在生成最终二进制程序时，把 Fortran 程序的目标文件和（操作码的）C 程序目标文件一起编译。我觉得[此处](https://gcc.gnu.org/wiki/GFortranGettingStarted)提供的文档很有帮助。请阅读 **-****- Compiling a mixed C-Fortran program** 一节。

用 gem5 操作配合 Fortran 代码的思路，本质上是把 m5 操作的 C 代码编译成目标文件，然后把该目标文件与调用 m5 操作的二进制程序链接起来。
Fortran 中的 C 函数调用约定是这样的：如果 C 代码中的函数名是 `void foo_bar_(void)`，那么在 Fortran 中可以通过 `call foo_bar` 调用该函数。

## 把 M5 链接到你的 C/C++ 代码

要把 m5 链接到你的代码，首先按上一节所述构建 `libm5.a`。

然后：

* 在你的源文件中包含 `gem5/m5ops.h`
* 把 `gem5/include` 加入编译器的包含搜索路径
* 把 `gem5/util/m5/build/{TARGET_ISA}/out` 加入链接器搜索路径
* 链接 `libm5.a`

例如，可以通过在 Makefile 中添加以下内容来实现：

```
CFLAGS += -I$(GEM5_PATH)/include
LDFLAGS += -L$(GEM5_PATH)/util/m5/build/$(TARGET_ISA)/out -lm5
```

下面是一个简单的 Makefile 示例：

```make
TARGET_ISA=x86

GEM5_HOME=$(realpath ./)
$(info   GEM5_HOME is $(GEM5_HOME))

CXX=g++

CFLAGS=-I$(GEM5_HOME)/include

LDFLAGS=-L$(GEM5_HOME)/util/m5/build/$(TARGET_ISA)/out -lm5

OBJECTS= hello_world

all: hello_world

hello_world:
	$(CXX) -o $(OBJECTS) hello_world.cpp $(CFLAGS) $(LDFLAGS)

clean:
	rm -f $(OBJECTS)
```


## 使用 M5ops 的 "_addr" 版本

m5ops 的 "_addr" 版本会触发与默认 m5ops 相同的模拟特定功能，但使用不同的触发机制。下面引用 m5 实用程序 README.md 中对触发机制的说明。

```markdown
The bare function name as defined in the header file will use the magic instruction based trigger mechanism, what would have historically been the default.

Some macros at the end of the header file will set up other declarations which mirror all of the other definitions, but with an “_addr” and “_semi” suffix. These other versions will trigger the same gem5 operations, but using the “magic” address or semihosting trigger mechanisms. While those functions will be unconditionally declared in the header file, a definition will exist in the library only if that trigger mechanism is supported for that ABI.
```

*注意*：生成 "_addr" 和 "_semi" m5ops 的宏名为 `M5OP`，定义在 `util/m5/abi/*/m5op_addr.S` 和 `util/m5/abi/*/m5op_semi.S` 中。

要使用 m5ops 的 "_addr" 版本，你需要包含 m5_mmap.h 头文件，把 "magic" 地址（例如 x86 为 "0xFFFF0000"，arm64/riscv 为 "0x10010000"）传给 m5op_addr，然后调用 map_m5_mem() 打开 /dev/mem。你可以在原 m5ops 函数名末尾添加 "_addr" 来插入 m5ops。

下面是一个使用 m5ops "_addr" 版本的简单示例：

```c
#include <gem5/m5ops.h>
#include <m5_mmap.h>
#include <stdio.h>

#define GEM5

int main(void) {
#ifdef GEM5
    m5op_addr = 0xFFFF0000;
    map_m5_mem();
    m5_work_begin_addr(0,0);
#endif

    printf("hello world!\n");

#ifdef GEM5
    m5_work_end_addr(0,0);
    unmap_m5_mem();
#endif
}
```

*注意*：你需要新增一个头文件位置，让编译器能够找到 `m5_mmap.h`。
如果沿用上面的示例 Makefile，你可以在定义 CFLAGS 的那一行下面加上：

```c
CFLAGS += $(GEM5_PATH)/util/m5/src/
```

当你在 FS 模式下配合 KVM CPU 运行插入了 m5ops 的应用程序时，可能会出现这个错误。

    ```illegal instruction (core dumped)```

这是因为 m5ops 指令对宿主机（host）来说不是有效指令。使用 m5ops 的 "_addr" 版本可以解决该问题，因此如果你想在应用程序中集成 m5ops，或在 KVM CPU 下使用 m5 二进制实用程序，就必须使用 "_addr" 版本。

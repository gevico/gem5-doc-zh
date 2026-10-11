---
layout: documentation
title: "作业 2"
doc: 学习 gem5
parent: gem5_101
permalink: /documentation/learning_gem5/gem5_101/homework-2
authors:
---

# CS 752 作业 2：高级计算机体系结构（architecture）I（2015 年秋季，唯一班级）

**截止日期：9 月 21 日，星期一，下午 1 点。**

**独立完成，不接受迟交。**

> **译注**：这是历史课程作业。FSUBR 缺失、源码路径、Mercurial 命令等说明对应当时的 gem5；开始实验前应核对所用版本。提交要求保留作资料，有关教程的问题应参照 [gem5 101 总览]({{ site.baseurl }}/documentation/learning_gem5/gem5_101/)。

## 目的

熟悉 gem5 的指令集描述语言。阅读 `src/arch/x86/isa`，理解指令如何解码并拆成最终执行的微操作，再实现当时缺失的 x87 指令 FSUBR。x87 是 x86 指令集架构（ISA）的浮点扩展子集，如今使用已较少。用 GCC 内联汇编编写调用该指令的小程序，再在 gem5 中验证。

x86 指令通常包含较多工作。不同指令之间存在可复用的步骤，因此通常将一条完整指令称为宏操作（macro-op），并拆为多个微操作（micro-op）。在 gem5 中实现时，先告知解码器该宏操作的编码，再用微操作组合实现它，最后补齐尚未实现的微操作。本作业参照已有 FSUB 实现完成 FSUBR。

> **译注：手册链接。** 原文两份 PDF 位于已无法解析的 `amd-dev.wpengine.netdna-cdn.com` 域名，分别为 `24594_APM_v3.pdf` 与 `26569_APM_v51.pdf`。这里改为可用的官方检索入口；下文第 443 页等页码仍对应原课程使用的版本。

## 实现与验证步骤

1. **理解编码与解码。** x86 有多种编码方式，本作业关注 x87。可参考 AMD 的指令编码手册，即 AMD64 Architecture Programmer’s Manual 第 3 卷（文档编号 24594），通过 [AMD 官方文档检索](https://www.amd.com/en/search/documentation/hub.html)查找。阅读 `src/arch/x86/isa/decoder/one_byte_opcodes.isa`，它采用专用描述语言，最终生成 C++ `switch`。首先解码操作码字节的高 5 位，共有 32 种组合。

   x87 操作码范围为 `0xD8`—`0xDF`，高 5 位均为 `0x1B`，因此该分支包含 `src/arch/x86/isa/decoder/x87.isa`。继续阅读此文件，它再解码低 3 位。手册第 443 页表 A-15 列出各分支对应指令。例如 FSUB 与 FSUBR 涉及 `0xD8` 和 `0xDC`，低位分支为 `0x0` 和 `0x4`。区分同一指令不同编码的含义，还需要理解 ModRM 字段。原课程版本中可以看到 FSUB 的相应分支，而 FSUBR 尚未实现。

   首先阅读 AMD64 Architecture Programmer’s Manual 第 5 卷（文档编号 26569）中的 FSUBR 说明，可通过 [AMD 官方文档检索](https://www.amd.com/en/search/documentation/hub.html)查找，理解操作码 `D8h` 与 `DCh` 两种形式的差异。

2. **修改解码声明。** 找出 `x87.isa` 中三处 `fsubr`，参照 FSUB 修改。使用 `Inst::FSUBR` 等声明，表示应执行该指令，而不是默认的“尚未实现”警告处理。

3. **实现宏操作。** 进入 `src/arch/x86/isa/insts/x87/arithmetic/`，查看 FSUB 如何由微操作构成。`FSUB1` 和 `FSUB2` 对应前述两类编码。每一类都需要三种形式：只使用寄存器；按指令指定地址读取内存操作数；相对于指令指针读取内存操作数。阅读这些微操作即可理解其分工。

   gem5 的解析方式要求 FSUBR 也定义全部三种形式，因此两类共需六个代码块，与 FSUB 对应。

4. **检查微操作。** 所需的 `subfp` 已在 `src/arch/x86/isa/micro-ops/fpop.isa` 实现，无需新增。

5. **编译。** 构建 x86 版本的 gem5，检查实现是否存在编译错误。指令描述语言还有许多本作业未介绍的部分，原文提醒其中不少需要直接阅读相关源码才能理解。

6. **编写测试程序。** 用 C 读取文件中的两个浮点数，计算减法并输出结果。通过 GCC 内联汇编显式使用 FSUBR。

`asm` 代码块包含汇编字符串和操作数约束。汇编字符串描述指令；GCC 不负责验证其中指令的语义，最终还需由汇编器处理。约束部分说明输入输出可以使用哪些位置，以及哪些寄存器或内存会被影响。建议阅读：

- <https://www.ibiblio.org/gferg/ldp/GCC-Inline-Assembly-HOWTO.html>
- <http://locklessinc.com/articles/gcc_asm/>

由于许多读者尚未使用过内联汇编，而约束不易写对，作业提供以下实现。

```cpp
  float subtract(float in1, float in2)
  {
    float ret = 0.0;
    asm ("fsubr %2, %0" : "=&t" (ret) : "%0" (in1), "u" (in2));
    return ret;
  }
```

该函数对两个浮点输入执行减法并返回结果，指令字符串为 `"fsubr %2, %0"`。输出约束指定变量 `ret`，随后指定输入 `in1` 和 `in2`。约束字母 `t` 与 `u` 分别表示 x87 栈顶和次栈顶寄存器。

将这个函数用于 C 程序：接收文件名，从文件读取两个浮点数，调用 FSUBR 完成减法，并将结果写到标准输出。静态编译得到可执行文件，也可使用 `-S` 查看编译器生成的汇编。

7. **运行模拟（simulation）。** 学习如何向 gem5 中的程序传递命令行实参。可以使用原示例脚本 `configs/example/se.py`，或者作业 1 的配置。阅读该脚本及 `configs/common/Options.py`，确定如何传入实参。

> **译注**：原文此处写作 `configs/examples/se.py`，目录名应为 `example`；较新版本中这类旧脚本还可能移至 `configs/deprecated/example/`。

## 提交内容

原课程要求发送邮件给 David Wood 教授 <david@cs.wisc.edu> 和 Nilay Vaish <nilay@cs.wisc.edu>，主题为 `[CS752 Homework2]`。

1. 写明姓名与学号，以下文件打包为 zip 附件。
2. `fsubr.c`：测试 FSUBR 的程序。
3. 修改 `src/arch/x86/isa/insts/x87/arithmetic/` 和 `src/arch/x86/isa/decoder/x87.isa` 的补丁。原文使用 Mercurial 命令 `hg diff src/arch/x86/isa > /tmp/changes.patch` 生成。
4. 分别使用 `TimingSimpleCPU` 和 `MinorCPU` 运行得到的两个 `stats.txt`。
5. 约 200 词的简短报告，说明使用 gem5 的语言与方法实现指令集架构（ISA）的体验。

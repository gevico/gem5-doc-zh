---
layout: documentation
title: "编译 SLICC 协议（protocol）"
doc: 学习 gem5
parent: part3
permalink: /documentation/learning_gem5/part3/MSIbuilding/
author: Jason Lowe-Power
---

## 构建 MSI 协议（protocol）

### SLICC 文件

实现完成后，需要将其编译进 gem5。完整文件见：

- [MSI-cache.sm](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/MSI-cache.sm)
- [MSI-dir.sm](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/MSI-dir.sm)
- [MSI-msg.sm](https://gem5.googlesource.com/public/gem5/+/refs/heads/stable/src/learning_gem5/part3/MSI-msg.sm)

构建前还需创建 `MSI.slicc`，告诉 SLICC 编译器需要处理哪些文件。首行声明协议（protocol）名称，随后用若干 `include` 列出文件。它们可以位于 SCons 构建环境变量 `PROTOCOL_DIRS` 指定的任一目录中。之前的 `SConsopts` 使用 `main.Append(PROTOCOL_DIRS=[Dir('.')])` 加入当前目录；公共定义位于 `src/mem/ruby/protocol/`。

这些文件像 C++ 头文件一样按顺序包含，实际相当于一个大 SLICC 文件。因此，类型定义必须先于使用它的文件出现。例如 `MSI-msg.sm` 必须在 `MSI-cache.sm` 之前，因为后者使用了 `RequestMsg`。

> **译注**：原文把公共定义目录写成 `src/mem/protocol/`，遗漏了 `ruby`。

```cpp
protocol "MSI";
include "RubySlicc_interfaces.slicc";
include "MSI-msg.sm";
include "MSI-cache.sm";
include "MSI-dir.sm";
```

可以[查看完整的 MSI.slicc](https://github.com/gem5/gem5/blob/stable/src/learning_gem5/part3/MSI.slicc)。

### 添加 RUBY_PROTOCOL_MSI 配置项（gem5 >= 23.1）

gem5 23.1 及之后版本需要额外配置 Kconfig。使用 23.0 或更早版本时，可跳到下一节对应的旧版构建方式。

在 `src/learning_gem5/part3/Kconfig` 中登记 MSI，使 SCons 能够启用它。

```
# Set the PROTOCOL="MSI" if the RUBY_PROTOCOL_MSI=y
config PROTOCOL
    default "MSI" if RUBY_PROTOCOL_MSI

# Add the new choice RUBY_PROTOCOL_MSI
cont_choice "Ruby protocol"
    config RUBY_PROTOCOL_MSI
        bool "MSI"
endchoice
```

然后修改 `src/Kconfig`：

```
rsource "base/Kconfig"
rsource "mem/ruby/Kconfig"
rsource "learning_gem5/part3/Kconfig"
```

在包含 `mem/ruby/Kconfig` 的语句下方，加入 `learning_gem5/part3/Kconfig`。

### 使用 SCons 编译

#### 旧版 gem5（gem5 <= 23.0）

本教程所对应版本的许多 `build_opts/` 默认配置选择了性能较低的教学示例 `MI_example`。因此，不能仅指定 `X86` 或 `ARM` 这样的默认构建名，还需要显式选择 MSI。以下命令使用 x86 指令集架构（ISA）构建：

```sh
scons build/X86_MSI/gem5.opt --default=X86 PROTOCOL=MSI SLICC_HTML=True
```

输出为 `build/X86_MSI/gem5.opt`，构建目录也可以另行命名。`--default` 指定从 `build_opts` 的哪个文件读取 SCons 默认变量，例如 `ISA` 和 `CPU_MODELS`；`PROTOCOL` 则覆盖该文件中的默认协议（protocol）。

`SLICC_HTML=True` 使 SLICC 生成 HTML 状态转换表，输出到 `<build directory>/mem/protocol/html`。默认跳过这一过程，因为它会增加构建耗时，在网络文件系统上尤为明显。

编译完成后，就得到了包含 MSI 的 gem5。若要切换其他协议（protocol），需要更改 `PROTOCOL`。尤其在进行对比时，建议为每种协议（protocol）使用独立构建目录。

SLICC 编译错误通常会报告文件名和行号，但行号可能在实际错误之后，有时相距很远。例如花括号不匹配时，错误位置可能指向文件末尾。

#### 新版 gem5（gem5 >= 23.1）

使用 Kconfig 后，需要通过 `menuconfig`、`setconfig` 等工具选择配置，不能假定默认构建已经启用 MSI。原文所用默认配置仍以 `MI_example` 为例。以下命令使用 x86 指令集架构（ISA）构建：

```sh
scons defconfig build/X86_MSI build_opts/X86
scons setconfig build/X86_MSI RUBY_PROTOCOL_MSI=y SLICC_HTML=y
scons build/X86_MSI/gem5.opt
```

输出同样为 `build/X86_MSI/gem5.opt`。第一条命令创建构建目录，以 `build_opts/X86` 为默认配置；第二条通过 `setconfig` 启用 `RUBY_PROTOCOL_MSI=y`，并设置 `SLICC_HTML=y`；最后一条按更新后的配置执行构建。也可以使用 `menuconfig` 交互式调整。

启用 `SLICC_HTML=y` 后，HTML 表格写入 `<build directory>/mem/protocol/html`。默认不生成它们，以减少构建开销，尤其是在网络文件系统上。

若要选择其他协议（protocol），在配置阶段启用对应的 `RUBY_PROTOCOL_{NAME}=y`。为不同协议（protocol）保留独立构建目录，有助于开展对比实验。

SLICC 的错误定位仍需注意：报告行号可能在实际错误之后；花括号不匹配可能直到文件末尾才被发现。

> **译注**：本节保留原文的单一协议（protocol）构建示例。更晚版本可能采用多协议（protocol）构建和不同的默认配置，应结合当前版本的 Kconfig 选项使用。

更多信息见 [gem5 Kconfig 构建系统文档]({{ site.baseurl }}/documentation/general_docs/kconfig_build_system/)。

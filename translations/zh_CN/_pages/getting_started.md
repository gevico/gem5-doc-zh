---
layout: page
title: gem5 快速开始
permalink: /getting_started/
author: Jason Lowe-Power
---

# gem5 快速开始

## 第一步

当你基于现有代码库构建新模型和新功能时，gem5 模拟器（simulator）对研究最为有用。
因此，最常见的使用方式是下载源码并自行构建。

要下载 gem5，你可以使用 [`git`](https://git-scm.com/) 检出当前的 stable 分支。
如果你不熟悉版本控制或 git，[git book](https://git-scm.com/book/en/v2)（可免费在线阅读）是了解 git、熟悉版本控制的极佳材料。
gem5 的规范版本托管在 [GitHub](https://github.com/gem5/gem5) 上。

```
git clone https://github.com/gem5/gem5
```

克隆源码后，你可以使用 [`scons`](https://scons.org/) 构建 gem5。
构建 gem5 所需时间从大型服务器上的几分钟到笔记本电脑上的 45 分钟不等。
构建 gem5 对计算和内存消耗较大，使用更多线程会使构建过程占用更多内存。
因此，在性能较低的机器上构建 gem5 时建议使用较少的线程（例如 -j 1 或 -j 2）。
gem5 必须在 Unix 平台上构建。
Linux 在每次提交上都会测试，也有人成功在 MacOS 上使用，但没有定期测试。
强烈建议*不要*在虚拟机上编译 gem5。
在笔记本电脑上的虚拟机中运行时，gem5 光编译就可能需要一个多小时。
[构建 gem5](/documentation/general_docs/building) 提供了关于构建 gem5 及其依赖项的更多细节。

```
cd gem5
scons build/ALL/gem5.opt -j <NUMBER OF CPUs ON YOUR PLATFORM>
```

现在你有了 gem5 二进制程序，可以运行你的第一次模拟（simulation）了！
gem5 的接口是 Python 脚本。
gem5 二进制程序读取并执行所提供的 Python 脚本，该脚本创建被测系统并执行模拟器。
在本例中，脚本会创建一个*非常*简单的系统，并执行一个 "hello world" 二进制程序。
关于该脚本的更多信息见 [Learning gem5](/documentation/learning_gem5/introduction) 一书的 [Simple Config 章节](/documentation/learning_gem5/part1/simple_config)。

```
build/ALL/gem5.opt configs/learning_gem5/part1/simple.py
```

运行该命令后，你会看到 gem5 的输出以及 `Hello world`，后者来自 hello world 二进制程序！
现在，你可以开始深入研究如何使用和扩展 gem5 了！

## 后续步骤

- [Learning gem5](/documentation/learning_gem5/introduction) 是一本仍在编写中的书，介绍如何使用 gem5 以及如何基于它进行开发。书中包含如何创建配置文件、如何用新模型扩展 gem5、gem5 的缓存一致性（cache coherence）模型等细节。
- [gem5 活动](/events)经常随计算机体系结构会议以及其他场合举办。
- 你可以通过 [gem5 的各个渠道](/ask-a-question)获取帮助，也可以关注 [Stack Overflow 上的 gem5 标签](https://stackoverflow.com/questions/tagged/gem5)。
- [贡献指南](/contributing)介绍了如何贡献代码修改，以及为 gem5 做贡献的其他方式。

## 在研究中使用 gem5 的建议

### 我应该使用哪个版本的 gem5？

gem5 的 git 仓库有两个分支：`develop` 和 `stable`。`develop`
分支包含最新的 gem5 变更，**但并不稳定**。它
更新频繁。**只有在为 gem5 项目做贡献时才应使用 `develop` 分支**
（关于如何向 gem5 提交代码，请参见我们的[贡献指南](
/contributing)）。

stable 分支包含稳定的 gem5 代码。stable 分支的 HEAD
指向最新的 gem5 发布版本。我们建议研究者使用
gem5 最新的稳定发布版本，并在发表结果时报告所使用的版本
（使用 `git describe` 查看最新的 gem5 发布版本号）。

如果要复现以前的工作，请查明当时使用的是哪个 gem5 版本。该
版本会在 `stable` 分支上打标签，因此可以用
`git checkout -b {branch} {version}` 在新分支上检出。
例如，要把 `v19.0.0` 检出到名为 `version19` 的新分支：
`git checkout -b version19 v19.0.0`。通过在 `stable` 分支上执行
`git tag` 可以得到完整的 gem5 已发布版本列表。

### 我应该如何引用 gem5？

你应当引用 [gem5-20 论文](https://arxiv.org/abs/2007.03152)。

```
The gem5 Simulator: Version 20.0+. Jason Lowe-Power, Abdul Mutaal Ahmad, Ayaz Akram, Mohammad Alian, Rico Amslinger, Matteo Andreozzi, Adrià Armejach, Nils Asmussen, Brad Beckmann, Srikant Bharadwaj, Gabe Black, Gedare Bloom, Bobby R. Bruce, Daniel Rodrigues Carvalho, Jeronimo Castrillon, Lizhong Chen, Nicolas Derumigny, Stephan Diestelhorst, Wendy Elsasser, Carlos Escuin, Marjan Fariborz, Amin Farmahini-Farahani, Pouya Fotouhi, Ryan Gambord, Jayneel Gandhi, Dibakar Gope, Thomas Grass, Anthony Gutierrez, Bagus Hanindhito, Andreas Hansson, Swapnil Haria, Austin Harris, Timothy Hayes, Adrian Herrera, Matthew Horsnell, Syed Ali Raza Jafri, Radhika Jagtap, Hanhwi Jang, Reiley Jeyapaul, Timothy M. Jones, Matthias Jung, Subash Kannoth, Hamidreza Khaleghzadeh, Yuetsu Kodama, Tushar Krishna, Tommaso Marinelli, Christian Menard, Andrea Mondelli, Miquel Moreto, Tiago Mück, Omar Naji, Krishnendra Nathella, Hoa Nguyen, Nikos Nikoleris, Lena E. Olson, Marc Orr, Binh Pham, Pablo Prieto, Trivikram Reddy, Alec Roelke, Mahyar Samani, Andreas Sandberg, Javier Setoain, Boris Shingarov, Matthew D. Sinclair, Tuan Ta, Rahul Thakur, Giacomo Travaglini, Michael Upton, Nilay Vaish, Ilias Vougioukas, William Wang, Zhengrong Wang, Norbert Wehn, Christian Weis, David A. Wood, Hongil Yoon, Éder F. Zulian. ArXiv Preprint ArXiv:2007.03152, 2021.

```

[下载 .bib 文件。](/assets/files/gem5-20.bib)

你也可以引用[最初的 gem5 论文](http://dx.doi.org/10.1145/2024716.2024718)。

```
The gem5 Simulator. Nathan Binkert, Bradford Beckmann, Gabriel Black, Steven K. Reinhardt, Ali Saidi, Arkaprava Basu, Joel Hestness, Derek R. Hower, Tushar Krishna, Somayeh Sardashti, Rathijit Sen, Korey Sewell, Muhammad Shoaib, Nilay Vaish, Mark D. Hill, and David A. Wood. May 2011, ACM SIGARCH Computer Architecture News.
```

你还应在方法论章节中说明所使用的 gem5 **版本**。
如果你没有使用某个特定的 gem5 稳定版本（例如 gem5-20.1.3），则应当注明
*如 https://github.com/gem5/gem5 所示*的提交哈希。

如果你使用了 GPU 模型、DRAM 模型或 gem5 中其他已[发表](/publications/)的模型，也建议引用相应的工作。
关于最初论文之外贡献给 gem5 的模型列表，请参见[论文发表页面](/publications/)。

### 我应该如何称呼 gem5？

"gem5" 中的 "g" *始终*小写。
如果以一个小写字母开头让你感到不适，或者你的编辑器要求首字母大写，你也可以将 gem5 称为 "The gem5 Simulator"。

### 我可以使用 gem5 徽标吗？

当然可以！
gem5 徽标由 [Nicole Hill](http://nicoledhill.com/) 创作，并以 CC0 许可放入公有领域。
你可以从以下链接下载完整尺寸的徽标：
- [垂直彩色版](/assets/img/gem5logo/Color/noBackground/vertical/gem5ColorVert.png)
- [水平彩色版](/assets/img/gem5logo/Color/noBackground/horizontal/gem5ColorLong.jpg)
- [全部徽标（svg）](/assets/img/gem5logo/gem5masterFile.svg)

使用 gem5 徽标时请遵循 [gem5 徽标样式指南](/assets/img/gem5logo/gem5styleguide.pdf)。
更多细节以及更多版本的徽标见 [gem5 文档源码](https://github.com/gem5/new-website/tree/master/assets/img/gem5logo)。

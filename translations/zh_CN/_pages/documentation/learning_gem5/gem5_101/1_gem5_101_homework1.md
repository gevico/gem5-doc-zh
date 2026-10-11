---
layout: documentation
title: "作业 1"
doc: 学习 gem5
parent: gem5_101
permalink: /documentation/learning_gem5/gem5_101/homework-1
authors:
---

# CS 752 作业 1：高级计算机体系结构（architecture）I（2015 年秋季，唯一班级）

**截止日期：9 月 14 日，星期一。**

**独立完成，不接受迟交。**

原课程联系人：Nilay Vaish，<nilay@cs.wisc.edu>。

本作业要求学习当时正在编写的 gem5 教程前几部分。原文提醒教程仍在完善，可能有笔误或缺陷，欢迎反馈大小问题，并指定向 <powerjg@cs.wisc.edu> 发送主题为 `gem5-tutorial comments` 的邮件。

> **译注**：以上及文末的联系方式和提交要求均为历史课程记录。如今有关教程的问题应按 [gem5 101 总览]({{ site.baseurl }}/documentation/learning_gem5/gem5_101/)的说明向 gem5-users 咨询。

## 第一步：完成教程第一部分

原作业写作时，教程包含四章，其中三章已完成：第一章介绍下载和构建，第二章编写简单配置并运行 gem5，第三章加入两级缓存（cache）层次，第四章介绍输出与统计信息，当时尚未完成。

各章末尾提供完整脚本，但建议逐步学习，自己编写脚本。

## 第二步：编写一个应用

实现埃拉托斯特尼筛法，最后只输出一个整数：小于等于 100,000,000 的素数数量。将程序静态编译，正确输出应为 `5761455`。

## 第三步：使用 gem5

在 gem5 中运行程序，改变 CPU 模型、频率与内存配置，并说明性能变化。

- 用筛法程序替换 `hello` 示例。**选择合适的输入规模**：既要有一定计算量，又不要让一次模拟（simulation）超过 10 分钟。作者在其机器上用 1,000,000 作为输入，约需 5 分钟；当时的实验中，下一步使用的 MinorCPU 约比 TimingSimpleCPU 慢 10 倍。
- 将 CPU 模型从 `TimingSimpleCPU` 改为 `MinorCPU`。提示：可以增加命令行选项来选择模型。
- 对两种模型，将频率从 1 GHz 调到 3 GHz，每次增加 500 MHz。也可以用命令行选项设置频率。
- 将内存从 `DDR3_1600_x64` 改为时钟更快的 `DDR3_2133_x64`，以及移动设备常用的低功耗 DRAM `LPDDR2_S4_1066_x32`。

## 提交内容

原课程要求发送邮件给 Nilay Vaish <nilay@cs.wisc.edu> 和 David Wood 教授 <david@cs.wisc.edu>，主题为 `[CS752 Homework1]`。

- 邮件中写明姓名和学号，以下文件打包为 zip 附件。
- `sieve.c`：筛法实现。
- `sieve-config.py` 及其他必要文件：运行 gem5 的配置，默认使用 1 GHz 的 `TimingSimpleCPU` 和 `DDR3_1600_x64`。**还需打印配置并带到课堂。**
- `report.pdf`：简短记录观察与结论，并回答下列问题。

报告应说明：哪种 CPU 对频率变化更敏感，为什么；哪种 CPU 对内存技术更敏感，为什么；筛法对频率还是内存更敏感，为什么；换成其他应用后，结论是否可能改变，为什么。

**星期一上课时带上纸质报告。**

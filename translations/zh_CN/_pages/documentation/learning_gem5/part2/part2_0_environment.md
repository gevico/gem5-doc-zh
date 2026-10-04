---
layout: documentation
title: Setting up your development environment
doc: 学习 gem5
parent: part2
permalink: /documentation/learning_gem5/part2/environment/
author: Jason Lowe-Power
---


搭建开发环境
=======================================

本节讨论如何开始开发 gem5。

gem5 风格指南
---------------------

修改任何开源项目时，遵循项目的风格指南都很重要。gem5 风格的细节见
gem5 的[编码风格页面](http://www.gem5.org/documentation/general_docs/development/coding_style/)。

为帮助你符合风格指南，gem5 包含一个脚本，
它会在你向 git 提交变更集时运行。第一次
构建 gem5 时，SCons 应当会自动把该脚本加入你的 .git/config 文件。请不要忽略这些警告/错误。不过，在
极少数情况下，你试图提交一个不符合
gem5 风格指南的文件（例如来自 gem5 源码
树之外的东西），可以使用 git 的 `--no-verify` 选项跳过风格
检查器。

风格指南的要点是：

-   使用 4 个空格，不要用制表符
-   对 include 排序
-   类名使用首字母大写驼峰命名法，成员
    变量和函数使用小驼峰命名法，局部变量使用蛇形命名法。
-   为代码写文档

git 分支
------------

大多数使用 gem5 进行开发的人都会用 git 的分支特性来跟踪
自己的改动。这让把你的改动提交回
gem5 变得相当简单。此外，使用分支还能在你保留自己改动的同时，
更容易用他人的新改动更新 gem5。《[Git book](https://git-scm.com/book/en/v2)》有一章
写得很好，描述了使用分支的细节，见
[这里](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)。

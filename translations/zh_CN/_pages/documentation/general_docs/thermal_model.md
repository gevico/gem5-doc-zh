---
layout: documentation
title: 功耗与热模型（power and thermal model）
doc: gem5 文档
parent: thermal_model
permalink: /documentation/general_docs/thermal_model
---

# 功耗与热模型（Power and Thermal Model）

本文档概述 Gem5 中的功耗与热建模基础设施。

其目的是给出整体图景：涉及哪些部分，以及它们之间、以及与模拟器（simulator）之间如何交互。

## 类概览

功耗模型涉及的类有：

* [PowerModel](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalResistor.html)：
表示某个硬件组件的功耗模型（power model）。
* [PowerModelState](
http://doxygen.gem5.org/release/current/classgem5_1_1PowerModelState.html)：表示
某个硬件组件在特定功耗状态下的功耗模型。它是一个
抽象类，定义了每个模型都必须实现的接口。
* [MathExprPowerModel](
http://doxygen.gem5.org/release/current/classgem5_1_1MathExprPowerModel.html)：[PowerModelState](
http://doxygen.gem5.org/release/current/classgem5_1_1PowerModelState.html) 的一个简单
实现，假定功耗可以用一个简单的表达式来建模。

热模型涉及的类有：

* [ThermalModel](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalModel.html)：
包含系统热模型的逻辑与状态。它执行功耗查询
和温度更新，同时让 gem5 可以查询温度（供操作系统
上报）。
* [ThermalDomain](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalDomain.html)：
表示一个发热实体。它本质上是一组
归在 SubSystem 组件下、具有自身热学行为的
[SimObject](http://doxygen.gem5.org/release/current/classgem5_1_1SubSystem.html)。
* [ThermalNode](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalNode.html)：
表示热学等效电路中的一个节点。该节点具有
温度，并通过连接（热阻与热容）与其他节点交互。
* [ThermalReference](
http://doxygen.gem5.org/release/current/classgem5_1_1ThermalReference.html)：热模型的
温度参考（本质上是一个温度固定的热学节点），可用于建模空气或任何其他温度恒定的
区域。
* [ThermalEntity](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalEntity.html)：
连接两个热学节点并建模两者之间热阻抗的热学组件。这个类只是一个抽象接口。
* [ThermalResistor](
http://doxygen.gem5.org/release/current/classgem5_1_1ThermalResistor.html)：实现
[ThermalEntity](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalEntity.html)，
对其连接的两个节点之间的热阻建模。热阻
建模材料传递热量的能力（单位 K/W）。
* [ThermalCapacitor](
http://doxygen.gem5.org/release/current/classgem5_1_1ThermalCapacitor.html)：实现
[ThermalEntity](http://doxygen.gem5.org/release/current/classgem5_1_1ThermalEntity.html)，
对热容建模。热容用于建模材料的热容，
即改变某种材料温度的能力（单位 J/K）。

## 热模型

热模型的工作方式是：为被模拟平台创建一个等效电路。
电路中的每个节点都有一个温度（等效于电压），
节点之间有功率流动（等效于电路中的电流）。

要构建这个等效温度模型，平台需要把
功耗参与者（任何带有功耗模型的组件）归入 SubSystem，并把 ThermalDomain 挂到这些子系统上。
还可以创建其他组件（例如 ThermalReference），并通过创建热学
实体（热容与热阻）把它们连接起来。

构建热模型的最后一步是创建 [ThermalModel](
http://doxygen.gem5.org/release/current/classgem5_1_1ThermalModel.html) 实例本身，
并把所有用到的实例都挂到它上面，以便它在运行时正确地更新它们。
目前只支持一个热模型实例，它会在适当的时候
自动上报温度（即平台传感器设备）。

## 功耗模型

每个 [ClockedObject](
http://doxygen.gem5.org/release/current/classgem5_1_1ClockedObject.html) 都关联一个功耗
模型。如果该功耗模型非空，就会在每次导出统计信息时计算功耗
（虽然也可以在其他任何时刻强制进行功耗求值，但如果功耗模型使用了统计信息，
最好让两个事件保持同步）。功耗模型的定义相当宽泛，因为它
可以像用户希望的那样灵活。到目前为止唯一强制性的约束
是：一个功耗模型有若干个功耗状态模型，对应硬件块
每种可能的功耗状态。在计算功耗
消耗时，功耗就是各个功耗模型的加权平均。

功耗状态模型本质上是一个接口，让我们可以为动态功耗和静态功耗分别定义
两个功耗函数。作为一个示例实现，我们提供了名为 [MathExprPowerModel](
http://doxygen.gem5.org/release/current/classgem5_1_1MathExprPowerModel.html) 的类。
该实现允许用户把功耗模型定义为包含若干统计信息的
方程。其中还有一些自动（或“魔法”）变量，例如 "temp"，它会上报温度。

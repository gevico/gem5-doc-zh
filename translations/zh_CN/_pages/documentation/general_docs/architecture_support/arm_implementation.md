---
layout: documentation
title: "ARM implementation"
doc: gem5 文档
parent: architecture_support
permalink: /documentation/general_docs/architecture_support/arm_implementation/
---

# ARM 实现

## 支持的特性与模式

gem5 中的 ARM 体系结构模型支持搭载多处理器扩展的 ARM® 体系结构的 [ARMv8.0-A](https://developer.arm.com/docs/den0024/latest/armv8-a-architecture-and-processors/armv8-a) 版本。
这包括所有 EL 上的 AArch32 和 AArch64 状态。这基本上意味着支持：

* [EL2：虚拟化](https://developer.arm.com/docs/100942/0100/aarch64-virtualization)
* [EL3：TrustZone®](https://developer.arm.com/ip-products/security-ip/trustzone)

基线模型符合 ARMv8.0，我们也支持一些 ARMv8.x（x > 0）的必选/可选特性

### 自 gem5 v21.2 起

要获得与 Arm 体系结构特性同步的版本，最好的方法是查看 release 对象所使用的 [ArmExtension](https://github.com/gem5/gem5/blob/develop/src/arch/arm/ArmSystem.py) 枚举，
以及同一文件中提供的各个示例 release。

用户可以选择以下选项之一：

* 使用默认 release
* 使用另一个示例 release（例如 Armv82）
* 根据可用的 ArmExtension 枚举值生成自定义 release

### gem5 v21.2 之前

要获得与 Arm 体系结构特性同步的版本，最好的方法是查看 Arm ID 寄存器和布尔值：

* [src/arch/arm/ArmISA.py](https://github.com/gem5/gem5/blob/v21.1.0.2/src/arch/arm/ArmISA.py)
* [src/arch/arm/ArmSystem.py](https://github.com/gem5/gem5/blob/v21.1.0.2/src/arch/arm/ArmSystem.py)

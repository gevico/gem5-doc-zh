# 术语表（gem5 官网中译）

适用项目与版本：gem5 官网 `gem5/website`，`stable` 分支
英文基线：`07ebfaf9bb1a0a4be2b822f3a4cf95abf20e4a4e`（2026-07-09）

渲染规则：策略为 `bilingual` 的词条，**每次出现**都写作“中文（English）”，包括标题、目录、表格与正文；
策略为 `keep-English` 的词条直接使用英文，不追加中文或括号。
代码、命令、路径、配置项、API 名、URL、`{% %}` 标签、图片路径不翻译、不加括号。

| 英文原名 | 语境/含义 | 策略 | 中文译名 | 固定展示形式 | 依据及版本 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| simulator | gem5 本体 | bilingual | 模拟器 | 模拟器（simulator） | gem5 官方中文资料通行译法 | 已确认 |
| simulation | 运行模拟的行为 | bilingual | 模拟 | 模拟（simulation） | 同上 | 已确认 |
| gem5 | 项目与工具名 | keep-English | — | gem5 | 产品名 | 已确认 |
| ISA / instruction set architecture | 指令集 | bilingual | 指令集架构 | 指令集架构（ISA） | 体系结构领域通行译法 | 已确认 |
| microarchitecture | CPU 微架构 | bilingual | 微架构 | 微架构（microarchitecture） | 同上 | 已确认 |
| architecture | 系统/计算机体系结构 | bilingual | 体系结构 | 体系结构（architecture） | 同上 | 已确认 |
| cache | 缓存 | bilingual | 缓存 | 缓存（cache） | 同上 | 已确认 |
| cache coherence | 缓存一致性 | bilingual | 缓存一致性 | 缓存一致性（cache coherence） | 同上 | 已确认 |
| out-of-order | CPU 模型 | bilingual | 乱序 | 乱序（out-of-order） | 同上 | 已确认 |
| in-order | CPU 模型 | bilingual | 顺序 | 顺序（in-order） | 同上 | 已确认 |
| full-system | 模拟模式 | bilingual | 全系统 | 全系统（full-system） | gem5 文档固定说法 | 已确认 |
| syscall emulation / SE mode | 模拟模式 | bilingual | 系统调用模拟 | 系统调用模拟（syscall emulation） | gem5 文档固定说法 | 已确认 |
| checkpoint | 模拟状态快照 | bilingual | 检查点 | 检查点（checkpoint） | 通行译法 | 已确认 |
| memory system | 包含缓存与内存的子系统 | bilingual | 内存系统 | 内存系统（memory system） | 同上 | 已确认 |
| interconnect | 片上互连 | bilingual | 互连 | 互连（interconnect） | 同上 | 已确认 |
| workload | 被模拟的程序集合 | bilingual | 工作负载 | 工作负载（workload） | 同上 | 已确认 |
| benchmark | 基准程序 | bilingual | 基准测试 | 基准测试（benchmark） | 同上 | 已确认 |
| trace | 执行轨迹 | bilingual | 跟踪 | 跟踪（trace） | 同上 | 已确认 |
| event-driven | 设计风格 | bilingual | 事件驱动 | 事件驱动（event-driven） | 同上 | 已确认 |
| power model | 功耗建模 | bilingual | 功耗模型 | 功耗模型（power model） | 同上 | 已确认 |
| clock domain | 时钟域 | bilingual | 时钟域 | 时钟域（clock domain） | 同上 | 已确认 |
| device tree | Linux 启动 | bilingual | 设备树 | 设备树（device tree） | 同上 | 已确认 |
| hypervisor | 虚拟化 | bilingual | 虚拟机管理程序 | 虚拟机管理程序（hypervisor） | 同上 | 已确认 |
| protocol | 一致性协议 | bilingual | 协议 | 协议（protocol） | 同上 | 已确认 |
| state machine | Ruby 协议实现 | bilingual | 状态机 | 状态机（state machine） | 同上 | 已确认 |
| transaction | Ruby 事务 | bilingual | 事务 | 事务（transaction） | 同上 | 已确认 |
| port | 组件接口 | bilingual | 端口 | 端口（port） | 同上 | 已确认 |
| packet | 互连传输单位 | bilingual | 数据包 | 数据包（packet） | 同上 | 已确认 |
| board | gem5 标准库封装 | bilingual | 板卡 | 板卡（board） | gem5 stdlib 语境下的项目约定 | 已确认 |
| parameter | 组件参数 | bilingual | 参数 | 参数（parameter） | 通行译法 | 已确认 |
| SimObject | gem5 基类标识符 | keep-English | — | SimObject | 代码标识符 | 已确认 |
| Ruby | gem5 内存系统名 | keep-English | — | Ruby | 产品/子系统名，不译 | 已确认 |
| Garnet | 片上网络模型 | keep-English | — | Garnet | 产品/模型名 | 已确认 |
| gem5 stdlib | 标准库 | keep-English | — | gem5 stdlib | 项目固定名称 | 已确认 |
| SCons | 构建工具 | keep-English | — | SCons | 工具名 | 已确认 |
| KVM | 虚拟化加速 | keep-English | — | KVM | 缩写，代码/配置名 | 已确认 |
| MOESI / MESI / MSI | 一致性协议名 | keep-English | — | MOESI | 协议缩写 | 已确认 |
| DVFS | 调频调压 | keep-English | — | DVFS | 缩写 | 已确认 |
| x86 / ARM / RISC-V / SPARC / MIPS / POWER / Alpha | 指令集名 | keep-English | — | RISC-V | 专有名 | 已确认 |
| SystemC | 协同仿真框架 | keep-English | — | SystemC | 框架名 | 已确认 |
| NoMali | GPU 模型 | keep-English | — | NoMali | 模型名 | 已确认 |
| SE mode / FS mode | 命令行选项 `--se` / `--fs` | keep-English | — | `--se` | 命令行选项 | 已确认 |
| Boot Camp | 社区活动名称 | keep-English | — | Boot Camp | 活动专名 | 已确认 |
| Bug report | 界面与流程用语 | bilingual | 缺陷报告 | 缺陷报告（bug report） | 通行译法 | 已确认 |
| pull request | 代码评审流程 | bilingual | 拉取请求 | 拉取请求（pull request） | 通行译法 | 已确认 |
| repository | 代码仓库 | bilingual | 仓库 | 仓库（repository） | 通行译法 | 已确认 |
| workload | 被模拟的程序 | bilingual | 工作负载 | 工作负载（workload） | 同上 | 已确认 |

## 冲突与待决事项

- `ruby`：既指 gem5 内存系统（保留英文），也指编程语言 Ruby（保留英文），两者均 `keep-English`，不存在冲突。
- `board`：在 `gem5 stdlib` 语境统一为“板卡（board）”；若后续出现“主板”“开发板”等通用语境，另行登记，不就地改写。
- `master` / `slave`：本项目中若出现，先按协议语义判断；未确认前保留英文。

## 审阅记录

- 术语表为初译阶段的项目约定，未经 gem5 项目官方确认，不得表述为官方译名。

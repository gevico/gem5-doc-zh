---
layout: documentation
title: "MOESI CMP directory"
doc: gem5 文档
parent: ruby
permalink: /documentation/general_docs/ruby/MOESI_CMP_directory/
author: Jason Lowe-Power
---

# MOESI CMP Directory

### 协议概述

  - 待补充：缓存层次结构

<!-- end list -->

  - 与 MESI 协议相比，MOESI 协议引入了一个
    额外的 **Owned（所有者）**状态。
  - MOESI 协议还包含许多 MESI 协议所不具备的
    合并（coalescing）优化。

### 相关文件

  - **src/mem/protocols**
      - **MOESI_CMP_directory-L1cache.sm**：L1 缓存控制器
        规范
      - **MOESI_CMP_directory-L2cache.sm**：L2 缓存控制器
        规范
      - **MOESI_CMP_directory-dir.sm**：目录控制器
        规范
      - **MOESI_CMP_directory-dma.sm**：dma 控制器规范
      - **MOESI_CMP_directory-msg.sm**：消息类型规范
      - **MOESI_CMP_directory.slicc**：容器文件

### L1 缓存控制器

#### **稳定状态与不变式**

| 状态      | 不变式                                                                                                                                                                                                                                                                                                                                                       |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **MM**    | 该缓存块由本节点独占持有，并且可能已被修改（类似传统的 "M" 状态）。                                                                                                                                                                                                                                            |
| **MM_W** | 该缓存块由本节点独占持有，并且可能已被修改（类似传统的 "M" 状态）。该状态下不允许替换和 DMA 访问。超时之后该块会自动转换到 MM 状态。                                                                                                              |
| **O**     | 该缓存块归本节点所有。它未被本节点修改。没有其他节点以独占模式持有该块，但可能存在共享者。                                                                                                                                                               |
| **M**     | 该缓存块以独占模式持有，但尚未写入（类似传统的 "E" 状态）。没有其他节点持有该块的副本。该状态下不允许存储。                                                                                                                                           |
| **M_W**  | 该缓存块以独占模式持有，但尚未写入（类似传统的 "E" 状态）。没有其他节点持有该块的副本。只允许加载和存储。存储时会静默升级到 MM_W 状态。该状态下不允许替换和 DMA 访问。超时之后该块会自动转换到 M 状态。 |
| **S**     | 该缓存块由 1 个或多个节点以共享状态持有。该状态下不允许存储。                                                                                                                                                                                                                                                            |
| **I**     | 该缓存块无效。                                                                                                                                                                                                                                                                                                                                                  |

#### **FSM 抽象**

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。**

![MOESI_CMP_directory_L1cache_FSM.jpg]({{ site.baseurl }}/assets/img/MOESI_CMP_directory_L1cache_FSM.jpg
"MOESI_CMP_directory_L1cache_FSM.jpg")

#### **优化**

| 状态   | 说明                                                                                                                                                                                                                              |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SM** | 已发出 GETX 以获得对即将写入该缓存块的独占权限，但该块的旧副本仍然存在。该状态下不允许存储和替换。                                     |
| **OM** | 已发出 GETX 以获得对即将写入该缓存块的独占权限，数据已经收到，但所有预期的确认尚未全部到达。该状态下不允许存储和替换。 |

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。**

![MOESI_CMP_directory_L1cache_optim_FSM.jpg]({{ site.baseurl }}/assets/img/MOESI_CMP_directory_L1cache_optim_FSM.jpg
"MOESI_CMP_directory_L1cache_optim_FSM.jpg")

### L2 缓存控制器

#### **稳定状态与不变式**

<table>
<thead>
<tr>
<th> 片内包含关系 </th>
<th> 片间排他关系 </th>
<th> 状态 </th>
<th> 说明
</th>
</tr>
</thead>
<tbody>
<tr>
<td> <b><span style="color:#808080">不在本芯片的任何 L1 或 L2 中</span></b> </td>
<td> <b>可能存在于其他芯片</b> </td>
<td> <b>NP/I</b> </td>
<td> 本芯片上的该缓存块无效。
</td></tr>
<tr>
<td rowspan="6"> <b><span style="color:#00CC99">不在 L2 中，但在本芯片的 1 个或多个 L1 中</span></b> </td>
<td rowspan="3"><b>可能存在于其他芯片</b> </td>
<td> <b>ILS</b> </td>
<td> 该缓存块不存在于本芯片的 L2 中。它由本芯片中的 L1 节点本地共享。
</td></tr>
<tr>
<td> <b>ILO</b> </td>
<td> 该缓存块不存在于本芯片的 L2 中。本芯片中的某个 L1 节点是该缓存块的所有者。
</td></tr>
<tr>
<td> <b>ILOS</b> </td>
<td> 该缓存块不存在于本芯片的 L2 中。本芯片中的某个 L1 节点是该缓存块的所有者。本芯片中还有该缓存块的 L1 共享者。
</td></tr>
<tr>
<td rowspan="3"><b>不存在于任何其他芯片</b> </td>
<td> <b>ILX</b> </td>
<td> 该缓存块不存在于本芯片的 L2 中。它由本芯片中的某个 L1 节点以独占模式持有。
</td></tr>
<tr>
<td> <b>ILOX</b> </td>
<td> 该缓存块不存在于本芯片的 L2 中。它由本芯片独占持有，并且本芯片中的某个 L1 节点是该块的所有者。
</td></tr>
<tr>
<td> <b>ILOSX</b> </td>
<td> 该缓存块不存在于本芯片的 L2 中。它由本芯片独占持有。本芯片中的某个 L1 节点是该块的所有者。本芯片中还有该缓存块的 L1 共享者。
</td></tr>
<tr>
<td rowspan="3"> <b><span style="color:#99CCFF">在 L2 中，但不在本芯片的任何 L1 中</span></b> </td>
<td rowspan="2"><b>可能存在于其他芯片</b> </td>
<td> <b>S</b> </td>
<td> 该缓存块不存在于本芯片的 L1 中。它以共享模式保存在本芯片的 L2 中，并且也可能跨芯片共享。
</td></tr>
<tr>
<td> <b>O</b> </td>
<td> 该缓存块不存在于本芯片的 L1 中。它以所有者模式保存在本芯片的 L2 中。它也可能跨芯片共享。
</td></tr>
<tr>
<td> <b>不存在于任何其他芯片</b> </td>
<td> <b>M</b> </td>
<td> 该缓存块不存在于本芯片的 L1 中。它存在于本芯片的 L2 中，并且可能已被修改。
</td></tr>
<tr>
<td rowspan="3"> <b><span style="color:#CC99FF">同时在 L2 以及本芯片的 1 个或多个 L1 中</span></b> </td>
<td rowspan="2"><b>可能存在于其他芯片</b> </td>
<td> <b>SLS</b> </td>
<td> 该缓存块以共享模式存在于本芯片的 L2 中。本芯片中该块存在本地 L1 共享者。它也可能跨芯片共享。
</td></tr>
<tr>
<td> <b>OLS</b> </td>
<td> 该缓存块以所有者模式存在于本芯片的 L2 中。本芯片中该块存在本地 L1 共享者。它也可能跨芯片共享。
</td></tr>
<tr>
<td> <b>不存在于任何其他芯片</b> </td>
<td> <b>OLSX</b> </td>
<td> 该缓存块以所有者模式存在于本芯片的 L2 中。本芯片中该块存在本地 L1 共享者。它由本芯片独占持有。
</td></tr>
</tbody>
</table>

#### **FSM 抽象**

该控制器分两部分描述。第一张图展示了所有“片内包含关系”类别之间以及类别 1、3、4 内部的转换。类别 2（不在 L2 中，但在本芯片的 1 个或多个 L1 中）内部的转换展示在第二张图中。

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。涉及其他芯片的转换用
<span style="color:#CC3300">棕色</span>标注。**

![MOESI_CMP_directory_L2cache_FSM_part_1.jpg]({{ site.baseurl }}/assets/img/MOESI_CMP_directory_L2cache_FSM_part_1.jpg
"MOESI_CMP_directory_L2cache_FSM_part_1.jpg")

下面第二张图把上图中央的六边形部分展开，展示类别 2（不在 L2 中，但在本芯片的 1 个或多个 L1 中）内部的转换。

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。涉及其他芯片的转换用
<span style="color:#CC3300">棕色</span>标注。**

![MOESI_CMP_directory_L2cache_FSM_part_2.jpg]({{ site.baseurl }}/assets/img/MOESI_CMP_directory_L2cache_FSM_part_2.jpg
"MOESI_CMP_directory_L2cache_FSM_part_2.jpg")

### 目录控制器

#### **稳定状态与
不变式**

| 状态   | 不变式                                                                                                                                                                      |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **M**  | 该缓存块仅由 1 个节点以独占状态持有（该节点也是所有者）。该块没有共享者。该数据可能与内存中的数据不同。 |
| **O**  | 该缓存块恰好由 1 个节点拥有。可能存在该块的共享者。该数据可能与内存中的数据不同。                                          |
| **S**  | 该缓存块由 1 个或多个节点以共享状态持有。没有节点拥有该块。该数据与内存中的数据一致（待核实）。                             |
| **I**  | 该缓存块无效。                                                                                                                                                     |

#### **FSM 抽象**

**控制器 FSM 图中使用的记法描述见
[此处](#Coherence_controller_FSM_Diagrams "wikilink")。**

![MOESI_CMP_directory_dir_FSM.jpg]({{ site.baseurl }}/assets/img/MOESI_CMP_directory_dir_FSM.jpg
"MOESI_CMP_directory_dir_FSM.jpg")

### 其他特性

#### **超时**：

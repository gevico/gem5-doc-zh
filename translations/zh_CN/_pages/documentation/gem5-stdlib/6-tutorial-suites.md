---
layout: documentation
title: Suites in gem5
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/suites
author: Kunal Pai, Harshil Patel
---

## 简介

Suite 是 gem5 23.1 版本引入的一类新资源，它允许用户把工作负载（workload）分组。
资源特化（resource specialization）中新增了 SuiteResource 类。
gem5 resources 中预先做好的 suite 可以像其他所有资源一样用 `obtain_resource()` 获取。

SuiteResource 类具有 `__iter__` 和 `__len__` 函数。
SuiteResource 会像迭代器一样工作，返回工作负载对象的生成器。

### 如何获取一个 Suite

要获取 gem5 resources 中已有的 suite，我们可以使用 `[resource.py](http://resource.py)` 中的 `obtain_resource` 函数。

获取 ID 为 “riscv-vertical-microbenchmarks”、版本为 “1.0.0” 的 suite：

```python
suite_obj = obtain_resource(id = "riscv-vertical-microbenchmarks", resource_version="1.0.0")
```

不指定 resource_version 会返回该资源最新的兼容版本。

**注意**：本教程其余部分所用的 Suite 是 “riscv-vertical-microbenchmarks”，它存在于 gem5 resources 中，但只与 gem5 23.1 及更高版本、且只与 RISC-V 指令集架构兼容。

### 如何按输入组筛选 Suite 中的工作负载

每个 suite 都有一个 workloads 字段，它是一个数组，包含该 suite 中所有工作负载的 ID、版本和输入组。

workloads 字段看起来如下：

```python
[
	{
		'id': 'riscv-cca-run',
		'resource_version': '1.0.0',
		'input_group': ['cca']
	},
	{
		'id': 'riscv-cce-run',
		'resource_version': '1.0.0',
		'input_group': ['cce']
	},
	{
		'id': 'riscv-ccm-run',
		'resource_version': '1.0.0',
		'input_group': ['ccm']
	},
	...
]
```

SuiteResource 类提供了让用户按输入组筛选工作负载的函数。
函数 `get_input_groups()` 返回该 suite 中存在的所有输入组的集合。
函数 `with_input_group(str)` 返回一个 SuiteResource 对象，其中只包含具有所传入输入组的工作负载。
例如，如果我们的 suite 的 workloads 字段如上定义，那么 `get_input_groups()` 将返回：

```python
set(['cca','cce','ccm',...])
```

我们可以这样使用 `with_input_group()`：

```python
suite_obj = obtain_resource('riscv-vertical-microbenchmarks')
filtered_suite = suite_obj.with_input_group('cca')
```

这会返回一个 `SuiteResource`，其中包含所有满足具有输入组 “cca” 这一条件的工作负载；在本例中就是 ID 为 “riscv-cca-run” 的 `WorkloadResource`。

我们也可以把 `with_input_group()` 函数与 for 循环和生成器一起使用。

```python
for workload in suite_obj.with_input_group('cca')
	board.set_workload(workload)
	simulator = Simulator(board=board)
	simulator.run()
```

### 制作自定义 Suite

也可以直接使用 `[resource.py](http://resource.py)` 中的 `SuiteResource` 类来制作自定义 suite。
要创建自定义 suite，我们还需要 `WorkloadResource` 对象。

```python
workload1= obtain_resource('workload-1', resource_version='1.0.0')
workload2= obtain_resource('workload-2', resource_version='1.0.0')

suite_obj = SuiteResource(workloads=[workload1, workload2])
```

上面的代码片段会创建一个包含两个工作负载的 suite 对象。
由于我们在上面的 suite 中没有定义 `workloads` 字段，`get_input_group()` 和 `with_input_group()` 函数会分别抛出警告并返回空集合和没有工作负载的 suite 对象。

如果加入 `workloads` 字段，该自定义 suite 的行为就会与用 `obtain_resource` 创建的 suite 相同。

```python
workload1= obtain_resource('workload-1', resource_version='1.0.0')
workload2= obtain_resource('workload-2', resource_version='1.0.0')
workloads = [
	{
		'id': 'workload-1',
		'resource_version': '1.0.0',
		'input_group': ['input_group_1', 'input_group_2']
	},
	{
		'id': 'workload-2',
		'resource_version': '1.0.0',
		'input_group': ['input_group_1', 'input_group_3']
	}]
suite_obj = SuiteResource(workloads=[workload1, workload2], worklaods= workloads)
```

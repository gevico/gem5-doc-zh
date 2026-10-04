---
layout: documentation
title: Local Resources Support in gem5
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/local-resources-support
author: Kunal Pai, Harshil Patel
---

本教程将带你走一遍在 gem5 中创建 WorkloadResource 并测试它的流程，所用的是 gem5 v23.0 引入的新 gem5 Resources 基础设施。

在 gem5 中，工作负载通过下面这一行设置到板卡上：

``` python
board.set_workload(obtain_resource(<ID_OF_WORKLOAD>))
```

下图展示了在 [gem5 Resources 网站](https://resources.gem5.org/)上看到的 Resource ID 是什么：
![gem5 resource ID 示例](/assets/img/stdlib/gem5-resource-id-example.png)

因此，ID 为 '<ID_OF_WORKLOAD>' 的 WorkloadResource 会被解析，并用于构造它定义的函数调用。

Workload JSON 的 `"function"` 字段中指定的函数调用随后会在板卡上执行，并带上它在 `"additional_parameters"` 字段中定义的任何参数。

## 简介

gem5 Resources 基础设施允许添加本地 JSON 数据源，它可以被加入主要的 gem5 Resources MongoDB 数据库。

我们将使用本地 JSON 数据源向 gem5 添加一个新的 WorkloadResource。

## 前置条件

本教程假定你已经有一个预编译好的 Resource，并希望把它做成 WorkloadResource。

## 定义工作负载

### 定义 Resource JSON

第一步是定义 WorkloadResource 中所使用的 Resource。
如果该 Resource 已存在于 gem5 中，可以跳过这一步。
假设我们要包装进 WorkloadResource 的 Resource 是为 `RISC-V` 编译的，类别为 `binary`，名称为 `my-benchmark`。

我们可以在 JSON 对象中如下定义该 Resource：

``` json
{
    "category": "binary",
    "id": "my-benchmark",
    "description": "A RISCV binary used to test a specific RISCV instruction.",
    "architecture": "RISCV",
    "is_zipped": false,
    "resource_version": "1.0.0",
    "gem5_versions": [
        "23.0"
    ],
}
```

在这里正确初始化所有字段很重要，因为 gem5 会用它们来初始化和运行该 Resource。

关于 Resource 必需与非必需的字段的更多信息，见 [gem5 Resources JSON Schema](https://github.com/gem5/gem5-resources-website/blob/main/public/gem5-resources-schema.json)。

### 定义 Workload JSON

假设该 Resource 的二进制程序已上传到 gem5 Resources 云，其源代码可在 [gem5-resources GitHub 仓库](https://github.com/gem5/gem5-resources/)获取，并且该 Resource 可在 [gem5 Resources 网站](https://resources.gem5.org)上查看，你现在就可以定义 Workload JSON 了。
假设我们正在构建的 WorkloadResource 包装 `my-benchmark`，并称为 `binary-workload`。

我们可以在本地 JSON 文件中如下定义该 WorkloadResource：

``` json
{
    "id": "binary-workload",
    "category": "workload",
    "description": "A RISCV binary used to test a specific RISCV instruction.",
    "architecture": "RISCV",
    "function": "set_se_binary_workload",
    "resource_version": "1.0.0",
    "gem5_versions": [
        "23.0"
    ],
    "resources": {
        "binary": "my-benchmark"
    },
    "additional_parameters": {
        "arguments": ["arg1", "arg2"]
    }
}
```

`"function"` 字段定义将在板卡上被调用的函数。
`"resources"` 字段定义将传入该 Workload 的 Resource。
`"additional_parameters"` 字段定义将传入该 WorkloadResource 的额外参数。
因此，上面定义的 WorkloadResource 等价于以下这行代码：

``` python
board.set_se_binary_workload(binary = obtain_resource("binary_resource"), arguments = ["arg1", "arg2"])
```

关于 workload 必需与非必需的字段的更多信息，见 [gem5 Resources JSON Schema](https://github.com/gem5/gem5-resources-website/blob/main/public/gem5-resources-schema.json)

## 测试工作负载

要测试该 WorkloadResource，我们首先必须把本地 JSON 文件添加为 gem5 的数据源。

这可以通过创建一个格式如下的新 JSON 文件来完成：

``` json
{
    "sources": {
        "my-resources": {
            "url": "<PATH_TO_JSON_FILE>",
            "isMongo": false,
        }
    }
}
```
运行 gem5 时，如果你创建的新的 JSON 配置文件存在于当前工作目录中，它就会被用作 gem5 的数据源。
如果该 JSON 文件不在当前工作目录中，你可以在构建 gem5 时用 `GEM5_CONFIG` 标志指定该 JSON 文件的路径。

现在你应该能通过名称 `binary-workload` 在模拟中使用该 WorkloadResource 了。

**注意**：要检查你在 WorkloadResource 中指定的 Resource 是否被正确传入该 WorkloadResource，可以使用 WorkloadResource 类中的 `get_parameters()` 函数。
该函数返回传入该 WorkloadResource 的 Resource 字典。
其实现见 [`src/python/gem5/resources/resource.py`](https://github.com/gem5/gem5/blob/6f5d877b1aacd551749dafa87da26600a4f01155/src/python/gem5/resources/resource.py#L673)。

自 gem5 v23.1 起，还有几种额外方式可以定义你的本地 `resources.json` 文件。
这两种方式都通过环境变量实现，并在运行 gem5 模拟时通过命令行定义。

1. `GEM5_RESOURCE_JSON` 变量：该变量会把 gem5 当前使用的所有数据源替换为该变量所传路径上的 JSON 文件。
这等价于如下的 gem5 数据源配置文件：

    ``` json
    {
        "sources": {
            "my-resources": {
                "url": $GEM5_RESOURCE_JSON,
                "isMongo": false,
            }
        }
    }
    ```

2. `GEM5_RESOURCE_JSON_APPEND` 变量：该变量会把该变量所传路径上的 JSON 文件加入 gem5 当前使用的所有数据源中。
这等价于如下的 gem5 数据源配置文件：

    ``` json
    {
        "sources": {
            "my-resources-1": {
                "url": '/local/local.json',
                "isMongo": false,
            },
                    "my-resources-2": {
                "url": $GEM5_RESOURCE_JSON_APPEND,
                "isMongo": false,
            },
        }
    }
    ```

## 支持资源的本地路径

自 gem5 v23.1 起，新增了通过上述方式使用本地资源构造工作负载的支持。

该方法使用与[定义 Resource JSON](#defining-the-resource-json)中相同的 JSON 对象，只是额外加上 "url" 字段。
该字段在 gem5 Resources 数据库中用于指出某个 Resource 的文件位于何处。
自 gem5 v23.1 起，该字段也接受 _file_ URI 方案。
你可以指定本地主机上的路径，gem5 就能运行它。

有了这些改动，`my-benchmark` 本地实例的 JSON 对象将如下所示：

``` json
{
    "category": "binary",
    "id": "my-benchmark",
    "description": "A RISCV binary used to test a specific RISCV instruction.",
		"url": "file:/<PATH_TO_LOCAL_FILE>",
    "architecture": "RISCV",
    "is_zipped": false,
    "resource_version": "1.1.0",
    "gem5_versions": [
        "23.0"
    ],
}
```

**注意**：如果你要创建的本地 Resource 版本其 ID 已存在于 gem5 Resources 中，请务必把 `"resource_version"` 字段改为 gem5 Resources 数据库中不存在的资源版本，以免在运行 gem5 模拟时收到错误。

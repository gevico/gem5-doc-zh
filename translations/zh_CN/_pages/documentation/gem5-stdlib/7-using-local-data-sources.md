---
layout: documentation
title: Setting gem5 Resources data sources to support local resources
parent: gem5-standard-library
doc: gem5 文档
permalink: /documentation/gem5-stdlib/using-local-resources
author: Harshil Patel
---

gem5 支持使用 MongoDB Atlas 与 JSON 数据源形式的本地数据源。gem5 在 `src/python/gem5_default_config.py` 中有一个默认的 resources 配置。该 resources 配置指向 gem5 resources 的 MongoDB Atlas 集合。要使用 gem5 resources 主数据库之外的数据源，你需要覆盖 gem5-resources-config。

有几种方式可以更新 gem5 resources 配置：

1. **设置 GEM5_CONFIG 环境变量：** 你可以设置 GEM5_CONFIG 环境变量来指定新的配置文件。这样做会用你指定的配置替换默认的 resources 配置。

2. **使用 gem5-config.json：** 如果当前工作目录中存在名为 gem5-config.json 的文件，它会优先于默认的 resources 配置。

3. **回退到默认 resources 配置：** 如果上述两种方式都未使用，系统将改为使用默认的 resources 配置。

此外，如果你希望使用或向当前所选配置（如上文方式所述）加入本地资源 JSON 文件，还有两种额外方式可用：

- **GEM5_RESOURCE_JSON 环境变量：** 该变量可用于覆盖当前 resources 配置并使用指定的 JSON 文件。

- **GEM5_RESOURCE_JSON_APPEND 环境变量：** 用该变量把一个 JSON 文件加入现有 resources 配置，而不替换它。

必须注意的是，覆盖或追加并不会修改实际配置文件本身。这些方式让你能在运行时临时指定或添加资源而无需改动原始配置文件。

MongoDB Atlas 配置格式：

```json
{
    "sources":{
        "example-atlas-config": {
            "dataSource": "datasource name",
            "database": "database name",
            "collection": "collection name",
            "url": "Atlas data API URL",
            "authUrl": "Atlas authentication URL",
            "apiKey": "API key for data API for MongoDB Atlas",
            "isMongo": true
        }
    }
}
```

JSON 配置格式：

```json
{
    "sources":{
        "example-json-config": {
            "url": "local path to JSON file or URL to a JSON file",
            "isMongo": false
        }
    }
}
```

### 搭建 MongoDB Atlas 数据库

你需要搭建一个 Atlas 集群，相关步骤见：
- https://www.mongodb.com/basics/mongodb-atlas-tutorial

你还需要启用 Atlas dataAPI，相关步骤见：
- https://www.mongodb.com/docs/atlas/app-services/data-api/generated-endpoints/

### 使用多个数据源

gem5 支持使用多个数据源。资源配置的结构如下：

```json
{
    "sources": {
         "gem5-resources": {
            "dataSource": "gem5-vision",
            "database": "gem5-vision",
            "collection": "resources",
            "url": "https://data.mongodb-api.com/app/data-ejhjf/endpoint/data/v1",
            "authUrl": "https://realm.mongodb.com/api/client/v2.0/app/data-ejhjf/auth/providers/api-key/login",
            "apiKey": "OIi5bAP7xxIGK782t8ZoiD2BkBGEzMdX3upChf9zdCxHSnMoiTnjI22Yw5kOSgy9",
            "isMongo": true,
        },
        "data-source-json-1": {
            "url": "path/to/json",
            "isMongo": false,
        },
        "data-source-json-2": {
            "url": "path/to/another/json",
            "isMongo": false,
        },
        // Add more data sources as needed
    }
}
```

上面的示例展示了一个包含 MongoDB Atlas 数据源和 2 个 JSON 数据源的 gem5 resources 配置。默认情况下，gem5 会取所有指定数据源中存在的所有资源的并集。如果你请求获取某个资源，而多个数据源中具有相同 `id` 和 `resource_version` 的资源，则会抛出错误。你也可以指定要从哪些数据源子集中获取资源：

```python
resource = obtain_resource("id", clients=["data-source-json-1"])
```

### 了解本地资源

在 gem5 的语境中，本地资源指用户拥有、并希望集成到 gem5 中、但尚未存在于 gem5 resources 数据库中的资源。

对用户而言，这提供了在 gem5 中无缝使用自己资源的灵活性，无需用 `BinaryResource(local_path=/path/to/binary)` 创建专门的资源对象。相反，他们可以直接通过 `obtain_resource()` 使用这些本地资源，从而简化集成流程。

### 使用自定义资源配置与本地资源

在本示例中，我们将介绍如何设置自定义配置并使用你自己的本地资源。为便于说明，我们将使用 JSON 文件作为资源数据源。

#### 创建自定义资源数据源

我们先创建一个本地资源。这是一个用作示例的最简资源。要配合 `obtain_resource()` 使用本地资源，我们的最简资源需要有一个二进制文件。这里我们使用名为 `fake-binary` 的空二进制程序。

**注意**：请确保 Gem5 二进制程序与 `fake-binary` 具有相同的指令集架构目标（此处是 RISCV）。

接下来创建 JSON 数据源。我把该文件命名为 `my-resources.json`。内容应如下所示：

```json
[
    {
        "category": "binary",
        "id": "test-binary",
        "description": "A test binary",
        "architecture": "RISCV",
        "size": 1,
        "tags": [
            "test"
        ],
        "is_zipped": false,
        "md5sum": "6d9494d22b90d817e826b0d762fda973",
        "source": "src/simple",
        "url": "file:// path to fake_binary",
        "license": "",
        "author": [],
        "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/simple",
        "resource_version": "1.0.0",
        "gem5_versions": [
            "23.0"
        ],
        "example_usage": "obtain_resource(resource_id=\"test-binary\")"
    }
]
```

资源的 JSON 文件应符合 [gem5 resources schema](https://resources.gem5.org/gem5-resources-schema.json)。

**注意**：虽然 `url` 字段可以是一个链接，但在本例中我使用的是本地文件。

#### 创建你的自定义资源配置

创建名为 `gem5-config.json` 的文件，内容如下：

```json
{
    "sources": {
        "my-json-data-source": {
            "url": "path/to/my-resources.json",
            "isMongo": false
        }
    }
}
```

**注意**：此处隐含 isMongo = false 表示该数据源是 JSON 数据源，因为 gem5 目前只支持 2 种数据源。

#### 用本地数据源运行 gem5

首先，用包含 RISCV 的 ALL 构建来构建 gem5：

```bash
scons build/ALL/gem5.opt -j`nproc`
```

接下来，使用我们本地的 `test-binary` 资源运行 `local-resource-example.py` 文件：

使用环境变量

```bash
GEM5_RESOURCE_JSON_APPEND=path/to/my-resources.json ./build/ALL/gem5.opt configs/example/gem5_library/local-resource-example.py --resource test-binary
```

或者你可以用自己自定义的配置覆盖 `gem5_default_config`：

```bash
GEM5_CONFIG=path/to/gem5-config.json ./build/ALL/gem5.opt configs/example/gem5_library/local-resource-example.py --resource test-binary
```

该命令会使用我们本地下载的资源执行 `local-resource-example.py` 脚本。该脚本只是调用 obtain_resource 函数并打印该资源的本地路径。该脚本表明，本地资源的运作方式与 gem5 resources 数据库上的资源类似。

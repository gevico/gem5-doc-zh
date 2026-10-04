---
layout: documentation
title: gem5-resources
doc: gem5 文档
parent: gem5_resources
permalink: /documentation/general_docs/gem5_resources/
authors: Bobby R. Bruce, Kunal Pai, Parth Shah
---

# gem5 Resources

gem5 Resources 是一个仓库，提供已知且经验证与 gem5 体系结构模拟器（simulator）兼容的制品（artifact）源码。这些资源对于编译或运行 gem5 并非必需，但可能有助于用户完成某些模拟（simulation）。

## 为什么需要 gem5 Resources？

gem5 在设计时注重灵活性。用户可以模拟各种各样的硬件，以及同样种类繁多的工作负载（workload）。不过，要求用户自行寻找并配置 gem5 所需的工作负载（自己的磁盘镜像、自己的操作系统启动、自己的测试等）是一项巨大的投入，对许多人来说也是一道门槛。

因此，gem5 Resources 的目的就是__提供一组稳定的常用资源，并保证其与 gem5 的兼容性经过验证并有文档记载__。除此之外，gem5 resources 还通过提供可引用、稳定、与特定 gem5 发布版本绑定的资源，强调__实验的可复现性__。

## 我在哪里可以获取 gem5 Resources？

要在 gem5 Resources 中查找特定资源，我们建议使用 [gem5 Resources 网站](https://resources.gem5.org)。关于该网站上搜索、筛选与排序如何工作的详细信息见此[帮助页面](https://resources.gem5.org/help)。

gem5 Resources 托管在我们的 Google Cloud Bucket 上。资源链接见
[gem5 resources README.md 文件](
https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/README.md)。
资源元数据存储在托管于 MongoDB Atlas 的 MongoDB 数据库中。
要请求更新 gem5 resources，请创建 issue 或发送邮件到 gem5-dev。

## 在 gem5 中使用 gem5 Resources 网站上的资源

当你在 gem5 Resources 网站上找到想在自己模拟中使用的资源后，请进入该资源的 'Usage' 标签页。

本教程假定你要找的资源是 `riscv-hello`，见[此处](https://resources.gem5.org/resources/riscv-hello)。在该资源的 ['Usage'](https://resources.gem5.org/resources/riscv-hello/usage) 标签页中，你会找到可以粘贴到 gem5 模拟中、用于使用该资源的代码。

在本例中，代码是 `obtain_resource(resource_id="riscv-hello")`。

要使用 `obtain_resource` 函数，你需要以下 import 语句：

```
from gem5.resources.resource import obtain_resource
```

`obtain_resource` 函数接受以下参数：

- `resource_id`：你想使用的资源的 ID。
- `resource_version`：可选参数，指定你想使用的资源版本。如果未指定，将使用与当前所用 gem5 版本兼容的最新资源版本。
- `clients`：可选参数，指定 gem5 在其中搜索该资源的客户端列表。如果未指定，gem5 将在 `src/python/gem5_default_config.py` 文件中指定的所有客户端中搜索该资源。默认情况下，gem5 使用公开的 MongoDB 元数据数据库来查找资源。可以通过覆盖该设置来指定你自己的本地资源元数据。

## 在 gem5 中使用 gem5 Resources 网站上的工作负载

当你在 gem5 Resources 网站上找到想在自己模拟中使用的工作负载（workload）后，请进入该工作负载的 'Usage' 标签页。

本教程假定你要找的工作负载是 `riscv-ubuntu-20.04-boot`，见[此处](https://resources.gem5.org/resources/riscv-ubuntu-20.04-boot)。在该工作负载的 ['Usage'](https://resources.gem5.org/resources/riscv-ubuntu-20.04-boot/usage) 标签页中，你会找到可以粘贴到 gem5 模拟中、用于使用该工作负载的代码。

在本例中，代码是 `Workload("riscv-ubuntu-20.04-boot")`。

要使用 `Workload` 类，你需要以下 import 语句：

```
from gem5.resources.workload import Workload
```

`Workload` 类接受以下参数：

- `workload_name`：你想使用的工作负载的名称。
- `resource_directory`：可选参数，指定资源应从何处下载和访问。
- `resource_version`：可选参数，指定应使用的资源版本。如果未指定，将使用与当前所用 gem5 版本兼容的最新资源版本。
- `clients`：可选参数，指定 gem5 在其中搜索该资源的客户端列表。如果未指定，gem5 将在 `src/python/gem5_default_config.py` 文件中指定的所有客户端中搜索该资源。

## 在 gem5 中使用自定义资源

要在 gem5 中使用自定义资源，我们建议使用 gem5 支持的某种数据源格式。目前我们支持 MongoDB Atlas、本地 JSON 文件和远程 JSON 文件。

你可以通过在运行文件时覆盖 `GEM5_DEFAULT_CONFIG` 变量来使用自己的配置文件。

注意：你添加的任何自定义资源都必须符合 [gem5 Resources Schema](https://resources.gem5.org/gem5-resources-schema.json)。

`utils/gem5-resources-manager` 中有一个实用工具，提供用于更新和创建资源的图形界面，既可用于公开资源（只有 gem5 管理员可以修改），也可用于本地资源元数据。
关于 gem5 Resources Manager 的更多信息可在其 README 文件中找到。

## 如何获取 gem5 Resource 的源码？

gem5 resources 的源码可以从
<https://github.com/gem5/gem5-resources> 获取：

```bash
git clone https://github.com/gem5/gem5-resources
```

`stable` 分支的 HEAD 会指向一组与最新 gem5 发布版本兼容的资源源码
（最新发布版本可通过
`git clone https://github.com/gem5/gem5.git` 获取）。

关于编译各个 gem5 资源的信息，请查阅 [README.md](
https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/README.md)
文件。在许可允许的情况下，[README.md](
https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/README.md)
文件会提供从我们的
dist.gem5.org Google Cloud Bucket 下载已编译资源的链接。

## gem5 Resources 仓库是如何组织的？

该仓库的结构如下：

* **README.md** ：该 README 会概述每个资源、它们的来源、
为了让它们在 gem5 上运行做了哪些修改（如适用）、相关
许可信息以及编译说明。对于想使用某个 gem5 资源的人来说，这应该是第一个查阅的地方。
* **src** ：资源源码。gem5 resources 就在这个
目录中。每个子目录对应一个资源。每个资源都包含自己的 README.md 文件，记录相关信息 —— 编译
说明、使用注意事项等。
* **CHANGELOG.md** ：该 CHANGELOG 会概述某个资源在各版本之间的变化。

### 版本管理

每个资源可以有多个版本。版本形式为
`<major>.<minor>.<patch>`。该版本管理方案基于[语义化
版本（Semantic Versioning）](https://semver.org/)。每个资源版本都关联到一个
或多个 gem5 版本（例如 v20.0、v20.1、v20.2 等）。

默认情况下，gem5 使用与当前所用 gem5 版本兼容的最新资源版本。
不过，用户可以指定要使用的特定资源版本。
如果用户指定的资源版本与当前所用 gem5 版本不兼容，gem5 会发出警告。
你仍可自行承担风险使用该资源。

### 引用资源

我们强烈建议在论文中引用 gem5 Resources，以便实验、教程等的复现。

以 URL 形式引用时，请使用以下格式：

```
# For the git repository at a particular revision:
https://github.com/gem5/gem5-resources/<revision>/src/<resource>

# For the git repository at a particular tag:
https://github.com/gem5/gem5-resources/tree/<branch>/src/<resource>
```

或者，以 BibTex 形式：

```
@misc{gem5-resources,
  title = {gem5 Resources. Resource: <resource>},
  howpublished = {\url{https://github.com/gem5/gem5-resources/<revision>/src/<resource>}},
  note = {Git repository at revision '<revision>'}
}

@misc{gem5-resources,
  title = {gem5 Resources. Resource: <resource>},
  howpublished = {\url{https://github.com/gem5/gem5-resources/tree/<branch>/src/<resource>}},
  note = {Git repository at tag '<tag>'}
}
```

## 如何为 gem5 Resources 做贡献？

对 gem5 Resources 仓库的改动通过我们的
Gerrit 代码评审系统提交到 develop 分支。因此，要做改动，请先克隆该
仓库：

```
git clone https://github.com/gem5/gem5-resources.git
```

然后进行修改并提交。准备好后，用以下命令推送到 Gerrit：

```
git push origin HEAD:refs/for/stable
```

这会把资源添加到最新 gem5 发布版本所使用的内容中。

要把资源贡献到下一个 gem5 发布版本，

```
git clone https://github.com/gem5/gem5-resources.git
git checkout --track origin/develop
```

然后进行修改、提交，并用以下命令推送：

```
git push origin HEAD:refs/for/develop
```

提交信息的标题不应超过 65 个字符，并以标签
`resources:` 开头。标题之后的描述不得超过 72 个字符。

例如：

```
resources: Adding a new resources X

This is where the description of this commit will occur taking into
note the 72 character line limit.
```

我们强烈建议贡献者在可能且合适的情况下遵循我们的[风格指南]({{ site.baseurl }}/documentation/general_docs/development/coding_style/)。

随后任何改动都会通过我们的 [Gerrit 代码评审系统](
https://gem5-review.googlesource.com)进行评审。一旦完全通过并被合并到
gem5 resources 仓库，请通过邮件联系 Bobby R. Bruce
（[bbruce@ucdavis.edu](mailto:bbruce@ucdavis.edu)），以便把已编译的源码
上传到 gem5 resources bucket。

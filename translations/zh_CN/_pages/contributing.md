---
layout: page
title: 贡献指南
permalink: contributing
author: Bobby R. Bruce
---

本文档是向 gem5 贡献代码的指南。
以下小节按顺序说明了向 gem5 项目做贡献所涉及的步骤。

## 确定你可以贡献什么

了解自己能为 gem5 做些什么，最简单的方法是查看我们的 GitHub
issue 跟踪器：<https://github.com/gem5/gem5/issues>。

浏览这些未关闭的 issue，看看是否有你能处理的。
当你找到一项乐意承担的任务时，先确认没有其他人正在负责，然后留言询问是否可以把它指派给自己。
虽然这不是必须的，但建议首次贡献者这样做，这样更熟悉该任务的开发者可以就如何最好地实现所需修改给出建议。

一旦有开发者回复你的留言并提供了建议，你就可以
正式把该任务指派给自己。这有助于 gem5 开发
社区了解项目当前有哪些部分正在推进。

**如果你因任何原因不再继续某项任务，请把自己从该任务上取消指派。**

## 获取 git 仓库

gem5 的 git 仓库托管在 <https://github.com/gem5/gem5>。
**重要提示：向其他 gem5 仓库提交的贡献不会被考虑。请只向 <https://github.com/gem5/gem5> 贡献。**

拉取 gem5 的 git 仓库：

```sh
git clone https://github.com/gem5/gem5
```

如果你只是想使用 gem5、并不打算贡献代码，这没有问题。不过，要
贡献代码，我们使用 [GitHub Pull-Request 模式](https://docs.github.com/en/pull-requests)，因此建议在贡献前先[复刻（fork）gem5 仓库](https://docs.github.com/en/get-started/quickstart/fork-a-repo)。

### 复刻（fork）

请参考 [GitHub 关于复刻 GitHub 仓库的文档](https://docs.github.com/en/get-started/quickstart/fork-a-repo)。由于我们将在 `develop` 分支上工作，务必复刻仓库的所有分支，而不只是 `stable` 分支。为此，在创建新的复刻时，不要勾选 "Copy the stable branch only" 选项，以确保你的复刻包含仓库的所有分支。

这会在你自己的 GitHub 账号下创建 gem5 仓库的复刻版本。
随后你可以在本地获取它：

```sh
git clone https://github.com/{your github account}/gem5
```

如果你只复刻了 `stable` 分支，运行以下两条命令以同时获取其他分支：

```sh
git remote add gem5 https://github.com/gem5/gem5.git
git fetch gem5
```

### stable 与 develop 分支

克隆后，git 仓库默认检出 `stable` 分支。`stable`
分支是 gem5 的稳定发布分支，也就是说，该分支的 HEAD
包含 gem5 最新的稳定发布版本。（在 `stable` 分支上执行 `git tag`
可以查看稳定发布版本列表。通过执行 `git checkout <release>`
可以检出某个特定发布版本。）由于 `stable`
分支只包含正式发布的 gem5 代码，**贡献者不应
在 `stable` 分支之上开发改动**，而应
**在 `develop` 分支之上开发改动**。

切换到 `develop` 分支：

```sh
git switch develop
```

`develop` 分支会在 gem5 发布时合并到 `stable` 分支。
因此，你所做的任何改动都会存在于 develop 分支上，直到下一次发布。

我们强烈建议创建自己的本地分支来进行改动。
如果不直接修改 `develop` 和 `stable`，开发流程的运作效果最好。
这有助于让你的改动在复刻仓库的不同分支之间保持条理。
下面的示例会基于 `develop` 创建一个名为 `new-feature` 的新分支：

```sh
git switch -c new-feature
```

## 进行修改

### C/CPP

不同任务需要以不同方式修改项目。
不过无论如何，都必须遵守我们的风格指南。完整的 C/C++ 风格
指南见[此处](/documentation/general_docs/development/coding_style)。

概括来说：

* 每行不得超过 79 个字符。
* 任何一行都不应有行尾空白。
* 缩进必须是 4 个空格（不能用制表符）。
* 类名必须使用大驼峰命名法（例如 `ThisIsAClass`）。
* 类的成员变量必须使用小驼峰命名法（例如
`thisIsAMemberVariable`）。
* 带有自身公有访问器的类成员变量必须以
下划线开头（例如 `_variableWithAccessor`）。
* 局部变量必须使用蛇形命名法（例如 `this_is_a_local_variable`）。
* 函数必须使用小驼峰命名法（例如 `thisIsAFunction`）
* 函数参数必须使用蛇形命名法。
* 宏必须全部大写并用下划线连接（例如 `THIS_IS_A_MACRO`）。
* 函数声明的返回类型必须单独占一行。
* 函数的括号必须单独占一行。
* `for`/`if`/`while` 分支语句的条件前必须有
一个空格（例如 `for (...)`）。
* `for`/`if`/`while` 分支语句的左括号必须与语句
同行，右括号单独占一行（例如
`for (...) {\n ... \n}\n`）。条件与左括号之间应有一个空格。
* C++ 的访问修饰符必须缩进两个空格，其中定义的方法/变量再缩进四个空格。

下面是一个简单的示例，展示类应当如何排版：

```C++
#DEFINE EXAMPLE_MACRO 7
class ExampleClass
{
  private:
    int _fooBar;
    int barFoo;

  public:
    int
    getFooBar()
    {
        return _fooBar;
    }

    int
    aFunction(int parameter_one, int parameter_two)
    {
        int local_variable = 0;
        if (true) {
            int local_variable = parameter_one + parameter_two + barFoo
                               + EXAMPLE_MACRO;
        }
        return local_variable;
    }

}
```

### Python

我们使用 [Python Black](https://github.com/psf/black) 把 Python 代码
格式化为正确的风格。安装方式：

```sh
pip install black
```

然后对修改过/新增的 python 文件运行：

```sh
black <files/directories>
```

关于变量/方法等的命名约定，请遵循 [PEP 8 命名
约定建议](
https://peps.python.org/pep-0008/#naming-conventions)。虽然我们尽力
在整个 gem5 项目中落实命名约定，但也知道存在
不满足约定的地方。在这些情况下，请**遵循你正在修改的代码
所用的约定**。

### 使用 pre-commit

为了帮助落实风格指南，我们使用 [pre-commit](
https://pre-commit.com)。pre-commit 是一个 git 钩子，因此必须
由 gem5 开发者显式安装。

要安装 gem5 的 pre-commit 检查，请在 gem5
目录中执行：

```sh
pip install pre-commit
pre-commit install
```

安装后，pre-commit 会在运行 `git commit` 命令之前
对修改过的代码执行检查（关于提交改动的更多细节，见
[我们关于提交的章节](#committing)）。如果这些测试失败，你将无法
提交。

同样的 pre-commit 检查也会作为 CI 检查的一部分运行（这些检查
必须通过，改动才能合并到 develop 分支）。因此
强烈建议开发者安装 pre-commit，以便尽早发现
风格错误。

## 编译并运行测试

提交改动的最低标准是代码
可以编译，并且测试用例通过。

下面的命令既编译项目，也运行我们的 "quick"
系统级检查：

```sh
cd tests
./main.py run
```

**注意：这些测试的构建与执行可能需要数小时。`main.py` 可以
用 `-j` 选项在多个线程上运行。例如：`python main.py run
-j6`。**

单元测试也应当通过。运行单元测试：

```sh
scons build/ALL/unittests.opt
```

编译单个 gem5 二进制程序：

```sh
scons build/ALL/gem5.opt
```

这会编译一个包含 "ALL" 指令集架构目标的 gem5 二进制程序。关于
构建 gem5 的更多信息，请查阅我们的[构建文档](
/documentation/general_docs/building)。

## 提交 {#committing}

当你认为改动已完成时，就可以提交了。首先把修改过的
文件加入暂存区 `git add <changed files>`。确保这些改动被添加到
你的复刻仓库。然后用 `git commit` 提交。

**提交信息必须符合我们的风格。**

- **标题格式：** 以一个标签（或多个用逗号分隔的标签）开头，然后是
一个冒号。可接受的标签列表见 [MAINTAINERS.yaml](
https://github.com/gem5/gem5/blob/stable/MAINTAINERS.yaml)。
使用哪些标签取决于你修改了 gem5 的哪些组件。冒号之后必须给出
对本次提交的简短描述。
**标题行不得超过 65 个字符。**

- **详细描述（可选）：** 写在标题下方，与标题之间空
一行。描述是可选的，但强烈建议填写。
描述可以有多行，也可以有多个段落。
**任何一行都不应超过 72 个字符。**

为了提高 gem5 项目的可导航性，如果提交信息中包含
相关 GitHub issue 的链接，我们将不胜感激。下面是
一条 gem5 提交信息的格式示例：

```
test,base: This commit tests some classes in the base component

This is a more detailed description of the commit. This can be as long
as is necessary to adequately describe the change.

A description may spawn multiple paragraphs if desired.

GitHub Issue: https://github.com/gem5/gem5/issues/123
```

如果你觉得需要修改提交，先加入必要的文件，然后用
`git commit --amend` 把改动*修正（amend）*到该提交上。这样你就
有机会编辑提交信息。

你可以继续添加更多提交，形成一串要包含在同一个拉取请求中的提交。
不过我们建议拉取请求保持小而聚焦。
例如，如果你想添加另一个功能或修复另一个缺陷，建议另开一个拉取请求。

## 保持复刻仓库与本地仓库同步

在推进你的贡献时，我们建议让复刻仓库与 gem5 源仓库保持同步。
为此，请定期[同步你的复刻仓库](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork)。
可以通过 GitHub 网页界面完成；如果这样做，之后应在本地 `stable` 和 `develop` 分支上执行 `git pull`，以确保本地仓库同步。
从命令行操作的步骤如下：

```sh
# Add the main gem5 repository as a remote on your local repository. This only
# needs done once.
git remote add upstream https://github.com/gem5/gem5.git

git fetch upstream # Obtain the latest from the gem5 repo.
git switch develop # Switch to the develop branch.
git merge upstream/develop # Merge the latest changes into the develop branch.
git push # Push to develop to your forked repo.
git switch stable # Switch to the stable branch.
git merge upstream/stable # Merge the latest changes into the stable branch.
git push # Push the changes to stable to your forked repo.
```

由于我们的本地分支建立在 `develop` 分支之上，同步复刻仓库之后，就可以把本地分支变基到 `develop` 分支之上。
假设本地分支名为 `new-feature`：

```sh
git switch develop # Switching back to the develop branch.
git pull # Ensuring we have the latest from the forked repository.
git switch new-feature # Switching back to our local branch.
git rebase develop # Rebasing our local branch on top of the develop branch.
```

你的分支与新改动之间可能需要解决冲突。

## 推送并创建拉取请求

在本地完成改动后，你就可以推送到自己的 gem5 复刻仓库。
假设我们正在处理的分支是 `new-feature`：

```sh
git switch new-feature # Ensure we are on the 'new-feature' branch.
git push --set-upstream origin new-feature
```

如果这是你第一次推送到自己的 gem5 复刻仓库，可能会遇到错误，提示 GitHub 在验证 Git 操作时不再接受账号密码。要解决该问题，请在 [github-tokens](https://github.com/settings/tokens) 生成个人访问令牌，然后按照[这些步骤](https://docs.github.com/en/get-started/getting-started-with-git/managing-remote-repositories#switching-remote-urls-from-https-to-ssh)把远程 URL 切换为 SSH。

现在，通过 GitHub 网页界面，你可以[创建拉取请求](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)，把你的改动从复刻仓库的分支合入 gem5 的 `develop` 分支。

## 通过检查

创建拉取请求后，gem5 的持续集成（CI）测试将会运行。
这些测试会执行一系列检查，以确保你的改动是有效的。
它们必须通过，你的改动才能合并到 gem5 的 `develop` 分支。

除 CI 测试之外，你的改动还会由 gem5 社区评审。
你的拉取请求在合并前必须获得至少一位社区成员的批准。

一旦你的拉取请求通过了所有 CI 测试，并且获得至少一位社区成员的批准，gem5 维护者就会对该拉取请求执行[合并](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges)。
gem5 维护者是被授予将拉取请求合并到 gem5 `develop` 分支权限的个人。

### 根据反馈迭代改进

评审者会在 GitHub 上提问并给出建议。你应当仔细阅读这些评论，并回应所有问题。
**评审者与贡献者之间的所有交流都应保持礼貌，粗鲁或轻慢的言论不会被容忍。**

当你理解了需要做哪些改动后，把补丁添加到同一分支再推送到复刻仓库，以此修正拉取请求。
如果你希望在本地改写提交来实现这些改动，Git 的 “force push”（即 `git push --force`）也是可以接受的。
我们鼓励贡献者帮助保持 `git log` 干净、可读。
我们建议用户经常把改动变基到 develop 分支之上，
在合适的时候压缩提交（例如同一个 PR 中有许多小的修正提交），
然后强制推送，以保持 PR 中的提交简洁。

推送到复刻仓库后，拉取请求会自动更新为你的改动。
评审者随后会重新评审你的改动，必要时要求进一步修改，或者批准你的拉取请求。

## 评审他人的贡献

我们鼓励所有 gem5 开发者评审他人的贡献。
任何人都可以评审 gem5 的改动，并在认为其已就绪时批准它。
所有拉取请求都可以在 <https://github.com/gem5/gem5/pulls> 找到。

评审拉取请求时，我们执行以下准则。
这些准则旨在确保各方之间清晰、礼貌的沟通：

* 在所有形式的交流中，贡献者和评审者都必须保持礼貌。
被视为粗鲁或轻慢的评论不会被容忍。
* 如果你选择不批准某个 PR，请清楚说明理由。
请求修改时，评论应当具体且可执行。
贡献者无法回应或理解的笼统批评是没有帮助的。
如果贡献需要改进，评审者应清楚列出所要求的修改。
如果评审者需要更多信息才能做出决定，他们应当提出明确的问题。
如果总体上认为该 PR 不值得贡献，则应给出充分理由，以便贡献者能够公平地回应。
* 默认情况下，假定改动归原作者所有。
也就是说，默认只有原作者可以向该拉取请求提交补丁。
如果原作者之外的人希望代表原作者提交补丁，应先征得许可。
如果看起来已被放弃的拉取请求有足够理由认为原作者不再推进，则可由新的贡献者接手。
* 维护者对改动是否合并有最终决定权。
你的评审会被维护者纳入考虑。
除极端情况外，通常期望评审者提出的问题得到解决，并由评审者批准该贡献，之后维护者才会合并拉取请求。

我们还建议参考 Google 的 ["How to write code review comments"](https://google.github.io/eng-practices/review/reviewer/comments.html)，了解如何向贡献者提供反馈。

## 发布

gem5 每年发布 3 次。gem5 的发布流程
如下：

1. 会通过 gem5-dev 邮件列表通知开发者即将发布新的
gem5 版本。通知时间应不晚于创建
staging 分支（发布新版 gem5 的第一步）前 2 周。这样开发者才有时间确保他们为下一次
发布所做的改动已提交到 develop 分支。
2. 当一次发布准备就绪时，项目
维护者会从 develop 创建名为 "release-staging-{VERSION}" 的新 staging 分支。
gem5-dev 邮件列表会收到通知：该 staging 分支将在两周后合并
到 stable 分支，从而标记新的发布。
3. 会在这条 staging 分支上运行 gem5 的完整测试套件，以
确保所有测试通过，并且待发布的代码处于良好状态。
4. 如果用户向 staging 分支提交拉取请求，它会被考虑
并走标准的 GitHub 评审流程。不过，只有不能等到下一次发布的改动才会被接受到该分支
（也就是说，为了“最后时刻”纳入发布而提交到 staging 分支的内容应具有高优先级，例如关键的缺陷
修复）。项目维护者将自行判断某项
改动是否可以直接提交到 staging 分支。所有其他提交
仍将继续提交到 develop 分支。提交到 staging 分支的补丁
不需要再添加到 develop 分支。
5. 一旦 staging 分支被认为可以发布，就会执行[发布流程](https://www.gem5.org/documentation/general_docs/development/release_procedures/)。
最后会把 staging 分支合并到 stable 分支。
6. stable 分支会打上该次发布对应的版本号标签。gem5 遵循
"v{YY}.{MAJOR}.{MINOR}.{HOTFIX}" 版本号规则。
例如，2022 年的第一个主要版本是 "v22.0.0.0"，之后是
"v22.1.0.0"。所有发布（热修复除外）都被视为
主要版本。在此期间没有次要版本，但我们
仍保留次要版本号，以防该策略将来发生变化。
7. 会通过 gem5-dev 和 gem5-user 邮件列表通知新的 gem5
发布。

### 例外情况

由于 GitHub 的限制，我们可能会在两次 gem5 发布之间更新 gem5 仓库 `stable` 分支中的 ".github" 目录。
这是因为 GitHub Actions 基础设施执行的某些流程依赖于仓库主分支上存在相应配置。
由于 ".github" 中的文件只影响我们的 GitHub actions 及其他 GitHub 活动的功能，更新这些文件不会以任何方式改变 gem5 的功能。
因此这样做是安全的。
尽管有这项对常规流程的例外，我们仍力求确保**`stable` 上的 ".github" 目录永远不会“领先于” `develop` 分支中的对应目录**。
因此，希望更新 ".github" 中文件的贡献者应把改动提交到 `develop`，然后再请求将这些改动应用到 `stable` 分支。


### 热修复

有时可能某项对 gem5 的改动被认为非常关键，
不能等待正式发布（例如高优先级的缺陷修复）。在这种情况下，应进行热修复。

首先，如果开发者怀疑可能需要热修复，应在 gem5-dev 邮件列表上讨论该问题。
社区将决定该问题是否值得热修复；如果没有共识，
则由 PMC 成员做出最终决定。假定允许热修复，
将执行以下步骤：

1. 从 stable 分支创建以 "hotfix-" 为前缀的新分支。
只有 gem5 维护者可以创建分支。如果非维护者需要
创建热修复分支，应联系 gem5 维护者。
2. 该改动应通过 GitHub 提交到热修复分支。与其他任何改动一样，
需要经过完整评审。
3. 完全提交后，热修复分支应由 gem5 维护者合并到
develop 分支和 stable 分支。
4. stable 分支会打上新版本号的标签；版本号与
上一个相同，但热修复号递增（例如 "v20.2.0.0" 将
变为 "v20.2.0.1"）。
4. 随后删除热修复分支。
5. 会通过 gem5-dev 和 gem5-user 邮件列表通知本次
热修复。

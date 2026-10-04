---
layout: documentation
title: 把进行中的改动从 Gerrit 迁移到 GitHub
doc: gem5 文档
parent: moving_to_github
permalink: /documentation/general_docs/moving_to_github/
---

# 把进行中的改动从 Gerrit 迁移到 GitHub

在转向用 GitHub 托管 gem5 项目的过程中，我们需要一种方式把 Gerrit 上仍在进行中的改动移到 GitHub 上评审。如果你的改动在 Gerrit 变为只读时还无法合并，请按以下步骤在 GitHub 上为你的改动创建拉取请求以供评审。

* 打开 https://github.com/gem5/gem5 并创建 gem5 仓库的复刻（fork），务必取消勾选 “Copy the stable branch only” 复选框
* 创建复刻后，克隆你的复刻仓库，然后运行 `git checkout --track origin/develop`，使你的改动位于 develop 分支之上
* 复刻仓库准备好后，打开 https://gem5-review.googlesource.com/q/status:open+-is:wip 找到你的改动
* 打开你的改动后，点击屏幕右侧的 “Download” 按钮，复制用于 cherry-pick 该改动的命令
* 把改动 cherry-pick 到你的复刻仓库，并处理可能出现的合并冲突。如果这些改动属于一个关联改动（relation change）的一部分，请确保 cherry-pick 它的每一个部分。
* 所有改动都 cherry-pick 完成后，运行 `git push origin` 更新你的复刻仓库
* 所有改动都推送上去后，你就可以创建拉取请求了。为此，在 https://github.com 上打开你的仓库，点击页面中部的 Contribute 按钮。操作时请确保你位于 develop 分支。点击 Contribute 后，应该会出现 “Open pull request” 按钮。
* 这会带你进入创建拉取请求的页面。基础仓库（base repository）应为 gem5/gem5，分支应为 develop。任何指向 stable 分支的拉取请求都会被忽略。头部仓库（head repository）应为你的复刻仓库，分支同样应为 develop。在拉取请求的正文中，你可以附上 Gerrit 中改动的链接，以便评论容易被找到。此外，在页面右侧可以添加评审者，因此你可以邀请任何在 Gerrit 上看过你改动的人来评审你的拉取请求
* 对拉取请求满意后，点击页面底部的 “Create pull request” 按钮。

如果你是第一次向 gem5 GitHub 仓库做贡献，你的拉取请求需要先获得一次正面评审，然后才能运行任何持续集成测试。改动要被合并，既需要这次正面评审，也需要这些测试通过。最后，在所有先前的检查都通过后，gem5 维护者会压缩并合并你的改动。

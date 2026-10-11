# Learning gem5 翻译与审校记录

日期：2026-10-11。工作分支：`translate/learning-gem5-zh`。

本批翻译主要由 AI（Codex）完成，补齐 Learning gem5 的中文内容。
英文基线为本仓库保存的 `gem5/website` stable 提交
`07ebfaf9bb1a0a4be2b822f3a4cf95abf20e4a4e`；工作分支基于已有链接修复提交 `0aef0a1`。
本项目将该基线作为固定快照，后续以补齐译文和修正本地问题为目标，不持续同步上游版本。
“查看英文源文”及页脚源码链接已固定到该提交。

## 覆盖范围

Learning gem5 共 35 篇，原先只有 4 篇中文文件。本批新增全部缺失的 31 篇，现为 35/35。

| 部分 | 新增译文 |
| --- | ---: |
| 第一部分：快速开始 | 4 |
| 第二部分：修改与扩展 | 8 |
| 第三部分：Ruby 与 MSI | 12 |
| gem5 101 总览与六份作业 | 7 |

译文位于 [Learning gem5 中文目录](../translations/zh_CN/_pages/documentation/learning_gem5/)。
按项目术语表统一专业术语，保留英文作者、父分组、permalink、代码、命令和日志。
已有四篇仅调整 front matter 标题，使其中文标题与导航一致，没有重译正文。

同步更新导航与翻译进度，并通过
`translations/zh_CN/pages/static -> ../../../_pages/static`
复用英文教程的图片和下载文件。所有 Learning gem5 侧栏链接现在都指向本地中文页。

## 技术审校中的主要处理

原文的历史示例和已确认错误不作静默修改；正文解释与译注相互区分，示例代码保持原样。

| 位置 | 处理 |
| --- | --- |
| 快速开始 | 区分 v24.1 标准库与 v21.0 配置；指出 `configs/examples/gem5-library` 等路径笔误，以及旧版脚本导入语句被原文 HTML 注释隐藏的问题。 |
| 配置参数 | 对照 `ParamDesc` 实现，明确一个位置实参表示说明，两个表示默认值与说明；字符串也可以是默认值。注明 `Simulator.full_system` 的 `None` 与 `False` 不同。 |
| SimObject 与事件 | 说明自动生成的 `Params::create()`、构造函数指针/引用混用、事件包装器版本差异，以及最后一个事件发生时间与模拟退出时间的区别。 |
| 内存对象 | 对照 `Packet::dataStatic`、`dataDynamic`、`deleteData` 明确数据释放责任；纠正请求/响应和重试接口名称混用，并说明同步重入时的状态更新顺序。 |
| 简单缓存 | 保留教学代码，同时指出写回路径未处理 `sendTimingReq` 返回 `false`；旧统计接口不等同于当前接口。 |
| ARM 功耗与 DVFS | 区分功率和能量、采样间隔和频率；标出原功耗示例的语法、类名、输入对象类型及系数量纲问题；说明单一电压可对应多个频率。 |
| Ruby 与 MSI | 核对虚拟网络、瞬态状态、确认计数、请求方与拥有者含义；说明动作资源检查和队列停顿的版本限制；保留调试过程中被作者否定的猜想及最终结论。 |
| Ruby 构建与配置 | 区分旧 SCons 与 Kconfig；注明较新版本的多协议构建；纠正块偏移位数、驱逐通知条件与原说明不一致之处。 |
| gem5 101 | 保留历史课程背景，修复 wiki 格式残留；明确第六课实际收录 CUDA 作业，与总览描述不符；纠正 GTX 480 核心数、作业日期等原文矛盾。 |

关键接口另与本机 gem5 源码中的 `src/mem/packet.hh`、`src/python/m5/params/`、
`src/python/gem5/simulate/simulator.py`、`src/mem/slicc/` 等实现交叉核对。
这不代表教程中跨版本的示例已全部编译或运行。

## 链接与资源

本问题并非仅凭重新部署就能解决：未翻译的页面原本不存在于中文源目录，部分链接还使用了源文件路径或旧 wiki 变量。
本批补齐 Learning gem5 正文，并确保相关静态资源进入构建产物。

- 28 个被正文引用的共享图片或下载文件均已生成，内容与英文源文件逐字节一致。
- 原文 `/_pages/static/...`、`/_static/...` 形式改为带 `site.baseurl` 的 `/pages/static/...` 发布路径。
- 恢复并验证了课程的配置压缩包、矩阵乘法源码与 CUDA 模板地址；核对 CUDA 压缩包确实包含所引用文件。
- 已失效的旧 AMD PDF 域名改为官方文档检索入口，并保留文档编号与历史页码说明。
- 修复 SimObject Doxygen 链接。失效的 GAPBS 资源详情页、Euler 集群资料和旧 ME964 课程页明确标注原始来源与状态。
- 两个历史 Python 下载地址返回 403，保留为不可点击的来源说明，没有假称可下载。

正文中最终保留 61 个不同外链，59 个检查返回 HTTP 200。
ACM 论文链接返回 403，旧 SBEL 论坛返回 202，未确认其正文可访问；保留历史引用并在本记录说明。
HTTP 状态检查不验证外部文件是否适配当前 gem5，也不保证外部服务未来持续可用。

## 验证结果

| 检查 | 结果 |
| --- | --- |
| 中文站点 Jekyll 构建 | 成功，116 个 HTML 页面；仅现有 Sass 弃用提示 |
| 全站站内链接和资源引用 | 8,845 处，0 断链 |
| Learning gem5 覆盖率 | 35/35，原作者、父分组与 permalink 保留 |
| Learning gem5 导航 | 全部指向中文页；章节当前项正确高亮 |
| 原始代码与输出块 | 用 Kramdown GFM 解析，300 个全部按顺序保留且内容一致 |
| ASCII 目录图 | 一处原先未围栏的目录图加上代码围栏，图中文字与缩进未改变 |
| 现有回归测试 | 5/5 通过 |
| 本地 HTTP 页面访问 | 35/35 返回 200，含不带扩展名的作业链接 |
| 页面显示 | Chrome 抽查内存对象章节，中文、侧栏与代码显示正常，图片请求成功 |

构建产物和一次性审校的详细记录保存在本地忽略目录中，不随本提交发布：

- 构建输出：`builds/learning-zh/`
- 全站链接报告：`builds/learning-links-report.json`
- 代码块、页面与资源比对、外链、HTTP 和页面显示抽查记录：`builds/learning-translation/`

准备好 Ruby、Bundler 和 Python 3 后，在仓库根目录复现构建、站内链接检查与回归测试：

```sh
export BUNDLE_PATH="$PWD/builds/gems"
export BUNDLE_GEMFILE="$PWD/translations/zh_CN/Gemfile"
bundle install
bundle exec jekyll build --source translations/zh_CN --destination builds/learning-zh --disable-disk-cache
python3 tools/check_site_links.py builds/learning-zh --report builds/learning-links-report.json
python3 -m unittest discover -s tests -v
```

本批已完成 AI 翻译与技术语义复核，尚未经人工逐段审定；未实际运行各篇历史教程的 gem5、功耗或 CUDA 实验。
构建和链接验证不能替代实验结果验证。

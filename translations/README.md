# gem5 官网中文翻译（gem5-doc-zh）

本目录是 [gem5 官方网站](https://www.gem5.org/)（[gem5/website](https://github.com/gem5/website)）
的中文翻译。翻译在**与英文原文完全相同的相对路径**下建立中文镜像，因此可以逐篇比对、增量推进，
并且不修改英文原文。

- 英文基线：`gem5/website` 的 `stable` 分支，提交 `07ebfaf9bb1a0a4be2b822f3a4cf95abf20e4a4e`
- 中文镜像：`translations/zh_CN/`
- 术语表：`translations/terminology.md`
- 维护脚本：`translations/zh_CN/_meta/`

## 目录结构

```
<仓库根>                       # gem5/website 的完整 Jekyll 站点（英文基线）
├── _config.yml                # 英文站点配置（未改动）
├── _data/documentation.yml    # 英文侧边栏数据（未改动）
├── _includes/ _layouts/ _sass/ assets/ css/ _pages/ _posts/ ...
└── translations/
    ├── terminology.md         # 中英术语对照表（含选取依据与状态）
    └── zh_CN/                 # 中文镜像：完整独立的 Jekyll 源根
        ├── _config.yml        # 中文站点配置
        ├── _data/documentation.yml   # 中文侧边栏（由 _meta/gen_nav.py 生成）
        ├── _includes/ _layouts/      # 界面模板（已中文化）
        ├── _pages/ _posts/ blog/     # 与英文同路径的中文页面
        ├── _meta/                    # 清单、导航抽取与生成脚本
        └── assets css _sass -> ../../  # 软链接复用上游静态资源，不复制
```

## 构建中文站点

```sh
cd translations/zh_CN
jekyll build --destination /tmp/gem5-zh-site
# 本地预览
jekyll serve --destination /tmp/gem5-zh-site
```

`translations/zh_CN/` 通过相对软链接引用仓库根目录的 `assets/`、`css/`、`_sass/`，
因此**必须在包含英文基线的仓库中构建**，不要单独把 `zh_CN/` 复制出去。

## 译文状态

| 项目 | 数值 |
| --- | --- |
| 英文手写文件总数 | 193（`_pages/` 155 + `_posts/` 33 + 首页/搜索/博客/404） |
| 合计词数 | 218,028 |
| 已完成初译 | 84 个文件，约 8.7 万词（39.9%） |
| 构建校验 | `jekyll build` 零错误，生成 85 个 HTML 页面 |

已完成的模块：站点界面（导航 / 页脚 / 首页 / 搜索 / 博客列表 / 404 / 6 个 layout）、
全部顶层页面（关于、快速开始、提问、参与贡献、项目治理、论文发表、加入 Slack）、
`documentation/general_docs/` 全部子目录（含 memory_system、cpu_models、
architecture_support、debugging_and_testing、fullsystem、gpu_models、statistics、
compiling_workloads 等）、`general_docs/ruby/` 全部 14 篇、
`gem5-stdlib/` 全部 8 篇。

待完成：`_posts/` 33 篇、`learning_gem5/` 31 篇、`community/events/` 24 篇、
`gem5art/` 12 篇、GB 级长文 3 篇（`minor_cpu`、`isa_parser`、`x86_microop_isa`）及零星 6 篇。

> **说明**：以上为「初译完成度」，**不等于人工审定完成**。当前译文仅经过结构校验与构建校验，
> 尚未逐段进行人工语义审校。使用时请以英文原文为准。

## 源文覆盖范围（有意不译的内容）

- `_pages/documentation/general_docs/sphinx_docs/`（188 个文件）：gem5 源码 Sphinx autodoc
  自动生成的 API 参考。
- `_pages/static/`、`assets/`、`css/`、`_sass/`、第三方 JS。
- 各处代码块、命令、寄存器/字段名、偏移、位宽、常量、API 名、Doxygen 链接、
  论文题录与作者列表、对外链接标题。

## 术语与行文约定

1. 语义优先于字面：译文准确传达原文技术含义，不逐词硬译，但不添加原文没有的
   解释、示例、结论、前提或学科背景。
2. 名词性术语在标题、导航、表格与正文中每次出现都写成「中文（English）」
   （例如「检查点（checkpoint）」「替换策略（replacement policy）」）；
   句式化的描述性标题只写中文。
3. 首次出现的外文概念按中文读者习惯正常译出；普通非专业词汇（developer、student）
   不必逐词附英文。
4. 代码块、命令、路径、参数、日志、ASCII 图、公式一律原样保留。
5. 完整对照见 `terminology.md`。

## 与上游的已知差异（非静默变更）

为让中文镜像可独立构建与安全托管，对上游做了以下**有意**调整，均在此记录：

1. **中文字体**：仅在正文/标题/按钮/表单上追加 CJK 字体栈；`pre`/`code`/`kbd`/`samp`
   保持等宽，避免破坏 ASCII 图与表格对齐。
2. **规范链接**：中文页的 canonical 指向同一路径的官方英文页面。
3. **移除 Google Analytics**：避免镜像流量污染 gem5 官方统计。
4. **移除 commentbox.io**：上游模板使用占位 `project-id`，镜像中不再加载。
5. **重复 canonical**：上游会输出两条 canonical，中文模板改为 `if/else`。
6. **缺失生成内容的回退**：`_data/documentation.yml` 中"Sphinx 文档"条目在中文镜像
   无对应页面，改指官方英文页面，避免空链接 / 404。
7. **上游既有不一致按原文保留**（未修复）：`apis.md` 的 `title` 为 `gem5-resources`、
   `gem5_memory_syste` 拼写残缺、`O3CPU` permalink 含双斜杠、
   `/publications/#original-paper` 为死锚点等。

另外，本仓库**未包含**上游以下两项，原因见括号：

- `CNAME`（内容为 `www.gem5.org`，属于 gem5 官方域名，不应用于本仓库；
  若需 GitHub Pages 请自行设置正确域名）。
- `.github/workflows/sphinx-to-website.yaml`（上游定时任务，会在本仓库中检出
  `gem5/website` 的 `stable` 分支并向本仓库提交自动生成的英文 API 文档）。

## 续译方式

1. 用 `_meta/make_manifest.py` 生成 / 刷新清单，对照 `_meta/manifest.tsv` 取下一个待译文件。
2. 英文原文在同名相对路径的仓库根目录下；译文写到 `translations/zh_CN/<完全相同的相对路径>`。
3. 文档页 front matter 约定：
   - `title`：按上述术语约定书写，并与 `_meta/nav_zh.tsv` 中对应条目保持一致；
   - `doc`：必须等于 `_data/documentation.yml` 中对应 `docs[].title`（分组标题）；
   - `parent` / `permalink` / `author`：沿用英文原值（`parent` 是内部 id，不翻译）。
4. 新增需翻译的导航文案时，先补 `_meta/nav_zh.tsv`，再运行
   `python3 _meta/gen_nav.py` 重新生成 `_data/documentation.yml`。
5. 每批完成后运行 `jekyll build` 并抽查锚点与术语一致性。

## 许可

英文原文版权归 gem5 项目所有，采用 MIT 许可（见仓库根目录 `LICENSE.md`）。
本翻译为原作品的衍生作品，同样在 MIT 许可下提供；引用、转载时请保留原版权声明，
并注明译自 gem5 官方网站对应页面。

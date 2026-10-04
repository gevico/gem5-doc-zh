#!/usr/bin/env python3
"""将英文 `_data/documentation.yml` 的 title/page 文案替换为中文，生成中文侧边栏数据。

结构、id、url 一律保持原样；未在映射表中登记的文案保持英文并报告。
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO, "_data", "documentation.yml")
MAP = os.path.join(HERE, "nav_zh.tsv")
DST = os.path.join(REPO, "translations", "zh_CN", "_data", "documentation.yml")

KEYS = ("title", "page")

# 中文镜像不包含源码自动生成的 Sphinx API 文档，该条目改指官方英文页面，避免空链接。
URL_OVERRIDES = {
    "/documentation/general_docs/stdlib_api/": "https://www.gem5.org/documentation/general_docs/stdlib_api/",
}


def load_map(path):
    table = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            en, _, zh = line.partition("\t")
            table[en] = zh
    return table


def main():
    table = load_map(MAP)
    leftover = []
    out = []
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = re.match(r"^(\s*(?:-\s+)?)(%s):\s*(.*?)\s*$" % "|".join(KEYS + ("url",)), line)
            if not m:
                out.append(line)
                continue
            prefix, key, val = m.group(1), m.group(2), m.group(3)
            if key == "url" and val in URL_OVERRIDES:
                out.append("%s%s: %s" % (prefix, key, URL_OVERRIDES[val]))
            elif val in table:
                out.append("%s%s: %s" % (prefix, key, table[val]))
            else:
                if val and key in KEYS:
                    leftover.append("%s: %s" % (key, val))
                out.append(line)
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote", DST)
    if leftover:
        print("KEPT ENGLISH (%d):" % len(leftover))
        for item in sorted(set(leftover)):
            print("  ", item)
    return 0


if __name__ == "__main__":
    sys.exit(main())

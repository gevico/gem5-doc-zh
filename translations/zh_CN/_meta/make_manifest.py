#!/usr/bin/env python3
"""生成英文基线文件清单，供翻译进度与一致性对照使用。

只读扫描，不修改任何文档。
"""

import csv
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.tsv")

FRONT_KEYS = ("layout", "title", "permalink", "parent", "doc", "author", "date", "tabs")
SKIP_DIRS = {"sphinx_docs", "static"}


def split_front_matter(text):
    if not text.startswith("---"):
        return "", text
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def simple_front_matter(fm):
    """解析顶层标量键；忽略 tabs 等多行结构。"""
    out = {}
    for line in fm.splitlines():
        if not line or line[0] in " \t#-":
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("", "|", ">"):
            out[key] = "<structured>"
        else:
            out[key] = val.strip("'\"")
    return out


def word_count(body):
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"`[^`]*`", "", body)
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", body))


def collect(subdir, pattern):
    rows = []
    root = os.path.join(REPO, subdir)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if not re.search(pattern, name):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, REPO)
            with open(full, encoding="utf-8") as fh:
                text = fh.read()
            fm, body = split_front_matter(text)
            meta = simple_front_matter(fm)
            rows.append({
                "path": rel,
                "words": word_count(body),
                "layout": meta.get("layout", ""),
                "title": meta.get("title", ""),
                "permalink": meta.get("permalink", ""),
                "parent": meta.get("parent", ""),
                "doc": meta.get("doc", ""),
                "author": meta.get("author", ""),
            })
    return rows


def main():
    rows = collect("_pages", r"\.(md|html)$") + collect("_posts", r"\.(md|html)$")
    rows.append({"path": "index.html", "words": word_count(open(os.path.join(REPO, "index.html"), encoding="utf-8").read()), "layout": "default", "title": "The gem5 simulator system", "permalink": "/", "parent": "", "doc": "", "author": ""})
    rows.append({"path": "404.md", "words": word_count(open(os.path.join(REPO, "404.md"), encoding="utf-8").read()), "layout": "page", "title": "", "permalink": "/404.html", "parent": "", "doc": "", "author": ""})
    rows.append({"path": "blog/index.html", "words": 0, "layout": "default", "title": "Blog", "permalink": "/blog/", "parent": "", "doc": "", "author": ""})
    rows.append({"path": "_pages/search.html", "words": 0, "layout": "page", "title": "Search", "permalink": "/search/", "parent": "", "doc": "", "author": ""})

    cols = ["path", "words", "layout", "title", "permalink", "parent", "doc", "author"]
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["path"]):
            w.writerow({c: r.get(c, "") for c in cols})

    total = sum(int(r["words"]) for r in rows)
    print(f"files={len(rows)} words={total} -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

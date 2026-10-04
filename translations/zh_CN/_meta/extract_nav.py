#!/usr/bin/env python3
"""从英文 `_data/documentation.yml` 提取侧边栏导航，与英文页面清单连接。

输出 doc_nav.tsv：doc_group / item_title / item_id / subitem_page / url / path / en_title
只读扫描，供建立中文标题映射使用。
"""

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO, "_data", "documentation.yml")
MANIFEST = os.path.join(HERE, "manifest.tsv")
OUT = os.path.join(HERE, "doc_nav.tsv")


def parse_nav(path):
    """极简解析：只关心 title/id/url/page 与层级缩进。"""
    rows = []
    doc_title = None
    doc_id = None
    item_title = None
    item_id = None
    subitem_page = None
    stack = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            m = re.match(r"^\s*(?:-\s+)?([A-Za-z_]+):\s*(.*)$", line)
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip().strip("'\"")
            # 顶层 docs: 下的条目用 "- title:" 表示，缩进 2
            if key == "title":
                if indent <= 0:
                    continue
                # 缩进 2 -> doc 或 item（按已见的 docs 层判断）
                if doc_title is None or (stack and stack[-1] == "docs"):
                    doc_title = val
                    doc_id = None
                    stack.append("doc")
                else:
                    item_title = val
                    item_id = None
                    stack.append("item")
            elif key == "id":
                if stack and stack[-1] == "doc":
                    doc_id = val
                else:
                    item_id = val
            elif key == "url":
                rows.append({
                    "doc": doc_title or "",
                    "item_title": item_title or "",
                    "item_id": item_id or "",
                    "subitem_page": "",
                    "url": val,
                })
            elif key == "items":
                stack = ["items"]
            elif key == "page":
                subitem_page = val
                rows.append({
                    "doc": doc_title or "",
                    "item_title": item_title or "",
                    "item_id": item_id or "",
                    "subitem_page": val,
                    "url": "",
                })
            elif key == "subitems":
                pass
    return rows


def main():
    nav = parse_nav(SRC)
    # 补齐 subitem 的 url（紧跟在 page 之后一行）
    with open(SRC, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    idx = 0
    for row in nav:
        if row["subitem_page"] and not row["url"]:
            for j in range(idx, len(lines)):
                if re.match(r"^\s*-\s+page:\s*" + re.escape(row["subitem_page"]) + r"\s*$", lines[j]):
                    for k in range(j + 1, min(j + 3, len(lines))):
                        m = re.match(r"^\s*url:\s*(.+)$", lines[k])
                        if m:
                            row["url"] = m.group(1).strip().strip("'\"")
                            break
                    idx = j
                    break

    permalink_to_path = {}
    with open(MANIFEST, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            pl = r["permalink"]
            if pl and not pl.startswith("http"):
                permalink_to_path[pl.rstrip("/") or "/"] = r["path"]
                permalink_to_path[(pl.rstrip("/") or "/") + "/"] = r["path"]

    out_rows = []
    for row in nav:
        url = row["url"]
        key = url.rstrip("/") or "/"
        path = permalink_to_path.get(key, permalink_to_path.get(key + "/", ""))
        out_rows.append({**row, "path": path, "en_title": row["subitem_page"] or row["item_title"]})

    cols = ["doc", "item_title", "item_id", "subitem_page", "url", "path", "en_title"]
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        for r in out_rows:
            w.writerow({c: r.get(c, "") for c in cols})

    missing = [r for r in out_rows if r["url"] and not r["url"].startswith("http") and not r["path"]]
    print(f"nav_rows={len(out_rows)} unmatched={len(missing)} -> {OUT}")
    for r in missing:
        print("  UNMATCHED:", r["url"], "|", r["en_title"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

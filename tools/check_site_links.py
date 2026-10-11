#!/usr/bin/env python3
"""Check local HTML links against the actual GitHub Pages build output.

This is an offline check: external URLs and fragment IDs are not validated.
GitHub Pages supports extensionless URLs for .html files, but a trailing slash
requires an index.html. File names are compared case-sensitively on every OS.
"""

import argparse
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr in {"href", "src", "action", "poster"} and value:
                self.links.append((self.getpos()[0], value))


def check_site(destination, baseurl, origin):
    destination = Path(destination)
    files = {p.relative_to(destination).as_posix()
             for p in destination.rglob("*") if p.is_file()}
    baseurl = "/" + baseurl.strip("/") if baseurl.strip("/") else ""
    origin = origin.rstrip("/")
    host = urlsplit(origin).netloc
    failures = []
    external = Counter()
    checked = 0
    pages = sorted(p for p in files if p.endswith(".html"))
    for page in pages:
        parser = Links()
        parser.feed((destination / page).read_text(encoding="utf-8"))
        page_path = page.removesuffix("index.html") if Path(page).name == "index.html" else page
        page_url = origin + baseurl + "/" + page_path
        for line, href in parser.links:
            href = href.strip()
            if not href or href.startswith("#"):
                continue
            target = urlsplit(urljoin(page_url, href))
            if target.scheme not in {"http", "https"}:
                continue
            if target.netloc != host:
                external[target.geturl()] += 1
                continue
            checked += 1
            path = unquote(target.path)
            reason = None
            if baseurl and path != baseurl and not path.startswith(baseurl + "/"):
                reason = "missing baseurl / outside the deployed site"
            else:
                relative = path[len(baseurl):].lstrip("/")
                candidates = {relative, relative.rstrip("/") + "/index.html"}
                if not relative:
                    candidates.add("index.html")
                if relative and not relative.endswith("/") and not Path(relative).suffix:
                    candidates.add(relative + ".html")
                if not candidates.intersection(files):
                    reason = "target does not exist in build output"
            if reason:
                failures.append({"page": page, "line": line, "href": href,
                                 "target": path, "reason": reason})
    return {"pages": len(pages), "checked_links": checked,
            "broken_targets": len({f["target"] for f in failures}),
            "failures": failures, "external_urls": sorted(external)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--baseurl", default="/gem5-doc-zh")
    parser.add_argument("--origin", default="https://gevico.github.io")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not (args.destination / "index.html").is_file():
        parser.error("destination must contain the built index.html")
    report = check_site(args.destination, args.baseurl, args.origin)
    print(f"Checked {report['pages']} HTML pages, {report['checked_links']} local links: "
          f"{len(report['failures'])} broken references to {report['broken_targets']} targets.")
    for failure in report["failures"][:40]:
        print(f"  {failure['page']}:{failure['line']}: {failure['href']} "
              f"({failure['reason']})")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

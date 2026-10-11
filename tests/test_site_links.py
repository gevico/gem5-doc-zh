"""Regression checks for published paths and translation fallback behavior."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.check_site_links import check_site


class LinkCheckerTests(unittest.TestCase):
    def setUp(self):
        (REPO / "builds").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=REPO / "builds")
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)

    def check(self, html, baseurl="/docs"):
        (self.site / "index.html").write_text(html)
        return check_site(self.site, baseurl, "https://example.test")

    def test_extensionless_and_directory_urls(self):
        (self.site / "chapter.html").touch()
        (self.site / "section").mkdir()
        (self.site / "section/index.html").touch()
        result = self.check('<a href="/docs/chapter?q=1#intro">chapter</a>'
                            '<a href="section/">section</a>'
                            '<a href="/docs/chapter/">wrong slash</a>')
        self.assertEqual([f["href"] for f in result["failures"]], ["/docs/chapter/"])

    def test_missing_baseurl_and_case_are_rejected(self):
        (self.site / "Chapter.html").touch()
        result = self.check('<a href="/Chapter">no prefix</a>'
                            '<a href="/docs/chapter">wrong case</a>')
        self.assertEqual(result["broken_targets"], 2)

    def test_encoded_assets_and_form_targets(self):
        (self.site / "a b.pdf").touch()
        (self.site / "search.html").touch()
        result = self.check('<a href="a%20b.pdf">download</a>'
                            '<form action="/docs/search"></form>'
                            '<img src="/docs/missing.png">')
        self.assertEqual([f["href"] for f in result["failures"]], ["/docs/missing.png"])

    def test_root_deployment_and_non_local_links(self):
        result = self.check('<a href="/">home</a><a href="#intro">anchor</a>'
                            '<a href="https://external.test/path">external</a>'
                            '<a href="mailto:user@example.test">email</a>', baseurl="")
        self.assertEqual(result["failures"], [])
        self.assertEqual(result["checked_links"], 1)


class SiteBuildTests(unittest.TestCase):
    def test_fallbacks_follow_translation_availability(self):
        (REPO / "builds").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=REPO / "builds") as directory:
            root = Path(directory)
            source = root / "translations/zh_CN"

            def write(path, content):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            def page(url):
                return f"---\npermalink: {url}\n---\n<p>Chapter</p>\n"

            write(root / "_pages/missing.md", page("/guide/missing/"))
            write(root / "_pages/translated.md", page("/translated/"))
            write(source / "_pages/translated.md", page("/translated/"))
            # A collection can also contain StaticFile objects, not just pages.
            write(source / "_pages/manual.txt", "A static collection file")
            write(source / "assets/a b.svg", "<svg></svg>")
            write(source / "index.html", '''---
---
<!DOCTYPE html><html lang="zh-CN"><head><title>Test</title></head><body>
<a href="{{ site.baseurl }}/translated">中文</a>
<a href="guide/missing?x=1&amp;y=2#intro">未翻译</a>
<a href="{{ site.baseurl }}/guide/typo">拼写错误</a>
<a href="https://other.test/guide/missing">站外</a>
<a href="#intro">锚点</a>
<a href="{{ site.baseurl }}/pages/manual.txt">静态文件</a>
<img src="{{ site.baseurl }}/assets/a%20b.svg">
<pre><code>&lt;a href="/guide/missing"&gt;example&lt;/a&gt;</code></pre>
</body></html>
''')
            env = dict(os.environ, BUNDLE_GEMFILE=str(REPO / "translations/zh_CN/Gemfile"))

            def build(baseurl):
                config = {
                    "url": "https://example.test", "baseurl": baseurl,
                    "english_url": "https://www.gem5.org",
                    "plugins_dir": str(REPO / "translations/zh_CN/_plugins"),
                    "collections": {"pages": {"output": True}},
                }
                write(source / "_config.yml", json.dumps(config))
                result = subprocess.run(
                    ["bundle", "exec", "jekyll", "build", "--source", str(source),
                     "--destination", str(root / "output"), "--disable-disk-cache"],
                    cwd=REPO, env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return (root / "output/index.html").read_text()

            for baseurl in ["/gem5-doc-zh", "", "/nested/preview"]:
                with self.subTest(baseurl=baseurl):
                    html = build(baseurl)
                    self.assertIn(f'href="{baseurl}/translated/">中文</a>', html)
                    self.assertIn('href="https://www.gem5.org/guide/missing/?x=1&amp;y=2#intro"', html)
                    self.assertIn('hreflang="en"', html)
                    self.assertIn('（英文）</span>', html)
                    self.assertIn('href="https://other.test/guide/missing">站外</a>', html)
                    self.assertIn('href="#intro">锚点</a>', html)
                    self.assertIn('&lt;a href="/guide/missing"&gt;example&lt;/a&gt;', html)
                    report = check_site(root / "output", baseurl, "https://example.test")
                    self.assertEqual([f["href"] for f in report["failures"]],
                                     [baseurl + "/guide/typo"])

            # Adding a translation automatically restores the local link on
            # the next build, without changing navigation or prose links.
            write(source / "_pages/missing.md", page("/guide/missing/"))
            html = build("/gem5-doc-zh")
            self.assertIn('href="/gem5-doc-zh/guide/missing/?x=1&amp;y=2#intro">未翻译</a>', html)
            self.assertNotIn("data-english-fallback", html)


if __name__ == "__main__":
    unittest.main()

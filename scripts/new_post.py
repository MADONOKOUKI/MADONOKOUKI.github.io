#!/usr/bin/env python3
"""Create a blog post skeleton in posts/ and print the next steps.

    python3 scripts/new_post.py "水墨画レンダリングのメモ"
    python3 scripts/new_post.py "Notes on brush rendering" --lang en --slug brush-notes

The new file is marked `draft: true`, so building and pushing will not publish
it until that line is changed to `draft: false`.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"

TEMPLATE = """---
title: {title}
date: {date}
summary:
tags:
lang: {lang}
draft: true
---

ここに本文を書きます。段落は空行で区切ります。

## 見出し

- 箇条書き
- **太字** と *斜体* と `コード`
- [リンク](https://example.com) と画像 ![説明](../images/foo.jpg)

> 引用はこう書きます。

```python
print("コードブロック")
```
"""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title", help="post title")
    ap.add_argument("--slug", help="URL slug (required if the title has no ASCII letters)")
    ap.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD (default: today)")
    ap.add_argument("--lang", default="ja", choices=["ja", "en"], help="post language (default: ja)")
    args = ap.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit(f"--date must be YYYY-MM-DD, got {args.date!r}")

    slug = args.slug or slugify(args.title)
    if not slug:
        raise SystemExit("could not build a slug from the title — pass one with --slug, e.g. --slug ink-notes")

    POSTS_DIR.mkdir(exist_ok=True)
    path = POSTS_DIR / f"{args.date}-{slug}.md"
    if path.exists():
        raise SystemExit(f"{path.relative_to(ROOT)} already exists")
    path.write_text(TEMPLATE.format(title=args.title, date=args.date, lang=args.lang), encoding="utf-8")

    print(f"created {path.relative_to(ROOT)}\n"
          "\nnext:\n"
          f"  1. edit {path.relative_to(ROOT)} (summary / tags / body)\n"
          "  2. python3 scripts/build_blog.py --drafts   # local preview, drafts included\n"
          "  3. set draft: false, then:\n"
          "     python3 scripts/build_blog.py && git add -A && git commit -m 'blog: new post' && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())

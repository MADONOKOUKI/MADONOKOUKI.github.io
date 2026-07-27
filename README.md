# MADONOKOUKI.github.io

Personal site — plain static HTML served by GitHub Pages.

| What | Where |
| --- | --- |
| Top page (about, news, grants, awards…) | `index.html` |
| Publication list | `data/publications.json` (rendered by `assets/pubs.js`) |
| Styles | `assets/style.css` — bump the `?v=` in the pages after editing |
| Blog posts (source) | `posts/*.md` |
| Blog pages (generated — do not edit by hand) | `blog/`, `data/posts.json` |

## Writing a blog post

```bash
python3 scripts/new_post.py "タイトル"          # creates posts/YYYY-MM-DD-slug.md
python3 scripts/build_blog.py --drafts         # build including drafts, for local preview
python3 scripts/build_blog.py                  # build published posts only
```

Each post is Markdown with front matter:

```markdown
---
title: タイトル
date: 2026-07-28
summary: 一覧・OGP・RSS に出る一行
tags: notes, ink painting
lang: ja
draft: true
---
```

A new post starts as `draft: true` and stays unpublished until that becomes
`draft: false`. Then rebuild, commit `posts/` and `blog/`, and push.

Adding or editing a file under `posts/` on GitHub also works: the **Build blog**
workflow (`.github/workflows/build-blog.yml`) rebuilds `blog/` and commits the
result.

Supported Markdown: headings, lists, blockquotes, fenced code, images, links,
bold/italic, horizontal rules, and raw HTML blocks. Wrapped Japanese lines are
joined without inserting spaces.

## Publications

`scripts/sync_researchmap.py` runs weekly (`.github/workflows/sync-researchmap.yml`)
and opens a PR with skeleton entries for papers found on researchmap but missing
from `data/publications.json`.

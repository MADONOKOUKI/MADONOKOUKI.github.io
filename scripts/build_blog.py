#!/usr/bin/env python3
"""Build the blog: posts/*.md  ->  blog/*.html + blog/feed.xml + data/posts.json.

Write a post as Markdown in posts/ (scripts/new_post.py makes the skeleton),
then run this script and commit. No third-party packages: the Markdown subset
below is deliberately small — headings, lists, quotes, fenced code, images,
links, bold/italic, horizontal rules, and raw HTML blocks pass through.

    python3 scripts/build_blog.py            # build published posts
    python3 scripts/build_blog.py --drafts   # include drafts (local preview)

Front matter (between two --- lines at the top of the file):

    title:   post title                        (required)
    date:    2026-07-28                        (required, ISO)
    summary: one line for the list, OGP, RSS   (optional, derived if missing)
    tags:    ink painting, notes               (optional, comma separated)
    lang:    ja | en                           (optional, default ja)
    image:   images/foo.jpg                    (optional, OGP + list thumbnail)
    draft:   true                              (optional, skipped unless --drafts)
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "blog"
DATA_FILE = ROOT / "data" / "posts.json"
LAYOUT = Path(__file__).resolve().parent / "blog_layout.html"

SITE_URL = "https://madonokouki.github.io"
SITE_TITLE = "Koki Madono — 真殿 航輝"
BLOG_TITLE = "Blog — Koki Madono"
BLOG_DESC = "Notes on computer graphics, ink painting research, and the things I build."
DEFAULT_OG_IMAGE = f"{SITE_URL}/images/avatar.jpg"
JST = timezone(timedelta(hours=9))

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# --------------------------------------------------------------------------
# Markdown (small subset — see module docstring)
# --------------------------------------------------------------------------

def esc(text: str, quote: bool = False) -> str:
    return html_mod.escape(text, quote=quote)


RE_CODE_SPAN = re.compile(r"`([^`]+)`")
RE_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
RE_BOLD = re.compile(r"\*\*([^*]+)\*\*")
RE_ITALIC = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])")
RE_LIST_ITEM = re.compile(r"\s*([-*+]|\d+[.)])\s+(.*)")
RE_HEADING = re.compile(r"(#{1,4})\s+(.*)")

# CJK ranges: joining two wrapped lines must not insert a space between them.
RE_CJK_TAIL = re.compile(r"[　-鿿＀-ﾟ]$")
RE_CJK_HEAD = re.compile(r"^[　-鿿＀-ﾟ]")


def join_lines(lines: list[str]) -> str:
    """Join wrapped source lines — no space between two CJK characters."""
    out = ""
    for line in lines:
        line = line.strip()
        if not out:
            out = line
        elif RE_CJK_TAIL.search(out) and RE_CJK_HEAD.match(line):
            out += line
        else:
            out += " " + line
    return out


def inline(text: str) -> str:
    """Inline markup on one already-joined chunk of text."""
    stash: list[str] = []

    def keep_code(m: re.Match) -> str:
        stash.append("<code>" + esc(m.group(1)) + "</code>")
        return f"\x00{len(stash) - 1}\x00"

    text = RE_CODE_SPAN.sub(keep_code, text)
    text = esc(text)

    def img(m: re.Match) -> str:
        alt, src, title = m.group(1), m.group(2), m.group(3)
        t = f' title="{esc(title, quote=True)}"' if title else ""
        return (f'<img src="{esc(src, quote=True)}" alt="{esc(alt, quote=True)}"{t} loading="lazy">')

    def link(m: re.Match) -> str:
        label, href, title = m.group(1), m.group(2), m.group(3)
        ext = href.startswith("http")
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        t = f' title="{esc(title, quote=True)}"' if title else ""
        return f'<a href="{esc(href, quote=True)}"{t}{attrs}>{label}</a>'

    text = RE_IMG.sub(img, text)
    text = RE_LINK.sub(link, text)
    text = RE_BOLD.sub(r"<strong>\1</strong>", text)
    text = RE_ITALIC.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def markdown_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):                       # fenced code
            lang = line[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{esc(lang, quote=True)}"' if lang else ""
            out.append(f"<pre><code{cls}>" + esc("\n".join(buf)) + "</code></pre>")
            continue

        m = RE_HEADING.match(line)
        if m:                                            # # .. #### -> h2 .. h5
            level = min(len(m.group(1)) + 1, 6)
            out.append(f"<h{level}>{inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line.strip()):
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith(">"):                # blockquote
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:])
                i += 1
            out.append("<blockquote><p>" + inline(join_lines(buf)) + "</p></blockquote>")
            continue

        m = RE_LIST_ITEM.match(line)
        if m:                                            # - item / 1. item
            tag = "ol" if re.match(r"\d+[.)]", m.group(1)) else "ul"
            items = []
            while i < len(lines):
                mm = RE_LIST_ITEM.match(lines[i])
                if not mm:
                    break
                items.append(inline(mm.group(2).strip()))
                i += 1
            body = "".join(f"<li>{x}</li>" for x in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        if line.lstrip().startswith("<"):                # raw HTML block
            buf = []
            while i < len(lines) and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        buf = []                                         # paragraph
        while i < len(lines) and lines[i].strip():
            stop = (lines[i].startswith("```")
                    or RE_HEADING.match(lines[i])
                    or lines[i].lstrip().startswith((">", "<"))
                    or RE_LIST_ITEM.match(lines[i]))
            if stop and buf:
                break
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(join_lines(buf)) + "</p>")

    return "\n".join(out)


# --------------------------------------------------------------------------
# Posts
# --------------------------------------------------------------------------

def parse_front_matter(text: str, path: Path) -> tuple[dict, str]:
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise SystemExit(f"{path.name}: missing front matter (the file must start with ---)")
    meta: dict[str, str] = {}
    for n, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[n + 1:])
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise SystemExit(f"{path.name}: front matter line without a colon: {line!r}")
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip()
    raise SystemExit(f"{path.name}: front matter is not closed with ---")


def is_true(value: str | None) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "on"}


def slug_of(path: Path) -> str:
    stem = path.stem
    m = re.match(r"\d{4}-\d{2}-\d{2}-(.+)", stem)
    return m.group(1) if m else stem


def pretty_date(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def strip_tags(html: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", html)).strip()


def load_posts(include_drafts: bool) -> tuple[list[dict], int]:
    posts, skipped = [], 0
    for path in sorted(POSTS_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path)
        if is_true(meta.get("draft")) and not include_drafts:
            skipped += 1
            continue
        for required in ("title", "date"):
            if not meta.get(required):
                raise SystemExit(f"{path.name}: front matter needs a {required}")
        try:
            datetime.strptime(meta["date"], "%Y-%m-%d")
        except ValueError:
            raise SystemExit(f"{path.name}: date must be YYYY-MM-DD, got {meta['date']!r}")

        content = markdown_to_html(body)
        summary = meta.get("summary") or ""
        if not summary:
            first = re.search(r"<p>(.*?)</p>", content, re.S)
            summary = strip_tags(first.group(1))[:160] if first else ""
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        slug = meta.get("slug") or slug_of(path)

        posts.append({
            "title": meta["title"],
            "date": meta["date"],
            "slug": slug,
            "url": f"blog/{slug}.html",
            "summary": summary,
            "tags": tags,
            "lang": meta.get("lang", "ja"),
            "image": meta.get("image", ""),
            "draft": is_true(meta.get("draft")),
            "html": content,
            "source": path.name,
        })

    slugs = [p["slug"] for p in posts]
    duplicate = {s for s in slugs if slugs.count(s) > 1}
    if duplicate:
        raise SystemExit(f"duplicate post slugs: {', '.join(sorted(duplicate))}")

    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts, skipped


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_layout(layout: str, *, lang: str, title: str, desc: str, og_title: str,
                  og_type: str, canonical: str, og_image: str, body: str) -> str:
    values = {
        "LANG": lang,
        "TITLE": esc(title, quote=True),
        "DESC": esc(desc, quote=True),
        "OG_TITLE": esc(og_title, quote=True),
        "OG_TYPE": og_type,
        "CANONICAL": esc(canonical, quote=True),
        "OG_IMAGE": esc(og_image, quote=True),
        "BODY": body,
    }
    out = layout
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def tag_html(tags: list[str]) -> str:
    if not tags:
        return ""
    chips = "".join(f'<span class="post-tag">{esc(t)}</span>' for t in tags)
    return f'<p class="post-tags">{chips}</p>'


def render_index(posts: list[dict]) -> str:
    parts = ['    <header class="blog-head">',
             "      <h1>Blog</h1>",
             f"      <p>{esc(BLOG_DESC)}</p>",
             '      <p class="blog-feed"><a href="feed.xml">RSS feed</a></p>',
             "    </header>"]
    if not posts:
        parts.append('    <p class="blog-empty">No posts yet — the first one is on its way.</p>')
    else:
        current_year = None
        parts.append('    <div class="post-list">')
        for post in posts:
            year = post["date"][:4]
            if year != current_year:
                current_year = year
                parts.append(f'      <h2 class="post-year">{year}</h2>')
            draft = '<span class="post-draft">draft</span>' if post["draft"] else ""
            summary = f'<p class="post-summary">{esc(post["summary"])}</p>' if post["summary"] else ""
            parts.append(
                f'      <article class="post-card">\n'
                f'        <p class="post-date"><time datetime="{post["date"]}">{esc(pretty_date(post["date"]))}</time>{draft}</p>\n'
                f'        <div>\n'
                f'          <h3><a href="{esc(post["slug"], quote=True)}.html">{esc(post["title"])}</a></h3>\n'
                f'          {summary}\n'
                f'          {tag_html(post["tags"])}\n'
                f'        </div>\n'
                f"      </article>"
            )
        parts.append("    </div>")
    return "\n".join(parts)


def render_post(post: dict, newer: dict | None, older: dict | None) -> str:
    nav = []
    if older:
        nav.append(f'<a href="{esc(older["slug"], quote=True)}.html">← {esc(older["title"])}</a>')
    if newer:
        nav.append(f'<a href="{esc(newer["slug"], quote=True)}.html">{esc(newer["title"])} →</a>')
    nav_html = f'    <nav class="post-nav">{"".join(nav)}</nav>' if nav else ""
    banner = ""
    if post["image"]:
        banner = f'    <img class="post-banner" src="../{esc(post["image"], quote=True)}" alt="">'
    draft = '<span class="post-draft">draft</span>' if post["draft"] else ""
    return "\n".join(x for x in [
        '    <article class="post">',
        '      <header class="post-head">',
        f'        <p class="post-date"><time datetime="{post["date"]}">{esc(pretty_date(post["date"]))}</time>{draft}</p>',
        f'        <h1>{esc(post["title"])}</h1>',
        f'        {tag_html(post["tags"])}',
        "      </header>",
        banner,
        '      <div class="post-body">',
        post["html"],
        "      </div>",
        "    </article>",
        '    <p class="post-back"><a href="./">← All posts</a></p>',
        nav_html,
    ] if x)


def render_feed(posts: list[dict]) -> str:
    items = []
    for post in posts[:20]:
        d = datetime.strptime(post["date"], "%Y-%m-%d").replace(hour=9, tzinfo=JST)
        link = f"{SITE_URL}/{post['url']}"
        items.append(
            "    <item>\n"
            f"      <title>{esc(post['title'])}</title>\n"
            f"      <link>{esc(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{esc(link)}</guid>\n"
            f"      <pubDate>{d.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>\n"
            f"      <description>{esc(post['summary'])}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{esc(BLOG_TITLE)}</title>\n"
        f"    <link>{SITE_URL}/blog/</link>\n"
        f"    <description>{esc(BLOG_DESC)}</description>\n"
        "    <language>ja</language>\n"
        + "\n".join(items) + "\n"
        "  </channel>\n"
        "</rss>\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drafts", action="store_true", help="also build posts marked draft: true")
    args = ap.parse_args()

    POSTS_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    layout = LAYOUT.read_text(encoding="utf-8")
    posts, skipped = load_posts(args.drafts)

    # Stale pages from renamed or deleted posts must not stay published.
    keep = {f"{p['slug']}.html" for p in posts} | {"index.html", "feed.xml"}
    for path in OUT_DIR.glob("*.html"):
        if path.name not in keep:
            path.unlink()
            print(f"removed stale {path.relative_to(ROOT)}")

    for n, post in enumerate(posts):
        newer = posts[n - 1] if n > 0 else None
        older = posts[n + 1] if n + 1 < len(posts) else None
        canonical = f"{SITE_URL}/{post['url']}"
        image = f"{SITE_URL}/{post['image']}" if post["image"] else DEFAULT_OG_IMAGE
        html = render_layout(
            layout,
            lang=post["lang"],
            title=f"{post['title']} — Koki Madono",
            desc=post["summary"] or post["title"],
            og_title=post["title"],
            og_type="article",
            canonical=canonical,
            og_image=image,
            body=render_post(post, newer, older),
        )
        (OUT_DIR / f"{post['slug']}.html").write_text(html, encoding="utf-8")

    (OUT_DIR / "index.html").write_text(render_layout(
        layout,
        lang="en",
        title=BLOG_TITLE,
        desc=BLOG_DESC,
        og_title=BLOG_TITLE,
        og_type="website",
        canonical=f"{SITE_URL}/blog/",
        og_image=DEFAULT_OG_IMAGE,
        body=render_index(posts),
    ), encoding="utf-8")

    (OUT_DIR / "feed.xml").write_text(render_feed(posts), encoding="utf-8")

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(
        [{k: p[k] for k in ("title", "date", "slug", "url", "summary", "tags", "lang", "image")}
         for p in posts], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"built {len(posts)} post(s) into {OUT_DIR.relative_to(ROOT)}/"
          + (f", skipped {skipped} draft(s)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

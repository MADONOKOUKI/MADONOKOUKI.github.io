#!/usr/bin/env python3
"""Mirror the documentation of the DetFill-with-DHT repository as static pages under projects/hintauc/docs/.

    python3 scripts/build_hintauc_docs.py --src /path/to/DetFill-with-DHT      (needs: pip install markdown)

Markdown files are converted with python-markdown (tables, fenced code, table of contents). Links between the mirrored
documents are rewritten to the local pages, images are copied, and every other repository link points at GitHub.
"""
from __future__ import annotations

import argparse
import html
import os
import posixpath
import re
import shutil
from pathlib import Path

import markdown

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "projects" / "hintauc" / "docs"
REPO_URL = "https://github.com/MADONOKOUKI/DetFill-with-DHT"
# (repository path, output name, navigation title)
PAGES = [
    ("README.md", "index", "Overview"),
    ("docs/setup.md", "setup", "Setup"),
    ("docs/evaluate_your_model.md", "evaluate-your-model", "Evaluate your own model"),
    ("docs/api.md", "api", "API reference"),
    ("checkpoints/README.md", "model-zoo", "Model zoo"),
    ("reproduce/README.md", "reproducing", "Reproducing the paper"),
    ("reproduce/examples/README.md", "examples", "Example suite"),
    ("replicability/README.md", "replicability", "Replicability script (Fig. 9)"),
    ("detfill/README.md", "detfill", "DetFill model"),
    ("hint_generation/README.md", "hint-generation", "Hint generation scripts"),
    ("evaluation/README.md", "evaluation", "Evaluation scripts"),
    ("reproduce/paper_experiments/README.md", "paper-experiments", "Paper experiment launchers"),
    ("docs/added_features.md", "added-features", "Added features"),
    ("docs/detail_explanation.md", "detail-explanation", "Detailed explanation"),
    ("CONTRIBUTING.md", "contributing", "Contributing"),
    ("THIRD_PARTY_NOTICES.md", "third-party-notices", "Third-party notices"),
]
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} — Hint-AUC documentation — Koki Madono</title>
  <meta name="description" content="Documentation of the Hint-AUC / DetFill repository (mirror): {title}.">
  <link rel="canonical" href="https://madonokouki.github.io/projects/hintauc/docs/{name}.html">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E🐳%3C/text%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../../assets/style.css?v=16">
  <style>
    .docs {{ display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 32px; align-items: start; }}
    .docs nav.toc {{ position: sticky; top: 72px; font-size: .86rem; }}
    .docs nav.toc h3 {{ margin: 0 0 .5rem; font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; color: #4a5b6a; }}
    .docs nav.toc ul {{ list-style: none; margin: 0; padding: 0; }}
    .docs nav.toc li {{ margin: .25rem 0; }}
    .docs nav.toc a {{ text-decoration: none; }}
    .docs nav.toc a[aria-current] {{ font-weight: 700; }}
    .doc-body {{ font-size: 14.5px; line-height: 1.75; min-width: 0; }}
    .doc-body h1 {{ font-size: 1.55rem; margin: 0 0 .8rem; line-height: 1.3; }}
    .doc-body h2 {{ font-size: 1.15rem; margin: 1.8rem 0 .6rem; padding-top: .4rem; border-top: 1px solid #dde6ee; }}
    .doc-body h3 {{ font-size: 1rem; margin: 1.3rem 0 .4rem; }}
    .doc-body h4 {{ font-size: .95rem; margin: 1rem 0 .3rem; }}
    .doc-body table {{ border-collapse: collapse; font-size: .84rem; margin: .8rem 0 1.2rem; display: block; overflow-x: auto; max-width: 100%; }}
    .doc-body th, .doc-body td {{ padding: .3rem .5rem; border: 1px solid #dde6ee; vertical-align: top; text-align: left; }}
    .doc-body thead th {{ background: #f3f7fa; }}
    .doc-body pre {{ background: #f3f7fa; border-radius: 8px; padding: .8rem 1rem; overflow-x: auto; font-size: .8rem; line-height: 1.55; }}
    .doc-body code {{ font-size: .88em; background: #f3f7fa; padding: .05em .3em; border-radius: 4px; }}
    .doc-body pre code {{ background: none; padding: 0; font-size: inherit; }}
    .doc-body img {{ max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #dde6ee; }}
    .doc-body blockquote {{ margin: .8rem 0; padding: .4rem .9rem; border-left: 4px solid #9fb6c9; color: #4a5b6a; }}
    .doc-body details {{ margin: .6rem 0 1rem; }}
    .doc-body details summary {{ cursor: pointer; color: #1f5f8b; }}
    .doc-banner {{ background: #eef6fb; border-left: 4px solid #6aa9d9; padding: .55rem .9rem; border-radius: 6px; font-size: .86rem; margin: 0 0 1.2rem; }}
    @media (max-width: 800px) {{ .docs {{ grid-template-columns: 1fr; }} .docs nav.toc {{ position: static; }} }}
  </style>
</head>
<body>
  <nav class="site-nav" aria-label="Site">
    <div class="bar">
      <a class="brand" href="../../../"><span class="brand-mark" aria-hidden="true">🐳</span>Koki Madono</a>
      <ul>
        <li><a href="../../../#about">About</a></li>
        <li><a href="../../../#publications">Publications</a></li>
        <li><a href="../">Hint-AUC project</a></li>
        <li><a href="index.html" aria-current="page">Docs</a></li>
        <li><button id="season-btn" class="season-btn" type="button" aria-label="Change season theme">🌊</button></li>
      </ul>
    </div>
  </nav>
  <main class="wrap blog-main">
    <div class="docs">
      <nav class="toc" aria-label="Documentation">
        <h3>Hint-AUC docs</h3>
        <ul>
{navlist}
        </ul>
        <h3 style="margin-top:1rem">Links</h3>
        <ul>
          <li><a href="../">Project page</a></li>
          <li><a href="https://pypi.org/project/hintauc/" target="_blank" rel="noopener">PyPI: hintauc</a></li>
          <li><a href="{repo}" target="_blank" rel="noopener">GitHub repository</a></li>
        </ul>
      </nav>
      <article class="doc-body">
        <p class="doc-banner">Mirror of the documentation in the <a href="{repo}" target="_blank" rel="noopener">DetFill-with-DHT</a>
        repository (source file <code>{src}</code>). Links to files and release downloads on GitHub work once the repository is public;
        the <code>hintauc</code> library is already available from PyPI.</p>
"""
FOOT = """
      </article>
    </div>
  </main>
  <div class="sea-floor">
    <svg class="footer-wave" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0,54 C130,26 260,18 400,36 C540,54 660,78 800,72 C940,66 1060,32 1200,28 C1320,25 1390,42 1440,52 L1440,90 L0,90 Z"/>
    </svg>
    <footer class="sea-footer"><p class="colophon">© Koki Madono</p></footer>
  </div>
  <script src="../../../assets/season.js?v=14"></script>
</body>
</html>
"""


def rewrite_links(md_text: str, src_rel: str, page_by_path: dict, repo: Path) -> str:
    """Rewrite Markdown links relative to ``src_rel`` (repository path of the source file)."""
    base = posixpath.dirname(src_rel)
    copied = []

    def target(url: str, is_image: bool) -> str:
        if re.match(r"^(https?:|mailto:|#)", url):
            return url
        path, _, anchor = url.partition("#")
        rel = posixpath.normpath(posixpath.join(base, path)) if path else src_rel
        if rel in page_by_path:
            return page_by_path[rel] + ".html" + (("#" + anchor) if anchor else "")
        if is_image or rel.lower().endswith(IMAGE_EXT):
            srcfile = repo / rel
            if srcfile.exists():
                dst = OUT / "assets" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(srcfile, dst)
                copied.append(rel)
                return "assets/" + rel
        return f"{REPO_URL}/blob/main/{rel}" + (("#" + anchor) if anchor else "")

    # one level of nesting so that badge links ``[![alt](img)](url)`` are rewritten inside and out
    link_re = re.compile(r"(!?)\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(([^)\s]+)\)")

    def repl(m: re.Match) -> str:
        bang, text, url = m.group(1), m.group(2), m.group(3)
        text = link_re.sub(repl, text)
        return f"{bang}[{text}]({target(url, bool(bang))})"

    return link_re.sub(repl, md_text)


def build(repo: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    page_by_path = {p: name for p, name, _ in PAGES}
    for src_rel, name, title in PAGES:
        src = repo / src_rel
        if not src.exists():
            print("missing:", src_rel)
            continue
        text = rewrite_links(src.read_text(encoding="utf-8"), src_rel, page_by_path, repo)
        body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists", "md_in_html"],
                                 extension_configs={"toc": {"toc_depth": "2-4"}})
        navlist = "\n".join(
            f'          <li><a href="{n}.html"{" aria-current=\"page\"" if n == name else ""}>{html.escape(t)}</a></li>'
            for _, n, t in PAGES)
        page = HEAD.format(title=html.escape(title), name=name, navlist=navlist, repo=REPO_URL, src=html.escape(src_rel)) + body + FOOT
        (OUT / f"{name}.html").write_text(page, encoding="utf-8")
        print("wrote", f"projects/hintauc/docs/{name}.html")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", required=True, help="path to a DetFill-with-DHT checkout")
    a = ap.parse_args()
    build(Path(a.src).expanduser().resolve())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sync check between researchmap and this site.

Fetches the public researchmap API for madorin0130 and compares its
published_papers against data/publications.json.

Usage:
  python3 scripts/sync_researchmap.py          # report only
  python3 scripts/sync_researchmap.py --write  # also append skeleton entries
                                               # for papers missing from the site

Skeleton entries render without links/teaser until you fill them in
(look for the "_todo" marker in data/publications.json).
Awards and research projects are printed for manual comparison only.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

PERMALINK = "madorin0130"
API_URL = f"https://api.researchmap.jp/{PERMALINK}"
REPO_ROOT = Path(__file__).resolve().parent.parent
PUBS_PATH = REPO_ROOT / "data" / "publications.json"


def fetch_researchmap():
    req = urllib.request.Request(API_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def lang_text(value, prefer=("en", "ja")):
    """researchmap wraps strings as {"en": ..., "ja": ...}."""
    if isinstance(value, dict):
        for key in prefer:
            if value.get(key):
                return value[key]
        for v in value.values():
            if v:
                return v
        return ""
    return value or ""


def author_names(paper):
    authors = paper.get("authors") or {}
    if isinstance(authors, dict):
        for key in ("en", "ja"):
            people = authors.get(key)
            if people:
                return ", ".join(p.get("name", "") for p in people if p.get("name"))
    return ""


def paper_year(paper):
    date = str(paper.get("publication_date") or "")
    match = re.match(r"(\d{4})", date)
    return int(match.group(1)) if match else None


def paper_doi(paper):
    ids = paper.get("identifiers") or {}
    dois = ids.get("doi") or []
    return dois[0] if dois else None


def normalize_title(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())


def titles_match(a, b):
    """Equal after normalization, or one contains the other (short vs full titles)."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return False
    return na == nb or (len(na) > 25 and na in nb) or (len(nb) > 25 and nb in na)


def paper_type(paper):
    return "journal" if paper.get("published_paper_type") == "scientific_journal" else "conference"


def graph_section(data, name):
    for section in data.get("@graph", []):
        if section.get("@type") == name:
            return section.get("items", [])
    return []


def main():
    write = "--write" in sys.argv

    data = fetch_researchmap()
    rm_papers = graph_section(data, "published_papers")
    rm_awards = graph_section(data, "awards")
    rm_projects = graph_section(data, "research_projects")

    site_pubs = json.loads(PUBS_PATH.read_text())
    site_titles = [p["title"] for p in site_pubs]

    missing = []
    for paper in rm_papers:
        title = lang_text(paper.get("paper_title"))
        if title and not any(titles_match(title, s) for s in site_titles):
            missing.append(paper)

    print(f"researchmap: {len(rm_papers)} papers / site: {len(site_pubs)} entries")
    if not missing:
        print("papers: in sync — nothing new on researchmap.")
    else:
        print(f"papers: {len(missing)} entr{'y' if len(missing) == 1 else 'ies'} on researchmap but not on the site:")
        for paper in missing:
            title = lang_text(paper.get("paper_title"))
            print(f"  - [{paper_year(paper)}] {title}")

    if write and missing:
        for paper in missing:
            doi = paper_doi(paper)
            entry = {
                "year": paper_year(paper) or 0,
                "type": paper_type(paper),
                "title": lang_text(paper.get("paper_title")),
                "authors": author_names(paper),
                "venue": lang_text(paper.get("publication_name")),
                "links": [{"label": "Paper", "url": f"https://doi.org/{doi}"}] if doi else [],
                "_todo": "auto-added from researchmap — fill links/thumb/abstract/bibtex",
            }
            site_pubs.append(entry)
        PUBS_PATH.write_text(json.dumps(site_pubs, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {len(missing)} skeleton entr{'y' if len(missing) == 1 else 'ies'} to {PUBS_PATH.relative_to(REPO_ROOT)}")

    print("\nawards on researchmap (compare manually with #awards / News):")
    for award in rm_awards:
        name = lang_text(award.get("award_name"))
        date = award.get("award_date", "")
        print(f"  - [{date}] {name}")

    print("\nresearch projects on researchmap (compare manually with #grants):")
    for project in rm_projects:
        name = lang_text(project.get("research_project_title"))
        frm = project.get("from_date", "")
        to = project.get("to_date", "")
        print(f"  - [{frm} – {to}] {name}")


if __name__ == "__main__":
    main()

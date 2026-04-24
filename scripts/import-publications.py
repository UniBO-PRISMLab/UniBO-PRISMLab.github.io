#!/usr/bin/env python3
"""
Import WordPress-exported publication posts into data/papers.csv.

Walks content/posts/*.html (each carrying a <div class="publication-*"> block
from the original WP export), normalises the fields, and writes them to the
single-source-of-truth CSV at data/papers.csv.

Curation is preserved across runs:
  * If a row with the same (year, normalised title) already exists in the CSV,
    its `id`, `research_areas`, `venue` and `featured` fields are kept.
  * New rows get empty `research_areas` and `featured = "0"` so the team can
    tag them later without fighting the script.

Usage:
    python3 scripts/import-publications.py           # update data/papers.csv in place
    python3 scripts/import-publications.py --dry-run # print summary only, don't write

The script is safe to re-run whenever publications are added to the WP export.
"""

from __future__ import annotations

import argparse
import csv
import html as htmllib
import re
import sys
import unicodedata
from pathlib import Path

SITE       = Path(__file__).resolve().parent.parent
POSTS_DIR  = SITE / "content" / "posts"
CSV_PATH   = SITE / "data" / "papers.csv"

COLUMNS = [
    "id", "title", "authors", "year", "venue",
    "type", "doi", "url", "research_areas", "featured",
]

# --- author normalisation -------------------------------------------------
#
# Map every full-name spelling that appears in the WP export to its team-member
# slug (matching content/team/<slug>.md). Unknown authors are emitted verbatim
# with an "ext:" prefix so they render as plain text.
TEAM_SLUGS: dict[str, str] = {
    "Luciano Bononi":                  "luciano-bononi",
    "Marco Di Felice":                 "marco-di-felice",
    "Angelo Trotta":                   "angelo-trotta",
    "Federico Montori":                "federico-montori",
    "Luca Sciullo":                    "luca-sciullo",
    "Ivan Dimitry Ribeiro Zyrianoff":  "ivan-zyrianoff",
    "Ivan D. Zyrianoff":               "ivan-zyrianoff",
    "Ivan Zyrianoff":                  "ivan-zyrianoff",
    "Ivan Dimitry":                    "ivan-zyrianoff",  # used in a few bios
    "Lorenzo Gigli":                   "lorenzo-gigli",
    "Leonardo Montecchiari":           "leonardo-montecchiari",
    "Carlos Alberto Kamienski":        "carlos-alberto-kamienski",
    "Carlos Kamienski":                "carlos-alberto-kamienski",
    "Alexandre Heideker":              "alexandre-heideker",
    "Yasmin Moghbelan":                "yasmin-moghbelan",
    "Yasamin Moghbelan":               "yasmin-moghbelan",
    "Leonardo Ciabattini":             "leonardo-ciabattini",
    "Alfonso Esposito":                "alfonso-esposito",
    "Mattia Forlesi":                  "mattia-forlesi",
    "Milena Mazza":                    "milena-mazza",
    "Marco Montanari":                 "marco-montanari",
    "Andrea Iannoli":                  "andrea-iannoli",
}

# --- publication-type vocabulary -----------------------------------------
TYPE_MAP: dict[str, str] = {
    "journal articles":                "journal",
    "conference and workshop papers":  "conference",
    "informal and other publications": "preprint",
    "editorship":                      "editorship",
    "books and theses":                "book",
    "parts in books or collections":   "chapter",
    "book chapters":                   "chapter",
    "reference works":                 "chapter",
}

FIELD_RE = re.compile(r'<div class="publication-(\w+)">(.*?)</div>', re.DOTALL)


def slugify(text: str, max_len: int = 50) -> str:
    """Make a filesystem- and URL-safe slug from the given title."""
    normalised = unicodedata.normalize("NFKD", text)
    ascii_only = normalised.encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return cleaned[:max_len].rstrip("-")


def clean(text: str) -> str:
    """Unescape HTML entities and collapse whitespace."""
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def map_author(raw: str) -> str | None:
    """Map a raw author name to either a team slug or ``ext:Full Name``."""
    name = clean(raw).strip()
    if not name:
        return None
    if name in TEAM_SLUGS:
        return TEAM_SLUGS[name]
    return f"ext:{name}"


def parse_post(path: Path) -> dict[str, str] | None:
    """Extract a canonical paper row from a WP publication post."""
    text = path.read_text(encoding="utf-8")
    fields: dict[str, str] = {m.group(1): m.group(2) for m in FIELD_RE.finditer(text)}

    title = clean(fields.get("title", ""))
    year  = clean(fields.get("year", ""))
    if not title or not year:
        return None

    # Authors are semicolon-separated with a trailing semicolon.
    raw_authors = fields.get("authors", "")
    authors = [a for a in (map_author(s) for s in raw_authors.split(";")) if a]

    pub_type = TYPE_MAP.get(clean(fields.get("type", "")).lower(), "other")

    # The WP export uses the "doi" slot for any canonical link (DOIs, arXiv…).
    # Split semantically: real DOIs go in `doi`, anything else in `url`.
    link = clean(fields.get("doi", ""))
    doi, url = "", ""
    if link:
        if "doi.org" in link or re.match(r"^10\.\d{4,9}/", link):
            doi = link
        else:
            url = link

    stem_short = path.stem[:10]
    slug = slugify(title, 40) or stem_short
    row_id = f"{year}-{slug}"

    return {
        "id":             row_id,
        "title":          title,
        "authors":        "|".join(authors),
        "year":           year,
        "venue":          "",
        "type":           pub_type,
        "doi":            doi,
        "url":            url,
        "research_areas": "",
        "featured":       "0",
    }


def load_existing(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Index the current CSV by (year, normalised title) for merge."""
    if not path.exists():
        return {}
    index: dict[tuple[str, str], dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("year", ""), clean(row.get("title", "")).lower())
            index[key] = row
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print summary without touching papers.csv")
    args = parser.parse_args(argv)

    existing = load_existing(CSV_PATH)
    parsed: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for path in sorted(POSTS_DIR.glob("*.html")):
        row = parse_post(path)
        if row is None:
            continue

        key = (row["year"], clean(row["title"]).lower())
        if key in existing:
            # Preserve curated fields on re-run.
            prev = existing[key]
            row["id"]             = prev.get("id") or row["id"]
            row["research_areas"] = prev.get("research_areas") or ""
            row["featured"]       = prev.get("featured") or "0"
            if prev.get("venue"):
                row["venue"] = prev["venue"]

        # Disambiguate id collisions (same year + similar title across papers).
        base_id = row["id"]
        suffix = 2
        while row["id"] in seen_ids:
            row["id"] = f"{base_id}-{suffix}"
            suffix += 1
        seen_ids.add(row["id"])

        parsed.append(row)

    # Preserve curated rows that have no matching WP post (e.g. hand-entered later).
    parsed_keys = {(r["year"], clean(r["title"]).lower()) for r in parsed}
    for key, row in existing.items():
        if key in parsed_keys:
            continue
        if not row.get("title") or not row.get("year"):
            continue
        # ensure no id collision
        if row["id"] in seen_ids:
            row["id"] = f"{row['id']}-2"
        seen_ids.add(row["id"])
        parsed.append({c: row.get(c, "") for c in COLUMNS})

    # Sort: year descending, then title ascending (stable across runs).
    parsed.sort(key=lambda r: (-int(r["year"] or 0), r["title"].lower()))

    summary = {
        "posts_scanned": sum(1 for _ in POSTS_DIR.glob("*.html")),
        "rows_written":  len(parsed),
        "curated_kept":  sum(1 for r in parsed if r["research_areas"] or r["featured"] == "1"),
    }
    print(f"scanned {summary['posts_scanned']} posts  "
          f"-> {summary['rows_written']} rows  "
          f"({summary['curated_kept']} curated rows preserved)")

    if args.dry_run:
        print("[dry-run] papers.csv untouched", file=sys.stderr)
        return 0

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writeheader()
        for row in parsed:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})
    print(f"wrote {CSV_PATH.relative_to(SITE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

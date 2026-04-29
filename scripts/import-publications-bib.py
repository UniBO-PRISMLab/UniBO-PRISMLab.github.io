#!/usr/bin/env python3
"""
Import BibTeX publications into data/papers.csv.

Source of truth:
  data/group_publications.bib

Destination:
  data/papers.csv

Notes:
  - Keeps curated fields from existing CSV rows matched by (year, title):
      id, research_areas, featured, venue (only if BibTeX venue is empty)
  - Maps internal authors to team slugs, external ones to `ext:Full Name`
  - Uses the same CSV schema used by the site templates
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
BIB_PATH = SITE / "data" / "group_publications.bib"
CSV_PATH = SITE / "data" / "papers.csv"
TEAM_DIR = SITE / "content" / "team"

COLUMNS = [
    "id", "title", "authors", "year", "venue",
    "type", "doi", "url", "research_areas", "featured",
]

ENTRY_TYPE_MAP = {
    "article": "journal",
    "inproceedings": "conference",
    "proceedings": "conference",
    "book": "book",
    "inbook": "chapter",
    "incollection": "chapter",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
}

SURNAME_PARTICLES = {"da", "de", "del", "della", "di", "van", "von"}

MANUAL_NAME_ALIASES: dict[str, str] = {
    # Current and former team members, plus common variants observed in exports.
    "Ivan Dimitry Ribeiro Zyrianoff": "ivan-zyrianoff",
    "Ivan D. Zyrianoff": "ivan-zyrianoff",
    "Ivan Dimitry": "ivan-zyrianoff",
    "Yasamin Moghbelan": "yasmin-moghbelan",
    "Carlos Kamienski": "carlos-alberto-kamienski",
    "M Di Felice": "marco-di-felice",
    "L Bononi": "luciano-bononi",
    "A Trotta": "angelo-trotta",
    "F Montori": "federico-montori",
    "L Sciullo": "luca-sciullo",
    "I Zyrianoff": "ivan-zyrianoff",
    "L Gigli": "lorenzo-gigli",
    "L Ciabattini": "leonardo-ciabattini",
    "M Forlesi": "mattia-forlesi",
    "M Montanari": "marco-montanari",
    "A Esposito": "alfonso-esposito",
    "A Heideker": "alexandre-heideker",
}


def clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def norm_ascii(text: str) -> str:
    n = unicodedata.normalize("NFKD", text)
    n = "".join(ch for ch in n if not unicodedata.combining(ch))
    n = n.lower()
    n = re.sub(r"[^a-z0-9 ]+", " ", n)
    return clean_ws(n)


def slugify(text: str, max_len: int = 40) -> str:
    normalised = unicodedata.normalize("NFKD", text)
    ascii_only = normalised.encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return cleaned[:max_len].rstrip("-")


def bib_text_cleanup(value: str) -> str:
    # Basic BibTeX de-escaping for this dataset.
    value = value.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    value = value.replace("{", "").replace("}", "")
    return clean_ws(value)


def split_person_list(authors: str) -> list[str]:
    return [clean_ws(p) for p in re.split(r"\s+\band\b\s+", authors, flags=re.IGNORECASE) if clean_ws(p)]


def canonical_person(name: str) -> str:
    # Convert "Last, First" -> "First Last" when needed.
    if "," in name:
        parts = [clean_ws(p) for p in name.split(",") if clean_ws(p)]
        if len(parts) >= 2:
            return clean_ws(" ".join(parts[1:] + [parts[0]]))
    return clean_ws(name)


def infer_surname(tokens: list[str]) -> str:
    if len(tokens) >= 2 and tokens[-2].lower() in SURNAME_PARTICLES:
        return f"{tokens[-2]} {tokens[-1]}"
    return tokens[-1] if tokens else ""


def load_team_aliases(team_dir: Path) -> dict[str, str]:
    """
    Build name->slug aliases from content/team/*.md titles plus manual aliases.
    Keys are normalized ASCII names for robust matching.
    """
    aliases: dict[str, str] = {}
    valid_slugs: set[str] = set()

    for path in sorted(team_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m_title = re.search(r'(?m)^title\s*=\s*"([^"]+)"', text)
        m_slug = re.search(r'(?m)^slug\s*=\s*"([^"]+)"', text)
        if not m_title or not m_slug:
            continue
        full = clean_ws(m_title.group(1))
        slug = clean_ws(m_slug.group(1))
        if not full or not slug:
            continue
        valid_slugs.add(slug)

        tokens = full.split()
        if len(tokens) >= 2:
            first = tokens[0]
            surname = infer_surname(tokens)
            variants = {
                full,
                f"{first} {tokens[-1]}",
                f"{first[0]} {tokens[-1]}",
                f"{first[0]}. {tokens[-1]}",
                f"{first} {surname}",
                f"{first[0]} {surname}",
                f"{first[0]}. {surname}",
            }
        else:
            variants = {full}

        for v in variants:
            aliases[norm_ascii(v)] = slug

    for raw_name, slug in MANUAL_NAME_ALIASES.items():
        if slug in valid_slugs:
            aliases[norm_ascii(raw_name)] = slug

    return aliases


def parse_bib_entries(text: str) -> list[tuple[str, str, dict[str, str]]]:
    """
    Parse BibTeX entries using a small brace-aware parser.
    Returns: [(entry_type, key, fields_dict), ...]
    """
    entries: list[tuple[str, str, dict[str, str]]] = []
    i = 0
    n = len(text)

    while i < n:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.match(r"@([A-Za-z]+)\s*\{", text[at:])
        if not m:
            i = at + 1
            continue
        entry_type = m.group(1).lower()
        brace_open = at + m.end() - 1  # position of '{'

        depth = 0
        j = brace_open
        while j < n:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= n:
            break

        body = text[brace_open + 1:j]
        i = j + 1

        comma = body.find(",")
        if comma < 0:
            continue
        key = clean_ws(body[:comma])
        rest = body[comma + 1:]
        fields: dict[str, str] = {}

        p = 0
        while p < len(rest):
            while p < len(rest) and rest[p] in " \t\r\n,":
                p += 1
            if p >= len(rest):
                break

            fm = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=", rest[p:])
            if not fm:
                p += 1
                continue
            fname = fm.group(1).lower()
            p += fm.end()

            while p < len(rest) and rest[p].isspace():
                p += 1
            if p >= len(rest):
                fields[fname] = ""
                break

            if rest[p] == "{":
                p += 1
                depth = 1
                start = p
                while p < len(rest):
                    if rest[p] == "{":
                        depth += 1
                    elif rest[p] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    p += 1
                value = rest[start:p]
                p += 1  # skip closing brace
            elif rest[p] == '"':
                p += 1
                start = p
                while p < len(rest):
                    if rest[p] == '"' and rest[p - 1] != "\\":
                        break
                    p += 1
                value = rest[start:p]
                p += 1  # skip closing quote
            else:
                start = p
                while p < len(rest) and rest[p] not in ",\n":
                    p += 1
                value = rest[start:p]

            fields[fname] = bib_text_cleanup(value)

        entries.append((entry_type, key, fields))

    return entries


def normalize_doi(doi: str) -> str:
    doi = clean_ws(doi)
    if not doi:
        return ""
    if doi.lower().startswith("http://") or doi.lower().startswith("https://"):
        return doi
    return f"https://doi.org/{doi}"


def map_author(name: str, aliases: dict[str, str]) -> str:
    canonical = canonical_person(bib_text_cleanup(name))
    key = norm_ascii(canonical)
    if key in aliases:
        return aliases[key]
    return f"ext:{canonical}"


def row_key(year: str, title: str) -> tuple[str, str]:
    return (clean_ws(year), clean_ws(title).lower())


def load_existing(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    idx: dict[tuple[str, str], dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            idx[row_key(row.get("year", ""), row.get("title", ""))] = row
    return idx


def convert_entry(
    entry_type: str,
    fields: dict[str, str],
    aliases: dict[str, str],
) -> dict[str, str] | None:
    title = clean_ws(fields.get("title", ""))
    year = clean_ws(fields.get("year", ""))
    if not title or not year:
        return None

    author_field = fields.get("author", "")
    authors = "|".join(map(lambda n: map_author(n, aliases), split_person_list(author_field)))

    venue = clean_ws(fields.get("journal", "") or fields.get("booktitle", ""))
    pub_type = ENTRY_TYPE_MAP.get(entry_type, "other")
    doi = normalize_doi(fields.get("doi", ""))
    url = clean_ws(fields.get("url", ""))

    row_id = f"{year}-{slugify(title, 40)}"
    if row_id.endswith("-"):
        row_id = row_id.rstrip("-")
    if row_id == f"{year}-":
        row_id = year

    return {
        "id": row_id,
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "type": pub_type,
        "doi": doi,
        "url": url,
        "research_areas": "",
        "featured": "0",
    }


def parse_year_for_sort(year: str) -> int:
    m = re.search(r"\d{4}", year or "")
    return int(m.group(0)) if m else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=BIB_PATH, help="path to BibTeX input")
    parser.add_argument("--csv", type=Path, default=CSV_PATH, help="path to CSV output")
    parser.add_argument("--dry-run", action="store_true", help="do not write output")
    args = parser.parse_args()

    bib_text = args.bib.read_text(encoding="utf-8")
    entries = parse_bib_entries(bib_text)
    aliases = load_team_aliases(TEAM_DIR)
    existing = load_existing(args.csv)

    rows: list[dict[str, str]] = []
    missing_core = 0
    seen_ids: set[str] = set()
    ext_author_tokens = 0

    for entry_type, _key, fields in entries:
        row = convert_entry(entry_type, fields, aliases)
        if row is None:
            missing_core += 1
            continue

        # Preserve curation from old CSV when the paper matches.
        k = row_key(row["year"], row["title"])
        prev = existing.get(k)
        if prev:
            if prev.get("id"):
                row["id"] = prev["id"]
            row["research_areas"] = prev.get("research_areas", "") or ""
            row["featured"] = prev.get("featured", "0") or "0"
            if not row["venue"] and prev.get("venue"):
                row["venue"] = prev["venue"]

        # Keep IDs unique.
        base = row["id"]
        suffix = 2
        while row["id"] in seen_ids:
            row["id"] = f"{base}-{suffix}"
            suffix += 1
        seen_ids.add(row["id"])

        ext_author_tokens += sum(1 for a in row["authors"].split("|") if a.startswith("ext:"))
        rows.append(row)

    rows.sort(key=lambda r: (-parse_year_for_sort(r["year"]), r["title"].lower()))

    print(
        f"entries={len(entries)} rows={len(rows)} skipped_missing_title_or_year={missing_core} "
        f"ext_author_tokens={ext_author_tokens}"
    )

    if args.dry_run:
        print("[dry-run] no files written")
        if rows:
            print("first_row_example:", rows[0]["id"], rows[0]["title"][:80])
        return 0

    with args.csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})

    print(f"wrote {args.csv.relative_to(SITE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

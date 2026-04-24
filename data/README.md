# `data/` — structured data loaded by the site

Hugo reads anything under this directory at build time. Templates access it as
`.Site.Data.<filename-without-extension>`, e.g. `getCSV` on `papers.csv`.

## `papers.csv`

The single source of truth for publications. One row = one paper.
Each paper can belong to multiple research areas and list any mix of team
members and external authors.

**Columns (RFC-4180 CSV — quote fields that contain commas):**

| column | meaning | example |
| --- | --- | --- |
| `id` | stable slug used for anchor links and dedup | `2021-wot-micro-servient` |
| `title` | full paper title, quote if it contains commas | `"WoT Micro Servient: Bringing the W3C Web of Things…"` |
| `authors` | pipe-separated. Use the **team-member slug** (as in `content/team/<slug>.md`) for group members; prefix externals with `ext:` | `luca-sciullo\|ext:Luca Bedogni\|marco-di-felice` |
| `year` | publication year | `2021` |
| `venue` | short venue name | `IEEE SMARTCOMP` |
| `type` | one of `journal`, `conference`, `workshop`, `book`, `chapter`, `editorship`, `preprint`, `other` | `conference` |
| `doi` | DOI or full DOI URL | `https://doi.org/10.1109/...` |
| `url` | optional alternative paper URL (arXiv, publisher page) | |
| `research_areas` | pipe-separated slugs from `content/research-areas/<slug>.md` | `iot-interoperability\|edge-computing` |
| `featured` | `1` to pin the paper at the top of filtered lists, else `0` | `0` |

**Linking rules at render time:**

- Author slug that matches a file in `content/team/` becomes a link to that
  profile; anything starting with `ext:` renders as plain text (stripping the
  prefix).
- Each `research_areas` slug links to `/research-areas/<slug>/` and controls
  which papers appear on each area page.
- Sorting inside lists: `featured = 1` first, then by `year` descending.

**Editing workflow:**

Edit `papers.csv` in a spreadsheet (Excel / Google Sheets), export as CSV with
comma separator and double-quote text-qualifier, commit. The site picks up
changes on the next build. No individual paper pages are generated — all
listings are dynamic.

**Adding a new research area or team member:**

Add the content file first (`hugo new research-areas/<slug>.md` or
`hugo new team/<slug>.md`), then reference the slug in `papers.csv`.

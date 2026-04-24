+++
# ----- identity -------------------------------------------------------------
title   = "{{ replace .Name "-" " " | title }}"
acronym = ""                       # optional short name, rendered over the title
slug    = "{{ .Name }}"

# Ordering inside the status group on the list page (lower = earlier)
weight = 999

# One-line summary for cards and meta descriptions
summary = ""

# ----- status & dates -------------------------------------------------------
# status: "active" | "completed" | "upcoming"
status = "active"
start  = ""                        # "2024" or "2024-03"
end    = ""                        # "2026" or "2026-12"

# ----- funding / admin ------------------------------------------------------
funder       = ""                  # e.g. "European Commission — Horizon Europe"
programme    = ""                  # e.g. "HORIZON-CL4-2023-DIGITAL-EMERGING-01-11"
grant_number = ""
budget       = ""                  # e.g. "EUR 4.2M"
role         = ""                  # "Coordinator" | "Partner" | "WP Leader"

# ----- assets (paths under /static) ----------------------------------------
icon  = ""                         # square icon/logo for cards
cover = ""                         # wide banner for the single page

# ----- external URLs (any may be omitted) ----------------------------------
website  = ""
github   = []                      # array — projects can have many repos
cordis   = ""
linkedin = ""
twitter  = ""

# ----- taxonomy -------------------------------------------------------------
# Linked to /research-areas/<slug>/
research_areas = []

# Free-form keywords
tags = []

# ----- people ---------------------------------------------------------------
# Team-member slugs (order preserved on the page)
people = []
pi     = ""                        # team slug of the PRISM-side PI, if any

# ----- publications ---------------------------------------------------------
# Paper IDs from data/papers.csv that are outputs of this project
publications = []

# ----- partners -------------------------------------------------------------
# Each [[partners]] block adds a logo tile on the project landing page.
# Logos live under /static/images/projects/partners/ and can be .svg or .png.
# [[partners]]
#   name    = "University of Bologna"
#   url     = "https://www.unibo.it/"
#   logo    = "/images/projects/partners/unibo.svg"
#   role    = "Coordinator"
#   country = "Italy"
+++

Describe the project here — objectives, approach, results, any call-outs.
Markdown and raw HTML are both allowed.

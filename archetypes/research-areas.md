+++
title = "{{ replace .Name "-" " " | title }}"
slug  = "{{ .Name }}"

# lower weight = shown first on the research-areas grid
weight = 999

# one-line summary rendered on the research-areas grid
summary = ""

# optional illustration, relative to /static (e.g. /images/research-areas/foo.jpg)
image = ""

[meta]
  # short typographic marker rendered on the card (keep 6 chars or fewer)
  tag = ""
+++

Body of the research area — one or two paragraphs describing the focus and
typical questions the lab investigates. Markdown and HTML are both allowed.

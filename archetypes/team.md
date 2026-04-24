+++
# --- identity ---------------------------------------------------------------
title = "{{ replace .Name "-" " " | title }}"
slug  = "{{ .Name }}"

# --- ordering ---------------------------------------------------------------
# lower weight = shown first inside the role group on the team listing
weight = 999

# --- role / affiliation -----------------------------------------------------
# role must match one of the labels below to appear on the team listing
# in the expected seniority order:
#   "Full Professor", "Associate Professor", "Assistant Professor",
#   "Junior Assistant Professor", "Postdoctoral Researcher",
#   "Research Fellow", "PhD Candidate", "Visiting Researcher", "Collaborator"
role        = ""
position    = ""
affiliation = "Department of Computer Science and Engineering, University of Bologna"

# --- research interests -----------------------------------------------------
research_interests = []

# --- photo ------------------------------------------------------------------
# path is relative to /static; falls back to initials if empty
photo = ""

# --- profile & identifiers --------------------------------------------------
orcid = ""  # 0000-0000-0000-0000 (digits only, no URL)

[links]
  email    = ""
  website  = ""
  scholar  = ""
  linkedin = ""
  github   = ""
+++

Short bio goes here.

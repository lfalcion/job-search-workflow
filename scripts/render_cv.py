#!/usr/bin/env python3
"""Render an ATS-safe CV PDF from a JSON spec. Agents write data, not code.

Usage:
  python3 scripts/render_cv.py cv.json            # writes output/<spec.output>
  python3 scripts/render_cv.py cv.json --strict   # exit 1 if over max_pages

Spec (all sections optional except name/contact; sections render in the order given):
{
  "name": "Alex Example",
  "headline": "Senior Programme Manager",                 # optional one-liner under the name
  "contact": "Amsterdam, NL | +31 6 0000 0000 | alex@example.com | linkedin.com/in/alex-example",
  "summary": "3-5 lines. Plain prose.",
  "sections": [
    {"type": "experience", "title": "Professional Experience",
     "items": [{"title": "Senior Programme Manager", "company_line": "Northwind Logistics | Rotterdam | 2022 - Present",
                "bullets": ["Outcome-first bullet with a number", "..."]}]},
    {"type": "skills", "title": "Skills", "rows": [{"label": "Delivery", "content": "A | B | C"}]},
    {"type": "lines", "title": "Education & Certifications", "lines": ["MSc ... | 2015", "PRINCE2 Practitioner | 2019"]},
    {"type": "bullets", "title": "Selected Projects", "bullets": ["..."]},
    {"type": "text", "title": "Profile note", "text": "A paragraph."}
  ],
  "output": "Alex Example - CV - Acme Group - Programme Manager.pdf",
  "max_pages": 2
}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_pdf import (body, bullet, finish, header_block, job_title, lines_section,  # noqa: E402
                    make_pdf, section_heading, skill_row)

REQUIRED = ("name", "contact")


def render(spec: dict) -> tuple[str, int]:
    missing = [k for k in REQUIRED if not spec.get(k)]
    if missing:
        raise SystemExit(f"spec missing required keys: {missing}")
    pdf = make_pdf()
    header_block(pdf, spec["name"], spec["contact"], spec.get("headline"))
    if spec.get("summary"):
        section_heading(pdf, spec.get("summary_title", "Professional Summary"))
        body(pdf, spec["summary"])
    for sec in spec.get("sections", []):
        kind = sec.get("type")
        title = sec.get("title", kind.title() if kind else "")
        if kind == "experience":
            section_heading(pdf, title)
            for item in sec.get("items", []):
                job_title(pdf, item["title"], item.get("company_line", ""))
                for b in item.get("bullets", []):
                    bullet(pdf, b)
                pdf.ln(1.5)
        elif kind == "skills":
            section_heading(pdf, title)
            for row in sec.get("rows", []):
                skill_row(pdf, row["label"], row["content"])
        elif kind == "lines":
            lines_section(pdf, title, sec.get("lines", []))
        elif kind == "bullets":
            section_heading(pdf, title)
            for b in sec.get("bullets", []):
                bullet(pdf, b)
        elif kind == "text":
            section_heading(pdf, title)
            body(pdf, sec.get("text", ""))
        else:
            raise SystemExit(f"unknown section type: {kind!r} (use experience|skills|lines|bullets|text)")
    filename = spec.get("output") or f"{spec['name']} - CV.pdf"
    out = finish(pdf, filename, max_pages=int(spec.get("max_pages", 2)))
    return out, pdf.page_no()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="path to the JSON spec")
    ap.add_argument("--strict", action="store_true", help="exit 1 if the PDF exceeds max_pages")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    out, pages = render(spec)
    if a.strict and pages > int(spec.get("max_pages", 2)):
        sys.exit(1)


if __name__ == "__main__":
    main()

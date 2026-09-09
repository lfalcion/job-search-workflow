"""Shared fpdf2 helpers for ATS-safe CV rendering. Used by render_cv.py; import-safe for custom scripts.

Battle-tested rules (do not change without reason):
- Every multi_cell call passes new_x/new_y explicitly (fpdf2 cursor drift otherwise).
- W(pdf) is a function so it recomputes after page breaks.
- clean() is applied to every rendered string (core Helvetica has no smart quotes/dashes/bullets).
- Single column, standard fonts, no tables/text boxes/icons: that is what makes it ATS-safe.
- Target: max 2 pages. If over, reduce pdf.ln() spacings or cut content (never shrink below 9pt).

Nothing personal lives in this file. Names, contact lines, education and certifications are all passed in.
"""
from __future__ import annotations

import os

from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUTPUT_DIR = "output"
BODY_PT = 9
LINE_H = 4.5


def clean(text: str) -> str:
    """Replace characters that core PDF fonts cannot render."""
    replacements = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
                    "•": "-", "·": "-", "…": "...", " ": " "}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def make_pdf() -> FPDF:
    class CV(FPDF):
        def header(self):  # no running header
            pass

        def footer(self):  # no running footer
            pass

    pdf = CV(format="A4")
    pdf.set_margins(20, 18, 20)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    return pdf


def W(pdf: FPDF) -> float:
    """Usable width; recomputed on every call."""
    return pdf.w - pdf.l_margin - pdf.r_margin


def header_block(pdf: FPDF, name: str, contact_line: str, headline: str | None = None) -> None:
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(W(pdf), 8, clean(name), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if headline:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(W(pdf), 5, clean(headline), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", BODY_PT)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(W(pdf), 5, clean(contact_line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def section_heading(pdf: FPDF, title: str) -> None:
    w = W(pdf)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(w, 6, clean(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(160, 160, 160)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + w, pdf.get_y())
    pdf.ln(2)


def job_title(pdf: FPDF, title: str, company_line: str) -> None:
    w = W(pdf)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w, 5, clean(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "I", BODY_PT)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(w, 4, clean(company_line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(0.5)


def bullet(pdf: FPDF, text: str) -> None:
    w = W(pdf)
    pdf.set_font("Helvetica", "", BODY_PT)
    pdf.set_xy(pdf.l_margin + 3, pdf.get_y())
    pdf.cell(4, LINE_H, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.multi_cell(w - 7, LINE_H, clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def body(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "", BODY_PT)
    pdf.multi_cell(W(pdf), LINE_H, clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def plain_line(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "", BODY_PT)
    pdf.multi_cell(W(pdf), 4.8, clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def skill_row(pdf: FPDF, label: str, content: str) -> None:
    """Label on its own line, then the content: reads cleanly for ATS parsers."""
    w = W(pdf)
    pdf.set_font("Helvetica", "B", BODY_PT)
    pdf.cell(w, LINE_H, clean(label), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", BODY_PT)
    pdf.multi_cell(w, LINE_H, clean(content), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def lines_section(pdf: FPDF, title: str, lines: list[str]) -> None:
    """Generic titled block of plain lines (education, certifications, languages, publications...)."""
    section_heading(pdf, title)
    for line in lines:
        plain_line(pdf, line)


def finish(pdf: FPDF, filename: str, max_pages: int = 2) -> str:
    """Write the PDF into output/ and report page count. Filename only, no path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, os.path.basename(filename))
    pdf.output(out)
    print(f"pages: {pdf.page_no()}")
    print(f"written: {out}")
    if pdf.page_no() > max_pages:
        print(f"WARNING: over {max_pages} pages - cut bullets or reduce spacing and regenerate")
    return out

# The CV workflow, in prose

## Why one master file
A tailored CV is a *selection* from a complete inventory, not a rewrite. `master.md` holds every role, bullet, metric and credential you could ever use. The agent never edits it during tailoring; it chooses. That keeps every CV you send consistent with every other one and with LinkedIn, and makes "did I ever claim that?" a one-file question.

## The seven steps the agent runs
1. **Parse the JD** into hard requirements, preferred skills, domain, tools, seniority, location/eligibility, stated pay.
2. **Strategic flags before any score.** Hard gates from `profile.md` (right to work, language, pay below anchor, relocation, on-site pattern, deadlines) can kill a role that would otherwise score 90. Seniority mismatch and title-track implications (e.g. a "product owner" role for a product manager, or a "PMO analyst" role for a programme manager) are named plainly. The tracker is checked for prior contact with the company.
3. **Score 0–100** with fixed weights: keyword/terminology alignment 30 · experience overlap 30 · tools/domain fit 15 · seniority alignment 10 · ATS readability 10 · outcomes evidence 5. Two numbers: before and after tailoring. Known-fit and known-miss patterns from `profile.md` calibrate it.
4. **Gate at 72** (change it in `profile.md`). Below or at the gate the agent stops and asks; it does not quietly generate.
5. **Tailor by selection.** Which role leads, which bullets survive, which skill groups appear, in what order. The agent translates the JD's language into common professional language; it never copies distinctive phrases and never mentions the company or role in the CV body. Test: could the hiring manager recognise their own sentences? Then it is mirroring, and it is rewritten.
6. **Render as data.** The agent writes `cv.json` (schema in `scripts/render_cv.py`) and runs the renderer. Layout rules live in `scripts/cv_pdf.py`: single column, Helvetica, standard section names, no tables or graphics, two pages maximum. Agents write data, not code, so the output is the same regardless of which agent produced it.
7. **Verify against master.** Every employer, title, date and metric identical; no skill that isn't in `master.md`; rephrasing allowed, upgraded claims not.

Then: a tracker row and a commit named for the company, role and score.

## Judgement calls the profile controls
- Comp anchors per market, and the standing rules about never disclosing current salary and quoting base, not total.
- Which role types have converted before and which reliably fail (the agent will still tell you the truth about a role you like).
- Honest gaps, so the agent names them instead of hiding them behind vocabulary.

## What "any profession" means here
Nothing in the mechanics assumes a job family. Section names, skill groups, and the shape of experience bullets all come from `master.md`. The example persona is a programme manager; the author used the same files for product management. A nurse, a lawyer or a data engineer changes `master.md` and `profile.md`, nothing else.

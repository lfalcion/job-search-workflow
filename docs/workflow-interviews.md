# The interview workflow, in prose

## Why record
Memory of your own interviews is unreliable in a specific direction: you remember the content you meant to deliver, not the words you said. A transcript shows the disclaimer you opened with, the salary figure you volunteered, the question you didn't ask. Two or three reviews in, patterns appear that no single debrief would show.

Record with consent where the law requires it (many jurisdictions require at least one-party consent, some require all parties). Keep the audio off git; the pipeline already does.

## Getting a transcript
`scripts/interview.py import <recording> --company X --role Y --stage Z` converts the audio with ffmpeg, transcribes it locally with whisper.cpp (nothing leaves your machine), and writes `interviews/transcripts/<date>_<company>_<stage>.md` with a header block the agent relies on: company, role, stage, date, duration, JD path, and a note that speakers are unlabelled. A `.txt` transcript from any other tool can be imported the same way. The optional `--backend scriba` shells out to the scriba CLI if you already use it.

Stages: `recruiter-screen` · `hiring-manager` · `panel` · `case` · `final` · `other`. The stage changes what the review judges against.

## What the review contains
1. **Verdict line**: overall 1–5 and whether the round would have advanced you, in one sentence.
2. **Scorecard**, each dimension scored 1–5 with a verbatim quote as evidence: answer structure · specificity and evidence · concision and verbal tics · listening (did you answer the question asked) · judgement · collaboration and leadership signals · questions you asked · close and next steps.
3. **Per-question table**: the question, what you said in ≤ 20 words, a verdict, and a better answer of 60–120 words in the first person built only from facts in `master.md` and the evidence bank. If the honest answer is weak, the review says so and shows the honest framing.
4. **Top 3 fixes**, each with a one-sentence drill, and one thing to keep doing.
5. **Recurring patterns** once two or more reviews exist, maintained in `interviews/reviews/patterns.md`.
6. **Follow-up note** when the stage warrants one.
7. **Open facts** for the tracker: comp band, process, timeline, names.

## Things the review is instructed to catch
- Deficit-first disclosures ("I'm not the most experienced…") before anyone asked.
- Salary handling against your standing rules: current salary disclosed, "total" instead of base, a floor named, a range accepted without positioning.
- Motivation expressed as complaint about a current or past employer.
- Intros longer than two minutes or told chronologically from the start of your career.
- Stories without numbers when the numbers exist in `master.md`.
- No questions asked; no explicit close.

## After the review
The agent updates the company's tracker rows (status, next step, comp signal) and commits. Read the top three fixes before the next round; rehearse the intro and the salary line until they are automatic.

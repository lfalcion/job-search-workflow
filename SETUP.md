# SETUP — from nothing to a tailored CV and a reviewed interview

**Shortcut:** create your private copy (step 1), open it in your agent, type `setup`. The agent performs steps 2–6 with you. The rest of this page is the manual route and the reference for what the agent does.

Commands are shown for macOS/Linux (`python3`) with the Windows PowerShell form where it differs (`python`, backslashes). Budget: 30 minutes plus the time to write your master CV.

## 0. Prerequisites
- A GitHub account, `git`, and Python 3.9+ (`python3 --version`; Windows: `python --version`, install from python.org or the Microsoft Store and tick *Add to PATH*).
- An agent that can read files and run commands in a folder: Claude Code (desktop app for macOS/Windows, `npm i -g @anthropic-ai/claude-code` or `winget install Anthropic.ClaudeCode`, the web app, or the IDE extension), or another agent that follows `AGENTS.md`.
- Optional, for transcribing recordings locally: nothing else — `setup_check.py --install` fetches ffmpeg and whisper.cpp for your OS (Homebrew on macOS, winget + prebuilt binary on Windows, prebuilt binary on Linux).

## 1. Create your private copy
On GitHub, open this repo → **Use this template** → **Create a new repository** → name it, set **Private**. Then:
```bash
git clone git@github.com:<you>/<your-repo>.git
cd <your-repo>
python3 scripts/setup_check.py
```
Do not fork publicly: your `master.md`, tracker and transcripts will live here.

## 2. Install tooling
Required only:
```bash
python3 -m pip install fpdf2
```
Everything, including local transcription (downloads a ~1.6 GB Whisper model to `~/.cache/whisper-cpp/`):
```bash
python3 scripts/setup_check.py --install            # Windows: python scripts\setup_check.py --install
# smaller/faster model instead:  python3 scripts/setup_check.py --install --model medium
```
- macOS: uses Homebrew for ffmpeg and whisper.cpp.
- Windows: installs ffmpeg with winget (open a new terminal afterwards) and unpacks the prebuilt `whisper-cli.exe` into `~/.cache/whisper-cpp/bin`.
- Linux: prints the package-manager command for ffmpeg (needs sudo) and unpacks the prebuilt whisper.cpp binary (Ubuntu x64/arm64 builds; other distros may need to build from source).

## 3. Prove the pipeline with the example persona
```bash
python3 scripts/render_cv.py examples/cv.example.json          # → output/Alex Example - CV - Acme Group - Programme Manager.pdf, 1 page
python3 scripts/interview.py import examples/interviews/example-transcript.txt \
    --company "Acme Group" --role "Programme Manager" --stage hiring-manager --date 2026-09-01
```
Open the PDF. Read `interviews/transcripts/2026-09-01_acme-group_hiring-manager.md` and compare with the sample review in `examples/interviews/`. Then delete the example transcript from `interviews/transcripts/` so it doesn't mix with your own.

## 4. Fill in your two personal files
```bash
cp examples/profile.example.md profile.md
cp examples/master.example.md master.md
```
- `profile.md`: target titles (any profession), locations and right to work, **base-salary anchors per market**, hard gates, known-fit/known-miss patterns, the evidence bank (true numbers only), honest gaps, LinkedIn titles verbatim. The agent applies these rules on every run; vague entries produce vague CVs.
- `master.md`: every role, every bullet you might ever want, every metric, skill and credential. Outcome-first bullets with numbers. This file is never edited during tailoring.
- `tracker.md`: leave the template; the agent fills it.

Commit: `git add profile.md master.md && git commit -m "Profile and master CV"`.

## 5. First tailored CV
Save a job description as `jds/<company>-<role>.md` (any text; the example in `examples/jds/` shows a useful header). Open your agent in the repo root and type:
```
tailor cv jds/<company>-<role>.md
```
Expected: strategic flags (gates, comp vs anchors, seniority), an initial → final fit score, a stop-and-ask if the score is at or below your gate, otherwise a PDF in `output/`, a tracker row, and a commit. Read the PDF against `master.md` once yourself the first time.

## 6. First interview review
Record the call on your phone (Voice Memos, or any recorder). Get the file onto your machine:
- macOS: AirDrop or Save to Files → drop it into `interviews/inbox/`. If you enable iCloud sync for Voice Memos and grant your terminal Full Disk Access, `list` finds them automatically.
- Windows/Linux/any phone: copy the file into `interviews/inbox/` (USB, cloud drive, email to yourself). A pasted `.txt` transcript works too.
```bash
python3 scripts/interview.py list
python3 scripts/interview.py import 1 --company "<Company>" --role "<Role>" --stage recruiter-screen
```
Then in your agent:
```
review interview interviews/transcripts/<date>_<company>_<stage>.md
```
Expected: `interviews/reviews/<same name>.md` with a scorecard, per-question better answers built only from your real facts, top 3 fixes, tracker updated, commit made. After two reviews the agent starts `interviews/reviews/patterns.md`.

## 7. Running it from your phone
Open a Claude Code web session on your private repo, paste a JD, type the same phrases. The PDF is committed to `output/`; download it from the GitHub app → share sheet → job portal. Transcription still happens on your computer (step 6), reviews can run from anywhere.

## 8. Keeping it healthy
- `python3 scripts/setup_check.py` whenever something feels off.
- Update `profile.md` when your anchors or targets change (`update profile: …` in the agent).
- Fix a mislabelled transcript: `python3 scripts/interview.py relabel interviews/transcripts/<file>.md --company X --role Y --stage Z --date YYYY-MM-DD`.
- Never commit audio. `.gitignore` already blocks it.

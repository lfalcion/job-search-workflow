# job-search-workflow

A job-search operating system you run with an AI agent: one source-of-truth CV, a per-role tailored ATS-safe PDF in minutes, a tracker that never forgets a company, and recorded interviews turned into transcripts and honest coaching reviews. Works for any profession — the example persona is a programme manager; the author used it for product roles.

Everything is plain markdown, JSON and two small Python scripts. No database, no service, no account beyond the agent you already use. Your data stays in **your private copy**; this public repo holds only the process and a synthetic example.

```
paste a JD  ──►  agent scores fit, flags gates, tailors by selection  ──►  output/<You> - CV - <Company> - <Role>.pdf + tracker row
record call ──►  scripts/interview.py (local whisper.cpp)  ──►  interviews/transcripts/*.md  ──►  agent review + patterns + tracker
```

## Fastest path: let your agent set you up (no terminal skills needed)
1. **Install an agent** if you don't have one: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (macOS, Windows, Linux; desktop app, terminal, or in your IDE). Any agent that reads `AGENTS.md` also works.
2. **Make your private copy of this repo:** on this page click **Use this template → Create a new repository**, choose **Private**, then open that repository in your agent (Claude Code: *Open folder* / `claude` in the cloned folder; the web app can open the GitHub repo directly).
3. **Type one word:** `setup`

The agent checks your computer, installs what is missing after asking you, turns your existing CV into the master file, asks you a handful of questions to build your profile, renders a test PDF, and tells you the two phrases you will use from then on: `tailor cv …` and `review interview …`. Ten to twenty minutes, mostly answering questions about yourself.

## Manual quickstart (if you prefer the terminal)
macOS, Windows (PowerShell) and Linux. Use `python` instead of `python3` on Windows.
1. Create your private copy (*Use this template* → **Private**) and clone it.
2. `python3 scripts/setup_check.py --install` — installs `fpdf2`; and, if you want local transcription, `ffmpeg`, `whisper.cpp` (Homebrew on macOS, winget + prebuilt binary on Windows, prebuilt binary on Linux) and a ~1.6 GB speech model. Only `fpdf2` is required.
3. Copy `examples/profile.example.md` → `profile.md` and `examples/master.example.md` → `master.md`, then replace every line with your own facts. `master.md` is your complete inventory; tailoring is subtraction.
4. `python3 scripts/render_cv.py examples/cv.example.json` renders the sample CV into `output/`.
5. Open your agent in the repo root and type `tailor cv jds/<company>-<role>.md` (after saving a JD there, or just paste one), or `review interview interviews/transcripts/<file>.md` after `python3 scripts/interview.py import <recording> --company X --role "Y" --stage hiring-manager`.

Full walkthrough: [`SETUP.md`](SETUP.md). The method itself: [`docs/workflow-cv.md`](docs/workflow-cv.md) and [`docs/workflow-interviews.md`](docs/workflow-interviews.md). Using it from a phone: [`docs/agent-guide.md`](docs/agent-guide.md).

## What is in the box
| Path | What it is |
|---|---|
| `CLAUDE.md` / `AGENTS.md` | The agent's operating instructions (identical files). Generic; every personal rule is read from `profile.md`. |
| `profile.md` | Your targets, comp anchors, hard gates, evidence bank, honest gaps, standing rules. Template. |
| `master.md` | Your source-of-truth CV. Never edited during tailoring. Template. |
| `tracker.md` | Applications + interview pipeline. Template. |
| `jds/` | One markdown file per job description. |
| `scripts/render_cv.py` | Renders an ATS-safe PDF from a JSON spec the agent writes. `scripts/cv_pdf.py` holds the layout rules. |
| `scripts/interview.py` | `list` / `import` / `relabel` recordings → LLM-ready transcripts. Local whisper.cpp by default; optional [scriba](https://github.com/giovannialberto/scriba) backend; accepts pasted `.txt` transcripts. |
| `scripts/setup_check.py` | One command that tells you what is missing and installs it (macOS, Windows, Linux). |
| `interviews/` | `inbox/` (drop recordings), `transcripts/`, `reviews/`. |
| `examples/` | Synthetic persona "Alex Example": profile, master CV, JD, CV spec + rendered PDF, interview transcript + review. |
| `docs/` | Method, agent guide, privacy notes. |

## Design principles
- **Tailor by selection, never by mirroring.** The agent chooses which experiences lead and which bullets exist; it never echoes JD phrases. A CV should read as if it happens to fit.
- **Honesty is enforced, not assumed.** Numbers may only come from `master.md` and the evidence bank. The agent names gaps instead of papering over them, in CVs and in interview coaching.
- **Gates before scores.** Right to work, language, salary, relocation and on-site rules are checked before any fit score is computed. A score gate (default 72) stops low-fit applications unless you overrule.
- **Humans and agents read the same files.** No hidden state. Every rule lives in `profile.md`/`CLAUDE.md`; every script has `--help`.
- **Private by default.** Audio never enters git. Transcripts and reviews do, in your private copy only. See [`docs/privacy.md`](docs/privacy.md).

## Requirements
| | macOS | Windows | Linux |
|---|---|---|---|
| Python 3.9+ and `fpdf2` (required) | python.org or Homebrew | python.org or Microsoft Store | distro package |
| `ffmpeg` (optional, transcription) | `brew install ffmpeg` | `winget install Gyan.FFmpeg` | `apt install ffmpeg` |
| `whisper.cpp` + model (optional, transcription) | `brew install whisper-cpp` | prebuilt binary, fetched by `setup_check.py --install` | prebuilt binary (x64/arm64), fetched by `setup_check.py --install` |
| An agent | Claude Code (desktop, terminal, IDE, or web on your phone) or any agent that reads `AGENTS.md` | same | same |

`setup_check.py --install` does all of this for you, and the `setup` phrase makes your agent run it.

## Companion tooling
Job discovery/scoring across career pages is a separate concern and not included here; this repo starts once you have a JD in hand.

## Licence
MIT. Fork it, change it, ship it. If you improve the method, a PR to this template is welcome.

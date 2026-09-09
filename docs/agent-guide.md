# Agent guide — exact phrases, what happens, where things land

Works with Claude Code (CLI, IDE extension, or web session on your phone) and with any agent that reads `AGENTS.md`. Always start the agent in the repo root.

| You type | The agent reads | The agent writes | Commit message |
|---|---|---|---|
| `setup` (first run) | `scripts/setup_check.py` output, your pasted CV, your answers | installs tooling with your OK · `master.md` · `profile.md` · optionally your private GitHub repo | `Profile and master CV` |
| `tailor cv examples/jds/acme-group-programme-manager.md` (or paste a JD) | `profile.md`, `master.md`, `tracker.md`, the JD | `jds/<company>-<role>.md` if new · `output/<You> - CV - <Company> - <Role>.pdf` · tracker row | `Add CV: <Company> - <Role> (<score>)` or `Skip: <Company> (<score>, <reason>)` |
| `review interview interviews/transcripts/<file>.md` | transcript, its JD, `master.md`, `profile.md`, earlier reviews | `interviews/reviews/<same stem>.md` · `interviews/reviews/patterns.md` (≥ 2 reviews) · tracker rows | `Interview review: <Company> - <stage>` |
| `list interviews` | — | runs `scripts/interview.py list` | — |
| `status` | `tracker.md` | ≤ 10-line summary | — |
| `update profile: <change>` | `profile.md` | proposes a diff, applies on your OK | `Profile: <what changed>` |

## What a good tailoring answer looks like
Three parts, nothing else: strategic flags and the score (initial → final), one paragraph of tailoring moves and residual gaps, the PDF path. If the score is at or below your gate, the agent stops with the analysis and asks. If a hard gate fails, it says so first.

## What a good review answer looks like
Overall score and the one-line verdict, the top three fixes, the path of the review file. The full scorecard and per-question table are in the file.

## From a phone
1. Open a Claude Code web session on your private repo.
2. Paste the JD and type `tailor cv`.
3. When the commit lands, open the GitHub app → `output/` → the PDF → share sheet → job portal, or save to files.
Interview transcription needs your computer (audio + whisper.cpp); reviews can run from the phone once the transcript is committed.

## Windows
Everything works in PowerShell: use `python` instead of `python3`. `setup_check.py --install` fetches ffmpeg via winget and a prebuilt `whisper-cli.exe`; open a new terminal after the ffmpeg install. Claude Code has a native Windows build (`winget install Anthropic.ClaudeCode`) and also runs under WSL.

## Other agents
`AGENTS.md` is byte-identical to `CLAUDE.md` after the first line. Point any agent that supports repo instructions at it. The scripts have `--help`; nothing depends on a specific model or vendor.

## When the agent should refuse or stop
- `profile.md` or `master.md` still starts with the `<!-- TEMPLATE` marker.
- A hard gate fails and you haven't explicitly overruled it.
- You ask it to add experience, metrics or credentials that are not in `master.md`.

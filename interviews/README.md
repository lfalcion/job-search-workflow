# interviews/

- `inbox/` — drop recordings (any audio) or `.txt` transcripts here. Git-ignored.
- `transcripts/` — produced by `scripts/interview.py import`. One markdown file per interview with a header block the agent reads.
- `reviews/` — written by the agent (`review interview <transcript>`). `patterns.md` appears after two or more reviews.

```bash
python3 scripts/interview.py list
python3 scripts/interview.py import 1 --company "Acme Group" --role "Programme Manager" --stage hiring-manager
python3 scripts/interview.py relabel interviews/transcripts/<file>.md --company X --role Y --stage Z --date YYYY-MM-DD
```
Stages: recruiter-screen · hiring-manager · panel · case · final · other. Backends: local whisper.cpp (default), `--backend scriba`, or import a `.txt`.

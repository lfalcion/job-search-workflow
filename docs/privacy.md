# Privacy

This template is public. **Your copy must be private.** It will contain your CV, every company you talk to, salary numbers, and verbatim interview transcripts.

## What never enters git
`.gitignore` blocks audio (`*.m4a`, `*.mp3`, `*.wav`, …), `interviews/inbox/`, generated PDFs in `output/` (commit them deliberately if you want phone access) and the local `.processed.json` state.

## What does enter your private repo
`profile.md`, `master.md`, `tracker.md`, JDs, transcripts and reviews. Treat the repo like a diary. Use a private GitHub repo; if you use a web agent session on it, understand that the agent provider processes the content.

## Transcripts
- Recording consent rules differ by jurisdiction. Know yours.
- Transcripts include the interviewer's words. Trim small talk and anything personal about other people before committing (`scripts/interview.py` does not do this for you).
- Whisper runs locally: audio never leaves your machine unless you choose a cloud-backed backend.

## macOS Voice Memos
If you enable iCloud sync for Voice Memos, recordings appear in `~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/`. macOS blocks terminal access to that folder until you grant **Full Disk Access** to your terminal app (System Settings → Privacy & Security). Memos *imported* into Voice Memos lose their original date; pass `--date` when importing.

## Publishing changes back
If you improve the method and want to send a PR to the template, send only changes to scripts, templates, docs and `examples/`. Run a search for your name, employers and companies before pushing anything public.

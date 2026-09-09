#!/usr/bin/env python3
"""Interview pipeline: recording -> transcript -> LLM-ready markdown for the review agent.

Usage (run from the repo root):
  python3 scripts/interview.py list
  python3 scripts/interview.py import <index|audio|transcript.txt|scriba-dir> \
      --company Acme --role "Programme Manager" --stage hiring-manager [--date 2026-09-01] \
      [--backend whisper|scriba] [--model large-v3-turbo|medium|small] [--lang auto|en|nl]
  python3 scripts/interview.py relabel interviews/transcripts/<file>.md --company X --role Y --stage Z --date YYYY-MM-DD

list     shows recordings not yet imported from interviews/inbox/ (and, on macOS, the iCloud Voice Memos folder
         when it is readable).
import   transcribes with the chosen backend (default: whisper.cpp, local and free), or reads a .txt/.md transcript
         as-is, then writes interviews/transcripts/<date>_<company>_<stage>.md with a header block.
relabel  fixes company/role/stage/date on an imported transcript and renames it (useful after batch imports).

Backends
  whisper  needs ffmpeg + whisper-cli (Homebrew: whisper-cpp) + a ggml model in ~/.cache/whisper-cpp/
           (run scripts/setup_check.py --install). Set WHISPER_MODEL=/path/to/ggml-*.bin to override.
  scriba   shells out to `scriba transcribe` (https://github.com/giovannialberto/scriba), uses its own config.

Stdlib only. Nothing leaves your machine unless you choose a cloud-backed backend.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INTERVIEWS = REPO / "interviews"
INBOX = INTERVIEWS / "inbox"
TRANSCRIPTS = INTERVIEWS / "transcripts"
JDS = REPO / "jds"
PROCESSED = INTERVIEWS / ".processed.json"

HOME = Path.home()
MODEL_DIR = Path(os.environ.get("WHISPER_MODEL_DIR", HOME / ".cache" / "whisper-cpp"))
SCRIBA_DIR = Path(os.environ.get("SCRIBA_DIR", HOME / "scriba_recordings"))
VM_RECORDINGS = HOME / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"

AUDIO_EXT = {".m4a", ".mp3", ".wav", ".caf", ".aac", ".mp4", ".ogg", ".flac", ".aiff", ".webm"}
TEXT_EXT = {".txt", ".md"}
STAGES = ["recruiter-screen", "hiring-manager", "panel", "case", "final", "other"]
CORE_DATA_EPOCH = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc)


# ----------------------------------------------------------------------------- helpers
def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "unknown"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_processed() -> list[dict]:
    if PROCESSED.exists():
        try:
            return json.loads(PROCESSED.read_text())
        except json.JSONDecodeError:
            return []
    return []


def save_processed(items: list[dict]) -> None:
    PROCESSED.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n")


def which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def ffprobe_duration(p: Path) -> int | None:
    if not which("ffprobe"):
        return None
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                             capture_output=True, text=True, check=True).stdout.strip()
        return int(float(out))
    except (subprocess.CalledProcessError, ValueError):
        return None


def fmt_duration(sec: int | None) -> str:
    if sec is None:
        return "?"
    m, s = divmod(int(sec), 60)
    return f"{m:d}:{s:02d}"


def ro_connect(db: Path) -> sqlite3.Connection | None:
    try:
        return sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error:
        return None


# ----------------------------------------------------------------------------- sources
def voice_memo_titles() -> dict[str, dict]:
    """macOS Voice Memos titles/dates from CloudRecordings.db, if readable."""
    out: dict[str, dict] = {}
    db = VM_RECORDINGS / "CloudRecordings.db"
    if not db.exists():
        return out
    con = ro_connect(db)
    if con is None:
        return out
    try:
        rows = con.execute("SELECT ZPATH, ZCUSTOMLABEL, ZENCRYPTEDTITLE, ZDATE FROM ZCLOUDRECORDING").fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        con.close()
    for zpath, label, title, zdate in rows:
        if not zpath:
            continue
        if label and re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:]+Z?", label):
            label = None
        when = (CORE_DATA_EPOCH + dt.timedelta(seconds=zdate)).astimezone() if isinstance(zdate, (int, float)) else None
        out[Path(zpath).name] = {"title": label or title or "", "date": when}
    return out


def discover_sources() -> list[dict]:
    items: list[dict] = []
    if sys.platform == "darwin" and VM_RECORDINGS.exists():
        try:
            files = [p for p in VM_RECORDINGS.iterdir() if p.is_file() and p.suffix.lower() == ".m4a"]
        except PermissionError:
            files = []
            print("Voice Memos folder exists but macOS blocks access. Grant Full Disk Access to your terminal "
                  "(System Settings > Privacy & Security), or drop files in interviews/inbox/.", file=sys.stderr)
        titles = voice_memo_titles() if files else {}
        for p in files:
            meta = titles.get(p.name, {})
            items.append({"path": p, "source": "voice-memos", "title": meta.get("title") or p.stem,
                          "date": meta.get("date") or dt.datetime.fromtimestamp(p.stat().st_mtime).astimezone()})
    if INBOX.exists():
        for p in INBOX.iterdir():
            if p.is_file() and (p.suffix.lower() in AUDIO_EXT or p.suffix.lower() in TEXT_EXT):
                items.append({"path": p, "source": "inbox", "title": p.stem,
                              "date": dt.datetime.fromtimestamp(p.stat().st_mtime).astimezone()})
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def unprocessed_sources() -> list[dict]:
    done = {d.get("sha256") for d in load_processed()}
    out = []
    for it in discover_sources():
        it["sha256"] = sha256_file(it["path"])
        if it["sha256"] not in done:
            out.append(it)
    return out


def cmd_list(_: argparse.Namespace) -> None:
    items = unprocessed_sources()
    if not items:
        print(f"No new recordings. Drop audio or .txt transcripts into {INBOX.relative_to(REPO)}/")
        return
    print(f"{'#':>2}  {'date':<16} {'len':>6}  {'source':<11} title")
    for i, it in enumerate(items, 1):
        dur = fmt_duration(ffprobe_duration(it["path"])) if it["path"].suffix.lower() in AUDIO_EXT else "text"
        print(f"{i:>2}  {it['date'].strftime('%Y-%m-%d %H:%M'):<16} {dur:>6}  {it['source']:<11} {it['title']}")
    print('\nNext: python3 scripts/interview.py import <#> --company X --role "Y" --stage <stage>')


# ----------------------------------------------------------------------------- backends
def to_wav16k(audio: Path, tmp: Path) -> Path:
    if not which("ffmpeg"):
        die("ffmpeg not found (brew install ffmpeg)")
    wav = tmp / "audio16k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
                   check=True)
    return wav


def whisper_model_path(model: str) -> Path:
    env = os.environ.get("WHISPER_MODEL")
    if env:
        return Path(env).expanduser()
    return MODEL_DIR / f"ggml-{model}.bin"


def transcribe_whisper(audio: Path, model: str, lang: str) -> tuple[str, str]:
    cli = which("whisper-cli", "whisper-cpp", "whisper")
    if not cli:
        die("whisper-cli not found. Run: python3 scripts/setup_check.py --install")
    mpath = whisper_model_path(model)
    if not mpath.exists():
        die(f"model not found: {mpath}. Run: python3 scripts/setup_check.py --install (or set WHISPER_MODEL)")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        wav = to_wav16k(audio, tmp)
        outbase = tmp / "out"
        # The initial prompt nudges whisper to keep punctuation and capitalisation (it otherwise drops them on some clips).
        cmd = [cli, "-m", str(mpath), "-f", str(wav), "-l", lang, "-otxt", "-of", str(outbase), "-np",
               "--prompt", "Hello. This is a transcript of a conversation, with punctuation and capital letters."]
        print("$", " ".join(cmd[:1] + ["-m", mpath.name, "-f", wav.name, "-l", lang]))
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            die(f"whisper failed:\n{res.stderr[-2000:]}")
        txt = outbase.with_suffix(".txt")
        if not txt.exists():
            die("whisper produced no text output")
        return txt.read_text(encoding="utf-8", errors="replace").strip(), f"whisper.cpp {model}"


def transcribe_scriba(audio: Path, name: str) -> tuple[str, str]:
    if not which("scriba"):
        die("scriba not found (see https://github.com/giovannialberto/scriba)")
    before = {p.name for p in SCRIBA_DIR.iterdir() if p.is_dir()} if SCRIBA_DIR.exists() else set()
    with tempfile.TemporaryDirectory() as td:
        src = audio
        if audio.suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"}:
            src = to_wav16k(audio, Path(td))  # scriba accepts a fixed set of containers; convert the rest
        cmd = ["scriba", "transcribe", "-n", name, str(src)]
        print("$", " ".join(cmd))
        if subprocess.run(cmd).returncode != 0:
            die("scriba transcribe failed")
    after = {p.name for p in SCRIBA_DIR.iterdir() if p.is_dir()}
    new = sorted(after - before)
    d = SCRIBA_DIR / new[-1] if new else max((p for p in SCRIBA_DIR.iterdir() if (p / "transcript.txt").exists()),
                                              key=lambda p: p.stat().st_mtime)
    return (d / "transcript.txt").read_text(encoding="utf-8", errors="replace").strip(), f"scriba ({d.name})"


# ----------------------------------------------------------------------------- transcript
def paragraphs(text: str, target_words: int = 120) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-Ý\"'(\[])", text)
    out, cur, n = [], [], 0
    for s in sentences:
        cur.append(s)
        n += len(s.split())
        if n >= target_words:
            out.append(" ".join(cur))
            cur, n = [], 0
    if cur:
        out.append(" ".join(cur))
    return out


def find_jd(company: str) -> Path | None:
    hits = sorted(JDS.glob(f"{slug(company)}*.md")) if JDS.exists() else []
    return hits[0] if hits else None


def unique_path(base: str) -> Path:
    out = TRANSCRIPTS / f"{base}.md"
    k = 2
    while out.exists():
        out = TRANSCRIPTS / f"{base}-{k}.md"
        k += 1
    return out


def write_transcript(*, text: str, company: str, role: str, stage: str, date: dt.date, duration: int | None,
                     source_desc: str, backend: str, notes: str | None) -> Path:
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    out = unique_path(f"{date.isoformat()}_{slug(company)}_{slug(stage)}")
    jd = find_jd(company)
    lines = [
        "---",
        f"company: {company}",
        f"role: {role}",
        f"stage: {stage}",
        f"date: {date.isoformat()}",
        f"duration: {fmt_duration(duration)}",
        f"words: {len(text.split())}",
        f"source: {source_desc}",
        f"transcription: {backend}",
        f"jd: {jd.relative_to(REPO) if jd else 'none (add jds/' + slug(company) + '-<role>.md)'}",
        "speakers: unlabelled — infer interviewer vs candidate from context; mark uncertain turns",
        f"review: interviews/reviews/{out.stem}.md (to be written by the review agent)",
    ]
    if notes:
        lines.append(f"notes: {notes}")
    lines += ["---", "", f"# {company} — {role} — {stage} ({date.isoformat()})", ""]
    lines += [p + "\n" for p in paragraphs(text)]
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out


# ----------------------------------------------------------------------------- import
def resolve_input(arg: str) -> tuple[str, Path]:
    """Return ("audio"|"text"|"scriba", path)."""
    if arg.isdigit():
        items = unprocessed_sources()
        i = int(arg)
        if not 1 <= i <= len(items):
            die(f"index {i} out of range; run `list` first")
        p = items[i - 1]["path"]
        return ("text" if p.suffix.lower() in TEXT_EXT else "audio"), p
    p = Path(arg).expanduser()
    if p.is_file():
        return ("text" if p.suffix.lower() in TEXT_EXT else "audio"), p.resolve()
    if p.is_dir() and (p / "transcript.txt").exists():
        return "scriba", p.resolve()
    if (SCRIBA_DIR / arg).is_dir():
        return "scriba", SCRIBA_DIR / arg
    die(f"not found: {arg}")
    return "", p


def cmd_import(a: argparse.Namespace) -> None:
    kind, target = resolve_input(a.input)
    date = dt.date.fromisoformat(a.date) if a.date else dt.datetime.fromtimestamp(target.stat().st_mtime).date()
    duration = None
    if kind == "text":
        text, backend = target.read_text(encoding="utf-8", errors="replace").strip(), "provided transcript"
    elif kind == "scriba":
        text, backend = (target / "transcript.txt").read_text(encoding="utf-8", errors="replace").strip(), f"scriba ({target.name})"
        m = re.match(r"(\d{4}-\d{2}-\d{2})", target.name)
        if m and not a.date:
            date = dt.date.fromisoformat(m.group(1))
        audio = next((p for p in target.iterdir() if p.suffix.lower() in AUDIO_EXT), None)
        duration = ffprobe_duration(audio) if audio else None
    else:
        duration = ffprobe_duration(target)
        if a.backend == "scriba":
            text, backend = transcribe_scriba(target, f"{a.company} {a.stage} {date.isoformat()}")
        else:
            text, backend = transcribe_whisper(target, a.model, a.lang)
    if not text:
        die("empty transcript")
    out = write_transcript(text=text, company=a.company, role=a.role, stage=a.stage, date=date, duration=duration,
                           source_desc=str(target), backend=backend, notes=a.notes)
    done = load_processed()
    done.append({"sha256": sha256_file(target) if target.is_file() else None, "source": str(target),
                 "transcript": str(out.relative_to(REPO)), "imported_at": dt.datetime.now().isoformat(timespec="seconds")})
    save_processed(done)
    print(f"\nTranscript: {out.relative_to(REPO)}  ({len(text.split())} words, {fmt_duration(duration)})")
    if not find_jd(a.company):
        print(f"Tip: save the job description as jds/{slug(a.company)}-<role>.md for a sharper review.")
    print(f"Next, in your agent (repo root): review interview {out.relative_to(REPO)}")


# ----------------------------------------------------------------------------- relabel
def cmd_relabel(a: argparse.Namespace) -> None:
    src = Path(a.transcript).expanduser().resolve()
    if not src.is_file():
        die(f"not found: {src}")
    text = src.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        die("transcript has no header block")
    _, header, body = text.split("---\n", 2)
    fields, order = {}, []
    for line in header.splitlines():
        k, _, v = line.partition(": ")
        fields[k] = v
        order.append(k)
    for k in ("company", "role", "stage", "date", "notes"):
        v = getattr(a, k)
        if v:
            if k not in order:
                order.insert(order.index("review") if "review" in order else len(order), k)
            fields[k] = v
    date = dt.date.fromisoformat(fields["date"])
    dst = unique_path(f"{date.isoformat()}_{slug(fields['company'])}_{slug(fields['stage'])}") if True else src
    if dst != src and dst.exists():
        die(f"target exists: {dst}")
    jd = find_jd(fields["company"])
    fields["jd"] = str(jd.relative_to(REPO)) if jd else f"none (add jds/{slug(fields['company'])}-<role>.md)"
    fields["review"] = f"interviews/reviews/{dst.stem}.md (to be written by the review agent)"
    body = re.sub(r"^# .*$", f"# {fields['company']} — {fields['role']} — {fields['stage']} ({date.isoformat()})",
                  body.lstrip("\n"), count=1, flags=re.M)
    dst.write_text("---\n" + "\n".join(f"{k}: {fields[k]}" for k in order) + "\n---\n\n" + body, encoding="utf-8")
    if dst != src:
        src.unlink()
    done = load_processed()
    for d in done:
        if d.get("transcript") == str(src.relative_to(REPO)):
            d["transcript"] = str(dst.relative_to(REPO))
    save_processed(done)
    print(f"{src.name} -> {dst.relative_to(REPO)}")


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show recordings/transcripts not yet imported").set_defaults(fn=cmd_list)
    im = sub.add_parser("import", help="transcribe (or read a .txt) and write an LLM-ready transcript")
    im.add_argument("input", help="list index, audio file, .txt/.md transcript, or scriba recording directory")
    im.add_argument("--company", required=True)
    im.add_argument("--role", required=True)
    im.add_argument("--stage", required=True, choices=STAGES)
    im.add_argument("--date", help="interview date YYYY-MM-DD (default: file date)")
    im.add_argument("--notes", help="free text for the header (interviewer, format, caveats)")
    im.add_argument("--backend", choices=["whisper", "scriba"], default=os.environ.get("TRANSCRIBE_BACKEND", "whisper"))
    im.add_argument("--model", default=os.environ.get("WHISPER_MODEL_NAME", "large-v3-turbo"),
                    help="whisper.cpp model name: large-v3-turbo (default), medium, small, base")
    im.add_argument("--lang", default="auto", help="language code or auto")
    im.set_defaults(fn=cmd_import)
    rl = sub.add_parser("relabel", help="fix company/role/stage/date of an imported transcript and rename it")
    rl.add_argument("transcript")
    rl.add_argument("--company"); rl.add_argument("--role"); rl.add_argument("--stage", choices=STAGES)
    rl.add_argument("--date", help="YYYY-MM-DD"); rl.add_argument("--notes")
    rl.set_defaults(fn=cmd_relabel)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

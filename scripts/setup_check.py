#!/usr/bin/env python3
"""Check (and optionally install) everything this repo needs. Safe to run repeatedly.

  python3 scripts/setup_check.py            # report
  python3 scripts/setup_check.py --install  # pip install fpdf2; brew install ffmpeg whisper-cpp; download the model
  python3 scripts/setup_check.py --model medium --install   # smaller model (~1.5 GB) instead of large-v3-turbo (~1.6 GB)

Required:  python3 >= 3.9, fpdf2 (PDF rendering)
Optional:  ffmpeg + whisper-cli + model  (local transcription; skip if you paste transcripts as .txt)
           scriba (alternative transcription backend), gh (GitHub CLI), claude (Claude Code)
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

MODEL_DIR = Path(os.environ.get("WHISPER_MODEL_DIR", Path.home() / ".cache" / "whisper-cpp"))
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{model}.bin"
MIN_SIZE = {"large-v3-turbo": 1_500_000_000, "medium": 1_400_000_000, "small": 400_000_000, "base": 100_000_000}

OK, MISS, OPT = "OK ", "MISSING", "optional"


def row(status: str, name: str, detail: str) -> None:
    print(f"  [{status:^8}] {name:<14} {detail}")


def sh(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd).returncode


def download(url: str, dest: Path) -> None:
    """Prefer curl (handles redirects, resumes, and system certificates); fall back to urllib."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    print(f"downloading {url}\n        -> {dest}")
    if shutil.which("curl"):
        rc = subprocess.run(["curl", "-L", "--fail", "--progress-bar", "-C", "-", "-o", str(tmp), url]).returncode
        if rc != 0:
            raise RuntimeError(f"curl exited {rc}")
    else:
        try:
            import certifi, ssl  # noqa: F401
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ctx = None
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx)) if ctx else urllib.request.build_opener()
        with opener.open(url) as r, tmp.open("wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
    tmp.rename(dest)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", action="store_true", help="install missing pieces (pip/brew/model download)")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL_NAME", "large-v3-turbo"),
                    choices=list(MIN_SIZE), help="whisper.cpp model to check/download")
    a = ap.parse_args()
    brew = shutil.which("brew")
    problems = 0
    print(f"job-search-workflow setup check — {platform.system()} {platform.machine()}, Python {platform.python_version()}\n")

    # python
    if sys.version_info < (3, 9):
        row(MISS, "python3", f"{platform.python_version()} < 3.9"); problems += 1
    else:
        row(OK, "python3", platform.python_version())

    # fpdf2
    try:
        import fpdf  # noqa: F401
        row(OK, "fpdf2", "importable")
    except ImportError:
        if a.install and sh([sys.executable, "-m", "pip", "install", "-q", "fpdf2"]) == 0:
            row(OK, "fpdf2", "installed")
        else:
            row(MISS, "fpdf2", f"fix: {sys.executable} -m pip install fpdf2"); problems += 1

    # ffmpeg
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        row(OK, "ffmpeg", shutil.which("ffmpeg"))
    elif a.install and brew and sh([brew, "install", "ffmpeg"]) == 0:
        row(OK, "ffmpeg", "installed")
    else:
        row(OPT, "ffmpeg", "needed for audio transcription — fix: brew install ffmpeg (Linux: apt install ffmpeg)")

    # whisper-cli
    cli = shutil.which("whisper-cli") or shutil.which("whisper-cpp")
    if cli:
        row(OK, "whisper-cli", cli)
    elif a.install and brew and sh([brew, "install", "whisper-cpp"]) == 0:
        row(OK, "whisper-cli", "installed")
        cli = shutil.which("whisper-cli")
    else:
        row(OPT, "whisper-cli", "needed for local transcription — fix: brew install whisper-cpp "
                                "(Linux: build https://github.com/ggml-org/whisper.cpp)")

    # model
    mpath = Path(os.environ.get("WHISPER_MODEL", MODEL_DIR / f"ggml-{a.model}.bin"))
    if mpath.exists() and mpath.stat().st_size >= MIN_SIZE[a.model]:
        row(OK, "whisper model", f"{mpath} ({mpath.stat().st_size / 1e9:.2f} GB)")
    elif a.install:
        try:
            download(MODEL_URL.format(model=a.model), mpath)
            row(OK, "whisper model", str(mpath))
        except Exception as e:  # noqa: BLE001
            row(MISS, "whisper model", f"download failed: {e}"); problems += 1
    else:
        row(OPT, "whisper model", f"fix: python3 scripts/setup_check.py --install  (downloads ggml-{a.model}.bin to {MODEL_DIR})")

    # optional tools
    for name, hint in [("scriba", "alternative backend: --backend scriba"),
                       ("gh", "GitHub CLI, for creating your private copy"),
                       ("claude", "Claude Code CLI; the web/IDE apps work too")]:
        p = shutil.which(name)
        row(OK if p else OPT, name, p or hint)

    # repo files
    repo = Path(__file__).resolve().parent.parent
    for f, hint in [("profile.md", "copy examples/profile.example.md and fill it in"),
                    ("master.md", "copy examples/master.example.md and replace with your real CV")]:
        p = repo / f
        filled = p.exists() and "<!-- TEMPLATE" not in p.read_text(errors="replace")[:400]
        row(OK if filled else OPT, f, "filled in" if filled else f"still a template — {hint}")

    print()
    if problems:
        print(f"{problems} required item(s) missing."); sys.exit(1)
    print("Required tooling present. Optional items above are only needed for the features they name.")


if __name__ == "__main__":
    main()

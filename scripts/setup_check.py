#!/usr/bin/env python3
"""Check (and optionally install) everything this repo needs. Works on macOS, Windows and Linux. Safe to run repeatedly.

  python3 scripts/setup_check.py             # report only            (Windows: python scripts/setup_check.py)
  python3 scripts/setup_check.py --install   # install what is missing (pip, ffmpeg, whisper.cpp binary, Whisper model)
  python3 scripts/setup_check.py --install --model medium   # smaller model (~1.5 GB) instead of large-v3-turbo (~1.6 GB)

Required:  Python >= 3.9, fpdf2 (PDF rendering)
Optional:  ffmpeg + whisper-cli + model  (local transcription; skip if you paste transcripts as .txt)
           scriba (alternative transcription backend), gh (GitHub CLI), claude (Claude Code)

How installs happen per OS
  macOS    brew install ffmpeg whisper-cpp
  Windows  winget install Gyan.FFmpeg ; whisper.cpp prebuilt zip from GitHub releases -> ~/.cache/whisper-cpp/bin
  Linux    ffmpeg via your package manager (command printed, needs sudo); whisper.cpp prebuilt tarball (x64/arm64 Ubuntu builds)
"""
from __future__ import annotations

import argparse
import io
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

MODEL_DIR = Path(os.environ.get("WHISPER_MODEL_DIR", Path.home() / ".cache" / "whisper-cpp"))
BIN_DIR = MODEL_DIR / "bin"
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{model}.bin"
RELEASES_API = "https://api.github.com/repos/ggml-org/whisper.cpp/releases/latest"
MIN_SIZE = {"large-v3-turbo": 1_500_000_000, "medium": 1_400_000_000, "small": 400_000_000, "base": 100_000_000}
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
PY_CMD = "python" if IS_WIN else "python3"

OK, MISS, OPT = "OK", "MISSING", "optional"


def row(status: str, name: str, detail: str) -> None:
    print(f"  [{status:^8}] {name:<14} {detail}")


def sh(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd).returncode


def fetch_bytes(url: str) -> bytes:
    if shutil.which("curl"):
        res = subprocess.run(["curl", "-L", "--fail", "-s", url], capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f"curl exited {res.returncode} for {url}")
        return res.stdout
    with urllib.request.urlopen(url) as r:  # noqa: S310
        return r.read()


def download(url: str, dest: Path) -> None:
    """Prefer curl (redirects, resume, system certificates); fall back to urllib."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    print(f"downloading {url}\n        -> {dest}")
    if shutil.which("curl"):
        rc = subprocess.run(["curl", "-L", "--fail", "--progress-bar", "-C", "-", "-o", str(tmp), url]).returncode
        if rc != 0:
            raise RuntimeError(f"curl exited {rc}")
    else:
        with urllib.request.urlopen(url) as r, tmp.open("wb") as f:  # noqa: S310
            shutil.copyfileobj(r, f, 1 << 20)
    tmp.replace(dest)


def find_whisper_cli() -> str | None:
    """whisper-cli on PATH, or a binary we unpacked under ~/.cache/whisper-cpp/bin."""
    for name in ("whisper-cli", "whisper-cpp"):
        p = shutil.which(name)
        if p:
            return p
    if BIN_DIR.exists():
        for p in BIN_DIR.rglob("whisper-cli*"):
            if p.is_file() and (p.suffix.lower() == ".exe" or os.access(p, os.X_OK)):
                return str(p)
    return None


def whisper_release_asset() -> str | None:
    """Pick the prebuilt whisper.cpp asset for this OS/arch, or None if we should build/brew instead."""
    arch = platform.machine().lower()
    if IS_WIN and arch in ("amd64", "x86_64"):
        return "whisper-bin-x64.zip"
    if sys.platform.startswith("linux"):
        return "whisper-bin-ubuntu-arm64.tar.gz" if arch in ("arm64", "aarch64") else "whisper-bin-ubuntu-x64.tar.gz"
    return None


def install_whisper_prebuilt() -> str | None:
    asset = whisper_release_asset()
    if not asset:
        return None
    import json
    rel = json.loads(fetch_bytes(RELEASES_API))
    url = next((a["browser_download_url"] for a in rel["assets"] if a["name"] == asset), None)
    if not url:
        raise RuntimeError(f"asset {asset} not found in whisper.cpp {rel.get('tag_name')}")
    print(f"downloading whisper.cpp {rel.get('tag_name')} ({asset})")
    data = fetch_bytes(url)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    if asset.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(data)).extractall(BIN_DIR)
    else:
        tarfile.open(fileobj=io.BytesIO(data), mode="r:gz").extractall(BIN_DIR)
    for p in BIN_DIR.rglob("*"):
        if p.is_file() and not IS_WIN:
            p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return find_whisper_cli()


def ffmpeg_fix() -> str:
    if IS_MAC:
        return "brew install ffmpeg"
    if IS_WIN:
        return "winget install --id Gyan.FFmpeg -e   (then open a new terminal)"
    return "sudo apt install ffmpeg   (or: sudo dnf install ffmpeg / sudo pacman -S ffmpeg)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", action="store_true", help="install missing pieces (pip / brew / winget / GitHub release / model download)")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL_NAME", "large-v3-turbo"), choices=list(MIN_SIZE),
                    help="whisper.cpp model to check/download")
    a = ap.parse_args()
    brew = shutil.which("brew") if IS_MAC else None
    winget = shutil.which("winget") if IS_WIN else None
    problems = 0
    print(f"job-search-workflow setup check - {platform.system()} {platform.machine()}, Python {platform.python_version()}\n")

    # python
    if sys.version_info < (3, 9):
        row(MISS, "python", f"{platform.python_version()} < 3.9 - install from https://www.python.org/downloads/"); problems += 1
    else:
        row(OK, "python", f"{platform.python_version()}  (run scripts with: {PY_CMD})")

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
    else:
        installed = False
        if a.install and brew:
            installed = sh([brew, "install", "ffmpeg"]) == 0
        elif a.install and winget:
            installed = sh([winget, "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements", "--accept-package-agreements"]) == 0
            if installed:
                print("  note: open a new terminal so ffmpeg is on PATH, then re-run this check")
        row(OK if installed else OPT, "ffmpeg", "installed" if installed else f"needed for audio transcription - fix: {ffmpeg_fix()}")

    # whisper-cli
    cli = find_whisper_cli()
    if cli:
        row(OK, "whisper-cli", cli)
    else:
        if a.install:
            try:
                if brew:
                    if sh([brew, "install", "whisper-cpp"]) == 0:
                        cli = find_whisper_cli()
                else:
                    cli = install_whisper_prebuilt()
            except Exception as e:  # noqa: BLE001
                print(f"  whisper.cpp install failed: {e}")
        if cli:
            row(OK, "whisper-cli", cli)
        else:
            hint = ("brew install whisper-cpp" if IS_MAC else
                    f"{PY_CMD} scripts/setup_check.py --install  (downloads the prebuilt binary to {BIN_DIR})"
                    if whisper_release_asset() else
                    "build https://github.com/ggml-org/whisper.cpp and put whisper-cli on PATH")
            row(OPT, "whisper-cli", f"needed for local transcription - fix: {hint}")

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
        row(OPT, "whisper model", f"fix: {PY_CMD} scripts/setup_check.py --install  (downloads ggml-{a.model}.bin to {MODEL_DIR})")

    # optional tools
    for name, hint in [("scriba", "alternative backend: --backend scriba"),
                       ("gh", "GitHub CLI, lets the agent create your private copy"),
                       ("claude", "Claude Code CLI; the desktop/web/IDE apps work too")]:
        p = shutil.which(name)
        row(OK if p else OPT, name, p or hint)

    # repo files
    repo = Path(__file__).resolve().parent.parent
    for f, hint in [("profile.md", "copy examples/profile.example.md and fill it in (or type `setup` in your agent)"),
                    ("master.md", "copy examples/master.example.md and replace with your real CV (or type `setup`)")]:
        p = repo / f
        filled = p.exists() and "<!-- TEMPLATE" not in p.read_text(errors="replace")[:400]
        row(OK if filled else OPT, f, "filled in" if filled else f"still a template - {hint}")

    print()
    if problems:
        print(f"{problems} required item(s) missing."); sys.exit(1)
    print("Required tooling present. Optional items above are only needed for the features they name.")


if __name__ == "__main__":
    main()

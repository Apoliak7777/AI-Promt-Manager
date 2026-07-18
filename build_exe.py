"""Pohodlný build skript — vygeneruje ikonu a zbuildí .exe cez PyInstaller.

Spusti:  python build_exe.py
Výstup:  dist/AIPromptManager.exe
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _ensure_icon() -> None:
    icon = ROOT / "assets" / "icon.ico"
    if icon.exists():
        return
    print("→ Generujem ikonu…")
    subprocess.run([sys.executable, str(ROOT / "assets" / "make_icon.py")], check=True)


def main() -> int:
    _ensure_icon()
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller nie je nainštalovaný. Spusti: pip install pyinstaller")
        return 1
    print("→ Buildujem .exe…")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "build.spec", "--noconfirm", "--clean"],
        cwd=str(ROOT),
    )
    if result.returncode == 0:
        print("\n✅ Hotovo → dist/AIPromptManager.exe")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

"""Build the frozen desktop application with platform-correct data paths."""
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    separator = os.pathsep
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", "GoldDiamondBrowser",
        "--collect-all", "PySide6",
        "--collect-all", "shiboken6",
        "--collect-all", "memingo",
        "--add-data", f"main.mgo{separator}.",
        "--add-data", f"ecosystem{separator}ecosystem",
        "run.py",
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())

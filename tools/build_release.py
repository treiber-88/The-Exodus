"""Builds a standalone game for the current operating system into dist/.

PyInstaller cannot cross-compile, so each OS must build its own copy.
Needs: pip install -r requirements.txt pyinstaller
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
subprocess.check_call([
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
    "--onefile" if sys.platform != "darwin" else "--onedir",
    "--name", "TheExodus", "--add-data", "assets:assets", "main.py",
], cwd=ROOT)

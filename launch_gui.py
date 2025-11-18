#!/usr/bin/env python3
"""
JellyRancher Studio Launcher

Launches the PyQt6-based `jelly_rancher_studio.py` GUI, preferring the
project virtual environment (.venv) when available.

Usage:
    python launch_gui.py
"""

import sys
import subprocess
from pathlib import Path


def _get_venv_python(project_root: Path) -> Path | None:
    """Return the .venv Python interpreter if it exists, else None."""
    if sys.platform.startswith("win"):
        candidate = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = project_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else None


def main():
    project_root = Path(__file__).parent.resolve()

    # Ensure project root is on sys.path so we can import jelly_rancher_studio
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    venv_python = _get_venv_python(project_root)

    # If we're already running inside the venv, just import and run directly.
    if venv_python is not None and Path(sys.executable).resolve() == venv_python:
        from jelly_rancher_studio import main as gui_main  # type: ignore[import]
        gui_main()
        return

    # If a venv Python exists but we're not using it, re-launch under the venv.
    if venv_python is not None:
        subprocess.call(
            [str(venv_python), str(project_root / "jelly_rancher_studio.py")]
        )
        return

    # Fallback: no venv found, run with current interpreter but warn.
    print(
        "Warning: .venv Python not found. "
        "Running jelly_rancher_studio.py with the current interpreter."
    )
    from jelly_rancher_studio import main as gui_main  # type: ignore[import]
    gui_main()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
JellyRancher - Unified Media Organization Platform GUI Launcher

Launches the professional PyQt5 interface for media organization.

Usage:
    python launch_gui.py

This is the primary entry point for the JellyRancher GUI.
"""

import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent

# Add scripts paths to sys.path
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "scripts" / "core"))
sys.path.insert(0, str(project_root / "scripts" / "_common"))
sys.path.insert(0, str(project_root / "scripts" / "core" / "tools" / "ravenmaven"))
sys.path.insert(0, str(project_root / "scripts" / "core" / "tools" / "code_cop" / "tools" / "audit"))

# Launch the UI
if __name__ == "__main__":
    try:
        from scripts.core.jelly_rancher_main import main
        main()
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Please ensure PyQt5 is installed: pip install PyQt5")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)
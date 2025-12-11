#!/usr/bin/env python3
"""
Quick dialog screenshot capture - NO TESTS, NO BROWSER LINKS.
Just opens each dialog/window, takes a screenshot, closes it.
"""

import sys
import os
from pathlib import Path

# Set encoding to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Set up paths FIRST
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "core" / "dialogs"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ui"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Suppress any browser/TMDB stuff
os.environ['SUPPRESS_BROWSER'] = '1'

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import time

OUTPUT_DIR = Path(__file__).parent.parent / "dialog_screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

def screenshot_dialog(dialog, name, delay=0.5):
    """Screenshot a dialog without showing browser."""
    try:
        dialog.show()
        app.processEvents()
        time.sleep(delay)

        pixmap = dialog.grab()
        filename = OUTPUT_DIR / f"{name}.png"
        pixmap.save(str(filename))
        print(f"[OK] {name}")

        dialog.close()
        app.processEvents()
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"[FAIL] {name}: {str(e)[:50]}")
        return False

# Create app
app = QApplication(sys.argv)

# Create minimal parent window
parent = QMainWindow()
parent.setWindowTitle("Screenshot Capture")
parent.resize(100, 100)

count = 0
success = 0

try:
    # 1. App Settings Dialog
    try:
        from app_settings_dialog import AppSettingsDialog
        dialog = AppSettingsDialog(parent)
        if screenshot_dialog(dialog, "01_AppSettingsDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] AppSettingsDialog: {e}")
        count += 1

    # 2. Jellyfin Settings Dialog
    try:
        from jellyfin_settings_dialog import JellyfinSettingsDialog
        dialog = JellyfinSettingsDialog(parent)
        if screenshot_dialog(dialog, "02_JellyfinSettingsDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] JellyfinSettingsDialog: {e}")
        count += 1

    # 3. Help System Dialog
    try:
        from help_system import HelpDialog
        dialog = HelpDialog(parent)
        if screenshot_dialog(dialog, "03_HelpDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] HelpDialog: {e}")
        count += 1

    # 4. JellyRancher Help Dialog
    try:
        from jelly_rancher_help import JellyRancherHelpDialog
        dialog = JellyRancherHelpDialog(parent)
        if screenshot_dialog(dialog, "04_JellyRancherHelpDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] JellyRancherHelpDialog: {e}")
        count += 1

    # 5. Welcome Wizard
    try:
        from getting_started_wizard import WelcomeWizard
        dialog = WelcomeWizard(parent)
        if screenshot_dialog(dialog, "05_WelcomeWizard"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] WelcomeWizard: {e}")
        count += 1

    # 6. Quick Start Dialog
    try:
        from getting_started_wizard import QuickStartDialog
        dialog = QuickStartDialog(parent)
        if screenshot_dialog(dialog, "06_QuickStartDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] QuickStartDialog: {e}")
        count += 1

    # 7. New RoundUp Dialog
    try:
        from welcome_screen import NewRoundUpDialog
        dialog = NewRoundUpDialog(parent)
        if screenshot_dialog(dialog, "07_NewRoundUpDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] NewRoundUpDialog: {e}")
        count += 1

    # 8. Folder Content Selection Dialog
    try:
        from scan_view import FolderContentSelectionDialog
        test_path = Path.home()
        dialog = FolderContentSelectionDialog(test_path, parent)
        if screenshot_dialog(dialog, "08_FolderContentSelectionDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] FolderContentSelectionDialog: {e}")
        count += 1

    # 9. Canonical DB Dialog (complex, may fail)
    try:
        from canonical_db_dialog import CanonicalDBDialog
        dialog = CanonicalDBDialog(parent)
        if screenshot_dialog(dialog, "09_CanonicalDBDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] CanonicalDBDialog: {e}")
        count += 1

    # 10. Episode Analysis Dialog (complex, may fail)
    try:
        from episode_analysis_dialog import EpisodeAnalysisDialog
        dialog = EpisodeAnalysisDialog(parent)
        if screenshot_dialog(dialog, "10_EpisodeAnalysisDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] EpisodeAnalysisDialog: {e}")
        count += 1

    # 11. Movie Analysis Dialog (complex, may fail)
    try:
        from movie_analysis_dialog import MovieAnalysisDialog
        dialog = MovieAnalysisDialog(parent)
        if screenshot_dialog(dialog, "11_MovieAnalysisDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] MovieAnalysisDialog: {e}")
        count += 1

    # 12. TMDB Cache Dialog (complex, may fail)
    try:
        from tmdb_cache_dialog import TMDBCacheDialog
        dialog = TMDBCacheDialog(parent)
        if screenshot_dialog(dialog, "12_TMDBCacheDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] TMDBCacheDialog: {e}")
        count += 1

    # 13. Wikipedia Cache Dialog (complex, may fail)
    try:
        from wikipedia_cache_dialog import WikipediaCacheDialog
        dialog = WikipediaCacheDialog(parent)
        if screenshot_dialog(dialog, "13_WikipediaCacheDialog"):
            success += 1
        count += 1
    except Exception as e:
        print(f"[X] WikipediaCacheDialog: {e}")
        count += 1

except KeyboardInterrupt:
    print("\n[INTERRUPTED] User stopped")

finally:
    parent.close()
    print(f"\n[DONE] Captured {success}/{count} dialog screenshots")
    print(f"[LOC] {OUTPUT_DIR}\n")
    sys.exit(0)

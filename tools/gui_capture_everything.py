#!/usr/bin/env python3
"""
GUI Capture Everything for JellyRancher

Goal:
- Capture screenshots for as many GUI "four-sided objects" as we can deterministically reach:
  - Main window (per main tab selection)
  - Nested QTabWidget tabs (captured at the tab-widget level so the tab bar renders)
  - Known dialogs/modals we can instantiate safely
- Write a manifest JSON mapping screenshot -> UI state metadata

Usage:
  .venv/Scripts/python.exe tools/gui_capture_everything.py
  python tools/gui_capture_everything.py --out gui_captures
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QTabWidget, QWidget  # noqa: E402


@dataclass
class CaptureItem:
    name: str
    path: str
    kind: str  # "window" | "tab_widget" | "dialog"
    widget_class: str
    object_name: str
    tab_widget_object_name: Optional[str] = None
    tab_index: Optional[int] = None
    tab_text: Optional[str] = None


def _clean(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in (s or "")).strip("_") or "untitled"


def _grab(widget: QWidget, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = widget.grab()
    pixmap.save(str(out_path))


def _pick_main_tab_widget(window: QMainWindow) -> Optional[QTabWidget]:
    tab_widgets = window.findChildren(QTabWidget)
    if not tab_widgets:
        return None

    def area(w: QWidget) -> int:
        try:
            return max(0, w.width()) * max(0, w.height())
        except Exception:
            return 0

    return max(tab_widgets, key=area)


def _capture_all_tabs(app: QApplication, window: QMainWindow, out_dir: Path) -> List[CaptureItem]:
    items: List[CaptureItem] = []

    # Always capture full window baseline
    app.processEvents()
    time.sleep(0.2)
    base_path = out_dir / "main_window.png"
    _grab(window, base_path)
    items.append(
        CaptureItem(
            name="main_window",
            path=str(base_path),
            kind="window",
            widget_class=window.__class__.__name__,
            object_name=window.objectName() or "",
        )
    )

    tab_widgets = window.findChildren(QTabWidget)
    main_tabs = _pick_main_tab_widget(window)

    for tw in tab_widgets:
        tw_name = tw.objectName() or f"{tw.__class__.__name__}_{id(tw)}"
        tw_name_clean = _clean(tw_name)

        for i in range(tw.count()):
            tab_text = tw.tabText(i)
            tab_text_clean = _clean(tab_text)

            tw.setCurrentIndex(i)
            app.processEvents()
            time.sleep(0.15)

            # Capture the tab widget itself (includes its tab bar + its current content).
            tw_path = out_dir / f"tabs__{tw_name_clean}__tab_{i}__{tab_text_clean}.png"
            _grab(tw, tw_path)
            items.append(
                CaptureItem(
                    name=f"tabs__{tw_name_clean}__tab_{i}__{tab_text_clean}",
                    path=str(tw_path),
                    kind="tab_widget",
                    widget_class=tw.__class__.__name__,
                    object_name=tw.objectName() or "",
                    tab_widget_object_name=tw.objectName() or "",
                    tab_index=i,
                    tab_text=tab_text,
                )
            )

            # For the primary tab widget, also capture full window state for each tab.
            if tw is main_tabs:
                win_path = out_dir / f"main_window__tab_{i}__{tab_text_clean}.png"
                _grab(window, win_path)
                items.append(
                    CaptureItem(
                        name=f"main_window__tab_{i}__{tab_text_clean}",
                        path=str(win_path),
                        kind="window",
                        widget_class=window.__class__.__name__,
                        object_name=window.objectName() or "",
                        tab_widget_object_name=tw.objectName() or "",
                        tab_index=i,
                        tab_text=tab_text,
                    )
                )

    return items


def _try_capture_dialog(
    app: QApplication, out_dir: Path, dialog: QDialog, name: str, delay: float = 0.25
) -> Optional[CaptureItem]:
    try:
        dialog.show()
        dialog.raise_()
        app.processEvents()
        time.sleep(delay)

        path = out_dir / f"dialog__{_clean(name)}.png"
        _grab(dialog, path)

        item = CaptureItem(
            name=f"dialog__{_clean(name)}",
            path=str(path),
            kind="dialog",
            widget_class=dialog.__class__.__name__,
            object_name=dialog.objectName() or "",
        )
        dialog.close()
        app.processEvents()
        time.sleep(0.1)
        return item
    except Exception:
        try:
            dialog.close()
        except Exception:
            pass
        return None


def _capture_known_dialogs(app: QApplication, parent: QMainWindow, out_dir: Path) -> List[CaptureItem]:
    """
    Curated set of dialogs that are expected to be safe to open without side effects.
    This deliberately avoids actions that move/delete/execute on real media.
    """
    items: List[CaptureItem] = []

    # Suppress browser/TMDB external side effects if code respects this flag.
    os.environ.setdefault("SUPPRESS_BROWSER", "1")

    # Import dialog classes via the same paths used elsewhere in the repo.
    dialog_specs: List[tuple[str, str, Dict[str, Any]]] = [
        ("scripts.core.dialogs.app_settings_dialog", "AppSettingsDialog", {}),
        ("scripts.core.dialogs.jellyfin_settings_dialog", "JellyfinSettingsDialog", {}),
        ("scripts.core.help_system", "HelpDialog", {"tab_name": None}),
        ("scripts.core.jelly_rancher_help", "JellyRancherHelpDialog", {"topic": "general"}),
        ("scripts.core.getting_started_wizard", "WelcomeWizard", {}),
        ("scripts.core.getting_started_wizard", "QuickStartDialog", {}),
        ("scripts.core.dialogs.episode_analysis_dialog", "EpisodeAnalysisDialog", {}),
        ("scripts.core.dialogs.movie_analysis_dialog", "MovieAnalysisDialog", {}),
        ("scripts.core.dialogs.tmdb_cache_dialog", "TMDBCacheDialog", {}),
        ("scripts.core.dialogs.wikipedia_cache_dialog", "WikipediaCacheDialog", {}),
        ("scripts.core.dialogs.canonical_db_dialog", "CanonicalDBDialog", {}),
    ]

    for module_name, cls_name, kwargs in dialog_specs:
        try:
            mod = __import__(module_name, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
        except Exception:
            continue

        try:
            dlg = cls(parent, **kwargs) if kwargs else cls(parent)
        except TypeError:
            # Some dialogs may not accept parent; try without.
            try:
                dlg = cls(**kwargs) if kwargs else cls()
            except Exception:
                continue
        except Exception:
            continue

        item = _try_capture_dialog(app, out_dir, dlg, cls_name)
        if item:
            items.append(item)

    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture screenshots of JellyRancher UI states")
    parser.add_argument("--out", type=str, default=str(project_root / "gui_captures"), help="Base output directory")
    args = parser.parse_args()

    base_out = Path(args.out)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = base_out / f"capture_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)

    # Load main window
    from scripts.core.jelly_rancher_main import JellyRancherMainWindow  # noqa: E402

    window = JellyRancherMainWindow()
    window.show()
    window.resize(1200, 800)
    app.processEvents()
    time.sleep(1.0)

    # Close any auto-shown dialogs (welcome wizard, etc.) so tab capture is stable.
    for w in app.topLevelWidgets():
        if isinstance(w, QDialog) and w is not window:
            try:
                w.close()
            except Exception:
                pass
    app.processEvents()
    time.sleep(0.2)

    captures: List[CaptureItem] = []
    captures.extend(_capture_all_tabs(app, window, out_dir))
    captures.extend(_capture_known_dialogs(app, window, out_dir))

    manifest = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "tool": "tools/gui_capture_everything.py",
            "output_dir": str(out_dir),
            "count": len(captures),
        },
        "captures": [asdict(c) for c in captures],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



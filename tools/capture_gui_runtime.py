#!/usr/bin/env python3
"""
GUI Runtime State Capture Tool for JellyRancher Studio

Launches the application, captures the complete widget hierarchy at runtime,
and saves to gui_runtime_state.json for LLM context.

Usage:
    python tools/capture_gui_runtime.py
    
    1. Application launches
    2. Navigate through tabs/dialogs you want to document
    3. Close the application normally
    4. Widget hierarchy is automatically saved to gui_runtime_state.json

This provides LLMs with visual context for accurate GUI code modifications.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Ensure UTF-8 console output on Windows (avoid cp1252 UnicodeEncodeError)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    # If the host terminal can't be reconfigured, continue with best effort.
    pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

# Import the main Studio window
from jelly_rancher_studio import JellyRancherStudio


def _to_jsonable(value: Any) -> Any:
    """Best-effort conversion of arbitrary Python/Qt values into JSON-serializable data."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # Common containers
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}

    # Qt types (avoid importing heavy modules at top-level)
    try:
        from PyQt6.QtCore import QModelIndex, QRect, QSize, QPoint  # type: ignore

        if isinstance(value, QModelIndex):
            return {
                "type": "QModelIndex",
                "row": value.row(),
                "column": value.column(),
                "isValid": value.isValid(),
            }
        if isinstance(value, QRect):
            return {
                "type": "QRect",
                "x": value.x(),
                "y": value.y(),
                "width": value.width(),
                "height": value.height(),
            }
        if isinstance(value, QSize):
            return {"type": "QSize", "width": value.width(), "height": value.height()}
        if isinstance(value, QPoint):
            return {"type": "QPoint", "x": value.x(), "y": value.y()}
    except Exception:
        pass

    # Fallback: string representation (keeps capture running)
    return str(value)


def build_widget_tree(widget) -> Dict[str, Any]:
    """
    Recursively build a JSON representation of the widget hierarchy.
    
    Captures:
    - Widget class name and object name
    - Common properties (text, title, tooltip, state)
    - Parent-child relationships
    - Layout information
    
    Args:
        widget: PyQt6 widget to inspect
        
    Returns:
        Dictionary containing widget information and children
    """
    info = {
        "object_name": widget.objectName() or "(unnamed)",
        "class_name": widget.__class__.__name__,
    }
    
    # Capture common useful properties
    # Using hasattr + try-except to handle different widget types gracefully
    property_names = [
        "text", "title", "placeholderText", "currentText", 
        "toolTip", "statusTip", "whatsThis",
        "isChecked", "isEnabled", "isVisible", "isReadOnly",
        "minimum", "maximum", "value", "currentIndex"
    ]
    
    for prop_name in property_names:
        if hasattr(widget, prop_name):
            try:
                # Get the property (might be a method or attribute)
                prop = getattr(widget, prop_name)
                
                # Call if it's a method
                if callable(prop):
                    value = prop()
                else:
                    value = prop
                
                # Only include non-empty/non-default values
                if value not in [None, "", False, 0]:
                    info[prop_name] = _to_jsonable(value)
                    
            except Exception:
                # Some properties might not be accessible, skip them
                pass
    
    # Capture layout information if widget has a layout
    if hasattr(widget, 'layout') and widget.layout() is not None:
        layout = widget.layout()
        info["layout_type"] = layout.__class__.__name__
        info["layout_spacing"] = layout.spacing()
        info["layout_margins"] = {
            "left": layout.contentsMargins().left(),
            "top": layout.contentsMargins().top(),
            "right": layout.contentsMargins().right(),
            "bottom": layout.contentsMargins().bottom()
        }
    
    # Recursively capture all direct widget children
    # Using children() but filtering to only actual widgets
    direct_children = [c for c in widget.children() if c.isWidgetType()]
    
    if direct_children:
        info["children"] = [build_widget_tree(child) for child in direct_children]
    
    return info


def capture_gui_state_on_close():
    """
    Capture the complete GUI state when the application closes.
    
    This function is connected to QApplication.aboutToQuit signal and
    runs automatically when the user closes the main window.
    """
    app = QApplication.instance()
    
    # Find the JellyRancherStudio main window
    main_window = None
    for widget in app.topLevelWidgets():
        if isinstance(widget, JellyRancherStudio):
            main_window = widget
            break
    
    if not main_window:
        print("\n[WARNING] Could not find JellyRancherStudio main window")
        return

    capture_gui_state(main_window=main_window, output_file=project_root / "gui_runtime_state.json")


def capture_gui_state(*, main_window: JellyRancherStudio, output_file: Path) -> None:
    """Capture and save the complete GUI state for the given main window."""
    print("\n" + "=" * 80)
    print("Capturing GUI Runtime State...")
    print("=" * 80)

    widget_tree = build_widget_tree(main_window)

    capture_data = {
        "metadata": {
            "captured_at": datetime.now().isoformat(),
            "main_window_class": main_window.__class__.__name__,
            "pyqt_version": "PyQt6",
            "capture_tool": "tools/capture_gui_runtime.py",
        },
        "tree": widget_tree,
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(capture_data, f, indent=2, ensure_ascii=False, default=str)

        print("\n[OK] GUI state captured successfully")
        print(f"[FILE] Saved to: {output_file}")
        print(f"[TIME] Timestamp: {capture_data['metadata']['captured_at']}")
        print("\nPaste this JSON into the chat when requested for GUI context.")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] Failed to save GUI state: {e}")
        print("=" * 80)


def main():
    """Main entry point for the GUI capture tool."""
    parser = argparse.ArgumentParser(description="Capture JellyRancher Studio GUI runtime widget tree")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Capture automatically after a delay and exit (non-interactive, useful for CI/agents)",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=1.0,
        help="Seconds to wait after showing the window before capturing (only with --auto)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(project_root / "gui_runtime_state.json"),
        help="Output JSON path (default: gui_runtime_state.json in project root)",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("JellyRancher Studio - GUI Runtime State Capture Tool")
    print("=" * 80)
    print("\nInstructions:")
    print("1. The Studio application will launch")
    print("2. Navigate through any tabs/views you want to document")
    print("3. Close the application normally (File -> Exit or X button)")
    print("4. GUI state will be automatically saved to gui_runtime_state.json")
    print("\n" + "=" * 80)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and show main window
    try:
        window = JellyRancherStudio()
        window.show()
    except Exception as e:
        print(f"\n[ERROR] Failed to launch Studio: {e}")
        print("\nMake sure:")
        print("- Virtual environment is activated (.venv)")
        print("- All dependencies are installed (PyQt6, etc.)")
        print("- Database files are accessible")
        sys.exit(1)
    
    output_path = Path(args.output)

    if args.auto:
        # Non-interactive mode: capture after delay and quit automatically.
        def _auto_capture():
            try:
                capture_gui_state(main_window=window, output_file=output_path)
            finally:
                app.quit()

        QTimer.singleShot(max(0, int(args.delay_seconds * 1000)), _auto_capture)
        print("\n[OK] Studio launched (auto mode)")
        print(f"[INFO] Capturing in {args.delay_seconds:.2f}s -> {output_path}\n")
    else:
        # Interactive mode: capture when the app closes.
        app.aboutToQuit.connect(capture_gui_state_on_close)
        print("\n[OK] Studio launched successfully")
        print("[INFO] Close the application when ready to capture state...\n")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

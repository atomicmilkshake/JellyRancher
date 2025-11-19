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
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import the main Studio window
from jelly_rancher_studio import JellyRancherStudio


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
                    info[prop_name] = value
                    
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
    
    print("\n" + "=" * 80)
    print("Capturing GUI Runtime State...")
    print("=" * 80)
    
    # Build the complete widget tree
    widget_tree = build_widget_tree(main_window)
    
    # Create comprehensive capture data
    capture_data = {
        "metadata": {
            "captured_at": datetime.now().isoformat(),
            "main_window_class": "JellyRancherStudio",
            "pyqt_version": "PyQt6",
            "capture_tool": "tools/capture_gui_runtime.py"
        },
        "tree": widget_tree
    }
    
    # Save to project root
    output_file = project_root / "gui_runtime_state.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(capture_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ GUI state captured successfully!")
        print(f"📄 Saved to: {output_file}")
        print(f"📊 Timestamp: {capture_data['metadata']['captured_at']}")
        print(f"\n💡 You can now paste this JSON to LLMs for accurate GUI code assistance")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to save GUI state: {e}")
        print("=" * 80)


def main():
    """Main entry point for the GUI capture tool."""
    print("=" * 80)
    print("JellyRancher Studio - GUI Runtime State Capture Tool")
    print("=" * 80)
    print("\nInstructions:")
    print("1. The Studio application will launch")
    print("2. Navigate through any tabs/views you want to document")
    print("3. Close the application normally (File → Exit or X button)")
    print("4. GUI state will be automatically saved to gui_runtime_state.json")
    print("\n" + "=" * 80)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and show main window
    try:
        window = JellyRancherStudio()
        window.show()
    except Exception as e:
        print(f"\n❌ ERROR: Failed to launch Studio: {e}")
        print("\nMake sure:")
        print("- Virtual environment is activated (.venv)")
        print("- All dependencies are installed (PyQt6, etc.)")
        print("- Database files are accessible")
        sys.exit(1)
    
    # Connect the capture function to run when app closes
    app.aboutToQuit.connect(capture_gui_state_on_close)
    
    print("\n✅ Studio launched successfully")
    print("📸 Close the application when ready to capture state...\n")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

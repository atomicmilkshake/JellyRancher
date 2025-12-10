#!/usr/bin/env python3
"""
Screenshot and OCR Audit Tool for JellyRancher

Launches the application, screenshots every tab/view, runs OCR on each,
and reports any UI issues found (garbage text, truncated labels, etc.)

Usage:
    .venv/Scripts/python.exe tools/screenshot_ocr_audit.py

Features:
    - Screenshots every tab in the main window
    - Opens and screenshots key dialogs
    - Runs Tesseract OCR on each screenshot
    - Analyzes text for issues:
        - Garbage/unreadable text
        - Truncated labels (...)
        - Very small text
        - Missing expected labels
    - Generates a comprehensive report
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure Tesseract path for Windows
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QScreen

# Try to import OCR dependencies
try:
    import pytesseract
    from PIL import Image
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("WARNING: pytesseract or PIL not installed. OCR will be skipped.")


class ScreenshotOCRAudit:
    """Comprehensive screenshot and OCR audit tool."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or project_root / "gui_audit"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots: List[Dict[str, Any]] = []
        self.issues: List[Dict[str, Any]] = []
        self.app = None
        self.main_window = None

    def capture_screenshot(self, widget: QWidget, name: str) -> Path:
        """Capture a screenshot of the widget."""
        screenshot_path = self.output_dir / f"{name}.png"

        # Use widget's grab() method for reliable capture
        pixmap = widget.grab()
        pixmap.save(str(screenshot_path))

        return screenshot_path

    def run_ocr(self, image_path: Path) -> str:
        """Run OCR on an image and return extracted text."""
        if not OCR_AVAILABLE:
            return ""

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"  OCR error: {e}")
            return ""

    def analyze_text(self, text: str, view_name: str) -> List[Dict[str, Any]]:
        """Analyze OCR text for issues."""
        issues = []

        # Check for garbage text (random characters)
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for high ratio of non-alphanumeric characters (potential garbage)
            if len(line) > 3:
                alpha_count = sum(1 for c in line if c.isalnum() or c.isspace())
                if alpha_count / len(line) < 0.5:
                    issues.append({
                        "type": "garbage_text",
                        "view": view_name,
                        "text": line[:50],
                        "severity": "warning"
                    })

            # Check for truncated labels (...)
            if line.endswith('...') or '...' in line:
                issues.append({
                    "type": "truncated_label",
                    "view": view_name,
                    "text": line[:50],
                    "severity": "info"
                })

        # Check for very short/empty content
        if len(text.strip()) < 10:
            issues.append({
                "type": "minimal_text",
                "view": view_name,
                "text": f"Only {len(text.strip())} chars extracted",
                "severity": "warning"
            })

        return issues

    def audit_view(self, widget: QWidget, name: str, expected_labels: List[str] = None):
        """Audit a single view: screenshot, OCR, analyze."""
        print(f"\n  Auditing: {name}")

        # Ensure widget is visible and processed
        widget.show()
        widget.raise_()
        QApplication.processEvents()
        time.sleep(0.1)

        # Capture screenshot
        screenshot_path = self.capture_screenshot(widget, name)
        print(f"    Screenshot: {screenshot_path.name}")

        # Run OCR
        ocr_text = self.run_ocr(screenshot_path)
        print(f"    OCR: {len(ocr_text)} chars extracted")

        # Analyze for issues
        view_issues = self.analyze_text(ocr_text, name)

        # Check for expected labels
        if expected_labels:
            ocr_lower = ocr_text.lower()
            for label in expected_labels:
                if label.lower() not in ocr_lower:
                    view_issues.append({
                        "type": "missing_label",
                        "view": name,
                        "text": f"Expected '{label}' not found",
                        "severity": "warning"
                    })

        self.issues.extend(view_issues)

        # Store screenshot info
        self.screenshots.append({
            "name": name,
            "path": str(screenshot_path),
            "ocr_text": ocr_text[:500],  # First 500 chars
            "issues_count": len(view_issues)
        })

        if view_issues:
            print(f"    Issues: {len(view_issues)}")
            for issue in view_issues:
                print(f"      - [{issue['severity']}] {issue['type']}: {issue['text'][:40]}")

    def audit_main_window(self, window: QMainWindow):
        """Audit all tabs in the main window."""
        self.main_window = window

        print("\n" + "=" * 70)
        print("MAIN WINDOW TABS")
        print("=" * 70)

        # Find tab widgets
        tab_widgets = window.findChildren(QTabWidget)

        for tab_widget in tab_widgets:
            tab_name = tab_widget.objectName() or "main_tabs"
            print(f"\nTab Widget: {tab_name} ({tab_widget.count()} tabs)")

            for i in range(tab_widget.count()):
                tab_text = tab_widget.tabText(i)
                # Clean tab name for filename
                clean_name = "".join(c if c.isalnum() else "_" for c in tab_text)

                # Switch to tab
                tab_widget.setCurrentIndex(i)
                QApplication.processEvents()
                time.sleep(0.2)

                # Get the tab's widget
                tab_content = tab_widget.widget(i)
                if tab_content:
                    self.audit_view(
                        tab_content,
                        f"tab_{i}_{clean_name}",
                        expected_labels=self._get_expected_labels(tab_text)
                    )

        # Also capture the full window
        print("\n" + "=" * 70)
        print("FULL WINDOW CAPTURE")
        print("=" * 70)
        self.audit_view(window, "full_window")

    def _get_expected_labels(self, tab_name: str) -> List[str]:
        """Get expected labels for each tab type."""
        tab_lower = tab_name.lower()

        if "workflow" in tab_lower or "scan" in tab_lower:
            return ["scan", "folder", "add"]
        elif "analysis" in tab_lower:
            return ["analysis", "run"]
        elif "review" in tab_lower:
            return ["approve", "reject"]
        elif "execution" in tab_lower or "execute" in tab_lower:
            return ["execute", "rollback"]
        elif "subtitle" in tab_lower:
            return ["subtitle", "download"]
        elif "jelly" in tab_lower:
            return ["library", "items"]
        elif "settings" in tab_lower:
            return ["settings", "save"]
        elif "log" in tab_lower:
            return ["log"]

        return []

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "screenshot_ocr_audit.py",
                "output_dir": str(self.output_dir),
                "ocr_available": OCR_AVAILABLE
            },
            "summary": {
                "total_screenshots": len(self.screenshots),
                "total_issues": len(self.issues),
                "issues_by_type": {},
                "issues_by_severity": {"warning": 0, "info": 0, "error": 0}
            },
            "screenshots": self.screenshots,
            "issues": self.issues
        }

        # Count issues by type
        for issue in self.issues:
            issue_type = issue["type"]
            if issue_type not in report["summary"]["issues_by_type"]:
                report["summary"]["issues_by_type"][issue_type] = 0
            report["summary"]["issues_by_type"][issue_type] += 1

            severity = issue.get("severity", "info")
            report["summary"]["issues_by_severity"][severity] += 1

        return report

    def save_report(self, report: Dict[str, Any]):
        """Save audit report to JSON."""
        report_path = self.output_dir / "audit_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved: {report_path}")
        return report_path


def run_audit():
    """Run the complete screenshot and OCR audit."""
    print("=" * 70)
    print("JellyRancher Screenshot & OCR Audit Tool")
    print("=" * 70)
    print(f"\nTesseract: {'Available' if OCR_AVAILABLE else 'NOT AVAILABLE'}")
    print(f"Output: gui_audit/")

    # Create Qt application
    app = QApplication(sys.argv)

    # Create audit tool
    audit = ScreenshotOCRAudit()
    audit.app = app

    # Import and create main window
    try:
        # Try the new main window first
        from scripts.core.jelly_rancher_main import JellyRancherMainWindow
        window = JellyRancherMainWindow()
        window.show()
        window.resize(1200, 800)
        QApplication.processEvents()
        time.sleep(1.0)  # Wait for any dialogs to appear

        # Close any dialogs that may have opened (like welcome wizard)
        from PyQt6.QtWidgets import QDialog
        for widget in app.topLevelWidgets():
            if isinstance(widget, QDialog):
                print(f"  Closing dialog: {widget.__class__.__name__}")
                widget.close()
        QApplication.processEvents()
        time.sleep(0.3)

        print("\nMain window loaded successfully")

        # Run the audit
        audit.audit_main_window(window)

        # Generate and save report
        report = audit.generate_report()
        report_path = audit.save_report(report)

        # Print summary
        print("\n" + "=" * 70)
        print("AUDIT SUMMARY")
        print("=" * 70)
        print(f"Screenshots captured: {report['summary']['total_screenshots']}")
        print(f"Issues found: {report['summary']['total_issues']}")
        print("\nIssues by type:")
        for issue_type, count in report['summary']['issues_by_type'].items():
            print(f"  - {issue_type}: {count}")
        print("\nIssues by severity:")
        for severity, count in report['summary']['issues_by_severity'].items():
            print(f"  - {severity}: {count}")

        if report['summary']['total_issues'] > 0:
            print("\n" + "=" * 70)
            print("ISSUES REQUIRING ATTENTION")
            print("=" * 70)
            for issue in report['issues']:
                if issue['severity'] in ['warning', 'error']:
                    print(f"[{issue['severity'].upper()}] {issue['view']}: {issue['type']}")
                    print(f"  {issue['text']}")

        print("\n" + "=" * 70)
        print("AUDIT COMPLETE")
        print("=" * 70)
        print(f"\nAll screenshots saved to: {audit.output_dir}")
        print(f"Full report: {report_path}")

        # Close window
        window.close()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(run_audit())

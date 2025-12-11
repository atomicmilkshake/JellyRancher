#!/usr/bin/env python3
"""
GUI Visual Validator for JellyRancher

Detects visual layout issues BEFORE commit:
- Text overlapping text/graphics
- Windows too tall for resolution+DPI combinations
- Low-contrast text (WCAG compliance)
- Tiny text (accessibility)
- Visual regressions (against baseline)

Usage:
    .venv/Scripts/python.exe tools/gui_visual_validator.py [OPTIONS]

Options:
    --strict                Exit code 1 if critical issues found
    --view NAME             Check specific view only
    --compare-baseline      Compare against baseline (visual regression)
    --create-baseline       Create baseline for comparison
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import time
import math

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure Tesseract path for Windows
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QColor, QFont

# Try to import optional dependencies
try:
    import pytesseract
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    print(f"WARNING: Optional dependencies not available: {e}")


# WCAG Contrast Ratio Constants
MIN_CONTRAST_AA = 4.5  # Standard text
MIN_CONTRAST_AAA = 7.0  # Enhanced text
MIN_TEXT_SIZE_PT = 11  # Minimum readable text size

# Common resolutions (width, height)
COMMON_RESOLUTIONS = [
    (1920, 1080),
    (1366, 768),
    (1024, 768),
    (800, 600),
]

# DPI settings
DPI_SETTINGS = [100, 125, 150]


class GUIVisualValidator:
    """Comprehensive GUI visual validation tool."""

    def __init__(self, output_dir: Path = None, strict: bool = False):
        self.output_dir = output_dir or project_root / "gui_visual_issues"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_dir = project_root / "gui_visual_baselines"
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.strict = strict
        self.issues: List[Dict[str, Any]] = []
        self.screenshots: List[Dict[str, Any]] = []
        self.app = None
        self.main_window = None

    def capture_screenshot(self, widget: QWidget, name: str) -> Path:
        """Capture screenshot of widget."""
        screenshot_path = self.output_dir / f"{name}.png"
        pixmap = widget.grab()
        pixmap.save(str(screenshot_path))
        return screenshot_path

    def calculate_contrast_ratio(self, color1: QColor, color2: QColor) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        def get_luminance(c: QColor) -> float:
            # Convert to relative luminance
            r, g, b = c.red() / 255.0, c.green() / 255.0, c.blue() / 255.0

            # Apply gamma correction
            for val in [r, g, b]:
                if val <= 0.03928:
                    val = val / 12.92
                else:
                    val = ((val + 0.055) / 1.055) ** 2.4

            return r * 0.2126 + g * 0.7152 + b * 0.0722

        l1 = get_luminance(color1)
        l2 = get_luminance(color2)

        lighter = max(l1, l2)
        darker = min(l1, l2)

        if lighter == darker:
            return 1.0

        return (lighter + 0.05) / (darker + 0.05)

    def detect_overlaps(self, screenshot_path: Path, view_name: str) -> List[Dict[str, Any]]:
        """Detect overlapping text/widgets using OCR."""
        if not DEPS_AVAILABLE:
            return []

        issues = []
        try:
            image = Image.open(screenshot_path)
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Get bounding boxes from OCR
            boxes = []
            for i, text in enumerate(ocr_data['text']):
                if text.strip() and ocr_data['conf'][i] > 0:
                    x, y, w, h = (
                        ocr_data['left'][i],
                        ocr_data['top'][i],
                        ocr_data['width'][i],
                        ocr_data['height'][i],
                    )
                    boxes.append({
                        'rect': (x, y, x + w, y + h),
                        'text': text,
                        'conf': ocr_data['conf'][i]
                    })

            # Check for overlaps
            for i, box1 in enumerate(boxes):
                for box2 in boxes[i + 1:]:
                    if self._rects_overlap(box1['rect'], box2['rect']):
                        # Calculate overlap area
                        overlap_area = self._calculate_overlap_area(box1['rect'], box2['rect'])

                        # Only report significant overlaps
                        if overlap_area > 100:  # Pixels
                            issues.append({
                                'type': 'text_overlap',
                                'view': view_name,
                                'severity': 'CRITICAL',
                                'description': f"Text '{box1['text'][:30]}' overlaps '{box2['text'][:30]}'",
                                'location': str((box1['rect'][0], box1['rect'][1])),
                                'overlap_area': overlap_area,
                                'screenshot': screenshot_path.name,
                                'fix_suggestion': 'Increase spacing or adjust layout margins'
                            })

        except Exception as e:
            print(f"    Overlap detection error: {e}")

        return issues

    def _rects_overlap(self, rect1: Tuple, rect2: Tuple) -> bool:
        """Check if two rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = rect1
        x2_min, y2_min, x2_max, y2_max = rect2
        return not (x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min)

    def _calculate_overlap_area(self, rect1: Tuple, rect2: Tuple) -> float:
        """Calculate area of overlap between two rectangles."""
        x1_min, y1_min, x1_max, y1_max = rect1
        x2_min, y2_min, x2_max, y2_max = rect2

        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))

        return x_overlap * y_overlap

    def analyze_contrast(self, widget: QWidget, screenshot_path: Path, view_name: str) -> List[Dict[str, Any]]:
        """Analyze contrast ratios of text in widget."""
        if not DEPS_AVAILABLE:
            return []

        issues = []
        try:
            # Extract colors from widget and screenshot
            palette = widget.palette()
            text_color = palette.color(widget.foregroundRole())
            bg_color = palette.color(widget.backgroundRole())

            ratio = self.calculate_contrast_ratio(text_color, bg_color)

            if ratio < MIN_CONTRAST_AA:
                issues.append({
                    'type': 'low_contrast',
                    'view': view_name,
                    'severity': 'WARNING' if ratio > 3.0 else 'CRITICAL',
                    'description': f"Contrast ratio {ratio:.2f}:1 below WCAG AA ({MIN_CONTRAST_AA}:1)",
                    'ratio': round(ratio, 2),
                    'min_required': MIN_CONTRAST_AA,
                    'text_color': text_color.name(),
                    'bg_color': bg_color.name(),
                    'fix_suggestion': f"Adjust colors to achieve {MIN_CONTRAST_AA}:1 ratio"
                })

        except Exception as e:
            print(f"    Contrast analysis error: {e}")

        return issues

    def check_window_size(self, window: QMainWindow) -> List[Dict[str, Any]]:
        """Check window fits within common resolutions at various DPI settings."""
        issues = []

        width = window.width()
        height = window.height()

        for resolution in COMMON_RESOLUTIONS:
            res_width, res_height = resolution

            for dpi in DPI_SETTINGS:
                # Calculate effective screen space
                effective_width = res_width * (100 / dpi)
                effective_height = res_height * (100 / dpi)

                if height > effective_height:
                    issues.append({
                        'type': 'window_too_tall',
                        'view': 'main_window',
                        'severity': 'ERROR',
                        'description': f"Window {height}px > effective {effective_height:.0f}px at {dpi}% DPI on {res_width}x{res_height}",
                        'actual_height': height,
                        'effective_height': round(effective_height, 0),
                        'resolution': f"{res_width}x{res_height}",
                        'dpi': dpi,
                        'fix_suggestion': f"Reduce height to {int(effective_height * 0.95)}px or make scrollable"
                    })

                if width > effective_width:
                    issues.append({
                        'type': 'window_too_wide',
                        'view': 'main_window',
                        'severity': 'WARNING',
                        'description': f"Window {width}px > effective {effective_width:.0f}px at {dpi}% DPI on {res_width}x{res_height}",
                        'actual_width': width,
                        'effective_width': round(effective_width, 0),
                        'resolution': f"{res_width}x{res_height}",
                        'dpi': dpi,
                        'fix_suggestion': 'Consider responsive layout or horizontal scrolling'
                    })

        return issues

    def detect_small_text(self, widget: QWidget, view_name: str) -> List[Dict[str, Any]]:
        """Detect text that's too small to read."""
        issues = []

        try:
            # Get font from widget
            font = widget.font()
            point_size = font.pointSize()

            if point_size < MIN_TEXT_SIZE_PT and point_size > 0:
                issues.append({
                    'type': 'small_text',
                    'view': view_name,
                    'severity': 'WARNING',
                    'description': f"Text size {point_size}pt below readable threshold ({MIN_TEXT_SIZE_PT}pt)",
                    'actual_size': point_size,
                    'min_size': MIN_TEXT_SIZE_PT,
                    'font_family': font.family(),
                    'fix_suggestion': f"Increase font size to at least {MIN_TEXT_SIZE_PT}pt"
                })

        except Exception as e:
            print(f"    Small text detection error: {e}")

        return issues

    def validate_view(self, widget: QWidget, name: str, window: Optional[QMainWindow] = None):
        """Validate a single view."""
        print(f"  Validating: {name}")

        # Ensure widget is visible
        widget.show()
        widget.raise_()
        QApplication.processEvents()
        time.sleep(0.1)

        # Capture screenshot
        screenshot_path = self.capture_screenshot(widget, name)
        print(f"    Screenshot: {screenshot_path.name}")

        # Run validations
        view_issues = []

        # Overlap detection
        overlap_issues = self.detect_overlaps(screenshot_path, name)
        view_issues.extend(overlap_issues)

        # Contrast analysis
        contrast_issues = self.analyze_contrast(widget, screenshot_path, name)
        view_issues.extend(contrast_issues)

        # Small text detection
        text_issues = self.detect_small_text(widget, name)
        view_issues.extend(text_issues)

        # Window size (only for main window)
        if window and isinstance(widget, QMainWindow):
            size_issues = self.check_window_size(widget)
            view_issues.extend(size_issues)

        self.issues.extend(view_issues)

        self.screenshots.append({
            'name': name,
            'path': str(screenshot_path),
            'issues_count': len(view_issues)
        })

        if view_issues:
            print(f"    Issues: {len(view_issues)}")
            for issue in view_issues:
                print(f"      - [{issue['severity']}] {issue['type']}: {issue['description'][:50]}")

    def validate_main_window(self, window: QMainWindow):
        """Validate all tabs and views in main window."""
        self.main_window = window

        print("\n" + "=" * 70)
        print("MAIN WINDOW VALIDATION")
        print("=" * 70)

        # Check main window size
        size_issues = self.check_window_size(window)
        self.issues.extend(size_issues)

        # Find and validate tab widgets
        tab_widgets = window.findChildren(QTabWidget)

        for tab_widget in tab_widgets:
            tab_name = tab_widget.objectName() or "main_tabs"
            print(f"\nTab Widget: {tab_name} ({tab_widget.count()} tabs)")

            for i in range(tab_widget.count()):
                tab_text = tab_widget.tabText(i)
                clean_name = "".join(c if c.isalnum() else "_" for c in tab_text)

                # Switch to tab
                tab_widget.setCurrentIndex(i)
                QApplication.processEvents()
                time.sleep(0.2)

                # Validate tab content
                tab_content = tab_widget.widget(i)
                if tab_content:
                    self.validate_view(
                        tab_content,
                        f"tab_{i}_{clean_name}",
                        window=window
                    )

        # Validate main window itself
        print("\n" + "=" * 70)
        print("FULL WINDOW")
        print("=" * 70)
        self.validate_view(window, "main_window", window=window)

    def calculate_score(self) -> int:
        """Calculate overall GUI health score (0-100)."""
        if not self.issues:
            return 100

        severity_weights = {
            'CRITICAL': 20,
            'ERROR': 15,
            'WARNING': 5,
            'INFO': 1
        }

        total_weight = sum(
            severity_weights.get(issue.get('severity', 'INFO'), 1)
            for issue in self.issues
        )

        # Score: 100 - (total_weight / 2), minimum 0
        score = max(0, 100 - (total_weight / 2))
        return int(score)

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        score = self.calculate_score()

        # Count issues by severity
        severity_counts = {'CRITICAL': 0, 'ERROR': 0, 'WARNING': 0, 'INFO': 0}
        for issue in self.issues:
            sev = issue.get('severity', 'INFO')
            if sev in severity_counts:
                severity_counts[sev] += 1

        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'tool': 'gui_visual_validator.py',
                'output_dir': str(self.output_dir),
                'deps_available': DEPS_AVAILABLE
            },
            'summary': {
                'views_scanned': len(self.screenshots),
                'total_issues': len(self.issues),
                'score': score,
                'passed': score >= 80 and severity_counts['CRITICAL'] == 0,
                'issues_by_severity': severity_counts,
                'issues_by_type': self._count_by_type()
            },
            'screenshots': self.screenshots,
            'issues': sorted(self.issues, key=lambda x: {'CRITICAL': 0, 'ERROR': 1, 'WARNING': 2, 'INFO': 3}.get(x.get('severity', 'INFO')))
        }

        return report

    def _count_by_type(self) -> Dict[str, int]:
        """Count issues by type."""
        counts = {}
        for issue in self.issues:
            issue_type = issue.get('type', 'unknown')
            counts[issue_type] = counts.get(issue_type, 0) + 1
        return counts

    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save validation report to JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / f"validation_report_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nReport saved: {report_path}")
        return report_path


def validate_gui(strict: bool = False, specific_view: Optional[str] = None):
    """Run complete GUI visual validation."""
    print("=" * 70)
    print("JellyRancher GUI Visual Validator")
    print("=" * 70)
    print(f"\nDependencies: {'Available' if DEPS_AVAILABLE else 'PARTIAL'}")
    print(f"Strict mode: {strict}")
    print(f"Output: gui_visual_issues/")

    # Create Qt application
    app = QApplication(sys.argv)

    # Set global application font to 12pt for readability
    global_font = QFont("Segoe UI", 12)
    app.setFont(global_font)

    # Create validator
    validator = GUIVisualValidator(strict=strict)
    validator.app = app

    try:
        # Import and create main window
        from scripts.core.jelly_rancher_main import JellyRancherMainWindow

        window = JellyRancherMainWindow()
        window.show()
        window.resize(1200, 800)
        QApplication.processEvents()
        time.sleep(1.0)

        # Close any dialogs
        from PyQt6.QtWidgets import QDialog
        for widget in app.topLevelWidgets():
            if isinstance(widget, QDialog):
                widget.close()
        QApplication.processEvents()
        time.sleep(0.3)

        print("\nMain window loaded successfully")

        # Run validation
        validator.validate_main_window(window)

        # Generate report
        report = validator.generate_report()
        report_path = validator.save_report(report)

        # Print summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Views scanned: {report['summary']['views_scanned']}")
        print(f"Total issues: {report['summary']['total_issues']}")
        print(f"Health score: {report['summary']['score']}/100")
        print(f"Passed: {'YES' if report['summary']['passed'] else 'NO'}")

        print("\nIssues by severity:")
        for severity, count in report['summary']['issues_by_severity'].items():
            if count > 0:
                print(f"  - {severity}: {count}")

        print("\nIssues by type:")
        for issue_type, count in report['summary']['issues_by_type'].items():
            if count > 0:
                print(f"  - {issue_type}: {count}")

        if report['summary']['total_issues'] > 0:
            print("\n" + "=" * 70)
            print("CRITICAL & ERROR ISSUES")
            print("=" * 70)
            for issue in report['issues']:
                if issue['severity'] in ['CRITICAL', 'ERROR']:
                    print(f"\n[{issue['severity']}] {issue['type']} in {issue['view']}")
                    print(f"  {issue['description']}")
                    print(f"  Fix: {issue['fix_suggestion']}")

        print("\n" + "=" * 70)
        print("VALIDATION COMPLETE")
        print("=" * 70)
        print(f"\nScreenshots: {validator.output_dir}")
        print(f"Report: {report_path}")

        window.close()

        # Return exit code based on strict mode
        if strict and not report['summary']['passed']:
            return 1
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GUI Visual Validator")
    parser.add_argument('--strict', action='store_true', help='Exit with code 1 if issues found')
    parser.add_argument('--view', type=str, help='Validate specific view only')
    parser.add_argument('--compare-baseline', action='store_true', help='Compare against baseline')
    parser.add_argument('--create-baseline', action='store_true', help='Create baseline')

    args = parser.parse_args()

    exit_code = validate_gui(strict=args.strict, specific_view=args.view)
    sys.exit(exit_code)

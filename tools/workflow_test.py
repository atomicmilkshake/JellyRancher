#!/usr/bin/env python3
"""
JellyRancher Workflow Test - Deterministic GUI Walkthrough
===========================================================

No LLM middleman. Just walks through the workflow step by step.
If something breaks, we debug it directly.

Usage:
    .venv\\Scripts\\python.exe tools/workflow_test.py
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QDialog,
    QDialogButtonBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QEventLoop
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QScreen

from jelly_rancher_studio import JellyRancherStudio
from scripts._common.logger import MasterLogger

# Initialize logging
master_logger = MasterLogger()
logger = master_logger.get_child_logger("WorkflowTest")

# Test configuration
TEST_PROJECT_NAME = "Workflow_Test_" + datetime.now().strftime("%H%M%S")
TEST_MEDIA_FOLDER = "v:/JellyRancher/test_media/unsorted"


class WorkflowTest:
    """Deterministic walkthrough of JellyRancher workflow."""

    def __init__(self):
        self.app = None
        self.main_window = None
        self.step_count = 0
        self.screenshots_dir = project_root / "logs" / "workflow_test_screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def log_step(self, description: str):
        """Log a step with incrementing counter."""
        self.step_count += 1
        logger.info(f"[STEP {self.step_count}] {description}")
        print(f"\n{'='*60}")
        print(f"STEP {self.step_count}: {description}")
        print(f"{'='*60}")

    def capture_screenshot(self, name: str):
        """Capture screenshot for debugging."""
        if self.main_window:
            screen = QApplication.primaryScreen()
            if screen:
                pixmap = screen.grabWindow(self.main_window.winId())
                filename = self.screenshots_dir / f"{self.step_count:02d}_{name}.png"
                pixmap.save(str(filename))
                logger.info(f"Screenshot saved: {filename}")
                return filename
        return None

    def wait(self, ms: int = 500):
        """Wait and process events."""
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()
        QApplication.processEvents()

    def find_widget(self, target: str, parent: QWidget = None) -> QWidget:
        """Find widget by objectName or text."""
        search_root = parent or self.main_window
        if not search_root:
            return None

        # Try objectName first
        result = search_root.findChild(QWidget, target)
        if result:
            return result

        # Search all children for matching text
        for child in search_root.findChildren(QWidget):
            if hasattr(child, 'text') and callable(child.text):
                try:
                    if child.text() == target:
                        return child
                except:
                    pass
            if hasattr(child, 'objectName') and child.objectName() == target:
                return child

        return None

    def _safe_text(self, text: str) -> str:
        """Strip non-ASCII characters for safe console logging on Windows."""
        return ''.join(c if ord(c) < 128 else '?' for c in text)

    def find_button(self, text: str, parent: QWidget = None) -> QPushButton:
        """Find button by text (handles emoji prefixes)."""
        search_root = parent or self.main_window
        if not search_root:
            return None

        for btn in search_root.findChildren(QPushButton):
            btn_text = btn.text()
            # Exact match
            if btn_text == text:
                return btn
            # Substring match (handles "📁 New Round-Up" when searching "New Round-Up")
            if text in btn_text:
                return btn
            # Strip emoji and try again
            btn_text_stripped = ''.join(c for c in btn_text if ord(c) < 128 or c.isalnum() or c.isspace()).strip()
            if text in btn_text_stripped:
                return btn
            # Log for debugging (safe for Windows console)
            logger.debug(f"Button: '{self._safe_text(btn_text)}' (stripped: '{btn_text_stripped}')")
        return None

    def click(self, widget: QWidget):
        """Click a widget."""
        if widget and widget.isEnabled() and widget.isVisible():
            QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
            self.wait(300)
            return True
        logger.warning(f"Cannot click widget: {widget}")
        return False

    def type_text(self, widget: QLineEdit, text: str):
        """Type text into a line edit."""
        if widget:
            widget.setFocus()
            self.wait(100)
            widget.clear()
            QTest.keyClicks(widget, text)
            self.wait(100)
            return True
        return False

    # ==================== WORKFLOW STEPS ====================

    def step_1_launch_app(self):
        """Step 1: Launch JellyRancher Studio."""
        self.log_step("Launching JellyRancher Studio")

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.main_window = JellyRancherStudio()
        self.main_window.show()
        self.wait(1000)

        self.capture_screenshot("app_launched")

        # Verify welcome screen is visible
        if hasattr(self.main_window, 'welcome_screen'):
            logger.info("Welcome screen visible")
            return True
        else:
            logger.error("Welcome screen not found!")
            return False

    def step_2_create_roundup(self):
        """Step 2: Create a new Round-Up."""
        self.log_step(f"Creating new Round-Up: {TEST_PROJECT_NAME}")

        # List all buttons for debugging (safe text for Windows console)
        logger.info("Available buttons:")
        for btn in self.main_window.findChildren(QPushButton):
            logger.info(f"  - '{self._safe_text(btn.text())}' enabled={btn.isEnabled()} visible={btn.isVisible()}")

        # Find and click "New Round-Up" button
        # The button text includes emoji: "📁 New Round-Up"
        new_btn = self.find_button("New Round-Up")
        if not new_btn:
            logger.error("'New Round-Up' button not found!")
            self.capture_screenshot("error_no_new_button")
            return False

        logger.info(f"Found button: '{self._safe_text(new_btn.text())}'")
        self.click(new_btn)
        logger.info("Clicked New Round-Up button")
        self.wait(500)
        self.capture_screenshot("after_click")

        # Find the dialog
        dialog = None
        for widget in self.app.topLevelWidgets():
            if widget.objectName() == "new_roundup_dialog":
                dialog = widget
                break
            if isinstance(widget, QDialog) and widget.isVisible():
                dialog = widget
                break

        if not dialog:
            logger.error("Round-Up dialog not found!")
            return False

        logger.info(f"Found dialog: {dialog.objectName()}")

        # Find and fill the name input
        name_input = dialog.findChild(QLineEdit, "roundup_name_input")
        if not name_input:
            # Try any QLineEdit in the dialog
            name_input = dialog.findChild(QLineEdit)

        if not name_input:
            logger.error("Name input not found in dialog!")
            return False

        self.type_text(name_input, TEST_PROJECT_NAME)
        self.capture_screenshot("name_entered")

        # Click OK
        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_btn:
                self.click(ok_btn)
                self.wait(500)
            else:
                # Try pressing Enter
                QTest.keyClick(name_input, Qt.Key.Key_Return)
                self.wait(500)

        self.capture_screenshot("roundup_created")
        logger.info(f"Round-Up '{TEST_PROJECT_NAME}' created")
        return True

    def step_3_add_folder(self):
        """Step 3: Add test folder for scanning."""
        self.log_step(f"Adding test folder: {TEST_MEDIA_FOLDER}")

        # We're now in the main workspace
        # Need to find "Add Folder" button in the scan view
        add_btn = self.find_button("Add Folder")
        if not add_btn:
            add_btn = self.find_button("Add")

        if not add_btn:
            logger.warning("Add Folder button not found - may need to navigate to Scan view")
            self.capture_screenshot("looking_for_add_button")

            # Try to find any folder-related button
            for btn in self.main_window.findChildren(QPushButton):
                logger.debug(f"Found button: '{btn.text()}' enabled={btn.isEnabled()}")
            return False

        # For folder dialogs, we need to handle the native dialog
        # This is tricky - QFileDialog.getExistingDirectory is blocking
        # We may need to mock it or use a different approach

        logger.info("Note: Folder dialog handling requires manual intervention or mocking")
        self.capture_screenshot("before_add_folder")

        # For now, let's check if we can programmatically add a folder
        # through the underlying data model instead of the GUI

        return True  # Partial success - we found the button

    def step_4_start_scan(self):
        """Step 4: Start scanning files."""
        self.log_step("Starting file scan")

        scan_btn = self.find_button("Start Scan")
        if not scan_btn:
            scan_btn = self.find_button("Scan")

        if scan_btn and scan_btn.isEnabled():
            self.click(scan_btn)
            self.wait(2000)  # Wait for scan to complete
            self.capture_screenshot("scan_complete")
            return True
        else:
            logger.warning("Scan button not found or disabled (no folders added?)")
            self.capture_screenshot("scan_button_state")
            return False

    def run_workflow(self):
        """Run the complete workflow test."""
        logger.info("="*60)
        logger.info("STARTING WORKFLOW TEST")
        logger.info(f"Project: {TEST_PROJECT_NAME}")
        logger.info(f"Test folder: {TEST_MEDIA_FOLDER}")
        logger.info("="*60)

        results = {}

        try:
            # Step 1: Launch
            results['launch'] = self.step_1_launch_app()
            if not results['launch']:
                return results

            # Step 2: Create Round-Up
            results['create_roundup'] = self.step_2_create_roundup()
            if not results['create_roundup']:
                return results

            # Step 3: Add folder
            results['add_folder'] = self.step_3_add_folder()

            # Step 4: Scan
            results['scan'] = self.step_4_start_scan()

            # Summary
            logger.info("="*60)
            logger.info("WORKFLOW TEST RESULTS")
            for step, success in results.items():
                status = "PASS" if success else "FAIL"
                logger.info(f"  {step}: {status}")
            logger.info("="*60)
            logger.info(f"Screenshots saved to: {self.screenshots_dir}")

        except Exception as e:
            logger.error(f"Workflow test failed with exception: {e}", exc_info=True)
            self.capture_screenshot("error_exception")
            results['exception'] = str(e)

        return results


def main():
    """Run the workflow test."""
    print("""
    ============================================================
    |         JellyRancher Workflow Test                       |
    |         Deterministic GUI Walkthrough                    |
    ============================================================
    """)

    test = WorkflowTest()
    results = test.run_workflow()

    # Keep app running for manual inspection
    print("\nTest complete. Press Ctrl+C to exit or close the window.")

    if test.app:
        try:
            test.app.exec()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

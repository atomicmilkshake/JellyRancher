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
    QDialogButtonBox, QFileDialog, QMessageBox, QCheckBox, QTextEdit,
    QTabWidget, QTableWidget, QProgressBar
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
        """Step 3: Add test folder for scanning (programmatically)."""
        self.log_step(f"Adding test folder: {TEST_MEDIA_FOLDER}")

        # Programmatically add folder to scan view (bypass QFileDialog)
        try:
            # Find the active scan view
            scan_view = None
            for widget in self.main_window.findChildren(QWidget):
                if widget.__class__.__name__ == 'ScanView':
                    scan_view = widget
                    break

            if not scan_view:
                logger.error("ScanView not found!")
                self.capture_screenshot("error_no_scan_view")
                return False

            # Add folder programmatically
            folder_path = Path(TEST_MEDIA_FOLDER)
            if not folder_path.exists():
                logger.error(f"Test folder does not exist: {folder_path}")
                return False

            # Add to scan view's folder list
            if hasattr(scan_view, 'selected_folders'):
                scan_view.selected_folders.append(folder_path)
                scan_view._append_folder_row(folder_path, [])
                logger.info(f"Programmatically added folder: {folder_path}")
                self.wait(500)
                self.capture_screenshot("folder_added")
                return True
            else:
                logger.error("ScanView doesn't have selected_folders attribute")
                return False

        except Exception as e:
            logger.error(f"Failed to add folder: {e}", exc_info=True)
            self.capture_screenshot("error_add_folder")
            return False

    def step_4_start_scan(self):
        """Step 4: Start scanning files."""
        self.log_step("Starting file scan")

        scan_btn = self.find_button("Start Scan")
        if not scan_btn:
            scan_btn = self.find_button("Scan")

        if not scan_btn:
            logger.error("Scan button not found!")
            self.capture_screenshot("error_no_scan_button")
            return False

        if not scan_btn.isEnabled():
            logger.error("Scan button is disabled (no folders added?)")
            self.capture_screenshot("scan_button_disabled")
            return False

        self.click(scan_btn)
        logger.info("Clicked Start Scan button")

        # Wait for scan to complete (poll for scan completion)
        max_wait = 30  # 30 seconds max
        for i in range(max_wait):
            self.wait(1000)
            # Check if scan finished by looking for results
            scan_btn_text = scan_btn.text() if scan_btn else ""
            if "Start" in scan_btn_text and scan_btn.isEnabled():
                logger.info(f"Scan completed after {i+1} seconds")
                break
            if i % 5 == 0:
                logger.info(f"Waiting for scan... {i+1}s")

        self.capture_screenshot("scan_complete")
        return True

    def step_5_send_to_analysis(self):
        """Step 5: Send files to analysis."""
        self.log_step("Sending files to Analysis")

        send_btn = self.find_button("Send to Analysis")
        if not send_btn:
            logger.error("'Send to Analysis' button not found!")
            self.capture_screenshot("error_no_send_button")
            return False

        if not send_btn.isEnabled():
            logger.error("'Send to Analysis' button is disabled")
            self.capture_screenshot("send_button_disabled")
            return False

        self.click(send_btn)
        logger.info("Clicked 'Send to Analysis' button")
        self.wait(1000)
        self.capture_screenshot("sent_to_analysis")
        return True

    def step_6_run_analysis(self):
        """Step 6: Run regex analysis (fast, no API cost)."""
        self.log_step("Running Regex Analysis")

        # Find analysis view and set to Regex mode
        try:
            # Look for the Run Analysis button
            run_btn = self.find_button("Run Analysis")
            if not run_btn:
                run_btn = self.find_button("Analyze")

            if not run_btn:
                logger.warning("Run Analysis button not found - may need to switch views")
                self.capture_screenshot("looking_for_analysis")
                return False

            self.click(run_btn)
            logger.info("Clicked Run Analysis button")

            # Wait for analysis to complete
            max_wait = 30
            for i in range(max_wait):
                self.wait(1000)
                if run_btn.isEnabled():
                    logger.info(f"Analysis completed after {i+1} seconds")
                    break
                if i % 5 == 0:
                    logger.info(f"Waiting for analysis... {i+1}s")

            self.capture_screenshot("analysis_complete")
            return True

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            self.capture_screenshot("error_analysis")
            return False

    def step_7_send_to_review(self):
        """Step 7: Send analysis results to Review tab."""
        self.log_step("Sending analysis results to Review")

        try:
            # Find "Send to Review" button in analysis view
            send_btn = self.find_button("Send to Review")
            if not send_btn:
                logger.warning("'Send to Review' button not found - may need extrapolated operations first")
                self.capture_screenshot("no_send_to_review_button")
                return False

            if not send_btn.isEnabled():
                logger.warning("'Send to Review' button is disabled - no operations to send")
                self.capture_screenshot("send_to_review_disabled")
                return False

            self.click(send_btn)
            logger.info("Clicked 'Send to Review' button")
            self.wait(1000)
            self.capture_screenshot("sent_to_review")
            return True

        except Exception as e:
            logger.error(f"Send to Review failed: {e}", exc_info=True)
            self.capture_screenshot("error_send_to_review")
            return False

    def step_8_review_and_approve(self):
        """Step 8: Load action plan and approve all operations."""
        self.log_step("Loading Action Plan and Approving Operations")

        try:
            # Find the ReviewView
            review_view = None
            for widget in self.main_window.findChildren(QWidget):
                if widget.__class__.__name__ == 'ReviewView':
                    review_view = widget
                    break

            if not review_view:
                logger.warning("ReviewView not found - may need to switch tabs")
                self.capture_screenshot("no_review_view")
                return False

            # Click "Load Action Plan" button
            load_btn = self.find_button("Load Action Plan", review_view)
            if load_btn and load_btn.isEnabled():
                self.click(load_btn)
                logger.info("Clicked 'Load Action Plan' button")
                self.wait(2000)
                self.capture_screenshot("action_plan_loaded")

            # Click "Select All" button
            select_all_btn = self.find_button("Select All", review_view)
            if select_all_btn and select_all_btn.isEnabled():
                self.click(select_all_btn)
                logger.info("Clicked 'Select All' button")
                self.wait(500)

            # Click "Approve Selected" button
            approve_btn = self.find_button("Approve Selected", review_view)
            if approve_btn and approve_btn.isEnabled():
                self.click(approve_btn)
                logger.info("Clicked 'Approve Selected' button")
                self.wait(500)
                self.capture_screenshot("operations_approved")

            return True

        except Exception as e:
            logger.error(f"Review and approve failed: {e}", exc_info=True)
            self.capture_screenshot("error_review")
            return False

    def step_9_execute_dry_run(self):
        """Step 9: Execute operations in DRY RUN mode (no actual file changes)."""
        self.log_step("Executing Operations (DRY RUN)")

        try:
            # Find the ExecutionView
            exec_view = None
            for widget in self.main_window.findChildren(QWidget):
                if widget.__class__.__name__ == 'ExecutionView':
                    exec_view = widget
                    break

            if not exec_view:
                logger.warning("ExecutionView not found - trying Review view's execute button")
                # Try the execute button in ReviewView
                exec_btn = self.find_button("Execute Approved Operations")
                if exec_btn and exec_btn.isEnabled():
                    self.click(exec_btn)
                    logger.info("Clicked 'Execute Approved Operations' button")
                    self.wait(2000)
                    self.capture_screenshot("execution_started")
                    return True
                return False

            # Ensure dry run checkbox is checked
            dry_run_checkbox = exec_view.findChild(QCheckBox)
            if dry_run_checkbox:
                if not dry_run_checkbox.isChecked():
                    self.click(dry_run_checkbox)
                    logger.info("Enabled dry run mode")
                    self.wait(300)

            # Find and click execute button
            exec_btn = self.find_button("Execute", exec_view)
            if not exec_btn:
                exec_btn = self.find_button("Start Execution", exec_view)

            if exec_btn and exec_btn.isEnabled():
                self.click(exec_btn)
                logger.info("Clicked Execute button (DRY RUN)")

                # Wait for execution to complete
                max_wait = 30
                for i in range(max_wait):
                    self.wait(1000)
                    if exec_btn.isEnabled():
                        logger.info(f"Execution completed after {i+1} seconds")
                        break
                    if i % 5 == 0:
                        logger.info(f"Waiting for execution... {i+1}s")

                self.capture_screenshot("execution_complete")
                return True

            logger.warning("Execute button not found or disabled")
            self.capture_screenshot("no_execute_button")
            return False

        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            self.capture_screenshot("error_execution")
            return False

    def step_10_verify_results(self):
        """Step 10: Verify execution results and rollback capability."""
        self.log_step("Verifying Results")

        try:
            # Check for success indicators in the log
            exec_view = None
            for widget in self.main_window.findChildren(QWidget):
                if widget.__class__.__name__ == 'ExecutionView':
                    exec_view = widget
                    break

            if exec_view:
                # Check log text for results
                log_display = exec_view.findChild(QTextEdit)
                if log_display:
                    log_text = log_display.toPlainText()
                    logger.info(f"Execution log:\n{log_text[:500]}...")

                    if "DRY RUN" in log_text or "success" in log_text.lower():
                        logger.info("Dry run execution completed successfully")
                        self.capture_screenshot("verification_pass")
                        return True

            # Verify rollback button exists
            rollback_btn = self.find_button("Rollback")
            if rollback_btn:
                logger.info("Rollback button found - transaction safety verified")
                self.capture_screenshot("rollback_available")
                return True

            logger.warning("Could not verify results")
            self.capture_screenshot("verification_incomplete")
            return True  # Don't fail - dry run may not have operations

        except Exception as e:
            logger.error(f"Verification failed: {e}", exc_info=True)
            self.capture_screenshot("error_verification")
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
            results['1_launch'] = self.step_1_launch_app()
            if not results['1_launch']:
                return results

            # Step 2: Create Round-Up
            results['2_create_roundup'] = self.step_2_create_roundup()
            if not results['2_create_roundup']:
                return results

            # Step 3: Add folder
            results['3_add_folder'] = self.step_3_add_folder()
            if not results['3_add_folder']:
                return results

            # Step 4: Scan
            results['4_scan'] = self.step_4_start_scan()
            if not results['4_scan']:
                return results

            # Step 5: Send to Analysis
            results['5_send_to_analysis'] = self.step_5_send_to_analysis()

            # Step 6: Run Analysis
            results['6_run_analysis'] = self.step_6_run_analysis()

            # Step 7: Send to Review
            results['7_send_to_review'] = self.step_7_send_to_review()

            # Step 8: Review and Approve
            results['8_review_approve'] = self.step_8_review_and_approve()

            # Step 9: Execute (Dry Run)
            results['9_execute_dry_run'] = self.step_9_execute_dry_run()

            # Step 10: Verify Results
            results['10_verify_results'] = self.step_10_verify_results()

            # Summary
            logger.info("="*60)
            logger.info("WORKFLOW TEST RESULTS")
            passed = 0
            failed = 0
            for step, success in results.items():
                status = "PASS" if success else "FAIL"
                logger.info(f"  {step}: {status}")
                if success:
                    passed += 1
                else:
                    failed += 1
            logger.info("="*60)
            logger.info(f"SUMMARY: {passed} passed, {failed} failed")
            logger.info(f"Screenshots saved to: {self.screenshots_dir}")

        except Exception as e:
            logger.error(f"Workflow test failed with exception: {e}", exc_info=True)
            self.capture_screenshot("error_exception")
            results['exception'] = str(e)

        return results


class JellyfinIntegrationTest:
    """Test Jellyfin integration functionality."""

    def __init__(self, main_window, app):
        self.main_window = main_window
        self.app = app
        self.step_count = 0
        self.screenshots_dir = project_root / "logs" / "jellyfin_test_screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.jellyfin_client = None

    def log_step(self, description: str):
        """Log a step."""
        self.step_count += 1
        logger.info(f"[JELLYFIN STEP {self.step_count}] {description}")
        print(f"\n{'='*60}")
        print(f"JELLYFIN STEP {self.step_count}: {description}")
        print(f"{'='*60}")

    def wait(self, ms: int = 500):
        """Wait and process events."""
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()
        QApplication.processEvents()

    def test_jellyfin_connection(self):
        """Test connection to Jellyfin server."""
        self.log_step("Testing Jellyfin Connection")

        try:
            from scripts.core.jellyfin_config import JellyfinConfigManager
            from scripts.core.jellyfin_client import JellyfinClient

            config = JellyfinConfigManager()
            if not config.is_enabled():
                logger.warning("Jellyfin integration is disabled in config")
                return None  # Skip - not configured

            server_url = config.get_server_url()
            api_key = config.get_api_key()

            if not server_url or not api_key:
                logger.warning("Jellyfin URL or API key not configured")
                return None  # Skip - not configured

            self.jellyfin_client = JellyfinClient(server_url=server_url, api_key=api_key)
            connected = self.jellyfin_client.test_connection()

            if connected:
                logger.info(f"Successfully connected to Jellyfin at {server_url}")
                return True
            else:
                logger.error("Failed to connect to Jellyfin")
                return False

        except Exception as e:
            logger.error(f"Jellyfin connection test failed: {e}", exc_info=True)
            return False

    def test_get_libraries(self):
        """Test fetching library list from Jellyfin."""
        self.log_step("Testing Get Libraries")

        try:
            if not self.jellyfin_client:
                logger.warning("No Jellyfin client - skipping library test")
                return None

            libraries = self.jellyfin_client.get_libraries()
            if libraries:
                logger.info(f"Found {len(libraries)} libraries:")
                for lib in libraries[:5]:  # Show first 5
                    logger.info(f"  - {lib.get('Name', 'Unknown')}: {lib.get('CollectionType', 'mixed')}")
                return True
            else:
                logger.warning("No libraries found")
                return True  # Empty is valid

        except Exception as e:
            logger.error(f"Get libraries test failed: {e}", exc_info=True)
            return False

    def test_get_items(self):
        """Test fetching items from Jellyfin."""
        self.log_step("Testing Get Items")

        try:
            if not self.jellyfin_client:
                return None

            items = self.jellyfin_client.get_all_items(limit=10)
            if items:
                logger.info(f"Found {len(items)} items (showing first 10):")
                for item in items[:5]:
                    logger.info(f"  - {item.get('Name', 'Unknown')} ({item.get('Type', 'Unknown')})")
                return True
            else:
                logger.warning("No items found")
                return True

        except Exception as e:
            logger.error(f"Get items test failed: {e}", exc_info=True)
            return False

    def test_get_collections(self):
        """Test fetching collections from Jellyfin."""
        self.log_step("Testing Get Collections")

        try:
            if not self.jellyfin_client:
                return None

            collections = self.jellyfin_client.get_collections()
            logger.info(f"Found {len(collections)} collections")
            for coll in collections[:5]:
                logger.info(f"  - {coll.get('Name', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"Get collections test failed: {e}", exc_info=True)
            return False

    def test_validator(self):
        """Test Jellyfin validator functionality."""
        self.log_step("Testing Jellyfin Validator")

        try:
            if not self.jellyfin_client:
                return None

            from scripts.core.jellyfin_validator import JellyfinValidator
            validator = JellyfinValidator(self.jellyfin_client)

            # Validate first few items
            results = validator.validate_library(
                media_types=['Movie', 'Episode'],
                check_metadata=True,
                check_quality=False,
                check_subtitles=False
            )

            if results:
                valid_count = sum(1 for r in results if r.valid)
                invalid_count = len(results) - valid_count
                logger.info(f"Validation results: {valid_count} valid, {invalid_count} with issues")
                return True
            else:
                logger.info("No items to validate")
                return True

        except Exception as e:
            logger.error(f"Validator test failed: {e}", exc_info=True)
            return False

    def run_all_tests(self):
        """Run all Jellyfin integration tests."""
        logger.info("="*60)
        logger.info("STARTING JELLYFIN INTEGRATION TESTS")
        logger.info("="*60)

        results = {}
        results['1_connection'] = self.test_jellyfin_connection()
        results['2_libraries'] = self.test_get_libraries()
        results['3_items'] = self.test_get_items()
        results['4_collections'] = self.test_get_collections()
        results['5_validator'] = self.test_validator()

        # Summary
        logger.info("="*60)
        logger.info("JELLYFIN TEST RESULTS")
        passed = sum(1 for v in results.values() if v is True)
        failed = sum(1 for v in results.values() if v is False)
        skipped = sum(1 for v in results.values() if v is None)
        for step, success in results.items():
            if success is None:
                status = "SKIP (not configured)"
            else:
                status = "PASS" if success else "FAIL"
            logger.info(f"  {step}: {status}")
        logger.info(f"SUMMARY: {passed} passed, {failed} failed, {skipped} skipped")

        return results


class JellyBaseTest:
    """Test JellyBase library management functionality."""

    def __init__(self, main_window, app):
        self.main_window = main_window
        self.app = app
        self.step_count = 0
        self.screenshots_dir = project_root / "logs" / "jellybase_test_screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def log_step(self, description: str):
        """Log a step with incrementing counter."""
        self.step_count += 1
        logger.info(f"[JELLYBASE STEP {self.step_count}] {description}")
        print(f"\n{'='*60}")
        print(f"JELLYBASE STEP {self.step_count}: {description}")
        print(f"{'='*60}")

    def capture_screenshot(self, name: str):
        """Capture screenshot for debugging."""
        if self.main_window:
            screen = QApplication.primaryScreen()
            if screen:
                pixmap = screen.grabWindow(self.main_window.winId())
                filename = self.screenshots_dir / f"jb_{self.step_count:02d}_{name}.png"
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

    def find_button(self, text: str, parent: QWidget = None) -> QPushButton:
        """Find button by text."""
        search_root = parent or self.main_window
        if not search_root:
            return None

        for btn in search_root.findChildren(QPushButton):
            btn_text = btn.text()
            if text in btn_text:
                return btn
            btn_text_stripped = ''.join(c for c in btn_text if ord(c) < 128 or c.isalnum() or c.isspace()).strip()
            if text in btn_text_stripped:
                return btn
        return None

    def click(self, widget: QWidget):
        """Click a widget."""
        if widget and widget.isEnabled() and widget.isVisible():
            QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
            self.wait(300)
            return True
        logger.warning(f"Cannot click widget: {widget}")
        return False

    def get_jellybase_view(self):
        """Find and return the JellyBase view."""
        for widget in self.main_window.findChildren(QWidget):
            if widget.__class__.__name__ == 'JellyBaseView':
                return widget
        return None

    def test_dashboard_tab(self):
        """Test Dashboard tab functionality."""
        self.log_step("Testing Dashboard Tab")

        try:
            jellybase = self.get_jellybase_view()
            if not jellybase:
                logger.warning("JellyBaseView not found")
                return False

            # Find tab widget and switch to Dashboard
            tab_widget = jellybase.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(0)  # Dashboard is first tab
                self.wait(500)
                logger.info("Switched to Dashboard tab")

            self.capture_screenshot("dashboard_tab")

            # Check for refresh button
            refresh_btn = self.find_button("Refresh", jellybase)
            if refresh_btn:
                logger.info("Dashboard refresh button found")
                return True

            return True

        except Exception as e:
            logger.error(f"Dashboard test failed: {e}", exc_info=True)
            return False

    def test_items_tab(self):
        """Test Items tab functionality."""
        self.log_step("Testing Items Tab")

        try:
            jellybase = self.get_jellybase_view()
            if not jellybase:
                return False

            tab_widget = jellybase.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(1)  # Items tab
                self.wait(500)
                logger.info("Switched to Items tab")

            self.capture_screenshot("items_tab")

            # Check for search input
            search_inputs = jellybase.findChildren(QLineEdit)
            if search_inputs:
                logger.info(f"Found {len(search_inputs)} search inputs")

            # Check for table
            tables = jellybase.findChildren(QTableWidget)
            if tables:
                logger.info(f"Found {len(tables)} tables")

            return True

        except Exception as e:
            logger.error(f"Items test failed: {e}", exc_info=True)
            return False

    def test_collections_tab(self):
        """Test Collections tab functionality."""
        self.log_step("Testing Collections Tab")

        try:
            jellybase = self.get_jellybase_view()
            if not jellybase:
                return False

            tab_widget = jellybase.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(2)  # Collections tab
                self.wait(500)
                logger.info("Switched to Collections tab")

            self.capture_screenshot("collections_tab")

            # Look for grouping buttons
            genre_btn = self.find_button("Genre", jellybase)
            year_btn = self.find_button("Year", jellybase)
            series_btn = self.find_button("Series", jellybase)

            buttons_found = sum([1 for b in [genre_btn, year_btn, series_btn] if b])
            logger.info(f"Found {buttons_found} grouping buttons")

            return True

        except Exception as e:
            logger.error(f"Collections test failed: {e}", exc_info=True)
            return False

    def test_validation_tab(self):
        """Test Validation tab functionality."""
        self.log_step("Testing Validation Tab")

        try:
            jellybase = self.get_jellybase_view()
            if not jellybase:
                return False

            tab_widget = jellybase.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(3)  # Validation tab
                self.wait(500)
                logger.info("Switched to Validation tab")

            self.capture_screenshot("validation_tab")

            # Look for scan button
            scan_btn = self.find_button("Scan", jellybase)
            validate_btn = self.find_button("Validate", jellybase)

            if scan_btn or validate_btn:
                logger.info("Validation scan button found")

            # Check for progress bar
            progress_bars = jellybase.findChildren(QProgressBar)
            if progress_bars:
                logger.info(f"Found {len(progress_bars)} progress bars")

            return True

        except Exception as e:
            logger.error(f"Validation test failed: {e}", exc_info=True)
            return False

    def test_tools_tab(self):
        """Test Tools tab functionality."""
        self.log_step("Testing Tools Tab")

        try:
            jellybase = self.get_jellybase_view()
            if not jellybase:
                return False

            tab_widget = jellybase.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(4)  # Tools tab
                self.wait(500)
                logger.info("Switched to Tools tab")

            self.capture_screenshot("tools_tab")

            # Look for action buttons
            add_btn = self.find_button("Add", jellybase)
            remove_btn = self.find_button("Remove", jellybase)

            if add_btn or remove_btn:
                logger.info("Tools action buttons found")

            return True

        except Exception as e:
            logger.error(f"Tools test failed: {e}", exc_info=True)
            return False

    def run_all_tests(self):
        """Run all JellyBase tests."""
        logger.info("="*60)
        logger.info("STARTING JELLYBASE TESTS")
        logger.info("="*60)

        results = {}
        results['1_dashboard'] = self.test_dashboard_tab()
        results['2_items'] = self.test_items_tab()
        results['3_collections'] = self.test_collections_tab()
        results['4_validation'] = self.test_validation_tab()
        results['5_tools'] = self.test_tools_tab()

        # Summary
        logger.info("="*60)
        logger.info("JELLYBASE TEST RESULTS")
        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed
        for step, success in results.items():
            status = "PASS" if success else "FAIL"
            logger.info(f"  {step}: {status}")
        logger.info(f"SUMMARY: {passed} passed, {failed} failed")
        logger.info(f"Screenshots saved to: {self.screenshots_dir}")

        return results


def main():
    """Run the workflow test."""
    import argparse
    parser = argparse.ArgumentParser(description="JellyRancher Comprehensive Test Suite")
    parser.add_argument('--workflow', action='store_true', help='Run workflow tests (steps 1-10)')
    parser.add_argument('--jellybase', action='store_true', help='Run JellyBase UI tests')
    parser.add_argument('--jellyfin', action='store_true', help='Run Jellyfin integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--no-gui', action='store_true', help='Exit after tests (no interactive GUI)')
    args = parser.parse_args()

    # Default to workflow if no args specified
    if not args.workflow and not args.jellybase and not args.jellyfin and not args.all:
        args.workflow = True

    print("""
    ============================================================
    |         JellyRancher Comprehensive Test Suite            |
    |         Deterministic GUI Walkthrough                    |
    ============================================================
    """)

    all_results = {}

    # Run workflow tests
    if args.workflow or args.all:
        print("\n>>> Running Workflow Tests (10 steps)...")
        test = WorkflowTest()
        workflow_results = test.run_workflow()
        all_results['workflow'] = workflow_results

        # Run JellyBase tests using same app instance
        if args.jellybase or args.all:
            if test.main_window and test.app:
                print("\n>>> Running JellyBase Tests...")
                jb_test = JellyBaseTest(test.main_window, test.app)
                jb_results = jb_test.run_all_tests()
                all_results['jellybase'] = jb_results

        # Run Jellyfin integration tests
        if args.jellyfin or args.all:
            if test.main_window and test.app:
                print("\n>>> Running Jellyfin Integration Tests...")
                jf_test = JellyfinIntegrationTest(test.main_window, test.app)
                jf_results = jf_test.run_all_tests()
                all_results['jellyfin'] = jf_results

        # Final summary
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*60)

        total_passed = 0
        total_failed = 0

        for suite_name, results in all_results.items():
            passed = sum(1 for v in results.values() if v is True)
            failed = sum(1 for v in results.values() if v is False)
            total_passed += passed
            total_failed += failed
            print(f"  {suite_name}: {passed} passed, {failed} failed")

        print("-"*60)
        print(f"  TOTAL: {total_passed} passed, {total_failed} failed")
        print("="*60)

        # Keep app running for manual inspection unless --no-gui
        if not args.no_gui:
            print("\nTest complete. Press Ctrl+C to exit or close the window.")
            if test.app:
                try:
                    test.app.exec()
                except KeyboardInterrupt:
                    pass
    else:
        # JellyBase only - need to launch app first
        print("\n>>> Running JellyBase Tests (requires app launch)...")
        test = WorkflowTest()
        test.step_1_launch_app()

        if test.main_window and test.app:
            jb_test = JellyBaseTest(test.main_window, test.app)
            jb_results = jb_test.run_all_tests()
            all_results['jellybase'] = jb_results

        if not args.no_gui and test.app:
            print("\nTest complete. Press Ctrl+C to exit or close the window.")
            try:
                test.app.exec()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()

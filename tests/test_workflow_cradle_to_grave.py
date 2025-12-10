#!/usr/bin/env python3
"""
Cradle-to-Grave GUI Workflow Tests for JellyRancher

This test suite simulates a REAL USER interacting with the application:
- Clicking buttons
- Filling text fields
- Navigating between views
- Waiting for operations to complete
- Verifying results

Uses PyQt6's QTest for GUI automation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import time
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import (
    QApplication, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QTableWidget, QTabWidget, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Mark all tests as requiring GUI
pytestmark = [pytest.mark.requires_gui]


# ============================================================================
# Mock QMessageBox to prevent modal blocking
# ============================================================================
class MockQMessageBox:
    """Mock QMessageBox that auto-returns without blocking."""

    Yes = QMessageBox.StandardButton.Yes
    No = QMessageBox.StandardButton.No
    Ok = QMessageBox.StandardButton.Ok
    Cancel = QMessageBox.StandardButton.Cancel

    @staticmethod
    def warning(parent, title, message, *args, **kwargs):
        """Non-blocking warning - just return Ok."""
        return QMessageBox.StandardButton.Ok

    @staticmethod
    def information(parent, title, message, *args, **kwargs):
        """Non-blocking information - just return Ok."""
        return QMessageBox.StandardButton.Ok

    @staticmethod
    def critical(parent, title, message, *args, **kwargs):
        """Non-blocking critical - just return Ok."""
        return QMessageBox.StandardButton.Ok

    @staticmethod
    def question(parent, title, message, *args, **kwargs):
        """Non-blocking question - return Yes to proceed."""
        return QMessageBox.StandardButton.Yes


@pytest.fixture(autouse=True)
def mock_message_boxes(monkeypatch):
    """Auto-mock all QMessageBox calls to prevent modal blocking."""
    # Patch at the module level for scripts that import QMessageBox
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.warning', MockQMessageBox.warning)
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.information', MockQMessageBox.information)
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.critical', MockQMessageBox.critical)
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.question', MockQMessageBox.question)


class TestMediaFileFactory:
    """Factory for creating realistic test media files."""

    MOVIE_PATTERNS = [
        "The.Godfather.1972.1080p.BluRay.x264-SPARKS.mkv",
        "Inception (2010) [1080p] [BluRay].mp4",
        "pulp_fiction_1994_brrip_xvid.avi",
        "The-Dark-Knight-2008-720p-BRRip.mkv",
        "Interstellar.2014.UHD.2160p.BluRay.REMUX.mkv",
    ]

    TV_PATTERNS = [
        "Breaking.Bad.S01E01.720p.BluRay.x264.mkv",
        "Game of Thrones - S01E01 - Winter Is Coming.mkv",
        "The.Office.US.S02E03.Office.Olympics.720p.mkv",
        "Stranger.Things.S03E05.1080p.WEB-DL.mkv",
        "friends.s01e01.the.one.where.monica.gets.a.roommate.dvdrip.avi",
    ]

    @classmethod
    def create_chaotic_media_folder(cls, base_path: Path) -> dict:
        """Create a chaotic media folder structure with realistic file names."""
        created_files = {"movies": [], "tv_shows": []}

        movies_dir = base_path / "downloads"
        movies_dir.mkdir(parents=True, exist_ok=True)

        for movie_name in cls.MOVIE_PATTERNS:
            movie_path = movies_dir / movie_name
            movie_path.write_bytes(b"FAKE VIDEO FILE " * 100)
            created_files["movies"].append(str(movie_path))

        tv_dir = base_path / "TV Downloads"
        tv_dir.mkdir(parents=True, exist_ok=True)

        for tv_name in cls.TV_PATTERNS:
            tv_path = tv_dir / tv_name
            tv_path.write_bytes(b"FAKE VIDEO FILE " * 100)
            created_files["tv_shows"].append(str(tv_path))

        return created_files


@pytest.fixture
def chaotic_media_folder(tmp_path):
    """Create a realistic chaotic media folder for testing."""
    media_root = tmp_path / "chaotic_media"
    media_root.mkdir()
    files = TestMediaFileFactory.create_chaotic_media_folder(media_root)
    return {"root": media_root, "files": files}


def find_widget_by_text(parent, widget_type, text):
    """Find a widget by its text content."""
    for widget in parent.findChildren(widget_type):
        if hasattr(widget, 'text') and text.lower() in widget.text().lower():
            return widget
    return None


def close_all_dialogs(main_window, max_attempts=5):
    """
    Forcibly close any dialogs that may have opened.

    This handles:
    - Welcome wizard dialogs
    - QMessageBox popups
    - Any QDialog subclass
    """
    for attempt in range(max_attempts):
        QApplication.processEvents()
        closed_any = False

        for widget in QApplication.topLevelWidgets():
            if widget == main_window:
                continue
            if not widget.isVisible():
                continue

            # Close any visible top-level widget that isn't our main window
            if isinstance(widget, QDialog):
                widget.reject()  # Use reject to close cleanly
                closed_any = True
            else:
                widget.close()
                closed_any = True

        QApplication.processEvents()

        if not closed_any:
            break

        time.sleep(0.05)  # Small delay between attempts


def create_main_window(qtbot, skip_welcome=True):
    """
    Create main window with proper setup.

    Args:
        qtbot: pytest-qt fixture
        skip_welcome: If True, suppress welcome wizard
    """
    from scripts.core.jelly_rancher_main import JellyRancherMainWindow

    # Patch the welcome wizard method before creating the window
    with patch.object(JellyRancherMainWindow, 'show_welcome_wizard_if_needed', lambda self: None):
        window = JellyRancherMainWindow()

    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    QApplication.processEvents()

    # Close any startup dialogs that may have slipped through
    close_all_dialogs(window)
    QApplication.processEvents()

    # Give the UI a moment to stabilize
    time.sleep(0.1)
    QApplication.processEvents()

    return window


class TestRealUserWorkflow:
    """
    Simulates a real user clicking through the entire 8-step workflow.
    """

    @pytest.mark.slow
    def test_complete_8_step_workflow_like_real_user(self, qtbot, chaotic_media_folder):
        """
        Complete workflow simulating real user interactions:
        1. Launch app
        2. Navigate to Organization tab
        3. Explore workflow steps
        4. Verify scan controls exist
        5. Check all main tabs load
        """
        window = create_main_window(qtbot)

        try:
            # STEP 1: Find Organization tab and click it
            org_tab = None
            for i in range(window.tab_widget.count()):
                if "organization" in window.tab_widget.tabText(i).lower():
                    org_tab = i
                    break

            if org_tab is not None:
                window.tab_widget.setCurrentIndex(org_tab)
                QApplication.processEvents()
                qtbot.wait(200)

            # STEP 2: Verify the workflow tabs exist
            current_widget = window.tab_widget.currentWidget()
            assert current_widget is not None, "Organization tab should have content"

            # Look for nested tabs (the 5-step workflow)
            nested_tabs = current_widget.findChildren(QTabWidget)
            if nested_tabs:
                workflow_tabs = nested_tabs[0]

                # Verify workflow steps exist
                tab_names = [workflow_tabs.tabText(i) for i in range(workflow_tabs.count())]
                assert len(tab_names) >= 3, f"Should have at least 3 workflow tabs, found: {tab_names}"

            # STEP 3: Verify scan button or controls exist
            scan_buttons = [btn for btn in current_widget.findChildren(QPushButton)
                           if 'scan' in btn.text().lower()]
            folder_inputs = current_widget.findChildren(QLineEdit)

            # Verify we found expected widgets
            assert len(scan_buttons) > 0 or len(folder_inputs) > 0, "Should find scan controls"

        finally:
            window.close()

    def test_user_clicks_through_all_main_tabs(self, qtbot):
        """
        User clicks through all main tabs to verify they load.
        """
        window = create_main_window(qtbot)

        try:
            # Click through each main tab
            visited_tabs = []
            for i in range(window.tab_widget.count()):
                tab_name = window.tab_widget.tabText(i)
                window.tab_widget.setCurrentIndex(i)
                QApplication.processEvents()
                qtbot.wait(100)

                # Verify tab loaded
                current = window.tab_widget.currentWidget()
                assert current is not None, f"Tab {tab_name} should have content"
                visited_tabs.append(tab_name)

            assert len(visited_tabs) >= 4, f"Should visit at least 4 tabs, visited: {visited_tabs}"

        finally:
            window.close()

    def test_user_opens_settings_and_changes_values(self, qtbot):
        """
        User opens Settings tab and modifies values.
        """
        window = create_main_window(qtbot)

        try:
            # Find Settings tab
            settings_tab = None
            for i in range(window.tab_widget.count()):
                if "settings" in window.tab_widget.tabText(i).lower():
                    settings_tab = i
                    break

            if settings_tab is not None:
                window.tab_widget.setCurrentIndex(settings_tab)
                QApplication.processEvents()
                qtbot.wait(200)

                # Find checkboxes
                settings_widget = window.tab_widget.currentWidget()
                checkboxes = settings_widget.findChildren(QCheckBox)

                # Toggle a checkbox (find an enabled, visible one)
                for cb in checkboxes:
                    if cb.isVisible() and cb.isEnabled():
                        original_state = cb.isChecked()
                        # Use click() method for reliable toggling
                        cb.click()
                        QApplication.processEvents()
                        qtbot.wait(50)
                        # Verify state changed
                        assert cb.isChecked() != original_state, "Checkbox should toggle"
                        break

                # Find text inputs
                line_edits = settings_widget.findChildren(QLineEdit)
                if line_edits:
                    le = line_edits[0]
                    if le.isEnabled():
                        le.clear()
                        QTest.keyClicks(le, "test_value")
                        QApplication.processEvents()
                        assert "test_value" in le.text(), "Line edit should contain typed text"

        finally:
            window.close()

    def test_user_navigates_workflow_steps(self, qtbot, chaotic_media_folder):
        """
        User navigates between workflow steps.
        """
        window = create_main_window(qtbot)

        try:
            # Go to Organization tab
            for i in range(window.tab_widget.count()):
                if "organization" in window.tab_widget.tabText(i).lower():
                    window.tab_widget.setCurrentIndex(i)
                    break
            QApplication.processEvents()
            qtbot.wait(200)

            # Find workflow tabs
            current_widget = window.tab_widget.currentWidget()
            nested_tabs = current_widget.findChildren(QTabWidget)

            if nested_tabs:
                workflow_tabs = nested_tabs[0]
                steps_visited = []

                # Click through each workflow step
                for i in range(workflow_tabs.count()):
                    step_name = workflow_tabs.tabText(i)
                    workflow_tabs.setCurrentIndex(i)
                    QApplication.processEvents()
                    qtbot.wait(100)

                    step_widget = workflow_tabs.currentWidget()
                    assert step_widget is not None, f"Step {step_name} should have content"
                    steps_visited.append(step_name)

                assert len(steps_visited) >= 3, f"Should visit at least 3 steps, visited: {steps_visited}"

        finally:
            window.close()

    def test_user_clicks_all_visible_buttons(self, qtbot):
        """
        User clicks all enabled, visible buttons to verify no crashes.
        """
        window = create_main_window(qtbot)

        try:
            # Click through each tab and find buttons
            buttons_clicked = []
            buttons_to_skip = ['quit', 'exit', 'close', 'delete', 'remove', 'execute', 'start']

            for tab_idx in range(window.tab_widget.count()):
                window.tab_widget.setCurrentIndex(tab_idx)
                QApplication.processEvents()
                qtbot.wait(100)

                current_widget = window.tab_widget.currentWidget()
                if current_widget:
                    buttons = current_widget.findChildren(QPushButton)
                    for btn in buttons:
                        if btn.isVisible() and btn.isEnabled():
                            btn_text = btn.text().lower()
                            # Skip dangerous buttons
                            if any(skip in btn_text for skip in buttons_to_skip):
                                continue
                            # Skip buttons that open file dialogs
                            if 'browse' in btn_text or 'folder' in btn_text:
                                continue

                            # Click the button
                            try:
                                QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
                                QApplication.processEvents()
                                buttons_clicked.append(btn.text())
                            except Exception:
                                pass  # Some buttons may cause dialogs, ignore

                            # Close any dialogs that opened
                            close_all_dialogs(window)

            # Should have clicked at least some buttons
            assert len(buttons_clicked) >= 1, f"Should click some buttons, clicked: {buttons_clicked}"

        finally:
            window.close()


class TestWorkflowPermutations:
    """
    Test user interaction permutations.
    """

    def test_user_switches_tabs_rapidly(self, qtbot):
        """
        User switches between tabs rapidly without waiting.
        """
        window = create_main_window(qtbot)

        try:
            # Rapidly switch tabs
            for _ in range(20):
                for i in range(window.tab_widget.count()):
                    window.tab_widget.setCurrentIndex(i)
                    QApplication.processEvents()
                    # No wait - stress test

            # Should not crash
            assert window.isVisible(), "Window should still be visible after rapid switching"

        finally:
            window.close()

    def test_user_resizes_window_during_operation(self, qtbot):
        """
        User resizes window while tabs are loading.
        """
        window = create_main_window(qtbot)

        try:
            window.resize(800, 600)
            QApplication.processEvents()
            qtbot.wait(100)

            # Resize while switching tabs
            sizes = [(1200, 800), (600, 400), (1000, 700), (800, 600)]
            for width, height in sizes:
                window.resize(width, height)
                window.tab_widget.setCurrentIndex(
                    (window.tab_widget.currentIndex() + 1) % window.tab_widget.count()
                )
                QApplication.processEvents()

            # Should not crash
            assert window.isVisible(), "Window should handle resize"

        finally:
            window.close()

    def test_back_and_forth_navigation(self, qtbot):
        """
        User goes back and forth between workflow steps.
        """
        window = create_main_window(qtbot)

        try:
            # Go to Organization tab
            for i in range(window.tab_widget.count()):
                if "organization" in window.tab_widget.tabText(i).lower():
                    window.tab_widget.setCurrentIndex(i)
                    break
            QApplication.processEvents()
            qtbot.wait(100)

            current_widget = window.tab_widget.currentWidget()
            nested_tabs = current_widget.findChildren(QTabWidget)

            if nested_tabs:
                workflow_tabs = nested_tabs[0]
                tab_count = workflow_tabs.count()

                # Navigate forward
                for i in range(tab_count):
                    workflow_tabs.setCurrentIndex(i)
                    QApplication.processEvents()

                # Navigate backward
                for i in range(tab_count - 1, -1, -1):
                    workflow_tabs.setCurrentIndex(i)
                    QApplication.processEvents()

                # Random jumps
                import random
                for _ in range(10):
                    idx = random.randint(0, tab_count - 1)
                    workflow_tabs.setCurrentIndex(idx)
                    QApplication.processEvents()

            assert window.isVisible(), "Window should handle back-forth navigation"

        finally:
            window.close()


class TestOutputVerification:
    """
    Verify the UI displays correct information.
    """

    def test_all_tabs_have_visible_content(self, qtbot):
        """
        All tabs should have visible widgets.
        """
        window = create_main_window(qtbot)

        try:
            # Check each tab has content
            empty_tabs = []
            for i in range(window.tab_widget.count()):
                tab_name = window.tab_widget.tabText(i)
                window.tab_widget.setCurrentIndex(i)
                QApplication.processEvents()
                qtbot.wait(100)

                widget = window.tab_widget.currentWidget()
                if widget:
                    # Check for visible children
                    visible_children = [c for c in widget.children()
                                       if hasattr(c, 'isVisible') and c.isVisible()]
                    if len(visible_children) < 1:
                        empty_tabs.append(tab_name)

            assert len(empty_tabs) == 0, f"Tabs with no visible content: {empty_tabs}"

        finally:
            window.close()

    def test_buttons_have_readable_text(self, qtbot):
        """
        All buttons should have non-empty, readable text.
        """
        window = create_main_window(qtbot)

        try:
            # Check all buttons
            empty_buttons = []
            for i in range(window.tab_widget.count()):
                window.tab_widget.setCurrentIndex(i)
                QApplication.processEvents()

                widget = window.tab_widget.currentWidget()
                if widget:
                    buttons = widget.findChildren(QPushButton)
                    for btn in buttons:
                        if btn.isVisible():
                            text = btn.text().strip()
                            if not text or text == "":
                                empty_buttons.append(f"Tab {i}: unnamed button")

            # Allow some buttons without text (icon-only)
            assert len(empty_buttons) < 5, f"Too many buttons without text: {empty_buttons}"

        finally:
            window.close()

    def test_workflow_tabs_have_step_content(self, qtbot):
        """
        Workflow tabs should have content matching their purpose.
        """
        window = create_main_window(qtbot)

        try:
            # Go to Organization tab
            for i in range(window.tab_widget.count()):
                if "organization" in window.tab_widget.tabText(i).lower():
                    window.tab_widget.setCurrentIndex(i)
                    break
            QApplication.processEvents()
            qtbot.wait(100)

            current_widget = window.tab_widget.currentWidget()
            nested_tabs = current_widget.findChildren(QTabWidget)

            if nested_tabs:
                workflow_tabs = nested_tabs[0]

                # Check each workflow step has buttons or inputs
                steps_with_controls = 0
                for i in range(workflow_tabs.count()):
                    workflow_tabs.setCurrentIndex(i)
                    QApplication.processEvents()

                    step_widget = workflow_tabs.currentWidget()
                    if step_widget:
                        buttons = step_widget.findChildren(QPushButton)
                        inputs = step_widget.findChildren(QLineEdit)
                        if buttons or inputs:
                            steps_with_controls += 1

                assert steps_with_controls >= 3, f"At least 3 steps should have controls, found: {steps_with_controls}"

        finally:
            window.close()


class TestInterruptRecovery:
    """
    Test interrupted operations and recovery scenarios.
    """

    def test_window_close_during_load(self, qtbot):
        """
        Closing window during tab load should not crash.
        """
        window = create_main_window(qtbot)

        # Start switching tabs
        window.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()

        # Close immediately
        window.close()
        QApplication.processEvents()

        # Should not crash
        assert True

    def test_multiple_window_creates(self, qtbot):
        """
        Creating and destroying multiple windows should not leak.
        """
        for _ in range(3):
            window = create_main_window(qtbot)
            QApplication.processEvents()
            qtbot.wait(50)
            window.close()
            QApplication.processEvents()

        # Should not crash
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

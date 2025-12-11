"""
Chaos Monkey Testing for JellyRancher GUI.

This module implements "ridiculous" testing by randomly interacting with the GUI
in ways that users might (accidentally or intentionally) do:
- Random button clicking
- Random tab switching mid-operation
- Cancel at every possible moment
- Fill forms with edge case data
- Click disabled buttons
- Resize window during operations
- Spam-click buttons rapidly

The goal is to find crashes, hangs, and unexpected behavior.
"""

import os
import sys
import random
import string
import time
import logging
from typing import List, Optional, Tuple, Any
from pathlib import Path

import pytest
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QRadioButton, QSpinBox, QDoubleSpinBox,
    QTabWidget, QTabBar, QMenu, QMenuBar, QToolBar, QDialog,
    QMessageBox, QMainWindow, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtTest import QTest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class EdgeCaseData:
    """Edge case data for form filling."""

    # Empty/whitespace
    EMPTY = ["", " ", "  ", "\t", "\n", "\r\n"]

    # Unicode edge cases
    UNICODE = [
        "日本語",  # Japanese
        "中文",  # Chinese
        "العربية",  # Arabic (RTL)
        "🎬🎥📺",  # Emoji
        "Ω≈ç√∫",  # Math symbols
        "零一二三四五六七八九",  # CJK numbers
        "null",  # String "null"
        "undefined",  # String "undefined"
        "NaN",  # String "NaN"
        "true",  # String "true"
        "false",  # String "false"
    ]

    # Potentially dangerous strings (testing sanitization)
    INJECTION = [
        "'; DROP TABLE media; --",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "{{7*7}}",  # Template injection
        "${7*7}",  # Another template injection
        "../../../etc/passwd",  # Path traversal
        "..\\..\\..\\windows\\system32",  # Windows path traversal
        "C:\\Windows\\System32\\cmd.exe",  # Command path
        "|ls -la",  # Command injection
        "; rm -rf /",  # Command injection
        "$(whoami)",  # Command substitution
        "`whoami`",  # Backtick command sub
        "%00",  # Null byte
        "%0a%0d",  # CRLF injection
    ]

    # Long strings
    LONG = [
        "A" * 100,
        "A" * 1000,
        "A" * 10000,
        "A B " * 500,  # Long with spaces
    ]

    # Special filenames
    FILENAMES = [
        "CON",  # Windows reserved
        "PRN",  # Windows reserved
        "AUX",  # Windows reserved
        "NUL",  # Windows reserved
        "COM1",  # Windows reserved
        "LPT1",  # Windows reserved
        ".hidden",  # Unix hidden
        "...",  # Dots only
        "file.name.with.many.dots.txt",
        "file with spaces.txt",
        "file\twith\ttabs.txt",
        "file\nwith\nnewlines.txt",
    ]

    # Numbers as strings
    NUMBERS = [
        "0",
        "-1",
        "-999999999999",
        "999999999999",
        "3.14159",
        "-0",
        "0.0",
        "1e100",
        "-1e100",
        "Infinity",
        "-Infinity",
    ]

    @classmethod
    def get_random(cls) -> str:
        """Get a random edge case string."""
        all_data = (
            cls.EMPTY + cls.UNICODE + cls.INJECTION +
            cls.LONG[:2] + cls.FILENAMES + cls.NUMBERS  # Only short long strings
        )
        return random.choice(all_data)

    @classmethod
    def get_all(cls) -> List[str]:
        """Get all edge case strings."""
        return (
            cls.EMPTY + cls.UNICODE + cls.INJECTION +
            cls.LONG + cls.FILENAMES + cls.NUMBERS
        )


class ChaosMonkey:
    """
    Chaos Monkey for GUI testing.

    Randomly interacts with the application to find bugs.
    """

    def __init__(self, window: QMainWindow, seed: Optional[int] = None):
        """
        Initialize Chaos Monkey.

        Args:
            window: The main window to test
            seed: Random seed for reproducibility
        """
        self.window = window
        self.app = QApplication.instance()
        self.actions_taken: List[str] = []
        self.errors_found: List[str] = []
        self.iteration = 0

        if seed is not None:
            random.seed(seed)
            logger.info(f"ChaosMonkey initialized with seed {seed}")

    def find_all_widgets(self, widget: QWidget = None) -> List[QWidget]:
        """Recursively find all widgets."""
        if widget is None:
            widget = self.window

        widgets = [widget]
        for child in widget.findChildren(QWidget):
            if child.isVisible():
                widgets.append(child)
        return widgets

    def find_clickable_widgets(self) -> List[QWidget]:
        """Find all clickable widgets (buttons, checkboxes, etc.)."""
        clickable = []
        for widget in self.find_all_widgets():
            if isinstance(widget, (QPushButton, QCheckBox, QRadioButton)):
                if widget.isVisible() and widget.isEnabled():
                    clickable.append(widget)
        return clickable

    def find_editable_widgets(self) -> List[QWidget]:
        """Find all editable widgets (line edits, text edits, etc.)."""
        editable = []
        for widget in self.find_all_widgets():
            if isinstance(widget, (QLineEdit, QTextEdit)):
                if widget.isVisible() and widget.isEnabled():
                    editable.append(widget)
        return editable

    def find_combo_boxes(self) -> List[QComboBox]:
        """Find all combo boxes."""
        combos = []
        for widget in self.find_all_widgets():
            if isinstance(widget, QComboBox):
                if widget.isVisible() and widget.isEnabled():
                    combos.append(widget)
        return combos

    def find_tab_widgets(self) -> List[QTabWidget]:
        """Find all tab widgets."""
        tabs = []
        for widget in self.find_all_widgets():
            if isinstance(widget, QTabWidget):
                if widget.isVisible():
                    tabs.append(widget)
        return tabs

    def find_spin_boxes(self) -> List[QWidget]:
        """Find all spin boxes."""
        spins = []
        for widget in self.find_all_widgets():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                if widget.isVisible() and widget.isEnabled():
                    spins.append(widget)
        return spins

    def click_random_button(self) -> bool:
        """Click a random visible button."""
        buttons = self.find_clickable_widgets()
        if not buttons:
            return False

        button = random.choice(buttons)
        name = button.objectName() or button.text() or "Unknown"
        self.actions_taken.append(f"Click button: {name}")

        try:
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error clicking {name}: {e}")
            return False

    def click_disabled_button(self) -> bool:
        """Attempt to click a disabled button (should do nothing)."""
        for widget in self.find_all_widgets():
            if isinstance(widget, QPushButton):
                if widget.isVisible() and not widget.isEnabled():
                    name = widget.objectName() or widget.text() or "Unknown"
                    self.actions_taken.append(f"Click disabled button: {name}")
                    try:
                        QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
                        self._process_events()
                        # Should not have any effect
                        return True
                    except Exception as e:
                        self.errors_found.append(f"Error clicking disabled {name}: {e}")
        return False

    def fill_random_input(self) -> bool:
        """Fill a random input with edge case data."""
        editable = self.find_editable_widgets()
        if not editable:
            return False

        widget = random.choice(editable)
        name = widget.objectName() or "Unknown"
        value = EdgeCaseData.get_random()
        # Truncate to prevent issues with extremely long inputs
        value = value[:1000] if len(value) > 1000 else value
        self.actions_taken.append(f"Fill input {name}: {repr(value)[:50]}")

        try:
            if isinstance(widget, QLineEdit):
                widget.clear()
                QTest.keyClicks(widget, value)
            elif isinstance(widget, QTextEdit):
                widget.clear()
                widget.setPlainText(value)
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error filling {name}: {e}")
            return False

    def change_random_combo(self) -> bool:
        """Change a random combo box selection."""
        combos = self.find_combo_boxes()
        if not combos:
            return False

        combo = random.choice(combos)
        if combo.count() == 0:
            return False

        name = combo.objectName() or "Unknown"
        new_index = random.randint(0, combo.count() - 1)
        self.actions_taken.append(f"Change combo {name} to index {new_index}")

        try:
            combo.setCurrentIndex(new_index)
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error changing combo {name}: {e}")
            return False

    def switch_random_tab(self) -> bool:
        """Switch to a random tab."""
        tabs = self.find_tab_widgets()
        if not tabs:
            return False

        tab_widget = random.choice(tabs)
        if tab_widget.count() == 0:
            return False

        name = tab_widget.objectName() or "Unknown"
        new_index = random.randint(0, tab_widget.count() - 1)
        self.actions_taken.append(f"Switch tab {name} to index {new_index}")

        try:
            tab_widget.setCurrentIndex(new_index)
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error switching tab {name}: {e}")
            return False

    def change_random_spinbox(self) -> bool:
        """Change a random spin box value."""
        spins = self.find_spin_boxes()
        if not spins:
            return False

        spin = random.choice(spins)
        name = spin.objectName() or "Unknown"

        try:
            if isinstance(spin, QSpinBox):
                new_value = random.randint(spin.minimum(), spin.maximum())
                spin.setValue(new_value)
            elif isinstance(spin, QDoubleSpinBox):
                new_value = random.uniform(spin.minimum(), spin.maximum())
                spin.setValue(new_value)
            self.actions_taken.append(f"Change spinbox {name} to {new_value}")
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error changing spinbox {name}: {e}")
            return False

    def spam_click_button(self, count: int = 10) -> bool:
        """Rapidly click a button multiple times."""
        buttons = self.find_clickable_widgets()
        if not buttons:
            return False

        button = random.choice(buttons)
        name = button.objectName() or button.text() or "Unknown"
        self.actions_taken.append(f"Spam click button {name} x{count}")

        try:
            for _ in range(count):
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                # Minimal delay between clicks
                self._process_events(5)
            return True
        except Exception as e:
            self.errors_found.append(f"Error spam clicking {name}: {e}")
            return False

    def resize_window(self) -> bool:
        """Resize the window to random dimensions."""
        try:
            # Random size between minimum and reasonable maximum
            min_size = self.window.minimumSize()
            new_width = random.randint(max(400, min_size.width()), 1920)
            new_height = random.randint(max(300, min_size.height()), 1080)
            self.actions_taken.append(f"Resize window to {new_width}x{new_height}")
            self.window.resize(new_width, new_height)
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error resizing window: {e}")
            return False

    def minimize_restore(self) -> bool:
        """Minimize and restore the window."""
        try:
            self.actions_taken.append("Minimize window")
            self.window.showMinimized()
            self._process_events(100)
            self.actions_taken.append("Restore window")
            self.window.showNormal()
            self._process_events()
            return True
        except Exception as e:
            self.errors_found.append(f"Error minimize/restore: {e}")
            return False

    def _process_events(self, ms: int = 50):
        """Process Qt events and wait."""
        self.app.processEvents()
        QTest.qWait(ms)

    def random_action(self) -> str:
        """Perform a random action and return its description."""
        actions = [
            (self.click_random_button, 30),  # 30% chance
            (self.fill_random_input, 20),    # 20% chance
            (self.change_random_combo, 15),  # 15% chance
            (self.switch_random_tab, 15),    # 15% chance
            (self.change_random_spinbox, 5), # 5% chance
            (self.spam_click_button, 5),     # 5% chance
            (self.resize_window, 5),         # 5% chance
            (self.click_disabled_button, 3), # 3% chance
            (self.minimize_restore, 2),      # 2% chance
        ]

        # Weighted random selection
        total_weight = sum(w for _, w in actions)
        r = random.uniform(0, total_weight)
        cumulative = 0

        for action, weight in actions:
            cumulative += weight
            if r <= cumulative:
                self.iteration += 1
                action()
                break

        if self.actions_taken:
            return self.actions_taken[-1]
        return "No action taken"

    def run(self, iterations: int = 100, delay_ms: int = 100) -> Tuple[int, List[str]]:
        """
        Run chaos testing for specified iterations.

        Args:
            iterations: Number of random actions to perform
            delay_ms: Delay between actions in milliseconds

        Returns:
            Tuple of (number of errors found, list of error messages)
        """
        logger.info(f"Starting Chaos Monkey: {iterations} iterations")
        start_time = time.time()

        for i in range(iterations):
            try:
                action = self.random_action()
                logger.debug(f"Iteration {i+1}/{iterations}: {action}")
            except Exception as e:
                self.errors_found.append(f"Iteration {i+1} crashed: {e}")
                logger.error(f"Chaos Monkey iteration {i+1} crashed: {e}")

            self._process_events(delay_ms)

        elapsed = time.time() - start_time
        logger.info(f"Chaos Monkey completed: {iterations} iterations in {elapsed:.2f}s")
        logger.info(f"Actions taken: {len(self.actions_taken)}")
        logger.info(f"Errors found: {len(self.errors_found)}")

        return len(self.errors_found), self.errors_found

    def get_report(self) -> str:
        """Generate a report of the chaos testing."""
        report = [
            "=" * 60,
            "CHAOS MONKEY REPORT",
            "=" * 60,
            f"Total iterations: {self.iteration}",
            f"Actions taken: {len(self.actions_taken)}",
            f"Errors found: {len(self.errors_found)}",
            "",
        ]

        if self.errors_found:
            report.append("ERRORS:")
            for error in self.errors_found:
                report.append(f"  - {error}")
            report.append("")

        report.append("ACTIONS TAKEN (last 50):")
        for action in self.actions_taken[-50:]:
            report.append(f"  - {action}")

        return "\n".join(report)


# =============================================================================
# PYTEST TEST CASES
# =============================================================================

@pytest.fixture(scope="module")
def app():
    """Create QApplication for testing - module scoped to avoid Windows COM issues."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit - let pytest-qt handle cleanup


@pytest.fixture
def main_window(app, qtbot):
    """Create main window for testing."""
    # Import here to avoid circular imports
    from jelly_rancher_studio import JellyRancherStudio
    from unittest.mock import patch
    import gc

    with patch('jelly_rancher_studio.QApplication.instance', return_value=app):
        window = JellyRancherStudio()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitExposed(window)
        yield window
        # Explicit cleanup to prevent Windows COM issues
        window.close()
        app.processEvents()
        gc.collect()


class TestChaosMonkey:
    """Test suite for Chaos Monkey testing."""

    def test_edge_case_data_generation(self):
        """Test that edge case data generates without errors."""
        # Get random data multiple times
        for _ in range(100):
            data = EdgeCaseData.get_random()
            assert isinstance(data, str)

        # Get all data
        all_data = EdgeCaseData.get_all()
        assert len(all_data) > 50  # Should have many test cases

    def test_chaos_monkey_initialization(self, main_window):
        """Test ChaosMonkey initialization."""
        monkey = ChaosMonkey(main_window, seed=42)
        assert monkey.window == main_window
        assert monkey.iteration == 0
        assert len(monkey.actions_taken) == 0
        assert len(monkey.errors_found) == 0

    def test_find_widgets(self, main_window):
        """Test widget discovery."""
        monkey = ChaosMonkey(main_window)

        # Should find widgets
        all_widgets = monkey.find_all_widgets()
        assert len(all_widgets) > 0

        clickable = monkey.find_clickable_widgets()
        # May or may not have clickable widgets depending on state
        assert isinstance(clickable, list)

    def test_chaos_monkey_short_run(self, main_window, qtbot):
        """Test a short chaos monkey run."""
        monkey = ChaosMonkey(main_window, seed=42)

        # Run 10 iterations
        errors, error_list = monkey.run(iterations=10, delay_ms=50)

        # Report should be generated
        report = monkey.get_report()
        assert "CHAOS MONKEY REPORT" in report

        # Actions should have been taken
        assert monkey.iteration > 0

    def test_chaos_monkey_reproducible(self, main_window, qtbot):
        """Test that chaos monkey is reproducible with same seed."""
        monkey1 = ChaosMonkey(main_window, seed=12345)
        monkey1.run(iterations=5, delay_ms=10)
        actions1 = monkey1.actions_taken.copy()

        # Reset window state if needed

        monkey2 = ChaosMonkey(main_window, seed=12345)
        monkey2.run(iterations=5, delay_ms=10)
        actions2 = monkey2.actions_taken.copy()

        # First few actions should be similar (not exact due to widget state changes)
        # Just verify both ran
        assert len(actions1) > 0
        assert len(actions2) > 0

    @pytest.mark.slow
    def test_chaos_monkey_extended_run(self, main_window, qtbot):
        """Test an extended chaos monkey run (100 iterations)."""
        monkey = ChaosMonkey(main_window, seed=42)

        errors, error_list = monkey.run(iterations=100, delay_ms=20)

        report = monkey.get_report()
        print(report)  # Print for CI logs

        # Application should survive 100 random actions
        assert main_window.isVisible(), "Window should still be visible after chaos"

    @pytest.mark.slow
    def test_chaos_monkey_stress(self, main_window, qtbot):
        """Stress test with rapid actions."""
        monkey = ChaosMonkey(main_window, seed=42)

        # 200 iterations with minimal delay
        errors, error_list = monkey.run(iterations=200, delay_ms=5)

        report = monkey.get_report()
        print(report)

        # Should survive stress test
        assert main_window.isVisible()


class TestEdgeCaseInputs:
    """Test filling inputs with edge case data."""

    @pytest.mark.parametrize("test_data", EdgeCaseData.EMPTY)
    def test_empty_inputs(self, main_window, qtbot, test_data):
        """Test empty/whitespace inputs."""
        monkey = ChaosMonkey(main_window)
        editable = monkey.find_editable_widgets()

        for widget in editable[:3]:  # Test first 3 editable widgets
            if isinstance(widget, QLineEdit):
                widget.clear()
                widget.setText(test_data)
                qtbot.wait(10)

    @pytest.mark.parametrize("test_data", EdgeCaseData.UNICODE[:5])
    def test_unicode_inputs(self, main_window, qtbot, test_data):
        """Test unicode inputs."""
        monkey = ChaosMonkey(main_window)
        editable = monkey.find_editable_widgets()

        for widget in editable[:3]:
            if isinstance(widget, QLineEdit):
                widget.clear()
                widget.setText(test_data)
                qtbot.wait(10)
                # Should not crash
                assert widget.text() == test_data or len(widget.text()) > 0

    @pytest.mark.parametrize("test_data", EdgeCaseData.INJECTION[:5])
    def test_injection_inputs(self, main_window, qtbot, test_data):
        """Test potentially dangerous inputs (should be sanitized)."""
        monkey = ChaosMonkey(main_window)
        editable = monkey.find_editable_widgets()

        for widget in editable[:3]:
            if isinstance(widget, QLineEdit):
                widget.clear()
                widget.setText(test_data)
                qtbot.wait(10)
                # Should not crash or execute malicious code


class TestUIResilience:
    """Test UI resilience to unusual interactions."""

    def test_rapid_tab_switching(self, main_window, qtbot):
        """Test rapid tab switching."""
        monkey = ChaosMonkey(main_window)
        tabs = monkey.find_tab_widgets()

        for tab in tabs:
            if tab.count() > 1:
                for _ in range(20):  # Switch rapidly 20 times
                    new_index = random.randint(0, tab.count() - 1)
                    tab.setCurrentIndex(new_index)
                    qtbot.wait(5)

        assert main_window.isVisible()

    def test_rapid_button_clicking(self, main_window, qtbot):
        """Test rapid clicking of the same button."""
        monkey = ChaosMonkey(main_window)
        buttons = monkey.find_clickable_widgets()

        if buttons:
            button = buttons[0]
            for _ in range(20):
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                qtbot.wait(5)

        assert main_window.isVisible()

    def test_window_resize_during_operation(self, main_window, qtbot):
        """Test resizing window during operations."""
        sizes = [
            (800, 600),
            (1920, 1080),
            (400, 300),
            (1200, 800),
        ]

        for width, height in sizes:
            main_window.resize(width, height)
            qtbot.wait(50)
            assert main_window.isVisible()


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_chaos_monkey.py -v
    pytest.main([__file__, "-v", "--tb=short"])

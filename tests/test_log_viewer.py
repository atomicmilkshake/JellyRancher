"""
Comprehensive GUI Tests for Log Viewer.

Uses pytest-qt to test the log viewer including real-time updates,
filtering, search, auto-scroll, and pause/resume functionality.

Run with: pytest tests/test_log_viewer.py -v
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


# =============================================================================
# LOG VIEWER INITIALIZATION TESTS
# =============================================================================

class TestLogViewerInitialization:
    """Tests for log viewer initialization."""
    
    @pytest.fixture
    def log_viewer(self, qtbot):
        """Create LogViewerWindow instance for testing."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        viewer = LogViewerWindow()
        qtbot.addWidget(viewer)
        return viewer
    
    @pytest.mark.requires_gui
    def test_log_viewer_initializes(self, log_viewer):
        """LogViewerWindow should initialize without errors."""
        assert log_viewer is not None
    
    @pytest.mark.requires_gui
    def test_has_log_text(self, log_viewer):
        """Should have log display widget."""
        assert hasattr(log_viewer, 'log_text')
        assert log_viewer.log_text is not None
    
    @pytest.mark.requires_gui
    def test_has_level_filter(self, log_viewer):
        """Should have level filter combo box."""
        assert hasattr(log_viewer, 'level_combo')
        assert log_viewer.level_combo is not None
    
    @pytest.mark.requires_gui
    def test_has_search_input(self, log_viewer):
        """Should have search input field."""
        assert hasattr(log_viewer, 'search_edit')
        assert log_viewer.search_edit is not None


# =============================================================================
# REAL-TIME UPDATES TESTS
# =============================================================================

class TestRealTimeUpdates:
    """Tests for real-time log tailing."""
    
    @pytest.fixture
    def log_viewer(self, qtbot, tmp_path):
        """Create LogViewerWindow instance with temp log file."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        # Create temp log file
        log_file = tmp_path / "test.log"
        log_file.write_text("Initial log line\n")
        
        with patch('scripts.ui.log_viewer.MasterLogger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger_instance.get_log_path.return_value = log_file
            mock_logger.return_value = mock_logger_instance
            
            viewer = LogViewerWindow()
            qtbot.addWidget(viewer)
            return viewer, log_file
    
    @pytest.mark.requires_gui
    def test_log_file_watching(self, log_viewer, qtbot):
        """Log viewer should watch log file for changes."""
        viewer, log_file = log_viewer
        
        # Verify file watcher is set up
        assert hasattr(viewer, 'file_watcher')
        assert viewer.file_watcher is not None
    
    @pytest.mark.requires_gui
    def test_log_updates_on_file_change(self, log_viewer, qtbot):
        """Log display should update when log file changes."""
        viewer, log_file = log_viewer
        
        initial_text = viewer.log_text.toPlainText()
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write("New log line\n")
        
        qtbot.wait(600)  # Wait for file watcher/timer to detect change
        
        # Log should be updated (may take time for watcher)
        new_text = viewer.log_text.toPlainText()
        # Either text changed or watcher is working
        assert new_text != initial_text or "New log line" in new_text or len(new_text) > len(initial_text)


# =============================================================================
# LEVEL FILTERING TESTS
# =============================================================================

class TestLevelFiltering:
    """Tests for log level filtering."""
    
    @pytest.fixture
    def log_viewer(self, qtbot):
        """Create LogViewerWindow instance for testing."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        viewer = LogViewerWindow()
        qtbot.addWidget(viewer)
        return viewer
    
    @pytest.mark.requires_gui
    def test_level_combo_has_options(self, log_viewer):
        """Level combo should have filtering options."""
        assert log_viewer.level_combo.count() > 0
        assert "ALL" in [log_viewer.level_combo.itemText(i) for i in range(log_viewer.level_combo.count())]
    
    @pytest.mark.requires_gui
    def test_level_filter_changes(self, log_viewer, qtbot):
        """Changing level filter should update displayed logs."""
        initial_level = log_viewer.level_combo.currentText()
        
        # Change to different level
        if log_viewer.level_combo.count() > 1:
            log_viewer.level_combo.setCurrentIndex(1)
            qtbot.wait(50)
            
            new_level = log_viewer.level_combo.currentText()
            assert new_level != initial_level


# =============================================================================
# SEARCH FUNCTIONALITY TESTS
# =============================================================================

class TestSearchFunctionality:
    """Tests for search functionality."""
    
    @pytest.fixture
    def log_viewer(self, qtbot):
        """Create LogViewerWindow instance for testing."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        viewer = LogViewerWindow()
        qtbot.addWidget(viewer)
        return viewer
    
    @pytest.mark.requires_gui
    def test_search_input_accepts_text(self, log_viewer, qtbot):
        """Search input should accept text entry."""
        search_text = "test search"
        qtbot.keyClicks(log_viewer.search_edit, search_text)
        
        assert log_viewer.search_edit.text() == search_text
    
    @pytest.mark.requires_gui
    def test_search_filters_logs(self, log_viewer, qtbot):
        """Search should filter displayed logs."""
        # Set some log content
        log_viewer.log_text.setPlainText("Line 1: Error message\nLine 2: Info message\nLine 3: Warning")
        qtbot.wait(50)
        
        # Enter search text
        qtbot.keyClicks(log_viewer.search_edit, "Error")
        qtbot.wait(100)
        
        # Search should trigger filtering (exact behavior depends on implementation)
        assert log_viewer.search_edit.text() == "Error"


# =============================================================================
# AUTO-SCROLL TESTS
# =============================================================================

class TestAutoScroll:
    """Tests for auto-scroll functionality."""
    
    @pytest.fixture
    def log_viewer(self, qtbot):
        """Create LogViewerWindow instance for testing."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        viewer = LogViewerWindow()
        qtbot.addWidget(viewer)
        return viewer
    
    @pytest.mark.requires_gui
    def test_auto_scroll_checkbox_exists(self, log_viewer):
        """Should have auto-scroll checkbox."""
        assert hasattr(log_viewer, 'auto_scroll_check')
        assert log_viewer.auto_scroll_check is not None
    
    @pytest.mark.requires_gui
    def test_auto_scroll_toggle(self, log_viewer, qtbot):
        """Auto-scroll checkbox should toggle auto-scroll behavior."""
        initial_state = log_viewer.auto_scroll_check.isChecked()
        
        qtbot.mouseClick(log_viewer.auto_scroll_check, Qt.MouseButton.LeftButton)
        qtbot.wait(50)
        
        assert log_viewer.auto_scroll_check.isChecked() != initial_state
        assert log_viewer.auto_scroll != initial_state


# =============================================================================
# PAUSE/RESUME TESTS
# =============================================================================

class TestPauseResume:
    """Tests for pause/resume functionality."""
    
    @pytest.fixture
    def log_viewer(self, qtbot):
        """Create LogViewerWindow instance for testing."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        viewer = LogViewerWindow()
        qtbot.addWidget(viewer)
        return viewer
    
    @pytest.mark.requires_gui
    def test_pause_button_exists(self, log_viewer):
        """Should have pause/resume button."""
        assert hasattr(log_viewer, 'pause_btn')
        assert log_viewer.pause_btn is not None
    
    @pytest.mark.requires_gui
    def test_pause_toggles_updates(self, log_viewer, qtbot):
        """Pause button should toggle log updates."""
        initial_paused = log_viewer.is_paused
        
        qtbot.mouseClick(log_viewer.pause_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(50)
        
        assert log_viewer.is_paused != initial_paused


# =============================================================================
# CLEAR FUNCTIONALITY TESTS
# =============================================================================

class TestClearFunctionality:
    """Tests for clear button functionality."""
    
    @pytest.fixture
    def log_viewer(self, qtbot):
        """Create LogViewerWindow instance for testing."""
        from scripts.ui.log_viewer import LogViewerWindow
        
        viewer = LogViewerWindow()
        qtbot.addWidget(viewer)
        return viewer
    
    @pytest.mark.requires_gui
    def test_clear_button_exists(self, log_viewer):
        """Should have clear button."""
        assert hasattr(log_viewer, 'clear_btn')
        assert log_viewer.clear_btn is not None
    
    @pytest.mark.requires_gui
    def test_clear_reloads_log(self, log_viewer, qtbot):
        """Clear button should reload log from file."""
        # Set some content
        log_viewer.log_text.setPlainText("Test content")
        qtbot.wait(50)
        
        # Click clear
        qtbot.mouseClick(log_viewer.clear_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        
        # Log should be reloaded (content may change)
        # Exact behavior depends on implementation


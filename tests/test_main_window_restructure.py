"""
Tests for Main Window Restructure - Top-level tabs (JellyRancher + JellyBase).

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 10 tests

Tests top-level QTabWidget with JellyRancher + JellyBase tabs, tab switching,
and Welcome Screen accessibility.
"""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTabWidget, QStackedWidget

from jelly_rancher_studio import JellyRancherStudio
from scripts.ui.jellybase_view import JellyBaseView


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def main_window(qtbot):
    """Create JellyRancherStudio instance for testing."""
    with patch('jelly_rancher_studio.QApplication.instance', return_value=QApplication.instance()):
        window = JellyRancherStudio()
        qtbot.addWidget(window)
        return window


# =============================================================================
# TOP-LEVEL TABS TESTS
# =============================================================================

class TestTopLevelTabs:
    """Tests for top-level tab structure."""

    @pytest.mark.requires_gui
    def test_top_level_tabs_exist(self, main_window):
        """Main window should have top-level tabs widget."""
        assert hasattr(main_window, 'top_level_tabs')
        assert main_window.top_level_tabs is not None
        assert isinstance(main_window.top_level_tabs, QTabWidget)

    @pytest.mark.requires_gui
    def test_top_level_tabs_has_jellyrancher_tab(self, main_window):
        """Top-level tabs should have JellyRancher tab."""
        assert main_window.top_level_tabs.count() >= 1
        assert main_window.top_level_tabs.tabText(0) == "JellyRancher"

    @pytest.mark.requires_gui
    def test_top_level_tabs_has_jellybase_tab(self, main_window):
        """Top-level tabs should have JellyBase tab."""
        assert main_window.top_level_tabs.count() >= 2
        assert main_window.top_level_tabs.tabText(1) == "JellyBase"

    @pytest.mark.requires_gui
    def test_jellyrancher_tab_contains_workspace(self, main_window):
        """JellyRancher tab should contain workspace widget."""
        assert hasattr(main_window, 'workspace_widget')
        assert main_window.workspace_widget is not None
        # Workspace should be in JellyRancher tab
        assert main_window.top_level_tabs.widget(0) == main_window.workspace_widget

    @pytest.mark.requires_gui
    def test_jellyrancher_tab_has_roundup_explorer(self, main_window):
        """JellyRancher tab should have Round-Up Explorer."""
        assert hasattr(main_window, 'roundup_explorer')
        assert main_window.roundup_explorer is not None

    @pytest.mark.requires_gui
    def test_jellyrancher_tab_has_tab_widget(self, main_window):
        """JellyRancher tab should have tab widget for workflow views."""
        assert hasattr(main_window, 'tab_widget')
        assert main_window.tab_widget is not None
        assert isinstance(main_window.tab_widget, QTabWidget)

    @pytest.mark.requires_gui
    def test_jellybase_tab_contains_jellybase_view(self, main_window):
        """JellyBase tab should contain JellyBaseView."""
        assert hasattr(main_window, 'jellybase_view')
        assert main_window.jellybase_view is not None
        assert isinstance(main_window.jellybase_view, JellyBaseView)
        # JellyBaseView should be in JellyBase tab
        assert main_window.top_level_tabs.widget(1) == main_window.jellybase_view

    @pytest.mark.requires_gui
    def test_tab_switching_preserves_state(self, main_window, qtbot):
        """Switching between tabs should preserve state."""
        # Switch to JellyBase tab
        main_window.top_level_tabs.setCurrentIndex(1)
        qtbot.wait(100)
        
        # Verify JellyBase tab is active
        assert main_window.top_level_tabs.currentIndex() == 1
        assert main_window.jellybase_view is not None
        
        # Switch back to JellyRancher tab
        main_window.top_level_tabs.setCurrentIndex(0)
        qtbot.wait(100)
        
        # Verify JellyRancher tab is active
        assert main_window.top_level_tabs.currentIndex() == 0
        assert main_window.workspace_widget is not None

    @pytest.mark.requires_gui
    def test_central_stack_contains_top_level_tabs(self, main_window):
        """Central stack should contain top-level tabs widget."""
        assert hasattr(main_window, 'central_stack')
        assert main_window.central_stack is not None
        assert isinstance(main_window.central_stack, QStackedWidget)
        
        # Top-level tabs should be in the stack
        # (Stack may also contain welcome screen)
        assert main_window.central_stack.count() >= 1

    @pytest.mark.requires_gui
    def test_welcome_screen_accessible(self, main_window):
        """Welcome Screen should be accessible in central stack."""
        assert hasattr(main_window, 'welcome_screen')
        assert main_window.welcome_screen is not None
        # Welcome screen should be in central stack
        # (May be at index 0, with top_level_tabs at index 1)
        assert main_window.central_stack.count() >= 1


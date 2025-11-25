#!/usr/bin/env python3
"""
JellyRancher Studio - Modern Round-Up-Based Media Library Manager

The next-generation GUI for JellyRancher, implementing the "Round-Up" persistence
system from master-prompt.md Section VII. Features Round-Up management, flexible
8-step workflow, and professional UI/UX.

Architecture:
    - Round-Up-centric: Everything revolves around Round-Ups (saved sessions)
    - 8-Step Workflow: Scan → Summary → Analysis → Metadata → Review → Execute → Subtitle Audit → Downloads
    - Welcome Screen: Always shows on launch, displays recent Round-Ups
    - Auto-Save: Saves after each step completion
    - Resume: Pick up exactly where you left off

Usage:
    python jelly_rancher_studio.py
"""

import sys
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel,
    QMenuBar, QMenu, QStatusBar, QPushButton, QMessageBox, QDialog,
    QLineEdit, QTextEdit, QDialogButtonBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QAction, QFont, QShortcut, QKeySequence

from scripts.core.roundup_manager import RoundUpManager, RoundUp
from scripts._common.logger import MasterLogger
from scripts.ui.welcome_screen import WelcomeScreen
from scripts.ui.styles import apply_stylesheet

# Import views - will need adapters
from scripts.ui.scan_view import ScanView
from scripts.ui.scan_results_view import ScanResultsView
from scripts.ui.analysis_view import AnalysisView
from scripts.ui.review_view import ReviewView
from scripts.ui.execution_view import ExecutionView
from scripts.ui.subtitles_view import SubtitlesView
from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog

# Initialize logging
logger = logging.getLogger(__name__)

# Global for dark mode state
DARK_MODE_ENABLED = True


class RoundUpProjectAdapter:
    """
    Adapter that makes a RoundUp look like the old Project class.

    This allows existing views to work with the new Round-Up system
    without immediate refactoring. Views expect:
    - id, name, description, settings attributes
    - scan_sessions, analyses, action_plans lists
    """

    def __init__(self, roundup: RoundUp, manager: RoundUpManager):
        self.roundup = roundup
        self.manager = manager

        # Map RoundUp attributes to Project-like interface
        self.id = hash(str(roundup.path))  # Generate stable ID from path
        self.name = roundup.name
        self.description = f"Step {roundup.current_step}/8"
        self.settings = roundup.config
        self.state = "active"

        # These will be populated from database
        self.scan_sessions: List[int] = []
        self.analyses: List[int] = []
        self.action_plans: List[int] = []

        self._load_session_ids()

    def _load_session_ids(self):
        """Load session IDs from the Round-Up database."""
        try:
            with self.manager.get_connection(self.roundup) as conn:
                cursor = conn.cursor()

                # Get scan count (we'll use row IDs as session IDs)
                cursor.execute('SELECT COUNT(*) FROM scan_files')
                scan_count = cursor.fetchone()[0]
                if scan_count > 0:
                    self.scan_sessions = [1]  # Simplified - one scan per roundup

                # Get analysis IDs
                cursor.execute('SELECT id FROM analysis_results ORDER BY created_at DESC')
                self.analyses = [row['id'] for row in cursor.fetchall()]

                # Get review action count as "plan"
                cursor.execute('SELECT COUNT(*) FROM review_actions')
                action_count = cursor.fetchone()[0]
                if action_count > 0:
                    self.action_plans = [1]  # Simplified

        except Exception as e:
            logger.warning(f"Failed to load session IDs: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'settings': self.settings
        }


class RoundUpManagerAdapter:
    """
    Adapter that makes RoundUpManager look like the old ProjectManager.

    This allows existing views to work with the new Round-Up system.
    Views expect methods like:
    - save_project(), load_project(), get_scan_summary(), etc.
    """

    def __init__(self, manager: RoundUpManager, current_roundup: Optional[RoundUp] = None):
        self.manager = manager
        self.current_roundup = current_roundup

        # Legacy database path for views that access it directly
        self.db_path = Path("data/media_library.db")

    def set_current_roundup(self, roundup: Optional[RoundUp]):
        """Set the current Round-Up context."""
        self.current_roundup = roundup

    def save_project(self, project: RoundUpProjectAdapter) -> bool:
        """Save the Round-Up (adapter method)."""
        if self.current_roundup:
            return self.manager.save(self.current_roundup)
        return False

    def load_project(self, project_id: Optional[int] = None, name: Optional[str] = None):
        """Load a Round-Up (adapter method)."""
        if name:
            roundup = self.manager.load(name)
            if roundup:
                return RoundUpProjectAdapter(roundup, self.manager)
        return None

    def get_scan_summary(self, session_id: int) -> dict:
        """Get scan statistics (adapter method)."""
        if not self.current_roundup:
            return {'files': 0, 'size_gb': 0.0}

        try:
            with self.manager.get_connection(self.current_roundup) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*), SUM(size_bytes) FROM scan_files')
                row = cursor.fetchone()
                if row:
                    return {
                        'files': row[0] or 0,
                        'size_gb': (row[1] or 0) / (1024**3)
                    }
        except Exception as e:
            logger.error(f"Failed to get scan summary: {e}")

        return {'files': 0, 'size_gb': 0.0}

    def get_analysis_summary(self, analysis_id: int) -> dict:
        """Get analysis summary (adapter method)."""
        if not self.current_roundup:
            return {'issues': 0, 'confidence': 'UNKNOWN'}

        try:
            with self.manager.get_connection(self.current_roundup) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT response_json FROM analysis_results WHERE id = ?',
                    (analysis_id,)
                )
                row = cursor.fetchone()
                if row and row['response_json']:
                    response = json.loads(row['response_json'])
                    issues = len(response.get('reorganization_plan', {}).get('folder_changes', []))
                    return {
                        'issues': issues,
                        'confidence': 'HIGH' if issues > 0 else 'LOW'
                    }
        except Exception as e:
            logger.error(f"Failed to get analysis summary: {e}")

        return {'issues': 0, 'confidence': 'UNKNOWN'}

    def save_project_state(self, state) -> bool:
        """Save project state (adapter - no-op, Round-Up handles this)."""
        return True

    def load_project_state(self, project_id: int):
        """Load project state (adapter - returns None)."""
        return None


class JellyRancherStudio(QMainWindow):
    """
    Main window for JellyRancher Studio.

    Layout:
        - Welcome Screen (when no Round-Up open)
        - Workspace (when Round-Up is open):
            - Left sidebar: Round-Up Explorer (8-step workflow)
            - Center: Tabbed workspace for views
            - Bottom: Status bar with save indicator
    """

    # Signals
    roundup_changed = pyqtSignal(object)  # Emitted when active Round-Up changes

    def __init__(self):
        super().__init__()

        # Initialize managers
        self.roundup_manager = RoundUpManager()
        self.current_roundup: Optional[RoundUp] = None

        # Create adapters for legacy view compatibility
        self.manager_adapter = RoundUpManagerAdapter(self.roundup_manager)
        self.project_adapter: Optional[RoundUpProjectAdapter] = None

        # Auto-save timer
        self.auto_save_timer = QTimer()

        # Track last scan session ID for results view
        self.last_scan_session_id: Optional[int] = None

        # Setup UI
        self.setWindowTitle("JellyRancher Studio")
        self.resize(1400, 720)

        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        self._setup_keyboard_shortcuts()
        self._setup_gui_capture_shortcut()

        # Start with Welcome Screen (always)
        self._show_welcome_screen()

        logger.info("JellyRancher Studio initialized")

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Round-Up...", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_roundup)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Round-Up...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_roundup_dialog)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Save Round-Up", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_roundup)
        file_menu.addAction(save_action)

        close_action = QAction("&Close Round-Up", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self._close_roundup)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        settings_action = QAction("Se&ttings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        dark_mode_action = QAction("&Dark Mode", self, checkable=True)
        dark_mode_action.setChecked(True)
        dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(dark_mode_action)

        view_menu.addSeparator()

        welcome_action = QAction("&Welcome Screen", self)
        welcome_action.triggered.connect(self._show_welcome_screen)
        view_menu.addAction(welcome_action)

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_keyboard_shortcuts)
        view_menu.addAction(shortcuts_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        jellyfin_action = QAction("&Jellyfin Settings", self)
        jellyfin_action.triggered.connect(self._show_jellyfin_settings)
        tools_menu.addAction(jellyfin_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_main_layout(self):
        """Create the main window layout."""
        # Central stacked widget (Welcome Screen / Workspace)
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Create Welcome Screen
        self.welcome_screen = WelcomeScreen(self.roundup_manager, self)
        self.welcome_screen.roundup_opened.connect(self._on_roundup_opened)
        self.welcome_screen.roundup_created.connect(self._on_roundup_created)
        self.central_stack.addWidget(self.welcome_screen)

        # Create Workspace (will be shown when Round-Up is open)
        self.workspace_widget = QWidget()
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter (left sidebar | center workspace)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left sidebar: Round-Up Explorer
        self.roundup_explorer = self._create_roundup_explorer()
        main_splitter.addWidget(self.roundup_explorer)

        # Center: Tabbed workspace
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.tabBar().installEventFilter(self)
        main_splitter.addWidget(self.tab_widget)

        # Set splitter sizes
        main_splitter.setSizes([250, 1150])

        workspace_layout.addWidget(main_splitter)
        self.workspace_widget.setLayout(workspace_layout)
        self.central_stack.addWidget(self.workspace_widget)

    def _create_roundup_explorer(self) -> QWidget:
        """Create the left sidebar Round-Up Explorer."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_widget = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 4)
        header_layout.setSpacing(2)

        title = QLabel("Round-Up Explorer")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(title)

        self.roundup_name_label = QLabel("(No Round-Up open)")
        self.roundup_name_label.setFont(QFont("Segoe UI", 9))
        self.roundup_name_label.setStyleSheet("font-style: italic;")
        header_layout.addWidget(self.roundup_name_label)

        self.step_label = QLabel("")
        self.step_label.setFont(QFont("Segoe UI", 9))
        header_layout.addWidget(self.step_label)

        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Tree widget for 8-step workflow
        self.explorer_tree = QTreeWidget()
        self.explorer_tree.setHeaderHidden(True)
        self.explorer_tree.setIndentation(20)
        self.explorer_tree.setAnimated(True)
        self.explorer_tree.setAlternatingRowColors(True)
        self.explorer_tree.itemClicked.connect(self._on_explorer_item_clicked)
        layout.addWidget(self.explorer_tree)

        widget.setLayout(layout)
        return widget

    def _create_status_bar(self):
        """Create the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)

        # Save indicator (right side)
        self.save_indicator = QLabel("No Round-Up open")
        self.statusBar.addPermanentWidget(self.save_indicator)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Already handled in menu actions
        pass

    def _setup_gui_capture_shortcut(self):
        """Setup F12 for GUI state capture."""
        shortcut = QShortcut(QKeySequence("F12"), self)
        shortcut.activated.connect(self._capture_gui_state)
        logger.info("F12 GUI capture shortcut registered")

    # ========================================================================
    # Welcome Screen / Workspace Navigation
    # ========================================================================

    def _show_welcome_screen(self):
        """Show the Welcome Screen."""
        self.welcome_screen.refresh()
        self.central_stack.setCurrentWidget(self.welcome_screen)
        self.setWindowTitle("JellyRancher Studio")
        self.save_indicator.setText("No Round-Up open")
        self.status_label.setText("Select or create a Round-Up")

    def _show_workspace(self):
        """Show the Workspace (when Round-Up is open)."""
        self.central_stack.setCurrentWidget(self.workspace_widget)

    # ========================================================================
    # Round-Up Management
    # ========================================================================

    def _new_roundup(self):
        """Create a new Round-Up via dialog."""
        from scripts.ui.welcome_screen import NewRoundUpDialog

        dialog = NewRoundUpDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                roundup = self.roundup_manager.create(
                    name=data['name'],
                    source_folders=data['source_folders']
                )
                self._load_roundup(roundup)
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _open_roundup_dialog(self):
        """Open Round-Up selection dialog."""
        from PyQt6.QtWidgets import QFileDialog

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Round-Up",
            str(self.roundup_manager.roundups_dir),
            QFileDialog.Option.ShowDirsOnly
        )

        if folder and folder.endswith(".roundup"):
            roundup = self.roundup_manager.load(folder)
            if roundup:
                self._load_roundup(roundup)
            else:
                QMessageBox.critical(self, "Error", f"Failed to load Round-Up: {folder}")
        elif folder:
            QMessageBox.warning(
                self, "Invalid Selection",
                "Please select a .roundup folder."
            )

    def _on_roundup_opened(self, roundup: RoundUp):
        """Handle Round-Up opened from Welcome Screen."""
        self._load_roundup(roundup)

    def _on_roundup_created(self, roundup: RoundUp):
        """Handle Round-Up created from Welcome Screen."""
        self._load_roundup(roundup)

    def _load_roundup(self, roundup: RoundUp):
        """Load a Round-Up into the workspace."""
        self.current_roundup = roundup

        # Create adapters for legacy views
        self.project_adapter = RoundUpProjectAdapter(roundup, self.roundup_manager)
        self.manager_adapter.set_current_roundup(roundup)

        # Update UI
        self._update_window_title()
        self._update_roundup_explorer()
        self._update_save_indicator()

        # Clear existing tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # Show workspace
        self._show_workspace()

        # Start auto-save timer
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(30000)  # 30 seconds

        self.status_label.setText(f"Loaded Round-Up: {roundup.name}")
        logger.info(f"Loaded Round-Up: {roundup.name} (Step {roundup.current_step}/8)")

        self.roundup_changed.emit(roundup)

    def _save_roundup(self):
        """Save the current Round-Up."""
        if not self.current_roundup:
            QMessageBox.information(self, "No Round-Up", "No Round-Up is currently open.")
            return

        if self.roundup_manager.save(self.current_roundup):
            self._update_save_indicator()
            self.status_label.setText(f"Saved: {self.current_roundup.name}")
            logger.info(f"Saved Round-Up: {self.current_roundup.name}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save Round-Up.")

    def _close_roundup(self):
        """Close the current Round-Up."""
        if not self.current_roundup:
            return

        # Check for unsaved changes
        if self.current_roundup.has_unsaved_changes:
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Round-Up '{self.current_roundup.name}' has unsaved changes.\n\n"
                f"Save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if result == QMessageBox.StandardButton.Cancel:
                return
            elif result == QMessageBox.StandardButton.Save:
                self._save_roundup()

        # Stop auto-save
        self.auto_save_timer.stop()

        # Clear state
        self.current_roundup = None
        self.project_adapter = None
        self.manager_adapter.set_current_roundup(None)

        # Clear tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # Show welcome screen
        self._show_welcome_screen()

        logger.info("Closed Round-Up")

    def _auto_save(self):
        """Auto-save current Round-Up."""
        if self.current_roundup and self.current_roundup.has_unsaved_changes:
            if self.roundup_manager.save(self.current_roundup):
                self._update_save_indicator()
                logger.debug(f"Auto-saved Round-Up: {self.current_roundup.name}")

    # ========================================================================
    # UI Updates
    # ========================================================================

    def _update_window_title(self):
        """Update the window title to show Round-Up info."""
        if self.current_roundup:
            step = self.current_roundup.current_step
            name = self.current_roundup.name
            self.setWindowTitle(f"JellyRancher Studio - {name} (Step {step} of 8)")
        else:
            self.setWindowTitle("JellyRancher Studio")

    def _update_save_indicator(self):
        """Update the save indicator in status bar."""
        if not self.current_roundup:
            self.save_indicator.setText("No Round-Up open")
            return

        if self.current_roundup.has_unsaved_changes:
            self.save_indicator.setText("⚠ Unsaved changes")
            self.save_indicator.setStyleSheet("color: #f39c12;")
        else:
            last_saved = self.current_roundup.last_modified
            if last_saved:
                try:
                    dt = datetime.fromisoformat(last_saved)
                    time_str = dt.strftime("%H:%M:%S")
                    self.save_indicator.setText(f"✓ Saved at {time_str}")
                    self.save_indicator.setStyleSheet("color: #2ecc71;")
                except:
                    self.save_indicator.setText("✓ Saved")
                    self.save_indicator.setStyleSheet("color: #2ecc71;")
            else:
                self.save_indicator.setText("✓ Saved")
                self.save_indicator.setStyleSheet("color: #2ecc71;")

    def _update_roundup_explorer(self):
        """Update the Round-Up Explorer tree."""
        self.explorer_tree.clear()

        if not self.current_roundup:
            self.roundup_name_label.setText("(No Round-Up open)")
            self.step_label.setText("")
            return

        # Update header
        self.roundup_name_label.setText(f"📁 {self.current_roundup.name}")
        self.roundup_name_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        self.step_label.setText(f"Step {self.current_roundup.current_step} of 8")

        # Create 8-step workflow tree
        steps = [
            ("1️⃣", "Scan Folders", 1),
            ("2️⃣", "Structure Summary", 2),
            ("3️⃣", "Analysis", 3),
            ("4️⃣", "Canonical Database", 4),
            ("5️⃣", "Review Table", 5),
            ("6️⃣", "Execute Operations", 6),
            ("7️⃣", "Subtitle Audit", 7),
            ("8️⃣", "Subtitle Downloads", 8),
        ]

        for emoji, name, step_num in steps:
            status = self.current_roundup.step_status.get(step_num, "not_started")

            # Format status
            if status == "completed":
                status_text = "✓"
                item_text = f"{emoji} {name} {status_text}"
            elif status == "in_progress":
                status_text = "⟳"
                item_text = f"{emoji} {name} {status_text}"
            else:
                item_text = f"{emoji} {name}"

            item = QTreeWidgetItem([item_text])
            item.setData(0, Qt.ItemDataRole.UserRole, step_num)

            # Highlight current step
            if step_num == self.current_roundup.current_step:
                item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))

            # Disable future steps (optional - for guided workflow)
            # if step_num > self.current_roundup.current_step + 1:
            #     item.setDisabled(True)

            self.explorer_tree.addTopLevelItem(item)

    def _on_explorer_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle click on explorer item."""
        step_num = item.data(0, Qt.ItemDataRole.UserRole)
        if step_num is None:
            return

        # Open the appropriate view for the step
        if step_num == 1:
            self._open_scan_view()
        elif step_num == 2:
            self._open_scan_results_view()
        elif step_num == 3:
            self._open_analysis_view()
        elif step_num == 4:
            # Metadata is part of analysis view
            self._open_analysis_view()
        elif step_num == 5:
            self._open_review_view()
        elif step_num == 6:
            self._open_execution_view()
        elif step_num in (7, 8):
            self._open_subtitles_view()

    # ========================================================================
    # View Opening Methods
    # ========================================================================

    def _check_step_prerequisites(self, step: int) -> tuple[bool, str]:
        """
        Check if prerequisites for a workflow step are met.

        Args:
            step: The step number to check (1-8)

        Returns:
            Tuple of (prerequisites_met, error_message)
        """
        if not self.current_roundup:
            return False, "No Round-Up is open."

        # Step dependencies:
        # 1 (Scan): No dependencies
        # 2 (Structure Summary): Requires Step 1 or scan data in database
        # 3 (Analysis): Requires scan data (Step 1)
        # 4 (Canonical Database): Part of Step 3, no separate check
        # 5 (Review): Requires analysis data (Step 3)
        # 6 (Execute): Requires review/plan data (Step 5)
        # 7 (Subtitle Audit): Requires scan data (Step 1)
        # 8 (Subtitle Downloads): Requires subtitle audit (Step 7)

        step_status = self.current_roundup.step_status
        config = self.current_roundup.config

        if step == 1:
            return True, ""

        elif step == 2:
            # Structure Summary requires scan data
            has_scan = (
                step_status.get(1) == "completed" or
                config.get('scan_session_id') is not None or
                self._has_roundup_scan_data()
            )
            if not has_scan:
                return False, "Please complete Step 1 (Scan Folders) first.\n\nNo scan data found."
            return True, ""

        elif step == 3:
            # Analysis requires scan data
            has_scan = (
                step_status.get(1) == "completed" or
                config.get('scan_session_id') is not None or
                self._has_roundup_scan_data()
            )
            if not has_scan:
                return False, "Please complete Step 1 (Scan Folders) first.\n\nAnalysis requires scan data."
            return True, ""

        elif step == 4:
            # Canonical Database is part of analysis flow
            return True, ""

        elif step == 5:
            # Review requires analysis
            has_analysis = (
                step_status.get(3) == "completed" or
                config.get('analysis_id') is not None
            )
            if not has_analysis:
                return False, "Please complete Step 3 (Analysis) first.\n\nReview requires analysis results."
            return True, ""

        elif step == 6:
            # Execute requires review/plan
            has_plan = (
                step_status.get(5) == "completed" or
                config.get('plan_id') is not None
            )
            if not has_plan:
                return False, "Please complete Step 5 (Review Table) first.\n\nExecution requires an approved plan."
            return True, ""

        elif step == 7:
            # Subtitle Audit requires scan data
            has_scan = (
                step_status.get(1) == "completed" or
                config.get('scan_session_id') is not None or
                self._has_roundup_scan_data()
            )
            if not has_scan:
                return False, "Please complete Step 1 (Scan Folders) first.\n\nSubtitle audit requires scan data."
            return True, ""

        elif step == 8:
            # Subtitle Downloads requires audit
            has_audit = step_status.get(7) == "completed"
            if not has_audit:
                return False, "Please complete Step 7 (Subtitle Audit) first."
            return True, ""

        return True, ""

    def _has_roundup_scan_data(self) -> bool:
        """Check if the Round-Up has scan data in its database."""
        if not self.current_roundup:
            return False
        try:
            db_path = self.current_roundup.path / "data.db"
            if not db_path.exists():
                return False
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM scan_files')
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False

    def _open_scan_view(self):
        """Open the Scan view."""
        if not self.current_roundup or not self.project_adapter:
            QMessageBox.information(self, "No Round-Up", "Please open a Round-Up first.")
            return

        # Check if tab already open
        for i in range(self.tab_widget.count()):
            if "Scan" in self.tab_widget.tabText(i) and "Results" not in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        # Create scan view using adapter
        scan_view = ScanView(self.project_adapter, self.manager_adapter, self)
        scan_view.scan_completed.connect(self._on_scan_completed)
        scan_view.results_ready.connect(self._on_results_ready)

        self.tab_widget.addTab(scan_view, f"1️⃣ Scan - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(scan_view)

        logger.info("Opened Scan view")

    def _open_scan_results_view(self, scan_session_id: Optional[int] = None):
        """Open the Scan Results view."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Check step prerequisites
        can_proceed, error_msg = self._check_step_prerequisites(2)
        if not can_proceed:
            QMessageBox.warning(self, "Step Not Available", error_msg)
            return

        # Check if tab already open
        for i in range(self.tab_widget.count()):
            if "Results" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        # Get scan session ID - use provided, stored in memory, from Round-Up config, or fetch most recent
        if scan_session_id is None:
            scan_session_id = self.last_scan_session_id

        if scan_session_id is None and self.current_roundup:
            # Try to get from Round-Up's persisted config
            scan_session_id = self.current_roundup.config.get('scan_session_id')

        if scan_session_id is None:
            # Last resort: fetch the most recent scan session from database
            scan_session_id = self._get_most_recent_scan_session_id()

        if scan_session_id is None:
            QMessageBox.information(
                self, "No Scan Data",
                "No scan data found. Please run a scan first."
            )
            return

        results_view = ScanResultsView(
            self.project_adapter, self.manager_adapter, scan_session_id, self
        )
        results_view.send_to_analysis.connect(self._on_send_to_analysis)

        self.tab_widget.addTab(results_view, f"2️⃣ Results - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(results_view)

        logger.info(f"Opened Scan Results view (session #{scan_session_id})")

    def _open_analysis_view(self, analysis_id: Optional[int] = None):
        """Open the Analysis view."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Check step prerequisites
        can_proceed, error_msg = self._check_step_prerequisites(3)
        if not can_proceed:
            QMessageBox.warning(self, "Step Not Available", error_msg)
            return

        # Check if tab already open
        for i in range(self.tab_widget.count()):
            if "Analysis" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        # Get analysis_id from Round-Up config if not provided
        if analysis_id is None and self.current_roundup:
            analysis_id = self.current_roundup.config.get('analysis_id')

        analysis_view = AnalysisView(self.project_adapter, self.manager_adapter, self)
        analysis_view.analysis_saved.connect(self._on_analysis_saved)
        analysis_view.metadata_built.connect(self._on_metadata_built)
        analysis_view.send_to_review.connect(self._on_send_to_review_from_analysis)

        # Set the analysis_id if we have one from a previous session
        if analysis_id is not None:
            analysis_view.current_analysis_id = analysis_id

        self.tab_widget.addTab(analysis_view, f"3️⃣ Analysis - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(analysis_view)

        logger.info(f"Opened Analysis view (analysis_id={analysis_id})")

    def _open_review_view(self):
        """Open the Review view."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Check step prerequisites
        can_proceed, error_msg = self._check_step_prerequisites(5)
        if not can_proceed:
            QMessageBox.warning(self, "Step Not Available", error_msg)
            return

        # Check if tab already open
        for i in range(self.tab_widget.count()):
            if "Review" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        review_view = ReviewView(self.project_adapter, self.manager_adapter, self)
        review_view.operations_ready.connect(self._on_operations_ready)

        self.tab_widget.addTab(review_view, f"5️⃣ Review - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(review_view)

        logger.info("Opened Review view")

    def _open_execution_view(self):
        """Open the Execution view."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Check step prerequisites
        can_proceed, error_msg = self._check_step_prerequisites(6)
        if not can_proceed:
            QMessageBox.warning(self, "Step Not Available", error_msg)
            return

        # Check if tab already open
        for i in range(self.tab_widget.count()):
            if "Execute" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        # Create backup before execution
        self.roundup_manager.create_backup(self.current_roundup, "pre_execution")

        execution_view = ExecutionView(
            self.project_adapter, self.manager_adapter, None, self
        )
        execution_view.execution_completed.connect(self._on_execution_completed)

        self.tab_widget.addTab(execution_view, f"6️⃣ Execute - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(execution_view)

        logger.info("Opened Execution view")

    def _open_subtitles_view(self):
        """Open the Subtitles view."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Check step prerequisites (Step 7 - Subtitle Audit)
        can_proceed, error_msg = self._check_step_prerequisites(7)
        if not can_proceed:
            QMessageBox.warning(self, "Step Not Available", error_msg)
            return

        # Check if tab already open
        for i in range(self.tab_widget.count()):
            if "Subtitles" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        subtitles_view = SubtitlesView(self.project_adapter, self.manager_adapter, self)

        self.tab_widget.addTab(subtitles_view, f"7️⃣ Subtitles - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(subtitles_view)

        logger.info("Opened Subtitles view")

    # ========================================================================
    # Signal Handlers
    # ========================================================================

    def _get_most_recent_scan_session_id(self) -> Optional[int]:
        """Get the most recent scan session ID from the database."""
        try:
            import sqlite3
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM project_scan_sessions
                ORDER BY scan_start DESC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get most recent scan session: {e}")
            return None

    def _on_scan_completed(self, scan_id: int):
        """Handle scan completion."""
        self.last_scan_session_id = scan_id
        if self.current_roundup:
            # Store scan_session_id in Round-Up config for persistence across restarts
            self.current_roundup.config['scan_session_id'] = scan_id
            self.current_roundup.complete_step(1)
            self.roundup_manager.save(self.current_roundup)
            self._update_roundup_explorer()
            self._update_save_indicator()

        self.status_label.setText("Scan completed")
        logger.info(f"Scan completed (session {scan_id})")

    def _on_results_ready(self, scan_session_id: int):
        """Handle scan results ready."""
        self.last_scan_session_id = scan_session_id
        # Also persist to Round-Up config
        if self.current_roundup:
            self.current_roundup.config['scan_session_id'] = scan_session_id
            self.roundup_manager.save(self.current_roundup)
        self._open_scan_results_view(scan_session_id)

    def _on_send_to_analysis(self, filtered_files: list, filter_config: dict):
        """Handle send to analysis from results view."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Update step status
        if self.current_roundup:
            self.current_roundup.complete_step(2)

        # Open analysis view with filtered data
        analysis_view = AnalysisView(
            self.project_adapter, self.manager_adapter, self,
            filtered_files=filtered_files,
            filter_config=filter_config
        )
        analysis_view.analysis_saved.connect(self._on_analysis_saved)
        analysis_view.metadata_built.connect(self._on_metadata_built)
        analysis_view.send_to_review.connect(self._on_send_to_review_from_analysis)

        self.tab_widget.addTab(
            analysis_view,
            f"3️⃣ Analysis (Filtered) - {self.current_roundup.name}"
        )
        self.tab_widget.setCurrentWidget(analysis_view)

        logger.info(f"Opened Analysis with {len(filtered_files)} filtered files")

    def _on_analysis_saved(self, analysis_id: int):
        """Handle analysis saved."""
        if self.current_roundup:
            # Persist analysis_id in Round-Up config for retrieval after restart
            self.current_roundup.config['analysis_id'] = analysis_id
            self.current_roundup.complete_step(3)
            self.roundup_manager.save(self.current_roundup)
            self._update_roundup_explorer()
            self._update_save_indicator()

        self.status_label.setText(f"Analysis saved (ID #{analysis_id})")

    def _on_metadata_built(self, metadata_id: int):
        """Handle metadata built."""
        if self.current_roundup:
            # Persist metadata_id in Round-Up config for retrieval after restart
            self.current_roundup.config['metadata_id'] = metadata_id
            self.current_roundup.complete_step(4)
            self.roundup_manager.save(self.current_roundup)
            self._update_roundup_explorer()
            self._update_save_indicator()

        self.status_label.setText("Canonical database built")

    def _on_send_to_review_from_analysis(self, operations: list):
        """Handle send to review signal from AnalysisView."""
        if not self.current_roundup or not self.project_adapter:
            return

        # Close any existing review tabs
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if "Review" in self.tab_widget.tabText(i):
                self.tab_widget.removeTab(i)

        # Create review view with preloaded operations
        from scripts.ui.review_view import ReviewView
        review_view = ReviewView(self.project_adapter, self.manager_adapter, self)
        review_view.operations_ready.connect(self._on_operations_ready)
        
        # Set the preloaded operations
        review_view.set_preloaded_operations(operations)

        self.tab_widget.addTab(review_view, f"5️⃣ Review - {self.current_roundup.name}")
        self.tab_widget.setCurrentWidget(review_view)

        # Update step status
        self.current_roundup.complete_step(3)  # Analysis complete
        self.roundup_manager.save(self.current_roundup)
        self._update_roundup_explorer()

        logger.info(f"Opened Review with {len(operations)} preloaded operations from Analysis")

    def _on_operations_ready(self, plan_id: int):
        """Handle operations ready from review."""
        if self.current_roundup:
            # Persist plan_id in Round-Up config for retrieval after restart
            self.current_roundup.config['plan_id'] = plan_id
            self.current_roundup.complete_step(5)
            self.roundup_manager.save(self.current_roundup)
            self._update_roundup_explorer()

        self.status_label.setText("Action plan ready")
        logger.info(f"Plan ready: ID={plan_id}")

    def _on_execution_completed(self, success_count: int, fail_count: int, batch_id: str):
        """Handle execution completion."""
        if self.current_roundup:
            # Persist execution_id in Round-Up config
            self.current_roundup.config['execution_id'] = batch_id
            self.current_roundup.config['execution_success_count'] = success_count
            self.current_roundup.config['execution_fail_count'] = fail_count
            self.current_roundup.complete_step(6)
            self.roundup_manager.save(self.current_roundup)
            self._update_roundup_explorer()
            self._update_save_indicator()

        self.status_label.setText(f"Execution complete: {success_count} succeeded, {fail_count} failed")
        logger.info(f"Execution completed: batch={batch_id}, success={success_count}, fail={fail_count}")

    # ========================================================================
    # Tab Management
    # ========================================================================

    def _close_tab(self, index: int):
        """Close a tab."""
        self.tab_widget.removeTab(index)

    def eventFilter(self, obj, event):
        """Handle middle-click to close tabs."""
        if obj == self.tab_widget.tabBar() and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.MiddleButton:
                tab_index = self.tab_widget.tabBar().tabAt(event.pos())
                if tab_index >= 0:
                    self.tab_widget.removeTab(tab_index)
                    return True
        return super().eventFilter(obj, event)

    # ========================================================================
    # Other Actions
    # ========================================================================

    def _show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(self, "Settings", "Settings dialog coming soon!")

    def _show_jellyfin_settings(self):
        """Show Jellyfin settings dialog."""
        dialog = JellyfinSettingsDialog(self)
        dialog.exec()

    def _toggle_dark_mode(self, checked: bool):
        """Toggle dark mode."""
        global DARK_MODE_ENABLED
        DARK_MODE_ENABLED = checked
        apply_stylesheet(QApplication.instance(), dark_mode=checked)
        logger.info(f"Dark mode: {'ENABLED' if checked else 'DISABLED'}")

    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
<b>JellyRancher Studio - Keyboard Shortcuts</b>

<b>File Menu:</b>
• Ctrl+N - New Round-Up
• Ctrl+O - Open Round-Up
• Ctrl+S - Save Round-Up
• Ctrl+W - Close Round-Up
• Alt+F4 - Exit

<b>Other:</b>
• F12 - Capture GUI state (for debugging)

<b>Workflow:</b>
• Click steps in the Explorer to navigate
• Auto-saves every 30 seconds
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText(shortcuts_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About JellyRancher Studio",
            "<h2>JellyRancher Studio</h2>"
            "<p>Version 3.0 (Round-Up Edition)</p>"
            "<p>Professional media library organization</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>8-step workflow</li>"
            "<li>Round-Up persistence (save/resume)</li>"
            "<li>LLM + Regex + Hybrid analysis</li>"
            "<li>Pre-analysis filtering</li>"
            "<li>Safe execution with rollback</li>"
            "</ul>"
        )

    def _build_widget_tree(self, widget) -> Dict[str, Any]:
        """Recursively build a JSON representation of the widget hierarchy."""
        info = {
            "object_name": widget.objectName() or "(unnamed)",
            "class_name": widget.__class__.__name__,
        }

        # Capture common useful properties
        property_names = [
            "text", "title", "placeholderText", "currentText",
            "toolTip", "isChecked", "isEnabled", "isVisible",
            "minimum", "maximum", "value", "currentIndex"
        ]

        for prop_name in property_names:
            if hasattr(widget, prop_name):
                try:
                    prop = getattr(widget, prop_name)
                    value = prop() if callable(prop) else prop
                    if value not in [None, "", False, 0]:
                        if isinstance(value, (str, int, float, bool)):
                            info[prop_name] = value
                except Exception:
                    pass

        # Capture layout information
        if hasattr(widget, 'layout') and widget.layout() is not None:
            layout = widget.layout()
            info["layout_type"] = layout.__class__.__name__

        # Recursively capture children
        direct_children = [c for c in widget.children() if c.isWidgetType()]
        if direct_children:
            info["children"] = [self._build_widget_tree(child) for child in direct_children]

        return info

    def _capture_gui_state(self):
        """Capture GUI state for debugging (F12)."""
        try:
            captures_dir = Path("gui_captures")
            captures_dir.mkdir(exist_ok=True)

            # Get current context
            current_tab_index = self.tab_widget.currentIndex()
            current_tab_name = self.tab_widget.tabText(current_tab_index) if current_tab_index >= 0 else "Welcome"

            # Build complete widget tree
            widget_tree = self._build_widget_tree(self)

            timestamp = datetime.now()
            capture_data = {
                "metadata": {
                    "captured_at": timestamp.isoformat(),
                    "current_view": current_tab_name,
                    "roundup": self.current_roundup.name if self.current_roundup else "None",
                    "step": self.current_roundup.current_step if self.current_roundup else 0,
                    "capture_method": "F12 Quick Capture"
                },
                "tree": widget_tree
            }

            # Generate filename
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            view_slug = current_tab_name.lower().replace(" ", "_").replace("-", "_")[:20]
            filename = f"{timestamp_str}_{view_slug}.json"
            output_file = captures_dir / filename

            # Custom encoder for Qt objects
            class QtEncoder(json.JSONEncoder):
                def default(self, obj):
                    if hasattr(obj, '__class__') and 'PyQt6' in str(type(obj)):
                        return f"<{obj.__class__.__name__}>"
                    return super().default(obj)

            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(capture_data, f, indent=2, ensure_ascii=False, cls=QtEncoder)

            # Also save to main state file
            with open(Path("gui_runtime_state.json"), 'w', encoding='utf-8') as f:
                json.dump(capture_data, f, indent=2, ensure_ascii=False, cls=QtEncoder)

            # Copy to clipboard
            json_text = json.dumps(capture_data, indent=2, ensure_ascii=False, cls=QtEncoder)
            clipboard = QApplication.clipboard()
            clipboard.setText(json_text)

            self.status_label.setText(f"📸 GUI captured: {filename}")
            logger.info(f"GUI state captured to {output_file}")

            QMessageBox.information(
                self,
                "📸 GUI State Captured",
                f"✅ Copied to clipboard!\n\n"
                f"View: {current_tab_name}\n"
                f"File: gui_captures/{filename}\n\n"
                f"Press Ctrl+V to paste in your next prompt."
            )

        except Exception as e:
            logger.error(f"Failed to capture GUI state: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to capture GUI state: {e}")

    def closeEvent(self, event):
        """Handle window close."""
        if self.current_roundup and self.current_roundup.has_unsaved_changes:
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if result == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif result == QMessageBox.StandardButton.Save:
                self._save_roundup()

        event.accept()


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for uncaught exceptions.
    Logs the exception and shows a user-friendly dialog.
    """
    # Don't handle KeyboardInterrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the full traceback
    import traceback
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Uncaught exception:\n{error_msg}")
    
    # Try to show error dialog if Qt app is running
    try:
        from PyQt6.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None,
                "JellyRancher Error",
                f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
                f"Please check the log file for details."
            )
    except Exception:
        pass  # Qt not available or crashed


def main():
    """Main entry point with comprehensive error handling."""
    # Install global exception handler FIRST
    sys.excepthook = global_exception_handler
    
    # Setup logging
    try:
        master_logger = MasterLogger()
    except Exception as e:
        print(f"CRITICAL: Failed to initialize logging: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("JellyRancher Studio Starting (Round-Up Edition)")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info("=" * 70)

    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("JellyRancher Studio")
        app.setOrganizationName("JellyRancher")
        logger.debug("QApplication created successfully")

        # Apply dark mode stylesheet
        try:
            apply_stylesheet(app, dark_mode=True)
            logger.debug("Stylesheet applied successfully")
        except Exception as e:
            logger.warning(f"Failed to apply stylesheet: {e}")
            # Continue without stylesheet

        # Create and show main window
        try:
            window = JellyRancherStudio()
            window.show()
            logger.info("Main window created and displayed")
        except Exception as e:
            logger.critical(f"Failed to create main window: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Startup Error",
                f"Failed to create main window:\n\n{e}\n\nCheck the log file for details."
            )
            sys.exit(1)

        # Run event loop
        logger.info("Entering Qt event loop")
        exit_code = app.exec()
        logger.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

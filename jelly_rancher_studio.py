#!/usr/bin/env python3
"""
JellyRancher Studio - Modern Project-Centric Media Library Manager

The next-generation GUI for JellyRancher, implementing the "Workflow Canvas"
design from Phase 32. Features project management, flexible workflow, and
professional UI/UX.

Architecture:
    - Project-centric: Everything revolves around projects
    - Task-based: "What do you want to do?" not "Step 3 of 9"
    - Flexible: Non-linear workflow, save/resume anywhere
    - Professional: Modern UI, keyboard shortcuts, smart interactions

Usage:
    python jelly_rancher_studio.py
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import sqlite3

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel,
    QMenuBar, QMenu, QStatusBar, QPushButton, QMessageBox, QDialog,
    QLineEdit, QTextEdit, QDialogButtonBox, QComboBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon

from scripts.core.project_manager import ProjectManager, Project, ProjectState
from scripts._common.logger import MasterLogger
from scripts.ui.scan_view import ScanView
from scripts.ui.analysis_view import AnalysisView
from scripts.ui.review_view import ReviewView
from scripts.ui.execution_view import ExecutionView
from scripts.ui.subtitles_view import SubtitlesView
from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog
from scripts.ui.styles import apply_stylesheet

# Initialize logging
logger = logging.getLogger(__name__)

# Global for dark mode state
DARK_MODE_ENABLED = False


class NewProjectDialog(QDialog):
    """Dialog for creating a new project."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # Project name
        layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My Media Library")
        layout.addWidget(self.name_input)
        
        # Description
        layout.addWidget(QLabel("Description (optional):"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Brief description of this project...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_project_data(self):
        """Get the entered project data."""
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText().strip()
        }


class OpenProjectDialog(QDialog):
    """Dialog for selecting and opening an existing project."""

    def __init__(self, project_manager: 'ProjectManager', parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.setWindowTitle("Open Project")
        self.resize(700, 450)
        self.setModal(True)

        self.projects = self.project_manager.list_projects()
        self.filtered_projects = list(self.projects)
        self.selected_project: Optional[Project] = None

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Search Projects:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name or description...")
        self.search_input.textChanged.connect(self._filter_projects)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Description", "State", "Last Opened"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._handle_double_click)
        layout.addWidget(self.table)

        self.empty_label = QLabel("No projects found. Create a new project first.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._handle_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self._populate_table(self.filtered_projects)

    def _populate_table(self, projects: List[Project]):
        self.table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            name_item = QTableWidgetItem(project.name)
            name_item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.table.setItem(row, 0, name_item)

            desc_text = project.description or ""
            desc_item = QTableWidgetItem(desc_text)
            self.table.setItem(row, 1, desc_item)

            state_item = QTableWidgetItem(project.state.title())
            self.table.setItem(row, 2, state_item)

            last_opened = project.last_opened or ""
            self.table.setItem(row, 3, QTableWidgetItem(last_opened))

        has_projects = bool(projects)
        self.table.setEnabled(has_projects)
        self.empty_label.setVisible(not has_projects)
        if has_projects:
            self.table.resizeColumnsToContents()
            self.table.selectRow(0)

    def _filter_projects(self, text: str):
        query = text.strip().lower()
        if not query:
            self.filtered_projects = list(self.projects)
        else:
            self.filtered_projects = [
                project for project in self.projects
                if query in project.name.lower()
                or query in (project.description or "").lower()
            ]
        self._populate_table(self.filtered_projects)

    def _handle_double_click(self, row: int, _column: int):
        self._select_row(row)

    def _handle_accept(self):
        row = self.table.currentRow()
        self._select_row(row)

    def _select_row(self, row: int):
        if 0 <= row < len(self.filtered_projects):
            self.selected_project = self.filtered_projects[row]
            self.accept()
        elif not self.filtered_projects:
            QMessageBox.information(self, "No Projects", "No projects are available to open.")

    def get_selected_project(self) -> Optional[Project]:
        return self.selected_project


class JellyRancherStudio(QMainWindow):
    """
    Main window for JellyRancher Studio.
    
    Layout:
        - Menu bar (top)
        - Project selector (top right)
        - Left sidebar: Project Explorer
        - Center: Tabbed workspace
        - Right panel: Context panel (collapsible)
        - Bottom: Status bar
    """
    
    # Signals
    project_changed = pyqtSignal(object)  # Emitted when active project changes
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.project_manager = ProjectManager()
        self.current_project: Optional[Project] = None
        self.auto_save_timer = QTimer()
        
        # Setup UI
        self.setWindowTitle("JellyRancher Studio")
        self.resize(1400, 900)

        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        self._setup_keyboard_shortcuts()
        self._setup_auto_save()
        
        # Load last project or show welcome
        self._load_last_project()
        
        logger.info("JellyRancher Studio initialized")
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project...", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        # Recent projects submenu
        self.recent_menu = QMenu("Open &Recent", self)
        file_menu.addMenu(self.recent_menu)
        self._populate_recent_menu()
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        close_action = QAction("&Close Project", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_project)
        file_menu.addAction(close_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("Se&ttings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        # TODO: Add edit actions
        
        # View menu
        view_menu = menubar.addMenu("&View")

        dark_mode_action = QAction("&Dark Mode", self, checkable=True)
        dark_mode_action.setChecked(False)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)

        view_menu.addSeparator()

        shortcuts_action = QAction("Keyboard &Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_keyboard_shortcuts)
        view_menu.addAction(shortcuts_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        jellyfin_settings_action = QAction("&Jellyfin Settings", self)
        jellyfin_settings_action.triggered.connect(self.show_jellyfin_settings)
        tools_menu.addAction(jellyfin_settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _create_main_layout(self):
        """Create the main window layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Main splitter (left sidebar | center workspace)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left sidebar: Project Explorer
        self.project_explorer = self._create_project_explorer()
        main_splitter.addWidget(self.project_explorer)
        
        # Center: Workspace
        self.workspace = self._create_workspace()
        main_splitter.addWidget(self.workspace)
        
        # Set splitter sizes (250px sidebar, rest for workspace)
        main_splitter.setSizes([250, 1150])
        
        main_layout.addWidget(main_splitter)
    
    def _create_project_explorer(self) -> QWidget:
        """Create the left sidebar Project Explorer."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Project Explorer")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("padding: 8px; background-color: #ecf0f1;")
        layout.addWidget(title)
        
        # Tree widget
        self.explorer_tree = QTreeWidget()
        self.explorer_tree.setHeaderHidden(True)
        self.explorer_tree.itemDoubleClicked.connect(self._on_explorer_item_double_clicked)
        layout.addWidget(self.explorer_tree)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(5)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        
        self.btn_scan = QPushButton("▶ Scan Folders")
        self.btn_scan.clicked.connect(self.action_scan)
        btn_layout.addWidget(self.btn_scan)
        
        self.btn_analyze = QPushButton("▶ Analyze Structure")
        self.btn_analyze.clicked.connect(self.action_analyze)
        btn_layout.addWidget(self.btn_analyze)
        
        self.btn_review = QPushButton("▶ Review Plan")
        self.btn_review.clicked.connect(self.action_review)
        btn_layout.addWidget(self.btn_review)
        
        self.btn_execute = QPushButton("▶ Execute Operations")
        self.btn_execute.clicked.connect(self.action_execute)
        btn_layout.addWidget(self.btn_execute)
        
        self.btn_subtitles = QPushButton("▶ Manage Subtitles")
        self.btn_subtitles.clicked.connect(self.action_subtitles)
        btn_layout.addWidget(self.btn_subtitles)
        
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def _create_workspace(self) -> QWidget:
        """Create the center workspace with tabs."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        
        # Welcome tab (shown when no project is open)
        self.welcome_tab = self._create_welcome_tab()
        self.tab_widget.addTab(self.welcome_tab, "Welcome")
        
        return self.tab_widget
    
    def _create_welcome_tab(self) -> QWidget:
        """Create the welcome tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Welcome to JellyRancher Studio")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Your professional media library management workspace")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #566573; padding-bottom: 40px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Action buttons
        btn_new = QPushButton("Create New Project")
        btn_new.setFont(QFont("Segoe UI", 12))
        btn_new.setMinimumHeight(50)
        btn_new.setMaximumWidth(300)
        btn_new.clicked.connect(self.new_project)
        layout.addWidget(btn_new, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn_open = QPushButton("Open Existing Project")
        btn_open.setFont(QFont("Segoe UI", 12))
        btn_open.setMinimumHeight(50)
        btn_open.setMaximumWidth(300)
        btn_open.clicked.connect(self.open_project)
        layout.addWidget(btn_open, alignment=Qt.AlignmentFlag.AlignCenter)
        
        widget.setLayout(layout)
        return widget
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)
        
        # Add permanent widgets (right side)
        self.project_label = QLabel("No project open")
        self.statusBar.addPermanentWidget(self.project_label)
    
    def _setup_auto_save(self):
        """Setup auto-save timer (every 30 seconds)."""
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(30000)  # 30 seconds
    
    def _auto_save(self):
        """Auto-save current project state."""
        if self.current_project:
            try:
                self.project_manager.save_project(self.current_project)
                logger.debug(f"Auto-saved project: {self.current_project.name}")
            except Exception as e:
                logger.error(f"Auto-save failed: {e}")
    
    def _populate_recent_menu(self):
        """Populate the recent projects menu."""
        self.recent_menu.clear()
        
        recent_projects = self.project_manager.get_recent_projects(limit=5)
        
        if not recent_projects:
            no_recent = QAction("(No recent projects)", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
        else:
            for project in recent_projects:
                action = QAction(project.name, self)
                action.triggered.connect(lambda checked, p=project: self.load_project(p.id))
                self.recent_menu.addAction(action)
    
    def _load_last_project(self):
        """Load the most recently opened project."""
        recent = self.project_manager.get_recent_projects(limit=1)
        if recent:
            self.load_project(recent[0].id)
    
    def _update_project_explorer(self):
        """Update the Project Explorer tree with current project data."""
        self.explorer_tree.clear()
        
        if not self.current_project:
            return
        
        # Scans section
        scans_item = QTreeWidgetItem(["📁 Scans"])
        scans_item.setExpanded(True)
        self.explorer_tree.addTopLevelItem(scans_item)
        
        if self.current_project.scan_sessions:
            for scan_id in self.current_project.scan_sessions:
                scan_item = QTreeWidgetItem([f"Scan #{scan_id}"])
                scans_item.addChild(scan_item)
        else:
            no_scans = QTreeWidgetItem(["(No scans yet)"])
            no_scans.setDisabled(True)
            scans_item.addChild(no_scans)
        
        # Analyses section
        analyses_item = QTreeWidgetItem(["🤖 Analyses"])
        analyses_item.setExpanded(True)
        self.explorer_tree.addTopLevelItem(analyses_item)
        
        if self.current_project.analyses:
            for analysis_id in self.current_project.analyses:
                analysis_item = QTreeWidgetItem([f"Analysis #{analysis_id}"])
                analyses_item.addChild(analysis_item)
        else:
            no_analyses = QTreeWidgetItem(["(No analyses yet)"])
            no_analyses.setDisabled(True)
            analyses_item.addChild(no_analyses)
        
        # Action Plans section
        plans_item = QTreeWidgetItem(["📋 Action Plans"])
        plans_item.setExpanded(True)
        self.explorer_tree.addTopLevelItem(plans_item)
        
        if self.current_project.action_plans:
            for plan_id in self.current_project.action_plans:
                plan_item = QTreeWidgetItem([f"Plan #{plan_id}"])
                plans_item.addChild(plan_item)
        else:
            no_plans = QTreeWidgetItem(["(No plans yet)"])
            no_plans.setDisabled(True)
            plans_item.addChild(no_plans)
        
        # Execution section
        execution_item = QTreeWidgetItem(["⚙️ Execution"])
        self.explorer_tree.addTopLevelItem(execution_item)
        
        # Reports section
        reports_item = QTreeWidgetItem(["📊 Reports"])
        self.explorer_tree.addTopLevelItem(reports_item)
    
    def _close_tab(self, index: int):
        """Close a tab."""
        if index > 0:  # Don't close welcome tab
            self.tab_widget.removeTab(index)
    
    def _on_explorer_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on explorer item."""
        parent = item.parent()
        if not parent:
            return

        section = parent.text(0)
        if section.startswith("📁 Scans"):
            self.action_scan()
        elif section.startswith("🤖 Analyses"):
            self.action_analyze()
        elif section.startswith("📋 Action Plans"):
            self.action_review()
        elif section.startswith("⚙️ Execution"):
            self.action_execute()
        elif section.startswith("📊 Reports"):
            QMessageBox.information(self, "Reports", "Reports view is coming soon.")
        else:
            logger.info(f"Explorer item double-clicked: {item.text(0)}")

    def _refresh_current_project(self, current_view: Optional[str] = None):
        """Reload project metadata and refresh explorer tree."""
        if not self.current_project:
            return
        refreshed = self.project_manager.load_project(project_id=self.current_project.id)
        if refreshed:
            self.current_project = refreshed
            self._update_project_explorer()
            if current_view and self.current_project.id:
                try:
                    state = ProjectState(project_id=self.current_project.id, current_view=current_view)
                    self.project_manager.save_project_state(state)
                except Exception as exc:
                    logger.warning("Failed to persist project state: %s", exc)

    def _on_scan_completed(self, scan_id: int):
        """Handle scan completion signal from ScanView."""
        self.status_label.setText(f"Scan session saved (ID #{scan_id})")
        self._refresh_current_project("scan")

    def _on_analysis_saved(self, analysis_id: int):
        """Handle analysis/metadata completion."""
        self.status_label.setText(f"Analysis saved (ID #{analysis_id})")
        self._refresh_current_project("analysis")

    def _on_action_plan_ready(self, action_plan_id: int):
        """Handle action plan readiness from ReviewView."""
        self.status_label.setText(f"Action plan ready (ID #{action_plan_id})")
        self._refresh_current_project("review")
    
    # ========================================================================
    # Project Management Actions
    # ========================================================================
    
    def new_project(self):
        """Create a new project."""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_project_data()
            
            if not data['name']:
                QMessageBox.warning(self, "Invalid Input", "Project name cannot be empty.")
                return
            
            try:
                project = self.project_manager.create_project(
                    data['name'],
                    data['description']
                )
                self.load_project(project.id)
                self.status_label.setText(f"Created project: {project.name}")
                logger.info(f"Created new project: {project.name}")
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def open_project(self):
        """Open an existing project using the selection dialog."""
        dialog = OpenProjectDialog(self.project_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project = dialog.get_selected_project()
            if project and project.id:
                self.load_project(project.id)
            else:
                QMessageBox.warning(self, "No Selection", "Select a project to open.")
    
    def load_project(self, project_id: int):
        """Load a project by ID."""
        try:
            project = self.project_manager.load_project(project_id=project_id)
            if project:
                self.current_project = project
                self.setWindowTitle(f"JellyRancher Studio - {project.name}")
                self.project_label.setText(f"📁 {project.name}")
                self.status_label.setText(f"Loaded project: {project.name}")
                self._update_project_explorer()
                self._populate_recent_menu()
                self.project_changed.emit(project)
                logger.info(f"Loaded project: {project.name}")
            else:
                QMessageBox.critical(self, "Error", f"Project ID {project_id} not found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {e}")
            logger.error(f"Failed to load project {project_id}: {e}")
    
    def save_project(self):
        """Save the current project."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "No project is currently open.")
            return
        
        try:
            self.project_manager.save_project(self.current_project)
            self.status_label.setText(f"Saved project: {self.current_project.name}")
            logger.info(f"Saved project: {self.current_project.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {e}")
    
    def close_project(self):
        """Close the current project."""
        if not self.current_project:
            return
        
        # Auto-save before closing
        self._auto_save()
        
        self.current_project = None
        self.setWindowTitle("JellyRancher Studio")
        self.project_label.setText("No project open")
        self.status_label.setText("Project closed")
        self._update_project_explorer()
        
        # Close all tabs except welcome
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
        
        logger.info("Closed project")
    
    # ========================================================================
    # Workflow Actions (Placeholders for Phase 32B)
    # ========================================================================
    
    def action_scan(self):
        """Start scan workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # Create and open scan view
        scan_view = ScanView(self.current_project, self.project_manager, self)
        scan_view.scan_completed.connect(self._on_scan_completed)
        self.tab_widget.addTab(scan_view, f"📁 Scan - {self.current_project.name}")
        self.tab_widget.setCurrentWidget(scan_view)
        
        logger.info(f"Opened scan view for project: {self.current_project.name}")
    
    def action_analyze(self):
        """Start analysis workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # Create and open analysis view
        analysis_view = AnalysisView(self.current_project, self.project_manager, self)
        analysis_view.analysis_saved.connect(self._on_analysis_saved)
        analysis_view.metadata_built.connect(self._on_analysis_saved)
        self.tab_widget.addTab(analysis_view, f"🤖 Analysis - {self.current_project.name}")
        self.tab_widget.setCurrentWidget(analysis_view)
        
        logger.info(f"Opened analysis view for project: {self.current_project.name}")
    
    def action_review(self):
        """Start review workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # Create and open review view
        review_view = ReviewView(self.current_project, self.project_manager, self)
        review_view.operations_ready.connect(self._on_action_plan_ready)
        self.tab_widget.addTab(review_view, f"📋 Review - {self.current_project.name}")
        self.tab_widget.setCurrentWidget(review_view)
        
        logger.info(f"Opened review view for project: {self.current_project.name}")
    
    def action_execute(self):
        """Start execution workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # Get most recent action plan
        action_plan_id = self._get_latest_action_plan_id()
        
        # Create and open execution view
        execution_view = ExecutionView(self.current_project, self.project_manager, action_plan_id, self)
        self.tab_widget.addTab(execution_view, f"⚙️ Execute - {self.current_project.name}")
        self.tab_widget.setCurrentWidget(execution_view)
        
        logger.info(f"Opened execution view for project: {self.current_project.name}")
    
    def action_subtitles(self):
        """Open subtitles workflow view."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return

        subtitles_view = SubtitlesView(self.current_project, self.project_manager, self)
        self.tab_widget.addTab(subtitles_view, f"💬 Subtitles - {self.current_project.name}")
        self.tab_widget.setCurrentWidget(subtitles_view)
        logger.info(f"Opened subtitles view for project: {self.current_project.name}")
    
    def _get_latest_action_plan_id(self) -> Optional[int]:
        """Get the most recent action plan ID for the current project."""
        try:
            import sqlite3
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM project_action_plans
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (self.current_project.id,))
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get latest action plan: {e}")
            return None
    
    # ========================================================================
    # Other Actions
    # ========================================================================
    
    def show_settings(self):
        """Show settings dialog."""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog coming soon!")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About JellyRancher Studio",
            "<h2>JellyRancher Studio</h2>"
            "<p>Version 2.0 (Phase 32A)</p>"
            "<p>Professional media library management workspace</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Project-centric workflow</li>"
            "<li>Flexible, non-linear operations</li>"
            "<li>Save and resume anywhere</li>"
            "<li>LLM-powered analysis</li>"
            "<li>Safe execution with rollback</li>"
            "</ul>"
        )

    def show_jellyfin_settings(self):
        """Show Jellyfin settings dialog."""
        dialog = JellyfinSettingsDialog(self)
        if dialog.exec():
            QMessageBox.information(
                self,
                "Jellyfin Settings Saved",
                "Jellyfin settings have been updated successfully.\n\n"
                "The refresh checkbox in Execution View will now be enabled."
            )

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for all major actions."""
        from PyQt6.QtGui import QKeySequence

        # File menu shortcuts - PyQt6 uses StandardKey enum
        QAction("New Project", self, shortcut=QKeySequence(QKeySequence.StandardKey.New), triggered=self.new_project)
        QAction("Open Project", self, shortcut=QKeySequence(QKeySequence.StandardKey.Open), triggered=self.open_project)
        QAction("Save Project", self, shortcut=QKeySequence(QKeySequence.StandardKey.Save), triggered=self._auto_save)
        QAction("Settings", self, shortcut=QKeySequence(QKeySequence.StandardKey.Preferences), triggered=self.show_settings)
        QAction("Exit", self, shortcut=QKeySequence(QKeySequence.StandardKey.Quit), triggered=self.close)

    def toggle_dark_mode(self, checked: bool):
        """Toggle dark mode on/off."""
        global DARK_MODE_ENABLED
        DARK_MODE_ENABLED = checked
        apply_stylesheet(QApplication.instance(), dark_mode=checked)
        logger.info(f"Dark mode: {'ENABLED' if checked else 'DISABLED'}")

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
<b>JellyRancher Studio - Keyboard Shortcuts</b>

<b>File Menu:</b>
• Ctrl+N - New Project
• Ctrl+O - Open Project
• Ctrl+S - Save Project
• Ctrl+, - Settings
• Ctrl+Q - Exit

<b>View Menu:</b>
• View > Dark Mode - Toggle dark/light theme
• View > Keyboard Shortcuts - Show this dialog

<b>Tools Menu:</b>
• Tools > Jellyfin Settings - Configure Jellyfin integration

<b>Tips:</b>
• All actions are also available through the menu bar
• Projects auto-save every 30 seconds
• Changes are persisted to the database
"""

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Keyboard Shortcuts")
        msg_box.setText(shortcuts_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def closeEvent(self, event):
        """Handle window close event."""
        # Auto-save before closing
        if self.current_project:
            self._auto_save()
        
        event.accept()


def main():
    """Main entry point."""
    # Setup logging - MasterLogger is a singleton that auto-initializes
    master_logger = MasterLogger()
    
    logger.info("=" * 70)
    logger.info("JellyRancher Studio Starting")
    logger.info("=" * 70)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("JellyRancher Studio")
    app.setOrganizationName("JellyRancher")
    
    # Apply modern stylesheet
    apply_stylesheet(app)
    
    # Create and show main window
    window = JellyRancherStudio()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


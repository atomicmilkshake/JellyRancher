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
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel,
    QMenuBar, QMenu, QStatusBar, QPushButton, QMessageBox, QDialog,
    QLineEdit, QTextEdit, QDialogButtonBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon

from scripts.core.project_manager import ProjectManager, Project, ProjectState
from scripts._common.logger import MasterLogger

# Initialize logging
logger = logging.getLogger(__name__)


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
        # TODO: Add view actions
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        # TODO: Add tools actions
        
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
        subtitle.setStyleSheet("color: #7f8c8d; padding-bottom: 40px;")
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
        # TODO: Open appropriate view based on item type
        logger.info(f"Double-clicked: {item.text(0)}")
    
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
        """Open an existing project (show selection dialog)."""
        # TODO: Implement project selection dialog
        projects = self.project_manager.list_projects()
        
        if not projects:
            QMessageBox.information(self, "No Projects", "No projects found. Create a new project first.")
            return
        
        # For now, just show a simple message
        QMessageBox.information(
            self,
            "Open Project",
            f"Found {len(projects)} projects. Full selection dialog coming in Phase 32B."
        )
    
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
        
        # TODO: Open scan view in Phase 32B
        QMessageBox.information(self, "Scan", "Scan view coming in Phase 32B!")
    
    def action_analyze(self):
        """Start analysis workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # TODO: Open analysis view in Phase 32B
        QMessageBox.information(self, "Analyze", "Analysis view coming in Phase 32B!")
    
    def action_review(self):
        """Start review workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # TODO: Open review view in Phase 32B
        QMessageBox.information(self, "Review", "Review view coming in Phase 32B!")
    
    def action_execute(self):
        """Start execution workflow."""
        if not self.current_project:
            QMessageBox.information(self, "No Project", "Please create or open a project first.")
            return
        
        # TODO: Open execution view in Phase 32B
        QMessageBox.information(self, "Execute", "Execution view coming in Phase 32B!")
    
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
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Auto-save before closing
        if self.current_project:
            self._auto_save()
        
        event.accept()


def main():
    """Main entry point."""
    # Setup logging
    MasterLogger.initialize(
        log_dir=Path("data/logs"),
        app_name="jelly_rancher_studio"
    )
    
    logger.info("=" * 70)
    logger.info("JellyRancher Studio Starting")
    logger.info("=" * 70)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("JellyRancher Studio")
    app.setOrganizationName("JellyRancher")
    
    # Create and show main window
    window = JellyRancherStudio()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


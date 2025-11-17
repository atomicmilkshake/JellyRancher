#!/usr/bin/env python3
"""
Action Plan Review View - Excel-like table for reviewing proposed operations

Implements Point 5 from plan.md: Interactive Review Table
Allows users to review, approve/reject, and edit proposed file operations.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHBoxLayout,
    QLineEdit, QHeaderView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from scripts.core.project_manager import ProjectManager, Project

logger = logging.getLogger(__name__)


class ReviewView(QWidget):
    """
    Review View - Action plan review interface.
    
    Features:
    - Excel-like table with sortable columns
    - Search and filter
    - Bulk approve/reject
    - Inline editing
    - Preview changes
    """
    
    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        
        self.project = project
        self.project_manager = project_manager
        
        self._init_ui()
        
        logger.info(f"ReviewView initialized for project: {project.name}")
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Action Plan Review")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search operations...")
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Bulk action buttons
        button_layout = QHBoxLayout()
        
        btn_select_all = QPushButton("Select All")
        button_layout.addWidget(btn_select_all)
        
        btn_approve = QPushButton("✓ Approve Selected")
        btn_approve.setStyleSheet("background-color: #27ae60; color: white;")
        button_layout.addWidget(btn_approve)
        
        btn_reject = QPushButton("✗ Reject Selected")
        btn_reject.setStyleSheet("background-color: #e74c3c; color: white;")
        button_layout.addWidget(btn_reject)
        
        btn_preview = QPushButton("👁️ Preview Changes")
        button_layout.addWidget(btn_preview)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Operations table
        table_group = QGroupBox("Proposed Operations")
        table_layout = QVBoxLayout()
        
        self.operations_table = QTableWidget()
        self.operations_table.setColumnCount(7)
        self.operations_table.setHorizontalHeaderLabels([
            "☑", "Type", "Current Path", "Proposed Path", "Confidence", "MD5", "Approve"
        ])
        self.operations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.operations_table.setColumnWidth(0, 30)
        self.operations_table.setColumnWidth(1, 80)
        self.operations_table.setColumnWidth(2, 250)
        self.operations_table.setColumnWidth(3, 250)
        self.operations_table.setColumnWidth(4, 90)
        self.operations_table.setColumnWidth(5, 80)
        self.operations_table.setColumnWidth(6, 70)
        self.operations_table.setSortingEnabled(True)
        table_layout.addWidget(self.operations_table)
        
        # Summary
        self.lbl_summary = QLabel("No operations to review")
        self.lbl_summary.setStyleSheet("color: #7f8c8d; padding: 5px;")
        table_layout.addWidget(self.lbl_summary)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group, 1)
        
        # Execute button
        btn_execute = QPushButton("▶ Execute Approved Operations")
        btn_execute.setMinimumHeight(40)
        btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_execute.clicked.connect(self._execute_operations)
        layout.addWidget(btn_execute)
        
        self.setLayout(layout)
    
    def _execute_operations(self):
        """Execute approved operations."""
        QMessageBox.information(
            self,
            "Execute Operations",
            "Operation execution functionality coming in Phase 32C!\n\n"
            "This will execute all approved file operations with full rollback capability."
        )


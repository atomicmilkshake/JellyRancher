#!/usr/bin/env python3
"""
Action Plan Review View - Excel-like table for reviewing proposed operations

Implements Point 5 from plan.md: Interactive Review Table
Allows users to review, approve/reject, and edit proposed file operations.
"""

import logging
import sqlite3
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHBoxLayout,
    QLineEdit, QHeaderView, QCheckBox, QDialog, QTextEdit,
    QDialogButtonBox, QComboBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.core.action_plan import ProposedOperation, ActionType, Confidence

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
    
    # Signal emitted when operations are ready for execution
    operations_ready = pyqtSignal(int)  # action_plan_id
    
    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        
        self.project = project
        self.project_manager = project_manager
        self.operations = []  # List of ProposedOperation objects
        self.current_action_plan_id = None
        
        self._init_ui()
        self._load_analysis_data()
        
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
        
        # Search bar with filter dropdown
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search operations...")
        search_layout.addWidget(self.search_input)

        search_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Operations",
            "Approved Only",
            "High Confidence (≥90%)",
            "Manual Review (70-89%)",
            "Moves Only",
            "Renames Only"
        ])
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        search_layout.addWidget(self.filter_combo)

        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Bulk action buttons
        button_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._select_all)
        button_layout.addWidget(self.btn_select_all)
        
        self.btn_approve = QPushButton("✓ Approve Selected")
        self.btn_approve.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_approve.clicked.connect(self._approve_selected)
        button_layout.addWidget(self.btn_approve)
        
        self.btn_reject = QPushButton("✗ Reject Selected")
        self.btn_reject.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_reject.clicked.connect(self._reject_selected)
        button_layout.addWidget(self.btn_reject)
        
        self.btn_preview = QPushButton("👁️ Preview Changes")
        self.btn_preview.clicked.connect(self._preview_changes)
        button_layout.addWidget(self.btn_preview)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Search functionality
        self.search_input.textChanged.connect(self._filter_operations)
        
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
    
    def _load_analysis_data(self):
        """Load most recent analysis and generate action plan."""
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            # Get most recent analysis for this project
            cursor.execute('''
                SELECT id, parsed_json, issues_found
                FROM project_analyses
                WHERE project_id = ?
                ORDER BY analysis_date DESC
                LIMIT 1
            ''', (self.project.id,))
            
            row = cursor.fetchone()
            if row:
                analysis_id, parsed_json_str, issues_found = row
                parsed_json = json.loads(parsed_json_str) if parsed_json_str else {}
                
                # Generate simple operations from LLM recommendations
                recommendations = parsed_json.get('recommendations', [])
                
                for i, rec in enumerate(recommendations[:20]):  # Limit to 20 for demo
                    # Create a simplified ProposedOperation
                    op = ProposedOperation(
                        record_id=f"op_{i}",
                        action_type=ActionType.RENAME,  # Simplified for demo
                        source_path=rec.get('current_path', f'/path/to/file_{i}.mkv'),
                        destination_path=rec.get('proposed_path', f'/path/to/renamed_{i}.mkv'),
                        confidence=Confidence.HIGH if rec.get('confidence', 0.8) > 0.9 else Confidence.MEDIUM,
                        color_code='green' if rec.get('confidence', 0.8) > 0.9 else 'yellow',
                        metadata=None,
                        notes=rec.get('reason', 'LLM recommendation'),
                        user_approved=False,
                        jellyfin_status="New"
                    )
                    self.operations.append(op)
                
                # If no recommendations, create demo data
                if not self.operations:
                    logger.info("No LLM recommendations found, creating demo operations")
                    self._create_demo_operations()
                
                # Populate table
                self._populate_table()
                
                logger.info(f"Loaded {len(self.operations)} operations from analysis {analysis_id}")
            else:
                logger.info("No analysis found, creating demo operations")
                self._create_demo_operations()
                self._populate_table()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load analysis data: {e}", exc_info=True)
            self._create_demo_operations()
            self._populate_table()
    
    def _create_demo_operations(self):
        """Create demo operations for testing."""
        demo_ops = [
            {
                'source': '/media/Movies/movie_2023.mkv',
                'dest': '/media/Movies/Movie Title (2023).mkv',
                'confidence': Confidence.HIGH,
                'notes': 'Standardize naming convention'
            },
            {
                'source': '/media/TV/show_s01e01.mkv',
                'dest': '/media/TV/Show Name/Season 01/Show Name - S01E01 - Episode Title.mkv',
                'confidence': Confidence.HIGH,
                'notes': 'Organize into season folders'
            },
            {
                'source': '/media/Movies/old_movie.avi',
                'dest': '/media/Movies/Old Movie (1999).avi',
                'confidence': Confidence.MEDIUM,
                'notes': 'Add year to filename'
            },
        ]
        
        for i, demo in enumerate(demo_ops):
            op = ProposedOperation(
                record_id=f"demo_{i}",
                action_type=ActionType.RENAME,
                source_path=demo['source'],
                destination_path=demo['dest'],
                confidence=demo['confidence'],
                color_code='green' if demo['confidence'] == Confidence.HIGH else 'yellow',
                metadata=None,
                notes=demo['notes'],
                user_approved=False,
                jellyfin_status="New"
            )
            self.operations.append(op)
    
    def _populate_table(self):
        """Populate the operations table."""
        self.operations_table.setRowCount(len(self.operations))
        
        for row, op in enumerate(self.operations):
            # Checkbox
            checkbox = QCheckBox()
            self.operations_table.setCellWidget(row, 0, checkbox)
            
            # Type
            type_item = QTableWidgetItem(op.action_type.value if hasattr(op.action_type, 'value') else str(op.action_type))
            self.operations_table.setItem(row, 1, type_item)
            
            # Current Path
            current_item = QTableWidgetItem(str(op.source_path))
            self.operations_table.setItem(row, 2, current_item)
            
            # Proposed Path
            proposed_item = QTableWidgetItem(str(op.destination_path))
            self.operations_table.setItem(row, 3, proposed_item)
            
            # Confidence
            conf_str = op.confidence.value if hasattr(op.confidence, 'value') else str(op.confidence)
            confidence_item = QTableWidgetItem(conf_str)
            if op.confidence == Confidence.HIGH:
                confidence_item.setBackground(QColor(39, 174, 96, 50))  # Green
            elif op.confidence == Confidence.MEDIUM:
                confidence_item.setBackground(QColor(243, 156, 18, 50))  # Orange
            else:
                confidence_item.setBackground(QColor(231, 76, 60, 50))  # Red
            self.operations_table.setItem(row, 4, confidence_item)
            
            # MD5 (placeholder)
            md5_item = QTableWidgetItem("N/A")
            self.operations_table.setItem(row, 5, md5_item)
            
            # Approve checkbox
            approve_checkbox = QCheckBox()
            approve_checkbox.setChecked(op.user_approved)
            approve_checkbox.stateChanged.connect(lambda state, r=row: self._on_approve_changed(r, state))
            self.operations_table.setCellWidget(row, 6, approve_checkbox)
        
        # Update summary
        approved_count = sum(1 for op in self.operations if op.user_approved)
        self.lbl_summary.setText(
            f"Total: {len(self.operations)} operations | "
            f"Approved: {approved_count} | "
            f"Pending: {len(self.operations) - approved_count}"
        )
    
    def _on_approve_changed(self, row: int, state: int):
        """Handle approve checkbox state change."""
        if 0 <= row < len(self.operations):
            self.operations[row].user_approved = (state == Qt.CheckState.Checked.value)
            self._update_summary()
    
    def _update_summary(self):
        """Update the summary label."""
        approved_count = sum(1 for op in self.operations if op.user_approved)
        self.lbl_summary.setText(
            f"Total: {len(self.operations)} operations | "
            f"Approved: {approved_count} | "
            f"Pending: {len(self.operations) - approved_count}"
        )
    
    def _select_all(self):
        """Select all operations."""
        for row in range(self.operations_table.rowCount()):
            checkbox = self.operations_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def _approve_selected(self):
        """Approve all selected operations."""
        for row in range(self.operations_table.rowCount()):
            checkbox = self.operations_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                approve_checkbox = self.operations_table.cellWidget(row, 6)
                if approve_checkbox:
                    approve_checkbox.setChecked(True)
    
    def _reject_selected(self):
        """Reject all selected operations."""
        for row in range(self.operations_table.rowCount()):
            checkbox = self.operations_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                approve_checkbox = self.operations_table.cellWidget(row, 6)
                if approve_checkbox:
                    approve_checkbox.setChecked(False)
    
    def _filter_operations(self, search_text: str):
        """Filter operations based on search text."""
        for row in range(self.operations_table.rowCount()):
            show_row = False
            if not search_text:
                show_row = True
            else:
                # Search in current and proposed paths
                for col in [2, 3]:
                    item = self.operations_table.item(row, col)
                    if item and search_text.lower() in item.text().lower():
                        show_row = True
                        break
            
            self.operations_table.setRowHidden(row, not show_row)

    def _apply_filter(self, filter_text: str):
        """Apply filter based on selected filter type."""
        for row in range(self.operations_table.rowCount()):
            show_row = True

            if filter_text == "Approved Only":
                # Only show approved operations
                approve_checkbox = self.operations_table.cellWidget(row, 6)
                if approve_checkbox:
                    show_row = approve_checkbox.isChecked()

            elif filter_text == "High Confidence (≥90%)":
                # Only show high confidence operations
                confidence_item = self.operations_table.item(row, 4)
                if confidence_item:
                    try:
                        confidence_pct = float(confidence_item.text().rstrip('%'))
                        show_row = confidence_pct >= 90
                    except ValueError:
                        show_row = True

            elif filter_text == "Manual Review (70-89%)":
                # Show medium confidence operations
                confidence_item = self.operations_table.item(row, 4)
                if confidence_item:
                    try:
                        confidence_pct = float(confidence_item.text().rstrip('%'))
                        show_row = 70 <= confidence_pct < 90
                    except ValueError:
                        show_row = True

            elif filter_text == "Moves Only":
                # Only show move operations
                op_type_item = self.operations_table.item(row, 1)
                if op_type_item:
                    show_row = "MOVE" in op_type_item.text().upper()

            elif filter_text == "Renames Only":
                # Only show rename operations
                op_type_item = self.operations_table.item(row, 1)
                if op_type_item:
                    show_row = "RENAME" in op_type_item.text().upper()

            self.operations_table.setRowHidden(row, not show_row)

    def _preview_changes(self):
        """Preview the proposed changes."""
        approved_ops = [op for op in self.operations if op.user_approved]
        
        if not approved_ops:
            QMessageBox.warning(self, "No Operations", "No operations are approved for preview.")
            return
        
        # Create preview dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Preview Changes")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        
        # Build preview text
        preview_content = f"Preview of {len(approved_ops)} Approved Operations:\n\n"
        for i, op in enumerate(approved_ops, 1):
            preview_content += f"{i}. {op.action_type}\n"
            preview_content += f"   FROM: {op.source_path}\n"
            preview_content += f"   TO:   {op.destination_path}\n"
            preview_content += f"   Confidence: {op.confidence}\n"
            preview_content += f"   Notes: {op.notes}\n\n"
        
        preview_text.setPlainText(preview_content)
        layout.addWidget(preview_text)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.close)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _execute_operations(self):
        """Execute approved operations."""
        approved_ops = [op for op in self.operations if op.user_approved]
        
        if not approved_ops:
            QMessageBox.warning(self, "No Operations", "No operations are approved for execution.")
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Execute Operations",
            f"Execute {len(approved_ops)} approved operations?\n\n"
            f"This will modify files on disk. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Save to database and signal for execution
        self._save_action_plan_to_database()
        
        QMessageBox.information(
            self,
            "Ready for Execution",
            f"{len(approved_ops)} operations are ready.\n\n"
            f"Open the Execution Monitor to run them."
        )
        
        # Emit signal
        if self.current_action_plan_id:
            self.operations_ready.emit(self.current_action_plan_id)
    
    def _save_action_plan_to_database(self):
        """Save the action plan to database."""
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            # Create action plan
            approved_count = sum(1 for op in self.operations if op.user_approved)
            
            cursor.execute('''
                INSERT INTO project_action_plans
                (project_id, plan_name, total_operations, approved_count, rejected_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.project.id,
                f"Action Plan {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                len(self.operations),
                approved_count,
                len(self.operations) - approved_count
            ))
            
            self.current_action_plan_id = cursor.lastrowid
            
            # Save operations
            for op in self.operations:
                cursor.execute('''
                    INSERT INTO project_operations
                    (action_plan_id, operation_type, current_path, proposed_path,
                     confidence, user_approved, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_action_plan_id,
                    str(op.action_type),
                    str(op.source_path),
                    str(op.destination_path),
                    str(op.confidence),
                    1 if op.user_approved else 0,
                    op.notes
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved action plan to database: ID={self.current_action_plan_id}")
            
        except Exception as e:
            logger.error(f"Failed to save action plan: {e}", exc_info=True)


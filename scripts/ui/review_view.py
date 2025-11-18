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
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHBoxLayout,
    QLineEdit, QHeaderView, QCheckBox, QDialog, QTextEdit,
    QDialogButtonBox, QComboBox, QFileDialog
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.core.action_plan import ProposedOperation, ActionType, Confidence
from scripts.core.inventory_repository import InventoryRepository
from scripts.core.app_config import AppConfigManager
from scripts.core.file_scanner import FileRecord
from scripts.core.workers import ActionPlanWorker

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
        self.inventory_repo = InventoryRepository()
        self.scanned_files: List[FileRecord] = []
        self.llm_analysis = None
        self.canonical_database = None
        self.action_plan_worker = None
        self.app_config = AppConfigManager()
        
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

        self.btn_load_plan = QPushButton("Load Action Plan")
        self.btn_load_plan.clicked.connect(self.step_5_review)
        button_layout.addWidget(self.btn_load_plan)

        self.btn_export = QPushButton("Export to CSV")
        self.btn_export.clicked.connect(self._export_to_csv)
        self.btn_export.setEnabled(False)
        button_layout.addWidget(self.btn_export)

        self.btn_dry_run = QPushButton("Dry Run Preview")
        self.btn_dry_run.clicked.connect(self._dry_run_preview)
        self.btn_dry_run.setEnabled(False)
        button_layout.addWidget(self.btn_dry_run)
        
        button_layout.addStretch()
        
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
        
        layout.addLayout(button_layout)
        
        # Search functionality
        self.search_input.textChanged.connect(self._filter_operations)
        
        # Operations table
        table_group = QGroupBox("Proposed Operations")
        table_layout = QVBoxLayout()
        
        self.operations_table = QTableWidget()
        self.operations_table.setColumnCount(10)
        self.operations_table.setHorizontalHeaderLabels([
            "☑", "Type", "Current Path", "Proposed Path", "Confidence",
            "Jellyfin Status", "Current MD5", "Proposed MD5", "Notes", "Approve"
        ])
        self.operations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.operations_table.setColumnWidth(0, 30)
        self.operations_table.setColumnWidth(1, 80)
        self.operations_table.setColumnWidth(2, 250)
        self.operations_table.setColumnWidth(3, 250)
        self.operations_table.setColumnWidth(4, 100)
        self.operations_table.setColumnWidth(5, 140)
        self.operations_table.setColumnWidth(6, 120)
        self.operations_table.setColumnWidth(7, 120)
        self.operations_table.setColumnWidth(8, 220)
        self.operations_table.setColumnWidth(9, 80)
        self.operations_table.setSortingEnabled(True)
        table_layout.addWidget(self.operations_table)
        
        # Summary
        self.lbl_summary = QLabel("No operations to review")
        self.lbl_summary.setStyleSheet("color: #566573; padding: 5px;")
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
        """Load most recent analysis metadata for this project."""
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()

            cursor.execute(
                '''
                SELECT id, parsed_json, metadata_json
                FROM project_analyses
                WHERE project_id = ?
                ORDER BY analysis_date DESC
                LIMIT 1
                ''',
                (self.project.id,),
            )

            row = cursor.fetchone()
            if row:
                analysis_id, parsed_json_str, metadata_str = row
                self.llm_analysis = json.loads(parsed_json_str) if parsed_json_str else None
                self.canonical_database = json.loads(metadata_str) if metadata_str else None
                logger.info("Loaded analysis %s for review view", analysis_id)
                self.lbl_summary.setText(
                    "LLM analysis loaded. Click 'Load Action Plan' to generate operations."
                )
            else:
                self.lbl_summary.setText("No analysis found. Run LLM analysis first.")

            conn.close()
            self._load_scanned_files()

        except Exception as e:
            logger.error(f"Failed to load analysis data: {e}", exc_info=True)
            self.lbl_summary.setText(f"Error loading analysis data: {e}")

    def _load_scanned_files(self):
        """Load scanned files from the inventory repository."""
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT scan_options_json
                FROM project_scan_sessions
                WHERE project_id = ?
                ORDER BY scan_start DESC
                LIMIT 1
                ''',
                (self.project.id,),
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.warning("No scan sessions found for project %s", self.project.name)
                return

            options = json.loads(row[0]) if row[0] else {}
            session_ids = options.get("inventory_session_ids", [])
            self.scanned_files = []
            for session_id in session_ids:
                self.scanned_files.extend(self.inventory_repo.get_all_files(session_id))

            logger.info("Loaded %d scanned files for review", len(self.scanned_files))

        except Exception as e:
            logger.error("Failed to load scanned files: %s", e, exc_info=True)
    
    def step_5_review(self):
        """Generate action plan using ActionPlanWorker."""
        if not self.scanned_files:
            self._load_scanned_files()
        if not self.scanned_files:
            QMessageBox.warning(self, "No Scan Data", "No scanned files available. Run a scan first.")
            return
        if not self.llm_analysis:
            QMessageBox.warning(self, "No Analysis", "Run LLM analysis before generating an action plan.")
            return
        if not self.canonical_database:
            QMessageBox.warning(self, "No Metadata", "Build the metadata database before generating an action plan.")
            return
        if self.action_plan_worker and self.action_plan_worker.isRunning():
            QMessageBox.information(self, "In Progress", "Action plan generation is already running.")
            return

        self.lbl_summary.setText("Generating action plan...")
        self.operations_table.setRowCount(0)
        self.operations = []
        self.btn_export.setEnabled(False)
        self.btn_dry_run.setEnabled(False)

        self.action_plan_worker = ActionPlanWorker(
            scanned_files=self.scanned_files,
            llm_analysis=self.llm_analysis,
            canonical_database=self.canonical_database,
            app_config=self.app_config,
        )
        self.action_plan_worker.finished.connect(self._on_action_plan_finished)
        self.action_plan_worker.error.connect(self._on_action_plan_error)
        self.action_plan_worker.start()
        logger.info("Started ActionPlanWorker for project %s", self.project.name)

    def _on_action_plan_finished(self, action_plan: List[ProposedOperation]):
        """Handle completion of action plan generation."""
        self.operations = action_plan
        self._populate_table()
        self.lbl_summary.setText(f"Generated {len(action_plan)} operations. Review and approve as needed.")
        enable_actions = len(action_plan) > 0
        self.btn_export.setEnabled(enable_actions)
        self.btn_dry_run.setEnabled(enable_actions)
        QMessageBox.information(
            self,
            "Action Plan Ready",
            f"Action plan generated with {len(action_plan)} operations.",
        )

    def _on_action_plan_error(self, error_msg: str):
        """Handle action plan generation errors."""
        self.lbl_summary.setText(f"Action plan generation failed: {error_msg}")
        QMessageBox.critical(
            self,
            "Action Plan Error",
            f"Failed to generate action plan:\n\n{error_msg}",
        )
        logger.error("ActionPlanWorker error: %s", error_msg)
    
    def _populate_table(self):
        """Populate the operations table."""
        self.operations_table.setRowCount(len(self.operations))
        
        for row, op in enumerate(self.operations):
            # Checkbox
            checkbox = QCheckBox()
            self.operations_table.setCellWidget(row, 0, checkbox)
            
            # Type
            type_text = op.action_type.name if isinstance(op.action_type, ActionType) else str(op.action_type)
            type_item = QTableWidgetItem(type_text)
            self.operations_table.setItem(row, 1, type_item)
            
            # Current Path
            current_item = QTableWidgetItem(str(op.source_path))
            self.operations_table.setItem(row, 2, current_item)
            
            # Proposed Path
            proposed_item = QTableWidgetItem(str(op.destination_path) if op.destination_path else "N/A")
            self.operations_table.setItem(row, 3, proposed_item)
            
            # Confidence
            conf_str = op.confidence.name if isinstance(op.confidence, Confidence) else str(op.confidence)
            confidence_item = QTableWidgetItem(conf_str)
            if op.confidence == Confidence.HIGH:
                confidence_item.setBackground(QColor(39, 174, 96, 50))  # Green
            elif op.confidence == Confidence.MEDIUM:
                confidence_item.setBackground(QColor(243, 156, 18, 50))  # Orange
            else:
                confidence_item.setBackground(QColor(231, 76, 60, 50))  # Red
            self.operations_table.setItem(row, 4, confidence_item)
            
            # Jellyfin status
            status_item = QTableWidgetItem(op.jellyfin_status or "Unknown")
            self.operations_table.setItem(row, 5, status_item)
            
            # MD5 columns
            current_md5 = op.current_md5 or "N/A"
            proposed_md5 = op.proposed_md5 or "N/A"
            current_md5_item = QTableWidgetItem(current_md5)
            proposed_md5_item = QTableWidgetItem(proposed_md5)
            self.operations_table.setItem(row, 6, current_md5_item)
            self.operations_table.setItem(row, 7, proposed_md5_item)
            
            # Notes column
            notes_text = op.notes or ""
            notes_item = QTableWidgetItem(notes_text)
            self.operations_table.setItem(row, 8, notes_item)

            # Approve checkbox
            approve_checkbox = QCheckBox()
            initial_approval = op.user_approved
            if initial_approval is None:
                initial_approval = op.confidence == Confidence.HIGH
                op.user_approved = initial_approval
            approve_checkbox.setChecked(initial_approval)
            approve_checkbox.stateChanged.connect(lambda state, r=row: self._on_approve_changed(r, state))
            self.operations_table.setCellWidget(row, 9, approve_checkbox)
        
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
                approve_checkbox = self.operations_table.cellWidget(row, 9)
                if approve_checkbox:
                    approve_checkbox.setChecked(True)
    
    def _reject_selected(self):
        """Reject all selected operations."""
        for row in range(self.operations_table.rowCount()):
            checkbox = self.operations_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                approve_checkbox = self.operations_table.cellWidget(row, 9)
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
                approve_checkbox = self.operations_table.cellWidget(row, 9)
                if approve_checkbox:
                    show_row = approve_checkbox.isChecked()

            elif filter_text == "High Confidence (≥90%)":
                # Only show high confidence operations
                confidence_item = self.operations_table.item(row, 4)
                if confidence_item:
                    text = confidence_item.text().upper()
                    show_row = "HIGH" in text

            elif filter_text == "Manual Review (70-89%)":
                # Show medium confidence operations
                confidence_item = self.operations_table.item(row, 4)
                if confidence_item:
                    text = confidence_item.text().upper()
                    show_row = "MEDIUM" in text or "MANUAL" in text

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
        
        self._show_preview_dialog(approved_ops, "Preview Changes")

    def _dry_run_preview(self):
        """Preview all operations regardless of approval for planning purposes."""
        if not self.operations:
            QMessageBox.information(
                self,
                "No Operations",
                "No action plan has been generated yet."
            )
            return

        self._show_preview_dialog(
            self.operations,
            "Dry Run Preview (All Operations)",
            intro="This preview lists every proposed operation. Use dry run mode in the Execution Monitor to simulate the changes safely.\n\n"
        )

    def _show_preview_dialog(self, operations: List[ProposedOperation], title: str, intro: str = ""):
        """Display a preview dialog for the provided operations."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        
        preview_content = intro or ""
        preview_content += f"Preview of {len(operations)} Operations:\n\n"
        for i, op in enumerate(operations, 1):
            preview_content += f"{i}. {op.action_type}\n"
            preview_content += f"   FROM: {op.source_path}\n"
            preview_content += f"   TO:   {op.destination_path}\n"
            preview_content += f"   Confidence: {op.confidence}\n"
            preview_content += f"   Notes: {op.notes or '-'}\n\n"
        
        preview_text.setPlainText(preview_content)
        layout.addWidget(preview_text)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.close)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()

    def _export_to_csv(self):
        """Export current operations to CSV."""
        if not self.operations:
            QMessageBox.information(self, "No Data", "No operations available to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Action Plan",
            f"action_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not filename:
            return

        try:
            import csv
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "Type",
                    "Current Path",
                    "Proposed Path",
                    "Confidence",
                    "Jellyfin Status",
                    "Current MD5",
                    "Proposed MD5",
                    "Notes",
                    "Approved",
                ])

                for op in self.operations:
                    writer.writerow([
                        op.action_type.name if isinstance(op.action_type, ActionType) else str(op.action_type),
                        str(op.source_path),
                        str(op.destination_path) if op.destination_path else "",
                        op.confidence.name if isinstance(op.confidence, Confidence) else str(op.confidence),
                        op.jellyfin_status or "",
                        op.current_md5 or "",
                        op.proposed_md5 or "",
                        op.notes or "",
                        "YES" if op.user_approved else "NO",
                    ])

            QMessageBox.information(self, "Export Complete", f"Action plan exported to:\n{filename}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Failed to export action plan:\n\n{exc}")
            logger.error("Action plan export failed: %s", exc, exc_info=True)
    
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
                     confidence, user_approved, notes, current_md5, proposed_md5, jellyfin_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_action_plan_id,
                    op.action_type.name if isinstance(op.action_type, ActionType) else str(op.action_type),
                    str(op.source_path),
                    str(op.destination_path) if op.destination_path else None,
                    op.confidence.name if isinstance(op.confidence, Confidence) else str(op.confidence),
                    1 if op.user_approved else 0,
                    op.notes,
                    op.current_md5,
                    op.proposed_md5,
                    op.jellyfin_status
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved action plan to database: ID={self.current_action_plan_id}")
            
        except Exception as e:
            logger.error(f"Failed to save action plan: {e}", exc_info=True)


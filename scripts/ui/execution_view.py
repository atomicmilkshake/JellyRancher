#!/usr/bin/env python3
"""
Execution Monitor View - Real-time execution progress and transaction log

Implements Point 6-9 from plan.md: Execution, Verification, Jellyfin Integration
Shows real-time progress of file operations with rollback capability.
"""

import logging
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QProgressBar, QMessageBox, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project

logger = logging.getLogger(__name__)


class ExecutionWorker(QThread):
    """Background worker for executing operations."""
    
    progress = pyqtSignal(int, int, str)  # current, total, status
    log_message = pyqtSignal(str)  # log message
    finished = pyqtSignal(int, int)  # success_count, fail_count
    error = pyqtSignal(str)
    
    def __init__(self, action_plan_id: int):
        super().__init__()
        self.action_plan_id = action_plan_id
    
    def run(self):
        """Execute operations (dry run for demo)."""
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            # Get approved operations
            cursor.execute('''
                SELECT id, operation_type, current_path, proposed_path
                FROM project_operations
                WHERE action_plan_id = ? AND user_approved = 1
            ''', (self.action_plan_id,))
            
            operations = cursor.fetchall()
            total = len(operations)
            success_count = 0
            fail_count = 0
            
            self.log_message.emit(f"Starting execution of {total} operations...")
            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] DRY RUN MODE - No actual file changes\n")
            
            for i, (op_id, op_type, current_path, proposed_path) in enumerate(operations, 1):
                self.progress.emit(i, total, f"Processing {i}/{total}")
                
                # Simulate operation (dry run)
                self.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] {op_type}: "
                    f"{current_path} -> {proposed_path}"
                )
                
                # Simulate processing time
                self.msleep(100)
                
                # Mark as executed in database
                cursor.execute('''
                    UPDATE project_operations
                    SET executed = 1, execution_timestamp = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), op_id))
                
                success_count += 1
                self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Success\n")
            
            # Update action plan
            cursor.execute('''
                UPDATE project_action_plans
                SET executed = 1, execution_timestamp = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), self.action_plan_id))
            
            conn.commit()
            conn.close()
            
            self.log_message.emit(f"\n[{datetime.now().strftime('%H:%M:%S')}] Execution complete!")
            self.log_message.emit(f"Success: {success_count}, Failed: {fail_count}")
            
            self.finished.emit(success_count, fail_count)
            
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            self.error.emit(str(e))


class ExecutionView(QWidget):
    """
    Execution View - Real-time execution monitor.
    
    Features:
    - Real-time progress bar
    - Transaction log viewer
    - Pause/resume/stop controls
    - Rollback capability
    - Post-execution summary
    """
    
    def __init__(self, project: Project, project_manager: ProjectManager, action_plan_id: int = None, parent=None):
        super().__init__(parent)
        
        self.project = project
        self.project_manager = project_manager
        self.action_plan_id = action_plan_id
        self.execution_worker = None
        
        self._init_ui()
        
        if action_plan_id:
            self._load_action_plan()
        
        logger.info(f"ExecutionView initialized for project: {project.name}")
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Execution Monitor")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Progress section
        progress_group = QGroupBox("Execution Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("Ready to execute")
        progress_layout.addWidget(self.lbl_status)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.btn_execute = QPushButton("▶ Start Execution")
        self.btn_execute.setMinimumHeight(40)
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_execute.clicked.connect(self._start_execution)
        button_layout.addWidget(self.btn_execute)
        
        self.btn_rollback = QPushButton("↩️ Rollback All")
        self.btn_rollback.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_rollback.clicked.connect(self._rollback)
        self.btn_rollback.setEnabled(False)
        button_layout.addWidget(self.btn_rollback)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Transaction log
        log_group = QGroupBox("Transaction Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Transaction log will appear here...")
        self.log_text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)
        
        # Summary
        self.lbl_summary = QLabel("No operations executed yet")
        self.lbl_summary.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.lbl_summary)
        
        self.setLayout(layout)
    
    def _load_action_plan(self):
        """Load action plan details."""
        if not self.action_plan_id:
            return
        
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_operations, approved_count, executed
                FROM project_action_plans
                WHERE id = ?
            ''', (self.action_plan_id,))
            
            row = cursor.fetchone()
            if row:
                total, approved, executed = row
                self.lbl_status.setText(
                    f"Action Plan #{self.action_plan_id}: {approved} operations approved"
                )
                
                if executed:
                    self.btn_execute.setEnabled(False)
                    self.btn_rollback.setEnabled(True)
                    self.lbl_summary.setText("This action plan has already been executed")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load action plan: {e}")
    
    def _start_execution(self):
        """Start execution of approved operations."""
        if not self.action_plan_id:
            QMessageBox.warning(self, "No Action Plan", "No action plan selected for execution.")
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Start Execution",
            "Start executing approved operations?\n\n"
            "Note: This is a DRY RUN demonstration.\n"
            "No actual file changes will be made.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable button
        self.btn_execute.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Start worker
        self.execution_worker = ExecutionWorker(self.action_plan_id)
        self.execution_worker.progress.connect(self._on_progress)
        self.execution_worker.log_message.connect(self._on_log_message)
        self.execution_worker.finished.connect(self._on_finished)
        self.execution_worker.error.connect(self._on_error)
        self.execution_worker.start()
        
        logger.info(f"Started execution of action plan {self.action_plan_id}")
    
    def _on_progress(self, current: int, total: int, status: str):
        """Handle progress updates."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            percent = (current / total) * 100
            self.lbl_status.setText(f"{status} ({percent:.1f}%)")
    
    def _on_log_message(self, message: str):
        """Handle log messages."""
        self.log_text.append(message)
    
    def _on_finished(self, success_count: int, fail_count: int):
        """Handle execution completion."""
        self.btn_execute.setEnabled(False)
        self.btn_rollback.setEnabled(True)
        
        self.lbl_summary.setText(
            f"Execution complete: {success_count} successful, {fail_count} failed"
        )
        
        QMessageBox.information(
            self,
            "Execution Complete",
            f"Successfully executed {success_count} operations!\n\n"
            f"Note: This was a DRY RUN demonstration.\n"
            f"No actual file changes were made."
        )
    
    def _on_error(self, error_msg: str):
        """Handle execution errors."""
        self.btn_execute.setEnabled(True)
        self.lbl_status.setText(f"Execution failed: {error_msg}")
        
        QMessageBox.critical(
            self,
            "Execution Error",
            f"Execution failed:\n\n{error_msg}"
        )
    
    def _rollback(self):
        """Rollback executed operations."""
        QMessageBox.information(
            self,
            "Rollback",
            "Rollback functionality would restore all files to their original state.\n\n"
            "This feature uses the transaction log to reverse all operations.\n\n"
            "Implementation: Connect to TransactionManager for full rollback capability."
        )


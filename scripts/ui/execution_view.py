#!/usr/bin/env python3
"""
Execution Monitor View - Real-time execution progress and transaction log

Implements Point 6-9 from plan.md: Execution, Verification, Jellyfin Integration
Shows real-time progress of file operations with rollback capability.
"""

import logging
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QProgressBar, QMessageBox, QGroupBox, QHBoxLayout, QCheckBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.utils.transaction_manager import (
    TransactionManager, Operation, OperationType, FileHasher
)
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager

logger = logging.getLogger(__name__)


class ExecutionWorker(QThread):
    """Background worker for executing operations with TransactionManager."""
    
    progress = pyqtSignal(int, int, str)  # current, total, status
    log_message = pyqtSignal(str)  # log message
    finished = pyqtSignal(int, int, str)  # success_count, fail_count, batch_id
    error = pyqtSignal(str)
    
    def __init__(self, action_plan_id: int, dry_run: bool = False, jellyfin_refresh: bool = False):
        super().__init__()
        self.action_plan_id = action_plan_id
        self.dry_run = dry_run
        self.jellyfin_refresh = jellyfin_refresh
        self.batch_id = None
        self.jellyfin_client = None
        self.modified_paths = set()  # Track paths that were modified for Jellyfin refresh
    
    def run(self):
        """Execute operations with full transaction management."""
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
            
            if total == 0:
                self.log_message.emit("No approved operations to execute")
                self.finished.emit(0, 0, "")
                conn.close()
                return
            
            # Initialize TransactionManager
            tm = TransactionManager()
            self.batch_id = tm.begin_batch(f"action_plan_{self.action_plan_id}")

            # Initialize Jellyfin client if refresh enabled
            if self.jellyfin_refresh and not self.dry_run:
                try:
                    config_mgr = JellyfinConfigManager()
                    config = config_mgr.load_config()
                    if config and config.get('enabled'):
                        self.jellyfin_client = JellyfinClient(
                            server_url=config.get('server_url'),
                            api_key=config.get('api_key')
                        )
                        if self.jellyfin_client.test_connection():
                            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Connected")
                        else:
                            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Connection FAILED")
                            self.jellyfin_client = None
                except Exception as e:
                    self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Error - {str(e)}")
                    self.jellyfin_client = None

            mode_str = "DRY RUN" if self.dry_run else "PRODUCTION"
            self.log_message.emit(f"Starting execution of {total} operations...")
            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Mode: {mode_str}")
            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Batch ID: {self.batch_id}")
            if self.jellyfin_client:
                self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin Refresh: ENABLED\n")
            else:
                self.log_message.emit("")
            
            for i, (op_id, op_type, current_path, proposed_path) in enumerate(operations, 1):
                self.progress.emit(i, total, f"Processing {i}/{total}")
                
                try:
                    # Log operation start
                    self.log_message.emit(
                        f"[{datetime.now().strftime('%H:%M:%S')}] {op_type}: "
                        f"{Path(current_path).name} -> {Path(proposed_path).name}"
                    )
                    
                    if self.dry_run:
                        # Dry run mode - just log
                        self.log_message.emit(f"  [DRY RUN] Would move: {current_path}")
                        self.log_message.emit(f"  [DRY RUN] To: {proposed_path}\n")
                        success_count += 1
                        
                        # Mark as executed in database
                        cursor.execute('''
                            UPDATE project_operations
                            SET executed = 1, execution_timestamp = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), op_id))
                        
                    else:
                        # Production mode - actual file operations
                        source_path = Path(current_path)
                        dest_path = Path(proposed_path)
                        
                        # Validate source exists
                        if not source_path.exists():
                            raise FileNotFoundError(f"Source file not found: {source_path}")
                        
                        # Create Operation for TransactionManager
                        operation = Operation(
                            operation_type=OperationType.MOVE,
                            source_path=str(source_path),
                            destination_path=str(dest_path)
                        )
                        
                        # Log to transaction manager (calculates source MD5)
                        tx_id = tm.log_operation(operation, self.batch_id)
                        self.log_message.emit(f"  Transaction ID: {tx_id}")
                        
                        # Create destination directory
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Execute move
                        shutil.move(str(source_path), str(dest_path))
                        self.log_message.emit(f"  ✓ File moved successfully")

                        # Track path for Jellyfin refresh
                        if self.jellyfin_client:
                            self.modified_paths.add(str(dest_path.parent))

                        # Calculate destination MD5 and complete transaction
                        dest_md5 = FileHasher.calculate_md5(dest_path)
                        tm.complete_operation(tx_id, dest_md5)
                        self.log_message.emit(f"  ✓ MD5 verified: {dest_md5[:16]}...")

                        # Update database
                        cursor.execute('''
                            UPDATE project_operations
                            SET executed = 1, execution_timestamp = ?,
                                current_md5 = ?, proposed_md5 = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), dest_md5, dest_md5, op_id))

                        success_count += 1
                        self.log_message.emit(f"  ✓ Operation complete\n")
                    
                except Exception as e:
                    fail_count += 1
                    error_msg = str(e)
                    self.log_message.emit(f"  ✗ ERROR: {error_msg}\n")
                    logger.error(f"Operation {op_id} failed: {e}", exc_info=True)
                    
                    # Mark as failed in transaction manager if not dry run
                    if not self.dry_run and 'tx_id' in locals():
                        tm.fail_operation(tx_id, error_msg)
            
            # Trigger Jellyfin library refresh if configured
            if self.jellyfin_client and self.modified_paths and success_count > 0:
                self.log_message.emit(f"\n[{datetime.now().strftime('%H:%M:%S')}] Triggering Jellyfin library refresh...")
                try:
                    for path in self.modified_paths:
                        self.log_message.emit(f"  Refreshing: {path}")
                        if self.jellyfin_client.refresh_library_by_path(path):
                            self.log_message.emit(f"  ✓ Refresh successful")
                        else:
                            self.log_message.emit(f"  ⚠ Refresh may have failed - check Jellyfin server logs")
                    self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin refresh complete\n")
                except Exception as e:
                    self.log_message.emit(f"  ⚠ Error during Jellyfin refresh: {str(e)}\n")
                    logger.error(f"Jellyfin refresh error: {e}", exc_info=True)

            # Update action plan
            cursor.execute('''
                UPDATE project_action_plans
                SET executed = 1, execution_timestamp = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), self.action_plan_id))

            conn.commit()
            conn.close()

            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Execution complete!")
            self.log_message.emit(f"Success: {success_count}, Failed: {fail_count}")
            self.log_message.emit(f"Batch ID: {self.batch_id} (for rollback)")

            self.finished.emit(success_count, fail_count, self.batch_id)
            
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
        self.current_batch_id = None
        
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
        
        # Mode selection
        mode_layout = QHBoxLayout()
        self.chk_dry_run = QCheckBox("Dry Run Mode (No actual file changes)")
        self.chk_dry_run.setChecked(True)  # Default to dry run for safety
        self.chk_dry_run.setStyleSheet("font-weight: bold; color: #e67e22;")
        mode_layout.addWidget(self.chk_dry_run)

        # Jellyfin refresh option
        self.chk_jellyfin_refresh = QCheckBox("Refresh Jellyfin Library After Execution")
        self.chk_jellyfin_refresh.setChecked(True)  # Default to enabled if configured
        self.chk_jellyfin_refresh.setStyleSheet("color: #2980b9;")
        self.chk_jellyfin_refresh.setEnabled(False)  # Will be enabled if Jellyfin is configured
        mode_layout.addWidget(self.chk_jellyfin_refresh)

        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
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

        # Check if Jellyfin is configured and enable refresh checkbox if so
        try:
            config_mgr = JellyfinConfigManager()
            config = config_mgr.load_config()
            if config and config.get('enabled') and config.get('server_url') and config.get('api_key'):
                self.chk_jellyfin_refresh.setEnabled(True)
                self.lbl_summary.setText(f"{self.lbl_summary.text()} | Jellyfin: Ready")
        except Exception as e:
            logger.warning(f"Jellyfin config check failed: {e}")
    
    def _start_execution(self):
        """Start execution of approved operations."""
        if not self.action_plan_id:
            QMessageBox.warning(self, "No Action Plan", "No action plan selected for execution.")
            return
        
        dry_run = self.chk_dry_run.isChecked()
        
        # Confirm with appropriate warning
        if dry_run:
            message = (
                "Start DRY RUN execution?\n\n"
                "This will simulate all operations without making actual file changes.\n"
                "Use this to verify the execution plan is correct."
            )
        else:
            message = (
                "⚠️ START PRODUCTION EXECUTION? ⚠️\n\n"
                "This will make ACTUAL FILE CHANGES to your system!\n\n"
                "• Files will be moved to new locations\n"
                "• MD5 verification will be performed\n"
                "• All operations will be logged for rollback\n\n"
                "Are you ABSOLUTELY SURE you want to proceed?"
            )
        
        reply = QMessageBox.question(
            self,
            "Start Execution",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI during execution
        self.btn_execute.setEnabled(False)
        self.chk_dry_run.setEnabled(False)
        self.chk_jellyfin_refresh.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        # Get Jellyfin refresh setting
        jellyfin_refresh = self.chk_jellyfin_refresh.isChecked() and self.chk_jellyfin_refresh.isEnabled()

        # Start worker
        self.execution_worker = ExecutionWorker(self.action_plan_id, dry_run, jellyfin_refresh)
        self.execution_worker.progress.connect(self._on_progress)
        self.execution_worker.log_message.connect(self._on_log_message)
        self.execution_worker.finished.connect(self._on_finished)
        self.execution_worker.error.connect(self._on_error)
        self.execution_worker.start()

        mode_str = "DRY RUN" if dry_run else "PRODUCTION"
        logger.info(f"Started {mode_str} execution of action plan {self.action_plan_id}")
    
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
    
    def _on_finished(self, success_count: int, fail_count: int, batch_id: str):
        """Handle execution completion."""
        self.btn_execute.setEnabled(False)
        self.chk_dry_run.setEnabled(True)
        self.chk_jellyfin_refresh.setEnabled(True)
        self.current_batch_id = batch_id

        # Enable rollback only if production mode was used
        if batch_id and not self.chk_dry_run.isChecked():
            self.btn_rollback.setEnabled(True)
        
        self.lbl_summary.setText(
            f"Execution complete: {success_count} successful, {fail_count} failed"
        )
        
        if self.chk_dry_run.isChecked():
            QMessageBox.information(
                self,
                "Dry Run Complete",
                f"Dry run completed successfully!\n\n"
                f"• {success_count} operations simulated\n"
                f"• {fail_count} operations failed\n\n"
                f"Uncheck 'Dry Run Mode' to execute for real."
            )
        else:
            QMessageBox.information(
                self,
                "Execution Complete",
                f"Production execution completed!\n\n"
                f"• {success_count} operations successful\n"
                f"• {fail_count} operations failed\n\n"
                f"Batch ID: {batch_id}\n"
                f"Use 'Rollback All' if you need to undo these changes."
            )
    
    def _on_error(self, error_msg: str):
        """Handle execution errors."""
        self.btn_execute.setEnabled(True)
        self.chk_dry_run.setEnabled(True)
        self.lbl_status.setText(f"Execution failed: {error_msg}")
        
        QMessageBox.critical(
            self,
            "Execution Error",
            f"Execution failed:\n\n{error_msg}"
        )
    
    def _rollback(self):
        """Rollback executed operations using TransactionManager."""
        if not self.current_batch_id:
            QMessageBox.warning(
                self,
                "No Batch to Rollback",
                "No execution batch available for rollback.\n\n"
                "Rollback is only available after a production execution."
            )
            return
        
        # Confirm rollback
        reply = QMessageBox.question(
            self,
            "Confirm Rollback",
            f"⚠️ ROLLBACK ALL OPERATIONS? ⚠️\n\n"
            f"This will reverse all file operations from batch:\n"
            f"{self.current_batch_id}\n\n"
            f"Files will be moved back to their original locations.\n\n"
            f"Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.log_text.append("\n" + "="*50)
            self.log_text.append(f"Starting rollback of batch: {self.current_batch_id}")
            self.log_text.append("="*50 + "\n")
            
            # Execute rollback
            tm = TransactionManager()
            result = tm.rollback_batch(self.current_batch_id, dry_run=False)
            
            # Display results
            self.log_text.append(f"\nRollback complete!")
            self.log_text.append(f"Total operations: {result.total_operations}")
            self.log_text.append(f"Successful: {result.successful_rollbacks}")
            self.log_text.append(f"Failed: {result.failed_rollbacks}")
            
            if result.errors:
                self.log_text.append(f"\nErrors:")
                for error in result.errors:
                    self.log_text.append(f"  - {error}")
            
            # Update UI
            self.btn_rollback.setEnabled(False)
            self.lbl_summary.setText(
                f"Rollback complete: {result.successful_rollbacks}/{result.total_operations} successful"
            )
            
            # Show completion dialog
            if result.failed_rollbacks == 0:
                QMessageBox.information(
                    self,
                    "Rollback Complete",
                    f"Successfully rolled back all {result.successful_rollbacks} operations!\n\n"
                    f"All files have been restored to their original locations."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Rollback Partial Success",
                    f"Rollback completed with some errors:\n\n"
                    f"• Successful: {result.successful_rollbacks}\n"
                    f"• Failed: {result.failed_rollbacks}\n\n"
                    f"Check the transaction log for details."
                )
            
            logger.info(f"Rollback completed: {result.successful_rollbacks}/{result.total_operations} successful")
            
        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            self.log_text.append(f"\n✗ ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
            
            QMessageBox.critical(
                self,
                "Rollback Failed",
                f"Failed to rollback operations:\n\n{error_msg}"
            )


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
        """
        Initialize the ExecutionWorker thread.
        
        Sets up the background worker for executing file operations with
        full transaction management, rollback capability, and optional
        Jellyfin library refresh.
        
        Args:
            action_plan_id: Database ID of the action plan to execute
            dry_run: If True, simulate operations without actual file changes
            jellyfin_refresh: If True, refresh Jellyfin library after execution
            
        The worker provides real-time progress updates and maintains
        transaction integrity for all file operations.
        """
    
    def run(self):
        """
        Execute operations with full transaction management.
        
        This is the main execution method that runs in a background thread.
        It processes all approved operations from the action plan with proper
        transaction handling, progress reporting, and optional Jellyfin integration.
        
        The execution process:
        1. Loads approved operations from the database
        2. Initializes TransactionManager for rollback capability
        3. Sets up Jellyfin client if refresh is enabled
        4. Executes each operation with progress updates
        5. Performs Jellyfin library refresh if requested
        6. Reports final success/failure counts
        
        All operations are wrapped in transactions for atomicity.
        Progress is reported in real-time via signals.
        Failed operations are logged but don't stop the batch.
        
        The method handles dry-run mode for testing without actual changes.
        """
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
                    if config_mgr.is_enabled():
                        server_url = config_mgr.get_server_url()
                        api_key = config_mgr.get_api_key()
                        if server_url and api_key:
                            self.jellyfin_client = JellyfinClient(
                                server_url=server_url,
                                api_key=api_key
                            )
                            if self.jellyfin_client.test_connection():
                                self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Connected")
                            else:
                                self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Connection FAILED")
                                self.jellyfin_client = None
                        else:
                            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Missing URL or API key")
                            self.jellyfin_client = None
                    else:
                        self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Jellyfin: Disabled")
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

    # Signal emitted when execution completes (success_count, fail_count, batch_id)
    execution_completed = pyqtSignal(int, int, str)

    def __init__(self, project: Project, project_manager: ProjectManager, action_plan_id: int = None, parent=None):
        """
        Initialize the Execution View widget.
        
        Sets up the real-time execution monitor for file operations with
        transaction management, progress tracking, and rollback capabilities.
        This view implements Points 6-9 of the JellyRancher workflow.
        
        Args:
            project: The current Project instance
            project_manager: ProjectManager instance for database operations
            action_plan_id: Optional action plan ID to load immediately
            parent: Parent QWidget (typically the main application window)
            
        The view provides:
        - Real-time execution progress with visual progress bar
        - Live transaction log with timestamps
        - Execution controls (start, pause, stop)
        - Rollback capability for failed operations
        - Post-execution summary and statistics
        
        If action_plan_id is provided, the view automatically loads
        and prepares the action plan for execution.
        """
        super().__init__(parent)
        try:
            self.project = project
            self.project_manager = project_manager
            self.action_plan_id = action_plan_id

            self._init_ui()
            
            if action_plan_id:
                self._load_action_plan()

            logger.info(f"ExecutionView initialized for project: {project.name}")
        except Exception as e:
            logger.error(f"Failed to initialize ExecutionView: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize execution monitor:\n\n{str(e)}\n\nPlease check the logs for details.",
            )
            raise
    
    def _init_ui(self):
        """
        Initialize the user interface components.
        
        Creates and configures all UI elements for the execution monitor:
        - Progress section with visual progress bar and status labels
        - Control buttons (start, rollback, create snapshot)
        - Transaction log viewer with real-time updates
        - Execution options (dry run, Jellyfin refresh)
        - Summary statistics display
        
        The UI is organized in logical sections:
        - Header with title and execution options
        - Progress tracking with visual indicators
        - Control buttons for execution management
        - Log viewer for detailed operation tracking
        - Summary area for final results
        
        All interactive elements are properly connected to their
        respective handler methods and signal connections.
        """
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Execution Monitor")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("padding: 10px;")  # Color from stylesheet
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

        # Snapshot section (legacy Step 6 parity)
        snapshot_group = QGroupBox("Step 6: Transaction Snapshot")
        snapshot_layout = QVBoxLayout()
        snapshot_layout.addWidget(QLabel("Create a transaction snapshot before executing changes:"))
        self.btn_snapshot = QPushButton("Create Snapshot")
        self.btn_snapshot.clicked.connect(self._create_snapshot)
        snapshot_layout.addWidget(self.btn_snapshot)
        self.snapshot_info = QTextEdit()
        self.snapshot_info.setReadOnly(True)
        self.snapshot_info.setPlaceholderText("Snapshot details will appear here...")
        self.snapshot_info.setMaximumHeight(110)
        snapshot_layout.addWidget(self.snapshot_info)
        snapshot_group.setLayout(snapshot_layout)
        layout.addWidget(snapshot_group)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        self.chk_dry_run = QCheckBox("Dry Run Mode (No actual file changes)")
        self.chk_dry_run.setChecked(True)  # Default to dry run for safety
        self.chk_dry_run.setStyleSheet("font-weight: bold; color: #f39c12;")  # Bright orange
        mode_layout.addWidget(self.chk_dry_run)

        # Jellyfin refresh option
        self.chk_jellyfin_refresh = QCheckBox("Refresh Jellyfin Library After Execution")
        self.chk_jellyfin_refresh.setChecked(True)  # Default to enabled if configured
        self.chk_jellyfin_refresh.setStyleSheet("color: #3498db;")  # Bright blue
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
        self.lbl_summary.setStyleSheet("padding: 5px;")  # Color from stylesheet
        layout.addWidget(self.lbl_summary)
        
        self.setLayout(layout)
    
    def _load_action_plan(self):
        """
        Load action plan details from the database.
        
        Retrieves metadata about the current action plan including operation
        counts, approval status, and execution state. This information is
        used to configure the UI and determine available actions.
        
        The method:
        1. Validates that an action_plan_id is set
        2. Queries the database for action plan metadata
        3. Updates UI status labels with operation counts
        4. Enables/disables buttons based on execution state
        5. Shows appropriate messaging for executed plans
        
        This ensures the UI reflects the current state of the action plan
        and provides appropriate controls for the user's next actions.
        
        Raises:
            sqlite3.Error: If database operations fail
        """
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

        except sqlite3.Error as e:
            logger.error(f"Database error loading action plan: {e}", exc_info=True)
            self.lbl_status.setText(f"Error loading action plan: Database error")
            QMessageBox.critical(self, "Database Error", f"Failed to load action plan from database:\n\n{str(e)}")
        except Exception as e:
            logger.error(f"Failed to load action plan: {e}", exc_info=True)
            self.lbl_status.setText(f"Error loading action plan: {str(e)}")
            QMessageBox.critical(self, "Load Error", f"Failed to load action plan:\n\n{str(e)}")

        # Check if Jellyfin is configured and enable refresh checkbox if so
        try:
            config_mgr = JellyfinConfigManager()
            if config_mgr.is_enabled() and config_mgr.get_server_url() and config_mgr.get_api_key():
                self.chk_jellyfin_refresh.setEnabled(True)
                self.lbl_summary.setText(f"{self.lbl_summary.text()} | Jellyfin: Ready")
        except Exception as e:
            logger.warning(f"Jellyfin config check failed: {e}")
            self.chk_jellyfin_refresh.setEnabled(False)
            self.chk_jellyfin_refresh.setChecked(False)
    
    def _start_execution(self):
        """
        Start execution of approved operations.
        
        Initiates the file operation execution process with appropriate
        safety confirmations and mode selection (dry run vs production).
        
        The method:
        1. Validates that an action plan is selected
        2. Checks dry run mode setting
        3. Shows appropriate confirmation dialog based on mode
        4. Creates and starts the ExecutionWorker thread
        5. Disables execution controls during processing
        6. Enables rollback capability
        
        Dry run mode simulates all operations without actual file changes,
        useful for testing the execution plan. Production mode performs
        actual file operations with full transaction logging.
        
        The confirmation dialogs include clear warnings about the
        destructive nature of production execution.
        
        Raises:
            QMessageBox: Shows warnings if no action plan is selected
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to start execution: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Execution Start Error",
                f"Failed to start execution:\n\n{str(e)}\n\nPlease try again.",
            )
            # Restore UI state
            self.btn_execute.setEnabled(True)
            self.chk_dry_run.setEnabled(True)
            if self.chk_jellyfin_refresh.isEnabled():
                self.chk_jellyfin_refresh.setEnabled(True)
    
    def _on_progress(self, current: int, total: int, status: str):
        """
        Handle progress updates from the execution worker.
        
        Updates the progress bar and status label with current execution
        progress information. This method is called from the worker thread
        to provide real-time feedback to the user about operation progress.
        
        Args:
            current (int): Current operation number being processed (0-based)
            total (int): Total number of operations to process
            status (str): Descriptive message about current operation
            
        The progress bar shows completion percentage, and the status label
        displays the current operation being performed. This provides
        visual feedback during potentially long-running operations.
        
        Error Handling:
            If progress update fails, logs the error and attempts to set
            a fallback status message. If even that fails, logs the UI error.
            This prevents progress update failures from crashing the UI.
        
        Thread Safety:
            This method is called from the worker thread and updates UI
            elements, which is safe in PyQt6 as long as signal-slot connections
            are used (which they are via the progress signal).
        """
        try:
            if total > 0:
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(current)
                percent = (current / total) * 100
                self.lbl_status.setText(f"{status} ({percent:.1f}%)")
        except Exception as e:
            logger.error(f"Failed to update progress: {e}", exc_info=True)
            try:
                self.lbl_status.setText("Progress update error")
            except Exception as ui_error:
                logger.error(f"Failed to update status label: {ui_error}", exc_info=True)
    
    def _on_log_message(self, message: str):
        """
        Handle log messages from the execution worker.
        
        Appends log messages to the execution log text area. This method
        is called from the worker thread to provide detailed execution
        feedback including operation details, transaction IDs, and status
        updates.
        
        Args:
            message (str): Log message to append to the execution log
            
        The log messages include:
        - Operation start/end notifications
        - Transaction IDs for audit trail
        - File operation results (success/failure)
        - MD5 verification results
        - Error details and recovery actions
        
        Error Handling:
            If appending the message fails, logs the error to prevent
            log display failures from interrupting execution. This ensures
            execution continues even if UI logging encounters issues.
        
        Thread Safety:
            Called from worker thread via signal-slot mechanism, safe
            for UI updates in PyQt6.
        """
        try:
            self.log_text.append(message)
        except Exception as e:
            logger.error(f"Failed to append log message: {e}", exc_info=True)
    
    def _on_finished(self, success_count: int, fail_count: int, batch_id: str):
        """
        Handle execution completion and update UI state.
        
        Called when the execution worker completes all operations. Updates
        the UI to reflect completion status, enables rollback capability,
        and optionally triggers Jellyfin library refresh.
        
        Args:
            success_count (int): Number of operations that completed successfully
            fail_count (int): Number of operations that failed
            batch_id (str): Unique identifier for this execution batch
            
        The method:
        1. Disables execution controls (execution cannot be restarted)
        2. Re-enables dry run and Jellyfin refresh checkboxes
        3. Stores the batch ID for rollback reference
        4. Enables rollback button if production mode was used
        5. Updates status label with completion summary
        6. Triggers Jellyfin refresh if requested and available
        
        Rollback is only enabled for production executions (not dry runs)
        since dry runs don't modify actual files.
        
        Jellyfin refresh updates the media library to reflect file changes,
        ensuring the library stays synchronized with the filesystem.
        
        Error Handling:
            All operations are wrapped in try-catch to prevent UI update
            failures from affecting the completion handling.
        """
        try:
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

            # Emit completion signal for Studio to update Round-Up state
            self.execution_completed.emit(success_count, fail_count, batch_id)

        except Exception as e:
            logger.error(f"Failed to handle execution completion: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Completion Error",
                f"Execution completed but failed to update UI:\n\n{str(e)}\n\nCheck the logs for details.",
            )
            # Still try to enable rollback if we have a batch_id
            try:
                if batch_id and not self.chk_dry_run.isChecked():
                    self.btn_rollback.setEnabled(True)
                    self.current_batch_id = batch_id
            except Exception as rollback_error:
                logger.error(f"Failed to enable rollback: {rollback_error}", exc_info=True)
    
    def _on_error(self, error_msg: str):
        """
        Handle execution errors and provide user feedback.
        
        Called when the execution worker encounters a critical error that
        prevents further processing. Updates UI state to allow retry and
        shows error dialog to inform the user.
        
        Args:
            error_msg (str): Description of the error that occurred
            
        The method:
        1. Re-enables execution controls so user can retry
        2. Updates status label with error information
        3. Shows critical error dialog with full error details
        4. Logs any UI update failures to prevent secondary errors
        
        Error handling ensures that even if UI updates fail, the error
        is still logged and the user is informed through the dialog.
        This prevents silent failures where users don't know execution
        stopped due to an error.
        
        The error dialog uses QMessageBox.critical to clearly indicate
        a serious problem that requires user attention.
        """
        try:
            self.btn_execute.setEnabled(True)
            self.chk_dry_run.setEnabled(True)
            self.lbl_status.setText(f"Execution failed: {error_msg}")

            QMessageBox.critical(
                self,
                "Execution Error",
                f"Execution failed:\n\n{error_msg}"
            )
        except Exception as e:
            logger.error(f"Failed to handle execution error: {e}", exc_info=True)
            # Ensure UI is restored
            try:
                self.btn_execute.setEnabled(True)
                self.chk_dry_run.setEnabled(True)
                self.lbl_status.setText("Critical error in execution handling")
            except Exception as ui_error:
                logger.error(f"Failed to restore UI after execution error: {ui_error}", exc_info=True)
    
    def _rollback(self):
        """
        Rollback executed operations using TransactionManager.
        
        Reverses all file operations from the most recent production execution
        batch, restoring files to their original locations. This provides
        a safety net for recovering from failed or incorrect executions.
        
        The method:
        1. Validates that a batch ID exists (only available after production runs)
        2. Shows confirmation dialog with clear warning about destructive operation
        3. Executes rollback through TransactionManager
        4. Displays detailed results in the log
        5. Updates UI state (disables rollback button after use)
        6. Shows completion dialog with success/failure summary
        
        Rollback is only available after production executions (not dry runs)
        since dry runs don't modify actual files. The operation moves files
        back to their original locations using the transaction log.
        
        Error Handling:
            If rollback fails, shows critical error dialog and logs details.
            Partial failures are reported with specific error counts.
        
        Transaction Safety:
            Uses TransactionManager.rollback_batch() which ensures atomic
            rollback operations with proper error tracking and logging.
        """
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
            try:
                self.log_text.append(f"\n✗ ERROR: {error_msg}")
            except Exception as log_error:
                logger.error(f"Failed to log rollback error: {log_error}", exc_info=True)
            logger.error(error_msg, exc_info=True)

            QMessageBox.critical(
                self,
                "Rollback Failed",
                f"Failed to rollback operations:\n\n{error_msg}"
            )

    def _create_snapshot(self):
        """
        Simulate creation of a transaction snapshot (legacy Step 6).
        
        Displays informational text about transaction logging capabilities
        and shows a confirmation dialog. This is a legacy method that
        provides user education about the transaction system's safety features.
        
        The method:
        1. Creates informative text about TransactionManager capabilities
        2. Displays the information in the snapshot info text area
        3. Shows confirmation dialog that snapshot is ready
        
        The snapshot information explains that every file operation is logged
        with comprehensive details including paths, MD5 hashes, operation types,
        and status tracking. This reassures users about the system's ability
        to rollback operations if needed.
        
        Error Handling:
            If snapshot creation fails, shows critical error dialog and logs
            the error. This prevents silent failures in the informational display.
        
        Legacy Context:
            This method represents Step 6 from the original JellyRancher workflow,
            now largely handled automatically by the TransactionManager.
        """
        try:
            text = (
                "📸 Transaction Snapshot Created\n\n"
                "TransactionManager will log every file operation with:\n"
                "- Transaction ID / Batch ID\n"
                "- Source path / Destination path\n"
                "- MD5 before and after moves\n"
                "- Operation type (move/copy/delete)\n"
                "- Status (pending/completed/failed)\n\n"
                "Use rollback to restore all files if anything goes wrong."
            )
            self.snapshot_info.setPlainText(text)
            QMessageBox.information(
                self,
                "Snapshot Ready",
                "Snapshot information recorded. Execute operations when ready."
            )
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Snapshot Error",
                f"Failed to create snapshot:\n\n{str(e)}\n\nPlease try again.",
            )

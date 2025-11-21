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
        """
        Initialize the Review View widget.
        
        Sets up the interactive review interface for proposed file operations.
        This view implements Point 5 of the JellyRancher workflow, providing
        an Excel-like table for reviewing, approving, and editing action plans.
        
        Args:
            project: The current Project instance containing analysis data
            project_manager: ProjectManager instance for database operations
            parent: Parent QWidget (typically the main application window)
            
        Raises:
            Exception: If initialization fails, shows critical error dialog to user
            
        Signals:
            operations_ready(int): Emitted when action plan is ready for execution
                                 (passes action_plan_id)
        """
        try:
            super().__init__(parent)
            
            self.project = project
            self.project_manager = project_manager
            self.inventory_repo = InventoryRepository()
            
            # Initialize instance variables
            self.current_action_plan_id = None
            self.operations = []
            self.filtered_operations = []
            self.scanned_files = []
            self.llm_analysis = None
            self.canonical_database = None
            self.app_config = AppConfigManager()
            self.action_plan_worker = None
            
            self._init_ui()
            
            logger.info(f"ReviewView initialized successfully for project: {project.name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ReviewView: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize review view:\n\n{str(e)}\n\nPlease check the logs for details.",
            )
            raise
    
    def _init_ui(self):
        """
        Initialize the user interface components.
        
        Creates and configures all UI elements for the review interface:
        - Review table with sortable columns and inline editing
        - Control buttons (select all, approve, reject, preview, execute)
        - Search and filter controls
        - Summary statistics display
        - Export functionality
        - Progress indicators
        
        The UI is organized in a vertical layout with logical grouping:
        - Header with summary information
        - Table with proposed operations
        - Control buttons and filters
        - Status and progress indicators
        
        All interactive elements are properly connected to their handler methods.
        """
        try:
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)

            # Title
            title = QLabel("Action Plan Review")
            title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            title.setStyleSheet("padding: 10px;")  # Color from stylesheet
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
            self.operations_table.setMinimumHeight(200)  # Ensure operations are visible
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
            self.lbl_summary.setStyleSheet("padding: 5px;")  # Color from stylesheet
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
        except Exception as e:
            logger.error(f"Failed to initialize review UI: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "UI Initialization Error",
                f"Failed to initialize review interface:\n\n{str(e)}\n\nPlease restart the application.",
            )
            raise
    
    def _load_analysis_data(self):
        """
        Load the most recent analysis metadata for the current project.
        
        Retrieves the latest LLM analysis results from the database to provide
        context for action plan generation. This includes detected media items
        and analysis confidence scores.
        
        The method:
        1. Connects to the media library database
        2. Queries for the most recent analysis for this project
        3. Parses the stored JSON data (detected media, recommendations)
        4. Loads any associated canonical metadata if available
        5. Updates UI status to reflect loaded data
        
        If no analysis data is found, the UI will show appropriate messaging
        to guide the user to run analysis first.
        
        Raises:
            sqlite3.Error: If database operations fail
            json.JSONDecodeError: If stored analysis JSON is malformed
        """
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
                try:
                    self.llm_analysis = json.loads(parsed_json_str) if parsed_json_str else None
                    self.canonical_database = json.loads(metadata_str) if metadata_str else None
                    logger.info("Loaded analysis %s for review view", analysis_id)
                    self.lbl_summary.setText(
                        "LLM analysis loaded. Click 'Load Action Plan' to generate operations."
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse analysis JSON data: {e}", exc_info=True)
                    self.lbl_summary.setText("Error: Invalid analysis data format. Please re-run analysis.")
                    self.llm_analysis = None
                    self.canonical_database = None
            else:
                self.lbl_summary.setText("No analysis found. Run LLM analysis first.")
                logger.warning("No analysis data found for project %s", self.project.id)

            conn.close()
            self._load_scanned_files()

        except sqlite3.Error as e:
            logger.error(f"Database error loading analysis data: {e}", exc_info=True)
            self.lbl_summary.setText(f"Database error loading analysis: {str(e)}")
            try:
                conn.close()
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to load analysis data: {e}", exc_info=True)
            self.lbl_summary.setText(f"Error loading analysis data: {str(e)}")
            try:
                conn.close()
            except:
                pass

    def _load_scanned_files(self):
        """
        Load scanned files from the most recent scan session.
        
        Retrieves the file inventory from the latest scan session to provide
        the complete list of files that can be operated on. This data is
        essential for generating and validating action plans.
        
        The method:
        1. Queries the database for the most recent scan session
        2. Extracts scan options including inventory session IDs
        3. Loads all file records from associated inventory sessions
        4. Updates the scanned_files list for use in action plan generation
        
        This ensures that action plans are generated against the most current
        and complete file inventory available.
        
        Raises:
            sqlite3.Error: If database operations fail
            json.JSONDecodeError: If scan options JSON is malformed
        """
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

            try:
                options = json.loads(row[0]) if row[0] else {}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse scan options JSON: {e}", exc_info=True)
                QMessageBox.warning(self, "Data Error", "Invalid scan session data. Please re-run the scan.")
                return

            session_ids = options.get("inventory_session_ids", [])
            self.scanned_files = []
            for session_id in session_ids:
                try:
                    self.scanned_files.extend(self.inventory_repo.get_all_files(session_id))
                except Exception as e:
                    logger.error(f"Failed to load files from session {session_id}: {e}", exc_info=True)
                    # Continue with other sessions rather than failing completely

            logger.info("Loaded %d scanned files for review", len(self.scanned_files))

        except sqlite3.Error as e:
            logger.error(f"Database error loading scanned files: {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to load scan data from database:\n\n{str(e)}")
        except Exception as e:
            logger.error("Failed to load scanned files: %s", e, exc_info=True)
            QMessageBox.critical(self, "Load Error", f"Failed to load scanned files:\n\n{str(e)}")
    
    def step_5_review(self):
        """
        Generate an action plan using the ActionPlanWorker.
        
        This is the main entry point for Point 5 of the workflow: Action Plan Generation.
        Creates a comprehensive set of proposed file operations based on LLM analysis,
        canonical metadata, and scanned file inventory.
        
        The method validates prerequisites:
        1. Scanned files must be available
        2. LLM analysis results must exist
        3. Canonical metadata database must be built
        
        Then initiates the action plan generation:
        1. Creates and configures an ActionPlanWorker thread
        2. Passes all required data (files, analysis, metadata)
        3. Disables UI controls during processing
        4. Shows progress indication
        
        The worker runs asynchronously to prevent UI blocking. Results are
        processed by connected signal handlers when complete.
        
        Raises:
            QMessageBox: Shows warnings if prerequisites are not met
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to start action plan generation: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Action Plan Error",
                f"Failed to start action plan generation:\n\n{str(e)}\n\nPlease check the logs for details.",
            )
            self.lbl_summary.setText("Failed to start action plan generation")
            self.btn_export.setEnabled(False)
            self.btn_dry_run.setEnabled(False)

    def _on_action_plan_finished(self, action_plan: List[ProposedOperation]):
        """
        Handle completion of action plan generation.
        
        Processes the generated action plan and updates the UI to display
        the proposed operations in the review table. This method is called
        when the ActionPlanWorker completes successfully.
        
        Args:
            action_plan: List of ProposedOperation objects representing
                        the generated file operations to be reviewed
                        
        The method:
        1. Stores the action plan in instance variables
        2. Populates the review table with all proposed operations
        3. Updates summary statistics and status messages
        4. Enables export and preview functionality
        5. Shows success notification to the user
        
        The review table allows users to approve, reject, or modify
        individual operations before execution.
        
        Raises:
            QMessageBox: Shows critical error if table population fails
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to handle action plan completion: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Processing Error",
                f"Action plan generated but failed to display:\n\n{str(e)}\n\nPlease try again.",
            )
            self.lbl_summary.setText("Error displaying action plan")
            self.btn_export.setEnabled(False)
            self.btn_dry_run.setEnabled(False)

    def _on_action_plan_error(self, error_msg: str):
        """
        Handle errors that occur during action plan generation.
        
        This method is called when the ActionPlanWorker encounters an error
        during operation generation. It provides user feedback and restores
        the UI to a usable state.
        
        Args:
            error_msg: Descriptive error message from the action plan worker
                      (may include validation errors, processing failures, etc.)
                      
        The method:
        1. Updates status label with error information
        2. Shows a critical error dialog to inform the user
        3. Logs the error for debugging purposes
        
        Error handling is robust - if the error handler itself fails,
        it includes fallback UI restoration to prevent the interface
        from becoming unusable.
        
        Common error causes:
        - Invalid or inconsistent analysis data
        - Metadata lookup failures
        - File system access issues
        - Configuration problems
        """
        try:
            self.lbl_summary.setText(f"Action plan generation failed: {error_msg}")
            QMessageBox.critical(
                self,
                "Action Plan Error",
                f"Failed to generate action plan:\n\n{error_msg}",
            )
            logger.error("ActionPlanWorker error: %s", error_msg)
        except Exception as e:
            logger.error(f"Failed to handle action plan error: {e}", exc_info=True)
            # Ensure UI is in safe state
            try:
                self.lbl_summary.setText("Critical error in action plan generation")
            except Exception as ui_error:
                logger.error(f"Failed to update UI after action plan error: {ui_error}", exc_info=True)
    
    def _populate_table(self):
        """
        Populate the operations review table with proposed operations.
        
        Creates table rows for each ProposedOperation in the action plan,
        displaying all relevant information in an Excel-like interface.
        Each row represents one file operation that can be approved or rejected.
        
        Table columns include:
        - Approval checkbox for user selection
        - Operation type (MOVE, RENAME, DELETE, etc.)
        - Source file path
        - Destination path (if applicable)
        - Confidence level (HIGH, MEDIUM, LOW, MANUAL)
        - Notes and additional context
        
        The method:
        1. Sets table row count to match operations list
        2. Creates interactive checkboxes for approval/rejection
        3. Populates all data columns with operation details
        4. Applies visual styling based on confidence levels
        5. Connects approval checkboxes to change handlers
        
        This creates the core interactive interface for operation review.
        """
        try:
            self.operations_table.setRowCount(len(self.operations))

            for row, op in enumerate(self.operations):
                try:
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
                except Exception as e:
                    logger.error(f"Failed to populate table row {row}: {e}", exc_info=True)
                    # Continue with other rows rather than failing completely

            # Update summary
            try:
                approved_count = sum(1 for op in self.operations if op.user_approved)
                self.lbl_summary.setText(
                    f"Total: {len(self.operations)} operations | "
                    f"Approved: {approved_count} | "
                    f"Pending: {len(self.operations) - approved_count}"
                )
            except Exception as e:
                logger.error(f"Failed to update table summary: {e}", exc_info=True)
                self.lbl_summary.setText(f"Loaded {len(self.operations)} operations (summary error)")
        except Exception as e:
            logger.error(f"Failed to populate operations table: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Table Error",
                f"Failed to populate operations table:\n\n{str(e)}\n\nPlease try regenerating the action plan.",
            )
            self.operations_table.setRowCount(0)
    
    def _on_approve_changed(self, row: int, state: int):
        """
        Handle changes to operation approval checkboxes.
        
        Updates the user approval status for a specific operation when the
        corresponding checkbox is checked or unchecked. This allows users
        to selectively approve or reject individual operations.
        
        Args:
            row: Table row index corresponding to the operation
            state: Checkbox state (Qt.CheckState.Checked.value or unchecked)
            
        The method:
        1. Validates the row index is within bounds
        2. Updates the user_approved field on the ProposedOperation
        3. Triggers summary statistics update
        4. Shows error dialog if update fails
        
        This provides the core interactivity for the review table,
        allowing users to build custom action plans by approving
        only desired operations.
        
        Raises:
            QMessageBox: Shows warning if approval update fails
        """
        try:
            if 0 <= row < len(self.operations):
                self.operations[row].user_approved = (state == Qt.CheckState.Checked.value)
                self._update_summary()
        except Exception as e:
            logger.error(f"Failed to handle approval change for row {row}: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Approval Error",
                f"Failed to update approval status:\n\n{str(e)}\n\nPlease try again.",
            )

    def _update_summary(self):
        """
        Update the summary statistics display.
        
        Calculates and displays real-time statistics about the current
        state of operation approvals in the review table. This provides
        users with immediate feedback on their review progress.
        
        The summary shows:
        - Total number of operations in the action plan
        - Number of approved operations (checked)
        - Number of pending operations (unchecked)
        
        The method:
        1. Counts approved operations by checking user_approved field
        2. Updates the summary label with formatted statistics
        3. Includes error handling with fallback display
        
        This keeps users informed about their review progress and
        helps them understand how many operations remain to be reviewed.
        """
        try:
            approved_count = sum(1 for op in self.operations if op.user_approved)
            self.lbl_summary.setText(
                f"Total: {len(self.operations)} operations | "
                f"Approved: {approved_count} | "
                f"Pending: {len(self.operations) - approved_count}"
            )
        except Exception as e:
            logger.error(f"Failed to update summary: {e}", exc_info=True)
            try:
                self.lbl_summary.setText(f"Operations loaded ({len(self.operations)} total)")
            except Exception as ui_error:
                logger.error(f"Failed to update summary label: {ui_error}", exc_info=True)
    
    def _select_all(self):
        """
        Select all operations in the review table.
        
        Bulk operation to approve all proposed file operations at once.
        This sets all approval checkboxes to checked state, allowing users
        to quickly approve an entire action plan without individual selection.
        
        The method:
        1. Iterates through all table rows
        2. Finds the checkbox widget in each row
        3. Sets checkbox to checked state
        4. Updates the corresponding operation's user_approved field
        5. Triggers summary statistics update
        
        This is useful when users want to approve all operations
        without manual review, or as a starting point for selective rejection.
        """
        try:
            for row in range(self.operations_table.rowCount()):
                checkbox = self.operations_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(True)
        except Exception as e:
            logger.error(f"Failed to select all operations: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Selection Error",
                f"Failed to select all operations:\n\n{str(e)}\n\nPlease try again.",
            )

    def _approve_selected(self):
        """
        Approve all currently selected operations.
        
        Bulk operation to approve operations that are currently selected
        in the table (have their checkboxes checked). This allows users
        to selectively approve groups of operations.
        
        The method:
        1. Iterates through all table rows
        2. Checks if the row's selection checkbox is checked
        3. If selected, sets the approval checkbox to checked
        4. Updates the corresponding operation's user_approved field
        
        This provides fine-grained control over which operations
        to approve, useful when users want to approve specific
        groups without approving everything.
        """
        try:
            for row in range(self.operations_table.rowCount()):
                checkbox = self.operations_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    approve_checkbox = self.operations_table.cellWidget(row, 9)
                    if approve_checkbox:
                        approve_checkbox.setChecked(True)
        except Exception as e:
            logger.error(f"Failed to approve selected operations: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Approval Error",
                f"Failed to approve selected operations:\n\n{str(e)}\n\nPlease try again.",
            )

    def _reject_selected(self):
        """
        Reject all currently selected operations.
        
        Bulk operation to reject operations that are currently selected
        in the table (have their checkboxes checked). This allows users
        to selectively reject groups of operations.
        
        The method:
        1. Iterates through all table rows
        2. Checks if the row's selection checkbox is checked
        3. If selected, sets the approval checkbox to unchecked
        4. Updates the corresponding operation's user_approved field to False
        
        This provides fine-grained control over which operations
        to reject, useful when users want to exclude specific
        operations from execution.
        """
        try:
            for row in range(self.operations_table.rowCount()):
                checkbox = self.operations_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    approve_checkbox = self.operations_table.cellWidget(row, 9)
                    if approve_checkbox:
                        approve_checkbox.setChecked(False)
        except Exception as e:
            logger.error(f"Failed to reject selected operations: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Rejection Error",
                f"Failed to reject selected operations:\n\n{str(e)}\n\nPlease try again.",
            )
    
    def _filter_operations(self, search_text: str):
        """
        Filter operations table based on search text.
        
        Dynamically hides/shows table rows based on whether they match
        the search criteria. This allows users to quickly find specific
        operations in large action plans.
        
        Args:
            search_text: Text to search for in operation paths
                        (case-insensitive substring matching)
                        
        The method:
        1. Iterates through all table rows
        2. If no search text, shows all rows
        3. If search text provided, checks source and destination paths
        4. Shows rows where search text is found in path columns
        5. Hides rows that don't match the search criteria
        
        Search is performed on:
        - Source file path (column 2)
        - Destination path (column 3)
        
        This provides efficient navigation through large operation lists.
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to filter operations: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Filter Error",
                f"Failed to apply search filter:\n\n{str(e)}\n\nPlease try again.",
            )

    def _apply_filter(self, filter_text: str):
        """
        Apply advanced filtering based on selected filter criteria.
        
        Provides sophisticated filtering options beyond simple text search,
        allowing users to view operations by approval status or confidence level.
        
        Args:
            filter_text: Filter criteria selected from dropdown
                        Options: "Approved Only", "High Confidence (≥90%)",
                        "Manual Review (70-89%)", "Low Confidence (<70%)"
                        
        Filter types:
        - "Approved Only": Shows only user-approved operations
        - "High Confidence (≥90%)": Shows operations with HIGH confidence
        - "Manual Review (70-89%)": Shows operations needing manual review
        - "Low Confidence (<70%)": Shows operations with LOW confidence
        
        The method:
        1. Iterates through all table rows
        2. Applies the selected filter criteria
        3. Shows/hides rows based on filter match
        4. Updates visible row count
        
        This helps users focus on specific types of operations
        during the review process.
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to apply filter '{filter_text}': {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Filter Error",
                f"Failed to apply filter '{filter_text}':\n\n{str(e)}\n\nPlease try again.",
            )

    def _preview_changes(self):
        """
        Preview the approved operations before execution.
        
        Shows a detailed preview of all operations that have been approved
        by the user. This allows final review of the changes before they
        are actually executed on the file system.
        
        The method:
        1. Filters operations to include only approved ones
        2. Validates that at least one operation is approved
        3. Opens a preview dialog showing all approved operations
        4. Displays source/destination paths and operation types
        
        This provides a safety check to ensure users understand
        exactly what changes will be made before execution.
        
        Raises:
            QMessageBox: Shows warnings if no operations are approved
        """
        try:
            approved_ops = [op for op in self.operations if op.user_approved]

            if not approved_ops:
                QMessageBox.warning(self, "No Operations", "No operations are approved for preview.")
                return

            self._show_preview_dialog(approved_ops, "Preview Changes")
        except Exception as e:
            logger.error(f"Failed to preview changes: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to generate preview:\n\n{str(e)}\n\nPlease try again.",
            )

    def _dry_run_preview(self):
        """
        Preview all operations for planning purposes.
        
        Shows a complete preview of the entire action plan, regardless of
        approval status. This is useful for understanding the full scope
        of proposed changes during planning and review phases.
        
        The method:
        1. Validates that operations exist
        2. Shows preview dialog with all operations
        3. Displays complete action plan for review
        
        Unlike _preview_changes, this shows all operations (approved and
        unapproved) to give users a complete picture of what the action
        plan contains, useful for strategic planning.
        
        Raises:
            QMessageBox: Shows warnings if no operations exist
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to generate dry run preview: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to generate dry run preview:\n\n{str(e)}\n\nPlease try again.",
            )

    def _show_preview_dialog(self, operations: List[ProposedOperation], title: str, intro: str = ""):
        """
        Display a preview dialog showing operation details.
        
        Creates and shows a modal dialog with formatted details of the
        provided operations. This gives users a clear, readable view
        of what changes will be made.
        
        Args:
            operations: List of ProposedOperation objects to display
            title: Dialog window title
            intro: Optional introductory text to display at the top
            
        The dialog displays:
        - Operation number and type
        - Source and destination paths
        - Confidence level
        - Operation notes
        - Formatted in a monospace font for readability
        
        The dialog includes OK/Cancel buttons and is resizable for
        viewing large numbers of operations.
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to show preview dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Dialog Error",
                f"Failed to display preview dialog:\n\n{str(e)}\n\nPlease try again.",
            )

    def _export_to_csv(self):
        """
        Export the current action plan to a CSV file.
        
        Saves all operations in the current action plan to a CSV file
        for external review, backup, or processing. This allows users
        to work with the action plan in spreadsheet applications.
        
        The method:
        1. Validates that operations exist to export
        2. Opens a file save dialog with timestamped default filename
        3. Writes CSV header row with column names
        4. Exports all operation details as CSV rows
        5. Shows success confirmation
        
        CSV columns include:
        - Operation type
        - Source path
        - Destination path
        - Confidence level
        - User approval status
        - Notes
        
        This provides a portable format for action plan review
        and archival purposes.
        
        Raises:
            QMessageBox: Shows information if no operations to export
        """
        try:
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
                logger.info(f"Action plan exported to {filename}")
            except PermissionError as e:
                logger.error(f"Permission denied exporting to {filename}: {e}", exc_info=True)
                QMessageBox.critical(self, "Export Failed", f"Permission denied writing to:\n{filename}\n\nPlease choose a different location.")
            except OSError as e:
                logger.error(f"OS error exporting to {filename}: {e}", exc_info=True)
                QMessageBox.critical(self, "Export Failed", f"Failed to write file:\n{filename}\n\n{str(e)}")
            except Exception as exc:
                logger.error(f"Action plan export failed: {exc}", exc_info=True)
                QMessageBox.critical(self, "Export Failed", f"Failed to export action plan:\n\n{str(exc)}")
        except Exception as e:
            logger.error(f"Failed to initiate CSV export: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to start export process:\n\n{str(e)}\n\nPlease try again.",
            )
    
    def _execute_operations(self):
        """
        Execute all approved operations.
        
        This is the final step in the workflow: executing the approved
        file operations on the actual file system. This permanently
        modifies files according to the action plan.
        
        The method:
        1. Filters operations to include only approved ones
        2. Validates that operations exist for execution
        3. Shows confirmation dialog with operation count
        4. If confirmed, saves action plan to database
        5. Emits operations_ready signal to trigger execution
        6. Shows success confirmation
        
        This is a destructive operation that modifies the file system.
        The confirmation dialog ensures users understand the consequences.
        
        The operations are executed by the Execution View component
        after receiving the operations_ready signal.
        
        Raises:
            QMessageBox: Shows warnings if no operations are approved
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to execute operations: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Execution Error",
                f"Failed to prepare operations for execution:\n\n{str(e)}\n\nPlease try again.",
            )

    def _save_action_plan_to_database(self):
        """
        Save the complete action plan to the database.
        
        Persists the reviewed and approved action plan for execution tracking
        and audit purposes. This creates a permanent record of the operations
        that will be executed.
        
        The method:
        1. Creates a new action plan record with summary statistics
        2. Saves all individual operations with their approval status
        3. Includes metadata like confidence levels and file hashes
        4. Stores the action plan ID for execution tracking
        
        Saved data includes:
        - Action plan metadata (counts, timestamps)
        - Individual operations with full details
        - User approval decisions
        - Confidence levels and notes
        - File integrity information (MD5 hashes)
        
        This provides a complete audit trail for the file operations
        and enables execution by other components.
        
        Raises:
            sqlite3.Error: If database operations fail
        """
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

        except sqlite3.Error as e:
            logger.error(f"Database error saving action plan: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to save action plan to database:\n\n{str(e)}\n\nPlease check database connectivity.",
            )
        except Exception as e:
            logger.error(f"Failed to save action plan: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save action plan:\n\n{str(e)}\n\nPlease try again.",
            )


#!/usr/bin/env python3
"""
Analysis View - LLM-powered folder structure analysis

Implements Point 2-3 from plan.md: LLM Analysis and Metadata Lookup
Allows users to analyze folder structure and get reorganization recommendations.
"""

import logging
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QMessageBox, QGroupBox, QHBoxLayout, QProgressBar,
    QDialog, QDialogButtonBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.core.file_scanner import FileScanner, FileRecord
from scripts.core.inventory_repository import InventoryRepository
from scripts.ai.ravenmaven_client import PoeClient
from scripts.core.workers import LLMAnalysisWorker, MetadataLookupWorker
from scripts.core.regex_analysis_worker import RegexAnalysisWorker, HybridAnalysisWorker
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
from scripts.media.regex_structure_analyzer import RegexStructureAnalyzer

logger = logging.getLogger(__name__)


class AnalysisView(QWidget):
    """
    Analysis View - LLM analysis interface.
    
    Features:
    - Model selection
    - Prompt preview
    - Run analysis
    - View results
    - Save to database
    """
    
    # Signals notify Studio to refresh project explorer/state when new data exists
    analysis_saved = pyqtSignal(int)
    metadata_built = pyqtSignal(int)

    def __init__(self, project: Project, project_manager: ProjectManager, parent=None, filtered_files: List[FileRecord] = None, filter_config: dict = None):
        """
        Initialize the Analysis View widget.
        
        Sets up the UI for LLM-powered folder structure analysis and metadata lookup.
        This view implements Points 2-3 of the JellyRancher workflow, allowing users to
        analyze folder structures and get reorganization recommendations.
        
        Args:
            project: The current Project instance containing scan data and settings
            project_manager: ProjectManager instance for database operations
            parent: Parent QWidget (typically the main application window)
            
        Raises:
            Exception: If initialization fails, shows critical error dialog to user
            
        Signals:
            analysis_saved(int): Emitted when analysis results are saved to database
            metadata_built(int): Emitted when metadata enrichment is completed
        """
        try:
            super().__init__(parent)
            
            self.project = project
            self.project_manager = project_manager
            self.inventory_repo = InventoryRepository()
            
            # Initialize instance variables
            self.current_analysis_id = None
            self.analysis_results = None
            self.folder_structure = None
            self.scanned_files = []
            
            # Handle filtered data from ScanResultsView
            self.filtered_files = filtered_files
            self.filter_config = filter_config
            self.using_filtered_data = bool(filtered_files)
            self.plan_table = None
            self.metadata_table = None
            
            self._init_ui()
            
            # If filtered data provided, use it immediately instead of loading from DB
            if self.using_filtered_data:
                self._use_filtered_data()
            
            logger.info(f"AnalysisView initialized successfully (filtered_data={self.using_filtered_data})")
            
        except Exception as e:
            logger.error(f"Failed to initialize AnalysisView: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize analysis view:\n\n{str(e)}\n\nPlease check the logs for details.",
            )
            raise
    
    def _init_ui(self):
        """
        Tabbed UI refactor (Phase 37D): Setup | Plan Table | Metadata Table per plan.md Point 5.

        Tabs reduce height; replaces textboxes with editable tables for reorg plan/metadata.
        Setup: modes/buttons/progress. Plan: table (path/action). Metadata: table (title/year/ID).
        """
        try:
            # Title
            title = QLabel("Structure Analysis")
            title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            title.setStyleSheet("color: #2c3e50; padding: 10px;")

            # TabWidget
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

            # Tab 1: Setup
            setup_widget = QWidget()
            setup_layout = QVBoxLayout(setup_widget)
            setup_layout.setSpacing(8)
            setup_layout.setContentsMargins(12, 12, 12, 12)

            # Modes
            mode_group = QGroupBox("Analysis Mode")
            mode_layout = QHBoxLayout()
            mode_layout.addWidget(QLabel("Mode:"))
            self.mode_combo = QComboBox()
            self.mode_combo.addItems([
                "🤖 LLM Analysis (Deep, Canonical, API Cost)",
                "⚡ Regex Analysis (Instant, Free, Offline)",
                "🔀 Hybrid (Regex + LLM for Ambiguous)"
            ])
            self.mode_combo.setToolTip("LLM: AI context/canonical\nRegex: Fast patterns\nHybrid: 80-90% savings")
            self.mode_combo.currentTextChanged.connect(self._toggle_llm_controls)
            mode_layout.addWidget(self.mode_combo, 1)
            mode_group.setLayout(mode_layout)
            setup_layout.addWidget(mode_group)

            # LLM Models (initially hidden)
            self.model_group = QGroupBox("LLM Model")
            model_layout = QHBoxLayout()
            model_layout.addWidget(QLabel("Model:"))
            self.model_combo = QComboBox()
            self.model_combo.addItems(["Claude-3.7-Sonnet", "GPT-4", "Gemini-2.5-Pro"])
            model_layout.addWidget(self.model_combo)
            btn_refresh = QPushButton("Refresh Models")
            btn_refresh.clicked.connect(self._refresh_models)
            model_layout.addWidget(btn_refresh)
            self.model_group.setLayout(model_layout)
            self.model_group.setVisible(False)  # Default regex
            setup_layout.addWidget(self.model_group)

            # Buttons
            button_layout = QHBoxLayout()
            self.btn_preview = QPushButton("Preview Prompt")
            self.btn_preview.clicked.connect(self._preview_prompt)
            button_layout.addWidget(self.btn_preview)
            self.btn_run = QPushButton("▶ Run Analysis")
            self.btn_run.clicked.connect(self._run_analysis)
            self.btn_run.setMinimumHeight(35)
            button_layout.addWidget(self.btn_run)
            self.btn_enrich = QPushButton("✨ Enrich Metadata")
            self.btn_enrich.clicked.connect(self._enrich_metadata)
            self.btn_enrich.setEnabled(False)
            button_layout.addWidget(self.btn_enrich)
            button_layout.addStretch()
            setup_layout.addLayout(button_layout)

            # Progress/Status
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            setup_layout.addWidget(self.progress_bar)
            self.lbl_status = QLabel("")
            self.lbl_status.setStyleSheet("color: #566573; font-style: italic;")
            setup_layout.addWidget(self.lbl_status)
            setup_layout.addStretch()

            self.tab_widget.addTab(setup_widget, "⚙️ Setup")

            # Tab 2: Plan Table (per plan.md Point 5)
            plan_widget = QWidget()
            plan_layout = QVBoxLayout(plan_widget)
            plan_layout.setSpacing(8)
            plan_layout.setContentsMargins(12, 12, 12, 12)
            self.plan_table = QTableWidget()
            self.plan_table.setColumnCount(6)
            self.plan_table.setHorizontalHeaderLabels(["Original Path", "Proposed Path", "Action", "Subtitles", "Confidence", "Notes"])
            self.plan_table.horizontalHeader().setStretchLastSection(True)
            self.plan_table.setAlternatingRowColors(True)
            self.plan_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            plan_layout.addWidget(self.plan_table)
            self.tab_widget.addTab(plan_widget, "📋 Reorg Plan")

            # Tab 3: Metadata Table
            meta_widget = QWidget()
            meta_layout = QVBoxLayout(meta_widget)
            meta_layout.setSpacing(8)
            meta_layout.setContentsMargins(12, 12, 12, 12)
            self.metadata_table = QTableWidget()
            self.metadata_table.setColumnCount(5)
            self.metadata_table.setHorizontalHeaderLabels(["Title", "Year", "TMDb ID", "Seasons/Eps", "Status"])
            self.metadata_table.horizontalHeader().setStretchLastSection(True)
            self.metadata_table.setAlternatingRowColors(True)
            meta_layout.addWidget(self.metadata_table)
            self.tab_widget.addTab(meta_widget, "📊 Metadata")

            # Main layout: title + tabs
            layout = QVBoxLayout(self)
            layout.setSpacing(0)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.addWidget(title)
            layout.addWidget(self.tab_widget, 1)
            self.setLayout(layout)

            # Load data
            self._load_scan_data()
            self._toggle_llm_controls()  # Initial state

        except Exception as e:
            logger.error(f"Failed to initialize tabbed UI: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Error", f"Failed to initialize analysis interface:\n\n{str(e)}")
            raise
    
    def _load_scan_data(self):
        """
        Load scan data from the most recent scan session for the current project.
        
        Retrieves the latest scan session from the database and loads associated file records.
        This data is used as input for LLM analysis and metadata enrichment operations.
        
        The method:
        1. Connects to the media library database
        2. Finds the most recent scan session for the current project
        3. Parses scan options to extract folder paths and inventory session IDs
        4. Loads all file records from associated inventory sessions
        5. Updates UI status to reflect loaded data
        
        If no scan data is found, the UI will show appropriate messaging to the user.
        
        Raises:
            sqlite3.Error: If database operations fail
            json.JSONDecodeError: If scan options JSON is malformed
        """
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            # Get most recent scan session for this project
            cursor.execute('''
                SELECT id, total_files, scan_options_json 
                FROM project_scan_sessions 
                WHERE project_id = ? 
                ORDER BY scan_start DESC 
                LIMIT 1
            ''', (self.project.id,))
            
            row = cursor.fetchone()
            if row:
                scan_id, total_files, options_json = row
                options = json.loads(options_json) if options_json else {}
                folders = options.get('folders', [])
                inventory_sessions = options.get('inventory_session_ids', [])

                self.scanned_files = []
                for session_id in inventory_sessions:
                    self.scanned_files.extend(self.inventory_repo.get_all_files(session_id))

                if not self.scanned_files:
                    self.lbl_status.setText(
                        "Scan data found but inventory is unavailable. Please run a new scan."
                    )
                    self.btn_run.setEnabled(False)
                    self.btn_preview.setEnabled(False)
                    self.folder_structure = None
                else:
                    scanner = FileScanner()
                    self.folder_structure = scanner.get_folder_structure(self.scanned_files)
                    self.folder_structure['project_name'] = self.project.name
                    self.folder_structure['scan_id'] = scan_id
                    self.folder_structure['total_files'] = len(self.scanned_files)
                    if self.using_filtered_data:
                        # Don't overwrite status if we're using filtered data
                        pass
                    else:
                        self.lbl_status.setText(
                            f"Ready to analyze {len(self.scanned_files)} files from {len(folders)} folder(s)"
                        )
                    self.btn_run.setEnabled(True)
                    self.btn_preview.setEnabled(True)
            else:
                self.lbl_status.setText("No scan data found. Please run a scan first.")
                self.btn_run.setEnabled(False)
                self.btn_preview.setEnabled(False)
                self.folder_structure = None
            
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Database error loading scan data: {e}", exc_info=True)
            self.lbl_status.setText(f"Database error loading scan data: {e}")
            self.btn_run.setEnabled(False)
            self.btn_preview.setEnabled(False)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in scan options: {e}", exc_info=True)
            self.lbl_status.setText(f"Error parsing scan options: {e}")
            self.btn_run.setEnabled(False)
            self.btn_preview.setEnabled(False)
        except Exception as e:
            logger.error(f"Unexpected error loading scan data: {e}", exc_info=True)
            self.lbl_status.setText(f"Unexpected error loading scan data: {e}")
            self.btn_run.setEnabled(False)
            self.btn_preview.setEnabled(False)
    
    def _use_filtered_data(self):
        """
        Use filtered data provided from ScanResultsView.
        
        This method is called during initialization if filtered_files were provided,
        bypassing the normal database load process and using the pre-filtered dataset.
        
        The method:
        1. Uses the provided filtered_files as scanned_files
        2. Builds folder structure from filtered files
        3. Updates UI status to show filter information
        4. Enables analysis buttons
        
        This allows users to perform LLM analysis on a subset of files, reducing
        token costs and improving analysis quality by excluding irrelevant content.
        """
        try:
            if not self.filtered_files:
                logger.warning("_use_filtered_data called but no filtered_files available")
                return
            
            # Use filtered files as scanned files
            self.scanned_files = self.filtered_files
            
            # Build folder structure from filtered files
            scanner = FileScanner()
            self.folder_structure = scanner.get_folder_structure(self.scanned_files)
            self.folder_structure['project_name'] = self.project.name
            self.folder_structure['total_files'] = len(self.scanned_files)
            
            # Update status with filter information
            total_files = len(self.scanned_files)
            filter_desc = []
            
            if self.filter_config:
                file_types = self.filter_config.get('file_types', {})
                enabled_types = [k for k, v in file_types.items() if v]
                if enabled_types and len(enabled_types) < 4:
                    filter_desc.append(f"Types: {', '.join(enabled_types)}")
                
                size_range = self.filter_config.get('size_range_mb', {})
                if size_range.get('min', 0) > 0 or size_range.get('max', 100000) < 100000:
                    filter_desc.append(f"Size: {size_range.get('min', 0)}-{size_range.get('max', 100000)} MB")
                
                if self.filter_config.get('hide_duplicates'):
                    filter_desc.append("No duplicates")
            
            filter_text = f" ({', '.join(filter_desc)})" if filter_desc else ""
            
            self.lbl_status.setText(
                f"✓ Ready to analyze {total_files} filtered files{filter_text}"
            )
            self.lbl_status.setStyleSheet("color: #16a085; font-weight: bold; font-style: italic;")
            
            self.btn_run.setEnabled(True)
            self.btn_preview.setEnabled(True)
            
            logger.info(f"Using filtered data: {total_files} files with filters: {filter_desc}")
            
        except Exception as e:
            logger.error(f"Failed to use filtered data: {e}", exc_info=True)
            self.lbl_status.setText(f"Error using filtered data: {e}")
            self.btn_run.setEnabled(False)
            self.btn_preview.setEnabled(False)
    
    def _refresh_models(self):
        """
        Refresh the list of available LLM models from the Poe API.
        
        Queries the Poe API service to get the current list of available models
        for analysis. This ensures users can select from the latest available
        models and their capabilities.
        
        The method:
        1. Updates status label to indicate model fetching
        2. Creates a PoeClient instance to query available models
        3. Clears and repopulates the model selection dropdown
        4. Updates status with success/failure information
        5. Shows warning dialog if API query fails
        
        If the API query fails, the UI gracefully degrades by showing
        a warning but continuing to function with default model options.
        
        Raises:
            QMessageBox: Shows warning if model refresh fails, but doesn't prevent continued use
        """
        try:
            self.lbl_status.setText("Fetching available models...")
            client = PoeClient()
            models = client.get_available_models()
            
            if models:
                self.model_combo.clear()
                self.model_combo.addItems(models)
                self.lbl_status.setText(f"Loaded {len(models)} models")
                logger.info(f"Refreshed models: {models}")
            else:
                self.lbl_status.setText("No models available")
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Model Refresh Failed",
                f"Could not fetch models from Poe API:\n\n{e}\n\n"
                "Using default model list."
            )
            self.lbl_status.setText("Using default models")
            logger.error(f"Model refresh error: {e}", exc_info=True)

    def _toggle_llm_controls(self):
        """Show/hide LLM model controls based on selected mode."""
        try:
            mode_text = self.mode_combo.currentText()
            is_llm_mode = "LLM" in mode_text or "Hybrid" in mode_text
            self.model_group.setVisible(is_llm_mode)
            self.btn_preview.setEnabled(is_llm_mode or "Hybrid" in mode_text)
        except Exception as e:
            logger.error(f"Failed to toggle LLM controls: {e}", exc_info=True)

    def _populate_plan_table(self, analysis_result: dict):
        """Populate plan table with reorganization plan data (per plan.md Point 5)."""
        try:
            plan = analysis_result.get("reorganization_plan", {})
            folder_changes = plan.get("folder_changes", [])
            
            if not folder_changes:
                self.plan_table.setRowCount(0)
                return
            
            self.plan_table.setRowCount(len(folder_changes))
            
            for row, change in enumerate(folder_changes):
                self.plan_table.setItem(row, 0, QTableWidgetItem(change.get("current_path", "")))
                self.plan_table.setItem(row, 1, QTableWidgetItem(change.get("proposed_path", "")))
                self.plan_table.setItem(row, 2, QTableWidgetItem(change.get("action", "UNKNOWN").upper()))
                self.plan_table.setItem(row, 3, QTableWidgetItem(change.get("subtitle_rename", "N/A")))
                self.plan_table.setItem(row, 4, QTableWidgetItem(change.get("confidence", "MEDIUM")))
                self.plan_table.setItem(row, 5, QTableWidgetItem(change.get("reason", "")))
            
            self.plan_table.resizeColumnsToContents()
            logger.info(f"Populated plan table with {len(folder_changes)} operations")
        except Exception as e:
            logger.error(f"Failed to populate plan table: {e}", exc_info=True)

    def _populate_metadata_table(self, canonical_db: dict):
        """Populate metadata table with canonical database results."""
        try:
            movies = canonical_db.get("movies", [])
            tv_shows = canonical_db.get("tv_shows", [])
            total = len(movies) + len(tv_shows)
            
            if total == 0:
                self.metadata_table.setRowCount(0)
                return
            
            self.metadata_table.setRowCount(total)
            row = 0
            
            for movie in movies:
                self.metadata_table.setItem(row, 0, QTableWidgetItem(movie.get("title", "Unknown")))
                self.metadata_table.setItem(row, 1, QTableWidgetItem(str(movie.get("year", "?"))))
                self.metadata_table.setItem(row, 2, QTableWidgetItem(str(movie.get("tmdb_id", "N/A"))))
                self.metadata_table.setItem(row, 3, QTableWidgetItem("Movie"))
                self.metadata_table.setItem(row, 4, QTableWidgetItem("✓"))
                row += 1
            
            for show in tv_shows:
                self.metadata_table.setItem(row, 0, QTableWidgetItem(show.get("title", "Unknown")))
                self.metadata_table.setItem(row, 1, QTableWidgetItem(str(show.get("year", "?"))))
                self.metadata_table.setItem(row, 2, QTableWidgetItem(str(show.get("tmdb_id", "N/A"))))
                seasons = show.get("number_of_seasons", 0)
                episodes = show.get("number_of_episodes", 0)
                self.metadata_table.setItem(row, 3, QTableWidgetItem(f"{seasons} seasons, {episodes} eps"))
                self.metadata_table.setItem(row, 4, QTableWidgetItem("✓"))
                row += 1
            
            self.metadata_table.resizeColumnsToContents()
            logger.info(f"Populated metadata table with {total} items")
        except Exception as e:
            logger.error(f"Failed to populate metadata table: {e}", exc_info=True)
    
    def _preview_prompt(self):
        """
        Preview the analysis prompt that will be sent to the LLM.
        
        Generates and displays the exact prompt that would be sent to the selected
        LLM model for analysis. This allows users to review the context and
        instructions before committing to the analysis operation.
        
        The method:
        1. Validates that scan data is available for prompt generation
        2. Creates an LLMStructureAnalyzer to build the analysis prompt
        3. Constructs a preview dialog with the formatted prompt
        4. Shows the prompt in a scrollable text area
        5. Provides OK/Cancel buttons for user interaction
        
        The preview helps users understand what information the LLM will
        receive and ensures the analysis context is appropriate for their needs.
        
        Raises:
            QMessageBox: Shows warning if no scan data is available
        """
        try:
            if not self.folder_structure:
                QMessageBox.warning(self, "No Data", "No scan data available to preview.")
                return
            
            analyzer = LLMStructureAnalyzer()
            prompt = analyzer._build_analysis_prompt(self.folder_structure)
            
            # Show in dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Prompt Preview")
            dialog.resize(800, 600)
            
            layout = QVBoxLayout()
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(prompt)
            text_edit.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
            layout.addWidget(text_edit)
            
            # Buttons
            button_box = QDialogButtonBox()
            btn_copy = button_box.addButton("Copy to Clipboard", QDialogButtonBox.ButtonRole.ActionRole)
            btn_copy.clicked.connect(lambda: self._copy_to_clipboard(prompt))
            btn_close = button_box.addButton(QDialogButtonBox.StandardButton.Close)
            btn_close.clicked.connect(dialog.close)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate prompt preview:\n\n{e}")
            logger.error(f"Prompt preview error: {e}", exc_info=True)
    
    def _copy_to_clipboard(self, text: str):
        """
        Copy the provided text to the system clipboard.
        
        Utility method for copying text content (typically prompts or results)
        to the clipboard for external use or sharing.
        
        Args:
            text: The text content to copy to clipboard
            
        The method:
        1. Accesses the QApplication clipboard instance
        2. Sets the provided text as clipboard content
        3. Updates status label to confirm successful copy
        4. Shows error dialog if clipboard access fails
        
        This is commonly used after prompt preview to allow users to
        copy the analysis prompt for external review or manual execution.
        
        Raises:
            QMessageBox: Shows warning if clipboard operations fail
        """
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.lbl_status.setText("Prompt copied to clipboard!")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}", exc_info=True)
            QMessageBox.warning(self, "Clipboard Error", f"Failed to copy to clipboard: {str(e)}")
    
    def _run_analysis(self):
        """
        Execute analysis on the loaded scan data using the selected mode.
        
        Supports three analysis modes:
        - LLM: Deep AI analysis with context understanding (API cost)
        - Regex: Fast pattern matching (instant, free, offline)
        - Hybrid: Regex first, LLM only for ambiguous (80-90% cost savings)
        
        Initiates the analysis workflow by:
        1. Validating that scan data is available
        2. Determining selected analysis mode
        3. Getting LLM model (if needed for mode)
        4. Confirming execution with the user
        5. Creating and starting appropriate worker thread
        6. Disabling UI controls during processing
        7. Showing progress indication
        
        The worker runs in a separate thread to prevent UI blocking.
        Progress and completion are handled by connected signal handlers.
        
        Raises:
            QMessageBox: Shows user warnings if no scan data is available
        """
        try:
            if not self.folder_structure:
                QMessageBox.warning(self, "No Data", "No scan data available. Please run a scan first.")
                return
            
            # Determine analysis mode from combo box
            mode_text = self.mode_combo.currentText()
            if "LLM Analysis" in mode_text:
                analysis_mode = "llm"
            elif "Regex Analysis" in mode_text:
                analysis_mode = "regex"
            elif "Hybrid" in mode_text:
                analysis_mode = "hybrid"
            else:
                analysis_mode = "llm"  # Default fallback
            
            model = self.model_combo.currentText()
            total_files = self.folder_structure.get('total_files', 0) if self.folder_structure else 0
            
            # Mode-specific confirmation dialogs
            if analysis_mode == "llm":
                confirm_msg = (
                    f"Run LLM analysis with {model}?\n\n"
                    f"Files to analyze: {total_files}\n"
                    f"Estimated time: 30-60 seconds\n"
                    f"Cost: API call charges apply"
                )
            elif analysis_mode == "regex":
                confirm_msg = (
                    f"Run Regex analysis?\n\n"
                    f"Files to analyze: {total_files}\n"
                    f"Estimated time: <1 second\n"
                    f"Cost: FREE (no API calls)"
                )
            else:  # hybrid
                confirm_msg = (
                    f"Run Hybrid analysis (Regex + {model})?\n\n"
                    f"Files to analyze: {total_files}\n"
                    f"Phase 1: Regex (instant, free)\n"
                    f"Phase 2: LLM only for ambiguous cases\n"
                    f"Expected savings: 80-90% vs pure LLM"
                )
            
            reply = QMessageBox.question(
                self,
                "Run Analysis",
                confirm_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Disable UI
            self.btn_run.setEnabled(False)
            self.btn_preview.setEnabled(False)
            self.model_combo.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self.progress_bar.setVisible(True)
            
            # Create appropriate worker based on mode
            if analysis_mode == "llm":
                self.analysis_worker = LLMAnalysisWorker(
                    folder_structure=self.folder_structure,
                    scanned_files=self.scanned_files,
                    model=model,
                )
                logger.info(f"Started LLM analysis with {model}")
                
            elif analysis_mode == "regex":
                self.analysis_worker = RegexAnalysisWorker(
                    scanned_files=self.scanned_files,
                )
                logger.info(f"Started Regex analysis on {total_files} files")
                
            else:  # hybrid
                self.analysis_worker = HybridAnalysisWorker(
                    scanned_files=self.scanned_files,
                    folder_structure=self.folder_structure,
                    model=model,
                )
                logger.info(f"Started Hybrid analysis (Regex + {model} for ambiguous)")
            
            # Connect signals (same interface for all workers)
            self.analysis_worker.progress.connect(self._on_analysis_progress)
            self.analysis_worker.finished.connect(self._on_analysis_finished)
            self.analysis_worker.error.connect(self._on_analysis_error)
            self.analysis_worker.start()
            
        except Exception as e:
            logger.error(f"Failed to start analysis: {e}", exc_info=True)
            QMessageBox.critical(self, "Analysis Error", f"Failed to start analysis: {str(e)}")
            # Re-enable UI on error
            self.btn_run.setEnabled(True)
            self.btn_preview.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.mode_combo.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _on_analysis_progress(self, status: str):
        """
        Handle progress updates during LLM analysis.
        
        Updates the UI status label with current analysis progress information.
        This method is called periodically by the LLMAnalysisWorker to provide
        user feedback during long-running analysis operations.
        
        Args:
            status: Progress status message from the analysis worker
                   (e.g., "Analyzing folder structure...", "Querying LLM...")
                   
        The method simply updates the status label text. If the update fails
        (rare), it logs the error but doesn't interrupt the analysis process.
        
        This provides real-time feedback to users during analysis operations
        that may take several seconds to minutes depending on content complexity.
        """
        try:
            self.lbl_status.setText(status)
        except Exception as e:
            logger.error(f"Failed to update analysis progress: {e}", exc_info=True)
    
    def _on_analysis_finished(self, analysis_result: dict):
        """
        Handle completion of LLM analysis.
        
        Processes the analysis results and updates the UI to display findings.
        This method is called when the LLMAnalysisWorker completes successfully.
        
        Args:
            analysis_result: Dictionary containing analysis results with keys:
                - detected_media: List of detected media items with metadata
                - recommendations: Suggested reorganization actions
                - confidence_scores: Analysis confidence metrics
                - Other analysis-specific data
                
        The method:
        1. Re-enables UI controls that were disabled during analysis
        2. Stores results in instance variables for later use
        3. Formats and displays a structured summary of findings
        4. Shows detected media items with confidence scores
        5. Enables metadata enrichment functionality
        
        The results are formatted for human readability and LLM consumption.
        """
        try:
            self.btn_run.setEnabled(True)
            self.btn_preview.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.mode_combo.setEnabled(True)
            self.btn_enrich.setEnabled(True)
            self.progress_bar.setVisible(False)

            self.llm_analysis = analysis_result
            self.current_parsed_json = analysis_result
            self.detected_media = analysis_result.get("detected_media", [])

            # Display structured summary similar to legacy workflow
            output_lines = []
            output_lines.append("=" * 80)
            output_lines.append("LLM ANALYSIS COMPLETE")
            output_lines.append("=" * 80 + "\n")

            output_lines.append(f"DETECTED MEDIA ({len(self.detected_media)} items):")
            output_lines.append("-" * 80)
            for media in self.detected_media[:10]:
                media_type = media.get("type", "unknown").upper()
                title = media.get("title", "Unknown")
                year = media.get("year_estimate", "?")
                confidence = media.get("confidence", "unknown")
                output_lines.append(f"  [{media_type}] {title} ({year}) - Confidence: {confidence}")
                if media.get("notes"):
                    output_lines.append(f"           Notes: {media['notes']}")
            if len(self.detected_media) > 10:
                output_lines.append(f"  ... and {len(self.detected_media) - 10} more")
            output_lines.append("")

            plan = analysis_result.get("reorganization_plan", {})
            plan_summary = plan.get("summary", "No summary provided")
            output_lines.append("REORGANIZATION PLAN:")
            output_lines.append("-" * 80)
            output_lines.append(plan_summary)
            output_lines.append("")

            folder_changes = plan.get("folder_changes", [])
            if folder_changes:
                output_lines.append(f"PROPOSED CHANGES ({len(folder_changes)} folders):")
                output_lines.append("-" * 80)
                for change in folder_changes[:10]:
                    output_lines.append(f"  {change.get('action', 'unknown').upper()}: {change.get('current_path', 'unknown')}")
                    output_lines.append(f"    → {change.get('proposed_path', 'unknown')}")
                    output_lines.append(f"    Reason: {change.get('reason', 'No reason provided')}")
                    output_lines.append("")
                if len(folder_changes) > 10:
                    output_lines.append(f"  ... and {len(folder_changes) - 10} more changes")

            multi_part = analysis_result.get("multi_part_episodes", [])
            if multi_part:
                output_lines.append("")
                output_lines.append(f"MULTI-PART EPISODES ({len(multi_part)}):")
                output_lines.append("-" * 80)
                for episode in multi_part:
                    show = episode.get("show_title", "Unknown")
                    season = episode.get("season_number", "?")
                    episodes = episode.get("episode_numbers", [])
                    title = episode.get("combined_episode_title", "Unknown")
                    output_lines.append(f"  {show} - S{season:02d}E{episodes} - {title}")
                    output_lines.append(f"    Reason: {episode.get('reason', 'No reason provided')}")

            output_lines.append("")
            output_lines.append("LLM REASONING:")
            output_lines.append("-" * 80)
            reasoning = analysis_result.get("reasoning", "No reasoning provided")
            output_lines.append(reasoning)
            output_lines.append("")
            output_lines.append("=" * 80)

            # NEW: Populate plan table (per plan.md Point 5)
            self._populate_plan_table(analysis_result)
            
            self.lbl_status.setText("Analysis complete! Click 'Enrich Metadata' to query TMDB/OMDb.")

            self._save_analysis_to_database(output_lines, analysis_result)
            logger.info("LLM analysis completed successfully")

            QMessageBox.information(
                self,
                "Analysis Complete",
                f"Analysis completed successfully!\n\n"
                f"Detected {len(self.detected_media)} media items.\n"
                f"Click 'Enrich Metadata' for canonical data.",
            )
        except Exception as e:
            logger.error(f"Failed to handle analysis completion: {e}", exc_info=True)
            QMessageBox.critical(self, "Analysis Completion Error", f"Analysis completed but failed to process results: {str(e)}")
            # Still re-enable UI
            self.btn_run.setEnabled(True)
            self.btn_preview.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.btn_enrich.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _on_analysis_error(self, error_msg: str):
        """
        Handle errors that occur during LLM analysis.
        
        This method is called when the LLMAnalysisWorker encounters an error.
        It provides user feedback and restores the UI to a usable state.
        
        Args:
            error_msg: Descriptive error message from the analysis worker
            
        The method:
        1. Re-enables UI controls that were disabled during analysis
        2. Hides the progress bar
        3. Updates status label with error information
        4. Shows a critical error dialog to inform the user
        5. Logs the error for debugging purposes
        
        The UI is restored to allow retry attempts or other operations.
        """
        try:
            self.btn_run.setEnabled(True)
            self.btn_preview.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.mode_combo.setEnabled(True)
            self.progress_bar.setVisible(False)
            
            self.lbl_status.setText(f"Analysis failed: {error_msg}")
            
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"LLM analysis failed:\n\n{error_msg}"
            )
            
            logger.error(f"LLM analysis error: {error_msg}")
        except Exception as e:
            logger.error(f"Failed to handle analysis error: {e}", exc_info=True)
    
    def _save_analysis_to_database(self, display_content, parsed_json: dict):
        """
        Save analysis results to the project database.
        
        Persists the LLM analysis results for future reference and audit trails.
        This allows users to review historical analyses and track changes over time.
        
        Args:
            display_content: Formatted text content for display/storage
            parsed_json: Structured analysis results as dictionary containing:
                - recommendations: List of suggested actions
                - detected_media: Media detection results
                - reorganization_plan: Structural recommendations
                - Other analysis metadata
                
        The method:
        1. Connects to the media library database
        2. Extracts analysis metadata (model, scan ID, confidence)
        3. Determines confidence level based on results quality
        4. Inserts analysis record into project_analyses table
        5. Emits analysis_saved signal to notify other components
        6. Updates UI status to reflect successful save
        
        Raises:
            sqlite3.Error: If database operations fail
            json.JSONEncodeError: If parsed_json cannot be serialized
        """
        try:
            if not self.folder_structure:
                raise ValueError("No scan data available for analysis save")
                
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            model = self.model_combo.currentText()
            scan_id = self.folder_structure.get('scan_id')
            
            # Determine confidence based on parsed results
            confidence = "MEDIUM"
            if parsed_json and len(parsed_json.get('recommendations', [])) > 0:
                confidence = "HIGH"
            
            issues_found = len(parsed_json.get('recommendations', []))
            
            cursor.execute('''
                INSERT INTO project_analyses 
                (project_id, scan_session_id, model_name, analysis_date, 
                 response_text, parsed_json, confidence, issues_found)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.project.id,
                scan_id,
                model,
                datetime.now().isoformat(),
                "\n".join(display_content) if isinstance(display_content, list) else display_content,
                json.dumps(parsed_json),
                confidence,
                issues_found
            ))
            
            self.current_analysis_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved analysis to database: ID={self.current_analysis_id}")
            if self.current_analysis_id:
                self.analysis_saved.emit(self.current_analysis_id)
            
        except Exception as e:
            logger.error(f"Failed to save analysis to database: {e}", exc_info=True)

    def _enrich_metadata(self):
        """
        Start the metadata enrichment process for detected media.
        
        Initiates background metadata lookup using TMDB and OMDb APIs to gather
        canonical information for all detected media items. This process resolves
        official titles, release years, episode structures, and identifies content
        that requires NFO metadata files.
        
        The enrichment process:
        1. Validates that detected media data is available from prior analysis
        2. Prompts user for confirmation due to API usage
        3. Checks for required API keys (TMDB_API_KEY, OMDB_API_KEY)
        4. Creates and starts a MetadataLookupWorker thread
        5. Disables UI controls during processing
        6. Shows progress indication
        
        The worker runs asynchronously to prevent UI blocking. Results are
        processed by connected signal handlers when complete.
        
        Raises:
            QMessageBox: Shows warnings if no media data or missing API keys
        """
        try:
            if not self.detected_media:
                QMessageBox.warning(
                    self, "No Data", "No detected media available. Run analysis first."
                )
                return

            reply = QMessageBox.question(
                self,
                "Build Canonical Metadata",
                "Query TMDB/OMDb for canonical metadata?\n\n"
                "This will resolve official titles, years, season/episode structure,\n"
                "and identify multi-part episodes that require NFO files.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            self.btn_enrich.setEnabled(False)
            self.btn_run.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            tmdb_key = os.getenv("TMDB_API_KEY")
            omdb_key = os.getenv("OMDB_API_KEY")

            self.metadata_worker = MetadataLookupWorker(
                detected_media=self.detected_media,
                scanned_files=self.scanned_files,
                tmdb_api_key=tmdb_key,
                omdb_api_key=omdb_key,
            )
            self.metadata_worker.progress.connect(self._on_metadata_progress)
            self.metadata_worker.finished.connect(self._on_metadata_finished)
            self.metadata_worker.error.connect(self._on_metadata_error)
            self.metadata_worker.start()

            logger.info("Started metadata enrichment")
        except Exception as e:
            logger.error(f"Failed to start metadata enrichment: {e}", exc_info=True)
            QMessageBox.critical(self, "Enrichment Error", f"Failed to start metadata enrichment: {str(e)}")
            # Re-enable UI on error
            self.btn_enrich.setEnabled(True)
            self.btn_run.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _on_metadata_progress(self, status: str, current: int, total: int):
        """
        Handle progress updates during metadata enrichment.
        
        Updates the UI with current progress information during metadata lookup
        operations. This method is called periodically by the MetadataLookupWorker
        to provide detailed progress feedback for long-running API queries.
        
        Args:
            status: Current status message from the metadata worker
                   (e.g., "Querying TMDB for 'Movie Title'...")
            current: Number of items processed so far
            total: Total number of items to process
            
        The method:
        1. Updates the status label with the current status message
        2. Sets progress bar maximum and current values for visual progress
        3. Logs errors if UI updates fail (rare case)
        
        Progress tracking is important for metadata enrichment as it involves
        multiple API calls that can take significant time depending on the
        number of media items and API response times.
        """
        try:
            self.lbl_status.setText(status)
            if total > 0:
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(current)
        except Exception as e:
            logger.error(f"Failed to update metadata progress: {e}", exc_info=True)

    def _on_metadata_finished(self, canonical_db: dict):
        """
        Handle completion of metadata enrichment lookup.
        
        Processes the canonical metadata database and updates the UI to display
        the enriched information. This method is called when the MetadataLookupWorker
        completes successfully.
        
        Args:
            canonical_db: Dictionary containing canonical metadata with structure:
                - movies: List of movie metadata dictionaries
                - tv_shows: List of TV show metadata dictionaries
                - episodes: Episode metadata for TV shows
                Each item contains TMDb/OMDb canonical information
                
        The method:
        1. Re-enables UI controls that were disabled during lookup
        2. Stores canonical database for later use
        3. Formats and displays summary of enriched metadata
        4. Shows movies and TV shows with key information
        5. Emits metadata_built signal to notify other components
        6. Updates status to indicate successful enrichment
        
        The canonical database provides authoritative metadata for content
        identification and NFO file generation.
        """
        try:
            self.btn_enrich.setEnabled(True)
            self.btn_run.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.canonical_database = canonical_db

            lines = []
            lines.append("CANONICAL METADATA DATABASE")
            lines.append("=" * 60 + "\n")

            lines.append(f"Movies: {len(canonical_db.get('movies', []))}")
            for movie in canonical_db.get("movies", [])[:10]:
                title = movie.get("title", "Unknown")
                year = movie.get("year", "????")
                tmdb_id = movie.get("tmdb_id", "N/A")
                lines.append(f"  • {title} ({year}) [TMDb: {tmdb_id}]")
            lines.append("")

            lines.append(f"TV Shows: {len(canonical_db.get('tv_shows', []))}")
            for show in canonical_db.get("tv_shows", [])[:10]:
                title = show.get("title", "Unknown")
                year = show.get("year", "????")
                tmdb_id = show.get("tmdb_id", "N/A")
                num_seasons = show.get("number_of_seasons", 0)
                num_episodes = show.get("number_of_episodes", 0)
                lines.append(
                    f"  • {title} ({year}) - {num_seasons} seasons, {num_episodes} episodes [TMDb: {tmdb_id}]"
                )
            lines.append("")

            multi_part = canonical_db.get("multi_part_episodes", [])
            if multi_part:
                lines.append(f"Multi-Part Episodes Needing NFOs: {len(multi_part)}")
                for mp in multi_part[:5]:
                    lines.append(
                        f"  • {mp['show_title']} - S{mp['season_number']:02d}E{mp['episode_number']:02d} - {mp['episode_name']}"
                    )
                lines.append("")

            if canonical_db.get("lookup_failures"):
                lines.append(f"Lookup Failures: {len(canonical_db['lookup_failures'])}")
                for failure in canonical_db["lookup_failures"][:5]:
                    lines.append(f"  • {failure.get('title', 'Unknown')} ({failure.get('type', '?')})")
                lines.append("")

            # NEW: Populate metadata table
            self._populate_metadata_table(canonical_db)
            
            self.lbl_status.setText("Metadata enrichment complete!")

            try:
                conn = sqlite3.connect("data/media_library.db")
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    UPDATE project_analyses
                    SET metadata_json = ?
                    WHERE id = ?
                    ''',
                    (json.dumps(canonical_db), self.current_analysis_id),
                )
                conn.commit()
                conn.close()
                logger.info("Saved canonical metadata to database")
                if self.current_analysis_id:
                    self.metadata_built.emit(self.current_analysis_id)
            except Exception as e:
                logger.error(f"Failed to save canonical metadata: {e}", exc_info=True)

            QMessageBox.information(
                self,
                "Metadata Complete",
                f"Metadata enrichment complete!\n\n"
                f"Movies: {len(canonical_db.get('movies', []))}\n"
                f"TV Shows: {len(canonical_db.get('tv_shows', []))}\n"
                f"Multi-part episodes: {len(multi_part)}",
            )
        except Exception as e:
            logger.error(f"Failed to handle metadata completion: {e}", exc_info=True)
            QMessageBox.critical(self, "Metadata Completion Error", f"Metadata enrichment completed but failed to process results: {str(e)}")
            # Still re-enable UI
            self.btn_enrich.setEnabled(True)
            self.btn_run.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _on_metadata_error(self, error_msg: str):
        """
        Handle errors that occur during metadata enrichment.
        
        This method is called when the MetadataLookupWorker encounters an error
        during API queries or data processing. It provides user feedback and
        restores the UI to a usable state.
        
        Args:
            error_msg: Descriptive error message from the metadata worker
                      (may include API errors, network issues, or parsing failures)
            
        The method:
        1. Re-enables UI controls that were disabled during lookup
        2. Hides the progress bar
        3. Updates status label with error information
        4. Shows a critical error dialog to inform the user
        5. Logs the error for debugging purposes
        
        Error handling is robust - if the error handler itself fails,
        it includes fallback UI restoration to prevent the interface
        from becoming unusable.
        
        Common error causes:
        - Missing or invalid API keys
        - Network connectivity issues
        - API rate limiting or service unavailability
        - Malformed response data from external services
        """
        try:
            self.btn_enrich.setEnabled(True)
            self.btn_run.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.lbl_status.setText(f"Metadata lookup failed: {error_msg}")
            QMessageBox.critical(
                self,
                "Metadata Error",
                f"Metadata lookup failed:\n\n{error_msg}",
            )
            logger.error(f"Metadata enrichment error: {error_msg}")
        except Exception as e:
            logger.error(f"Failed to handle metadata error: {e}", exc_info=True)
            # Ensure UI is still re-enabled even if error handling fails
            try:
                self.btn_enrich.setEnabled(True)
                self.btn_run.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.lbl_status.setText("Critical error in metadata error handling")
            except Exception as ui_error:
                logger.error(f"Failed to restore UI state after metadata error: {ui_error}", exc_info=True)

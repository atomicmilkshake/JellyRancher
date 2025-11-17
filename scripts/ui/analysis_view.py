#!/usr/bin/env python3
"""
Analysis View - LLM-powered folder structure analysis

Implements Point 2-3 from plan.md: LLM Analysis and Metadata Lookup
Allows users to analyze folder structure and get reorganization recommendations.
"""

import logging
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QMessageBox, QGroupBox, QHBoxLayout, QProgressBar,
    QDialog, QDialogButtonBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
from scripts.ai.ravenmaven_client import PoeClient

logger = logging.getLogger(__name__)


class LLMAnalysisWorker(QThread):
    """Background worker for LLM analysis."""
    
    finished = pyqtSignal(str, dict)  # response_text, parsed_json
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # status message
    
    def __init__(self, model: str, folder_structure: dict):
        super().__init__()
        self.model = model
        self.folder_structure = folder_structure
    
    def run(self):
        """Execute LLM analysis in background."""
        try:
            self.progress.emit("Initializing LLM analyzer...")
            
            analyzer = LLMStructureAnalyzer()
            
            self.progress.emit(f"Sending request to {self.model}...")
            
            # Run analysis
            result = analyzer.analyze_structure(
                self.folder_structure,
                model_name=self.model
            )
            
            self.progress.emit("Analysis complete!")
            
            # Extract response and parsed data
            response_text = result.get('raw_response', 'No response')
            parsed_json = result.get('parsed_response', {})
            
            self.finished.emit(response_text, parsed_json)
            
        except Exception as e:
            logger.error(f"LLM analysis error: {e}", exc_info=True)
            self.error.emit(str(e))


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
    
    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        
        self.project = project
        self.project_manager = project_manager
        self.current_analysis_id = None
        self.folder_structure = None
        
        self._init_ui()
        self._load_scan_data()
        
        logger.info(f"AnalysisView initialized for project: {project.name}")
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("LLM Analysis")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout()
        
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Claude-3.7-Sonnet", "GPT-4", "Gemini-2.5-Pro"])
        model_row.addWidget(self.model_combo)
        
        btn_refresh = QPushButton("Refresh Models")
        btn_refresh.clicked.connect(self._refresh_models)
        model_row.addWidget(btn_refresh)
        model_row.addStretch()
        
        model_layout.addLayout(model_row)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.btn_preview = QPushButton("Preview Prompt")
        self.btn_preview.clicked.connect(self._preview_prompt)
        button_layout.addWidget(self.btn_preview)
        
        self.btn_run = QPushButton("▶ Run Analysis")
        self.btn_run.clicked.connect(self._run_analysis)
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.btn_run)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.lbl_status)
        
        # Results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)
        
        self.setLayout(layout)
    
    def _load_scan_data(self):
        """Load scan data from most recent scan session."""
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
                
                self.lbl_status.setText(
                    f"Ready to analyze {total_files} files from {len(folders)} folder(s)"
                )
                
                # Build folder structure for LLM
                self.folder_structure = {
                    'project_name': self.project.name,
                    'total_files': total_files,
                    'folders': folders,
                    'scan_id': scan_id
                }
                
                self.btn_run.setEnabled(True)
                self.btn_preview.setEnabled(True)
            else:
                self.lbl_status.setText("No scan data found. Please run a scan first.")
                self.btn_run.setEnabled(False)
                self.btn_preview.setEnabled(False)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load scan data: {e}")
            self.lbl_status.setText(f"Error loading scan data: {e}")
            self.btn_run.setEnabled(False)
            self.btn_preview.setEnabled(False)
    
    def _refresh_models(self):
        """Refresh available models from Poe API."""
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
            logger.error(f"Model refresh error: {e}")
    
    def _preview_prompt(self):
        """Preview the prompt that will be sent to LLM."""
        if not self.folder_structure:
            QMessageBox.warning(self, "No Data", "No scan data available to preview.")
            return
        
        try:
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
            logger.error(f"Prompt preview error: {e}")
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.lbl_status.setText("Prompt copied to clipboard!")
    
    def _run_analysis(self):
        """Run LLM analysis."""
        if not self.folder_structure:
            QMessageBox.warning(self, "No Data", "No scan data available. Please run a scan first.")
            return
        
        model = self.model_combo.currentText()
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Run Analysis",
            f"Run analysis with {model}?\n\n"
            f"This will analyze {self.folder_structure.get('total_files', 0)} files "
            f"and may take 30-60 seconds.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI
        self.btn_run.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.model_combo.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # Start worker
        self.analysis_worker = LLMAnalysisWorker(model, self.folder_structure)
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)
        self.analysis_worker.start()
        
        logger.info(f"Started LLM analysis with {model}")
    
    def _on_analysis_progress(self, status: str):
        """Handle analysis progress updates."""
        self.lbl_status.setText(status)
    
    def _on_analysis_finished(self, response_text: str, parsed_json: dict):
        """Handle analysis completion."""
        # Re-enable UI
        self.btn_run.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Display results
        self.results_text.setPlainText(response_text)
        self.lbl_status.setText("Analysis complete!")
        
        # Save to database
        self._save_analysis_to_database(response_text, parsed_json)
        
        logger.info("LLM analysis completed successfully")
        
        QMessageBox.information(
            self,
            "Analysis Complete",
            f"Analysis completed successfully!\n\n"
            f"Found {len(parsed_json.get('recommendations', []))} recommendations."
        )
    
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis errors."""
        self.btn_run.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.lbl_status.setText(f"Analysis failed: {error_msg}")
        
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"LLM analysis failed:\n\n{error_msg}"
        )
        
        logger.error(f"LLM analysis error: {error_msg}")
    
    def _save_analysis_to_database(self, response_text: str, parsed_json: dict):
        """Save analysis results to database."""
        try:
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
                response_text,
                json.dumps(parsed_json),
                confidence,
                issues_found
            ))
            
            self.current_analysis_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved analysis to database: ID={self.current_analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to save analysis to database: {e}", exc_info=True)


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
    QDialog, QDialogButtonBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.core.file_scanner import FileScanner, FileRecord
from scripts.core.inventory_repository import InventoryRepository
from scripts.ai.ravenmaven_client import PoeClient
from scripts.core.workers import LLMAnalysisWorker, MetadataLookupWorker
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer

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

    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        super().__init__(parent)

        self.project = project
        self.project_manager = project_manager
        self.current_analysis_id = None
        self.folder_structure = None
        self.current_parsed_json = None  # Store parsed JSON for enrichment
        self.enrichment_worker = None
        self.canonical_database = None
        self.inventory_repo = InventoryRepository()
        self.scanned_files: List[FileRecord] = []
        self.detected_media: List[dict] = []
        self.llm_analysis: Optional[dict] = None
        self.metadata_worker = None

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

        self.btn_enrich = QPushButton("✨ Enrich Metadata")
        self.btn_enrich.clicked.connect(self._enrich_metadata)
        self.btn_enrich.setMinimumHeight(40)
        self.btn_enrich.setEnabled(False)
        self.btn_enrich.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.btn_enrich)

        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #566573; font-style: italic;")
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

        metadata_group = QGroupBox("Canonical Metadata Database")
        metadata_layout = QVBoxLayout()
        metadata_layout.addWidget(QLabel("TMDB/OMDb lookup results:"))
        self.metadata_output = QTextEdit()
        self.metadata_output.setReadOnly(True)
        self.metadata_output.setPlaceholderText("Click 'Enrich Metadata' to build the canonical database...")
        metadata_layout.addWidget(self.metadata_output)
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
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
                else:
                    scanner = FileScanner()
                    self.folder_structure = scanner.get_folder_structure(self.scanned_files)
                    self.folder_structure['project_name'] = self.project.name
                    self.folder_structure['scan_id'] = scan_id
                    self.folder_structure['total_files'] = len(self.scanned_files)
                    self.lbl_status.setText(
                        f"Ready to analyze {len(self.scanned_files)} files from {len(folders)} folder(s)"
                    )
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
        self.analysis_worker = LLMAnalysisWorker(
            folder_structure=self.folder_structure,
            scanned_files=self.scanned_files,
            model=model,
        )
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)
        self.analysis_worker.start()
        
        logger.info(f"Started LLM analysis with {model}")
    
    def _on_analysis_progress(self, status: str):
        """Handle analysis progress updates."""
        self.lbl_status.setText(status)
    
    def _on_analysis_finished(self, analysis_result: dict):
        """Handle analysis completion."""
        self.btn_run.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.model_combo.setEnabled(True)
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

        self.results_text.setPlainText("\n".join(output_lines))
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
    
    def _save_analysis_to_database(self, display_content, parsed_json: dict):
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
        """Start metadata enrichment process."""
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

    def _on_metadata_progress(self, status: str, current: int, total: int):
        """Handle metadata lookup progress updates."""
        self.lbl_status.setText(status)
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

    def _on_metadata_finished(self, canonical_db: dict):
        """Handle metadata lookup completion."""
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

        self.metadata_output.setPlainText("\n".join(lines))
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
            logger.error(f"Failed to save canonical metadata: {e}")

        QMessageBox.information(
            self,
            "Metadata Complete",
            f"Metadata enrichment complete!\n\n"
            f"Movies: {len(canonical_db.get('movies', []))}\n"
            f"TV Shows: {len(canonical_db.get('tv_shows', []))}\n"
            f"Multi-part episodes: {len(multi_part)}",
        )

    def _on_metadata_error(self, error_msg: str):
        """Handle metadata lookup errors."""
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


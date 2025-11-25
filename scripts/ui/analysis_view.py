#!/usr/bin/env python3
"""
Analysis View - Unified analysis workflow with folder-to-file extrapolation.

Redesigned per analysis-tab-redesign.plan.md:
- Single scrollable view with collapsible sections (not tabs)
- Section 1: Source Data - folder structure preview
- Section 2: Analysis Controls - mode selector, buttons
- Section 3: Analysis Output - LLM results, detected media
- Section 4: Extrapolated Actions Table - color-coded file operations
- Section 5: Snapshot & Metadata - pre-operation safety, TMDB enrichment

Key feature: ExtrapolationEngine converts folder-level LLM suggestions to file-level actions.
"""

import logging
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QMessageBox, QGroupBox, QProgressBar, QScrollArea,
    QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QFrame, QSplitter, QApplication,
    QTabWidget, QStatusBar
)
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtCore import Qt, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.core.file_scanner import FileScanner, FileRecord
from scripts.core.inventory_repository import InventoryRepository
from scripts.core.roundup_manager import RoundUpManager
from scripts.core.action_plan import ProposedOperation, ActionType, Confidence
from scripts.core.extrapolation_engine import ExtrapolationEngine
from scripts.ai.ravenmaven_client import PoeClient
from scripts.core.workers import LLMAnalysisWorker, MetadataLookupWorker
from scripts.core.regex_analysis_worker import RegexAnalysisWorker, HybridAnalysisWorker
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer

logger = logging.getLogger(__name__)


# Color scheme for confidence levels (per user spec Point 5)
CONFIDENCE_COLORS = {
    Confidence.HIGH: QColor(144, 238, 144),      # Green - Auto-safe
    Confidence.MEDIUM: QColor(255, 255, 150),    # Yellow - Review recommended
    Confidence.LOW: QColor(255, 200, 100),       # Orange - Manual decision needed
    Confidence.MANUAL: QColor(255, 150, 150),    # Red - Cannot process
    Confidence.NONE: QColor(173, 216, 230),      # Blue - No action needed
}


class CollapsibleSection(QGroupBox):
    """A QGroupBox that can be collapsed/expanded by clicking the title."""
    
    def __init__(self, title: str, parent=None, initially_collapsed: bool = False):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(not initially_collapsed)
        self.toggled.connect(self._on_toggled)
        self._content_widget = None
        
    def setContentWidget(self, widget: QWidget):
        """Set the content widget that will be shown/hidden."""
        self._content_widget = widget
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(widget)
        self.setLayout(layout)
        self._on_toggled(self.isChecked())
    
    def _on_toggled(self, checked: bool):
        """Handle collapse/expand."""
        if self._content_widget:
            self._content_widget.setVisible(checked)


class AnalysisView(QWidget):
    """
    Analysis View - Unified workflow from folder analysis to file-level actions.
    
    Flow:
    1. Show folder structure (what LLM/Regex will see)
    2. Run analysis (LLM/Regex/Hybrid)
    3. Extrapolate folder-level changes to file-level operations
    4. Display color-coded actions table for user review
    5. Optional metadata enrichment and snapshots
    """
    
    # Signals notify Studio when data is saved
    analysis_saved = pyqtSignal(int)
    metadata_built = pyqtSignal(int)
    send_to_review = pyqtSignal(list)  # Emit extrapolated operations to ReviewView

    def __init__(
        self, 
        project: Project, 
        project_manager: ProjectManager, 
        parent=None, 
        filtered_files: List[FileRecord] = None, 
        filter_config: dict = None
    ):
        """Initialize the Analysis View."""
        try:
            super().__init__(parent)
            
            self.project = project
            self.project_manager = project_manager
            self.inventory_repo = InventoryRepository()
            
            # State variables
            self.current_analysis_id = None
            self.analysis_results = None
            self.folder_structure = None
            self.scanned_files = []
            self.extrapolated_operations: List[ProposedOperation] = []
            self.detected_media = []
            self.canonical_database = None
            
            # Handle filtered data from ScanResultsView
            self.filtered_files = filtered_files
            self.filter_config = filter_config
            self.using_filtered_data = bool(filtered_files)
            
            # Workers
            self.analysis_worker = None
            self.metadata_worker = None
            
            self._init_ui()
            
            # Load data
            if self.using_filtered_data:
                self._use_filtered_data()
            else:
                self._load_scan_data()
            
            logger.info(f"AnalysisView initialized (filtered={self.using_filtered_data})")
            
        except Exception as e:
            logger.error(f"Failed to initialize AnalysisView: {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize: {e}")
            raise
    
    def _init_ui(self):
        """Build the UI with sub-tabs for better organization."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title
        title = QLabel("Analysis")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("padding: 12px; background: transparent;")
        main_layout.addWidget(title)
        
        # Sub-tabs for better organization
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setDocumentMode(True)
        
        # Tab 1: Setup - Source Data + Analysis Controls
        setup_tab = self._create_setup_tab()
        self.sub_tabs.addTab(setup_tab, "⚙️ Setup")
        
        # Tab 2: Results - Analysis Output + Extrapolated Actions
        results_tab = self._create_results_tab()
        self.sub_tabs.addTab(results_tab, "📊 Results")
        
        # Tab 3: Safety - Snapshots & Metadata
        safety_tab = self._create_safety_tab()
        self.sub_tabs.addTab(safety_tab, "🔒 Safety")
        
        main_layout.addWidget(self.sub_tabs, 1)
    
    def _create_setup_tab(self) -> QWidget:
        """Create the Setup tab with Source Data and Analysis Controls."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Source Data section
        self._create_source_data_section(layout)
        
        # Analysis Controls section
        self._create_controls_section(layout)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab
    
    def _create_results_tab(self) -> QWidget:
        """Create the Results tab with Analysis Output and Actions Table."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Analysis Output section
        self._create_output_section(layout)
        
        # Extrapolated Actions Table section
        self._create_actions_table_section(layout)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab
    
    def _create_safety_tab(self) -> QWidget:
        """Create the Safety tab with Snapshots & Metadata."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Snapshot & Metadata section
        self._create_snapshot_metadata_section(layout)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    def _create_source_data_section(self, parent_layout: QVBoxLayout):
        """Section 1: Folder structure preview - what the LLM will see."""
        section = CollapsibleSection("📁 Source Data (What Analysis Will See)", initially_collapsed=True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Info label
        self.source_info_label = QLabel("Load scan data to preview folder structure")
        self.source_info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.source_info_label)
        
        # Folder structure tree
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["Folder", "Files", "Size", "Types"])
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.setMaximumHeight(200)
        layout.addWidget(self.folder_tree)
        
        section.setContentWidget(content)
        parent_layout.addWidget(section)
        self.source_section = section

    def _create_controls_section(self, parent_layout: QVBoxLayout):
        """Section 2: Analysis controls - mode, model, buttons."""
        group = QGroupBox("⚙️ Analysis Controls")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Row 1: Mode and Model selection
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "🤖 LLM Analysis (Deep, Canonical, API Cost)",
            "⚡ Regex Analysis (Instant, Free, Offline)",
            "🔀 Hybrid (Regex + LLM for Ambiguous)"
        ])
        self.mode_combo.setToolTip(
            "LLM: Uses AI to understand context and suggest canonical naming\n"
            "Regex: Fast pattern matching, free, works offline\n"
            "Hybrid: Best of both - regex first, LLM for ambiguous cases"
        )
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        row1.addWidget(self.mode_combo, 2)
        
        row1.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Grok-4.1-Fast-Reasoning", "GPT-4", "Gemini-2.5-Pro"])
        row1.addWidget(self.model_combo, 1)
        
        self.btn_refresh_models = QPushButton("🔄")
        self.btn_refresh_models.setToolTip("Refresh available models from Poe API")
        self.btn_refresh_models.setMaximumWidth(40)
        self.btn_refresh_models.clicked.connect(self._refresh_models)
        row1.addWidget(self.btn_refresh_models)
        
        layout.addLayout(row1)
        
        # Row 2: Action buttons
        row2 = QHBoxLayout()
        
        self.btn_preview = QPushButton("👁️ Preview Prompt")
        self.btn_preview.setToolTip("See the exact prompt that will be sent to the LLM")
        self.btn_preview.clicked.connect(self._preview_prompt)
        row2.addWidget(self.btn_preview)
        
        self.btn_run = QPushButton("▶️ Run Analysis")
        self.btn_run.setToolTip("Execute analysis using selected mode")
        self.btn_run.setStyleSheet("font-weight: bold;")
        self.btn_run.clicked.connect(self._run_analysis)
        row2.addWidget(self.btn_run)
        
        self.btn_snapshot = QPushButton("📸 Create Snapshot")
        self.btn_snapshot.setToolTip("Create a pre-operation snapshot for rollback capability")
        self.btn_snapshot.clicked.connect(self._create_snapshot)
        row2.addWidget(self.btn_snapshot)
        
        row2.addStretch()
        layout.addLayout(row2)
        
        # Token estimate (updated when data loads)
        self.lbl_token_estimate = QLabel("📊 Token estimate: N/A (load scan data)")
        self.lbl_token_estimate.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.lbl_token_estimate)
        
        # Progress bar and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-style: italic;")
        layout.addWidget(self.status_label)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
        # Initial state
        self._on_mode_changed()

    def _create_output_section(self, parent_layout: QVBoxLayout):
        """Section 3: Analysis output - detected media, folder changes."""
        section = CollapsibleSection("📊 Analysis Output", initially_collapsed=True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Detected media summary
        self.detected_media_label = QLabel("Run analysis to see detected media")
        self.detected_media_label.setStyleSheet("color: #888;")
        layout.addWidget(self.detected_media_label)
        
        # Raw output text (for LLM reasoning)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(150)
        self.output_text.setPlaceholderText("Analysis output will appear here...")
        layout.addWidget(self.output_text)
        
        section.setContentWidget(content)
        parent_layout.addWidget(section)
        self.output_section = section

    def _create_actions_table_section(self, parent_layout: QVBoxLayout):
        """Section 4: Color-coded extrapolated actions table (main content)."""
        group = QGroupBox("📋 Extrapolated File Actions")
        layout = QVBoxLayout()
        
        # Stats bar
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Run analysis to generate file-level actions")
        self.stats_label.setStyleSheet("color: #888;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        # Legend
        legend = QHBoxLayout()
        legend.addWidget(QLabel("Legend:"))
        for conf, color in [
            (Confidence.HIGH, "green"), 
            (Confidence.MEDIUM, "yellow"),
            (Confidence.LOW, "orange"),
            (Confidence.MANUAL, "red"),
            (Confidence.NONE, "lightblue")
        ]:
            lbl = QLabel(f"● {conf.name}")
            lbl.setStyleSheet(f"color: {color};")
            legend.addWidget(lbl)
        legend.addStretch()
        stats_layout.addLayout(legend)
        layout.addLayout(stats_layout)
        
        # Actions table
        self.actions_table = QTableWidget()
        self.actions_table.setColumnCount(7)
        self.actions_table.setHorizontalHeaderLabels([
            "Status", "Original Path", "Proposed Path", "Action", "Subtitles", "Confidence", "Notes"
        ])
        self.actions_table.setAlternatingRowColors(True)
        self.actions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.actions_table.setSortingEnabled(True)
        self.actions_table.horizontalHeader().setStretchLastSection(True)
        self.actions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.actions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.actions_table, 1)
        
        # Bulk operations bar
        bulk_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(lambda: self.actions_table.selectAll())
        bulk_layout.addWidget(self.btn_select_all)
        
        self.btn_approve_selected = QPushButton("✓ Approve Selected")
        self.btn_approve_selected.clicked.connect(self._approve_selected)
        bulk_layout.addWidget(self.btn_approve_selected)
        
        self.btn_reject_selected = QPushButton("✗ Reject Selected")
        self.btn_reject_selected.clicked.connect(self._reject_selected)
        bulk_layout.addWidget(self.btn_reject_selected)
        
        bulk_layout.addStretch()
        
        self.btn_send_to_review = QPushButton("➡️ Send to Review")
        self.btn_send_to_review.setToolTip("Send approved operations to Review tab for final confirmation")
        self.btn_send_to_review.setStyleSheet("font-weight: bold;")
        self.btn_send_to_review.clicked.connect(self._send_to_review)
        self.btn_send_to_review.setEnabled(False)
        bulk_layout.addWidget(self.btn_send_to_review)
        
        layout.addLayout(bulk_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group, 1)

    def _create_snapshot_metadata_section(self, parent_layout: QVBoxLayout):
        """Section 5: Snapshot management and metadata enrichment."""
        section = CollapsibleSection("🔒 Snapshots & Metadata", initially_collapsed=True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Snapshot info
        snapshot_row = QHBoxLayout()
        self.snapshot_label = QLabel("No snapshots created")
        self.snapshot_label.setStyleSheet("color: #888;")
        snapshot_row.addWidget(self.snapshot_label)
        snapshot_row.addStretch()
        
        self.btn_restore_snapshot = QPushButton("↩️ Restore Latest")
        self.btn_restore_snapshot.setEnabled(False)
        self.btn_restore_snapshot.clicked.connect(self._restore_snapshot)
        snapshot_row.addWidget(self.btn_restore_snapshot)
        layout.addLayout(snapshot_row)
        
        # Metadata enrichment
        meta_row = QHBoxLayout()
        self.btn_enrich = QPushButton("✨ Enrich with TMDB/TVDB")
        self.btn_enrich.setToolTip("Query canonical metadata databases for official titles, years, episode info")
        self.btn_enrich.clicked.connect(self._enrich_metadata)
        self.btn_enrich.setEnabled(False)
        meta_row.addWidget(self.btn_enrich)
        
        self.metadata_status = QLabel("")
        meta_row.addWidget(self.metadata_status)
        meta_row.addStretch()
        layout.addLayout(meta_row)
        
        section.setContentWidget(content)
        parent_layout.addWidget(section)
        self.snapshot_section = section

    # =========================================================================
    # Data Loading
    # =========================================================================
    
    def _load_scan_data(self):
        """Load scan data from the Round-Up database."""
        try:
            # Check if using Round-Up system
            if hasattr(self.project, 'roundup') and self.project.roundup:
                self._load_from_roundup()
            else:
                # Legacy fallback for old project system
                self._load_from_legacy_db()
                
        except Exception as e:
            logger.error(f"Error loading scan data: {e}", exc_info=True)
            self._set_status(f"Error loading scan data: {e}", error=True)
    
    def _load_from_roundup(self):
        """Load scan data from Round-Up database."""
        roundup = self.project.roundup
        manager = self.project.manager if hasattr(self.project, 'manager') else RoundUpManager()
        
        # Get scan files from Round-Up
        scan_file_dicts = manager.get_scan_files(roundup)
        
        if not scan_file_dicts:
            self._set_status("No scan data found. Please run a scan first.", error=True)
            self.btn_run.setEnabled(False)
            return
        
        # Convert dicts to FileRecord-like objects for folder structure
        self.scanned_files = []
        for file_dict in scan_file_dicts:
            # Create a simple object that has the attributes needed by get_folder_structure
            file_record = FileRecord(
                absolute_path=Path(file_dict['path']),
                relative_path=Path(file_dict['relative_path']) if file_dict.get('relative_path') else None,
                size_bytes=file_dict.get('size_bytes', 0),
                extension=file_dict.get('extension', ''),
                md5_hash=file_dict.get('md5_hash'),
                created_at=file_dict.get('created_at'),
                modified_at=file_dict.get('modified_at')
            )
            self.scanned_files.append(file_record)
        
        # Build folder structure
        scanner = FileScanner()
        self.folder_structure = scanner.get_folder_structure(self.scanned_files)
        self.folder_structure['project_name'] = self.project.name
        self.folder_structure['total_files'] = len(self.scanned_files)
        
        # Count unique folders
        metadata_keys = {'project_name', 'scan_id', 'total_files'}
        folder_count = sum(1 for k in self.folder_structure.keys() if k not in metadata_keys)
        
        self._update_source_data_display()
        self._update_token_estimate()
        self._set_status(f"✓ Ready: {len(self.scanned_files)} files from {folder_count} folder(s)", success=True)
        self.btn_run.setEnabled(True)
        self.btn_preview.setEnabled(True)
        
        logger.info(f"Loaded {len(self.scanned_files)} files from Round-Up '{roundup.name}'")
    
    def _load_from_legacy_db(self):
        """Load scan data from legacy media_library.db (fallback)."""
        conn = sqlite3.connect("data/media_library.db")
        cursor = conn.cursor()
        
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

            if self.scanned_files:
                scanner = FileScanner()
                self.folder_structure = scanner.get_folder_structure(self.scanned_files)
                self.folder_structure['project_name'] = self.project.name
                self.folder_structure['scan_id'] = scan_id
                self.folder_structure['total_files'] = len(self.scanned_files)
                
                self._update_source_data_display()
                self._update_token_estimate()
                self._set_status(f"Ready: {len(self.scanned_files)} files from {len(folders)} folder(s)")
                self.btn_run.setEnabled(True)
                self.btn_preview.setEnabled(True)
            else:
                self._set_status("Scan data found but inventory unavailable. Please run a new scan.", error=True)
                self.btn_run.setEnabled(False)
        else:
            self._set_status("No scan data found. Please run a scan first.", error=True)
            self.btn_run.setEnabled(False)
        
        conn.close()
    
    def _use_filtered_data(self):
        """Use filtered data from ScanResultsView."""
        if not self.filtered_files:
            return
        
        self.scanned_files = self.filtered_files
        
        scanner = FileScanner()
        self.folder_structure = scanner.get_folder_structure(self.scanned_files)
        self.folder_structure['project_name'] = self.project.name
        self.folder_structure['total_files'] = len(self.scanned_files)
        
        # Build filter description
        filter_desc = []
        if self.filter_config:
            file_types = self.filter_config.get('file_types', {})
            enabled = [k for k, v in file_types.items() if v]
            if enabled and len(enabled) < 4:
                filter_desc.append(f"Types: {', '.join(enabled)}")
            if self.filter_config.get('hide_duplicates'):
                filter_desc.append("No duplicates")
        
        filter_text = f" ({', '.join(filter_desc)})" if filter_desc else ""
        
        self._update_source_data_display()
        self._update_token_estimate()
        self._set_status(f"✓ Ready: {len(self.scanned_files)} filtered files{filter_text}", success=True)
        self.btn_run.setEnabled(True)
        self.btn_preview.setEnabled(True)
            
    def _update_source_data_display(self):
        """Update the folder structure tree display."""
        self.folder_tree.clear()
        
        if not self.folder_structure:
            return
            
        total_files = 0
        total_size = 0
        
        # Filter out metadata keys and normalize Path keys to strings for sorting
        metadata_keys = {'project_name', 'scan_id', 'total_files'}
        folder_items = [
            (folder_path, data)
            for folder_path, data in self.folder_structure.items()
            if folder_path not in metadata_keys and isinstance(data, dict)
        ]
        
        # Sort by string representation of folder path (handles both Path and str)
        for folder_path, data in sorted(folder_items, key=lambda x: str(x[0])):
                
            file_count = data.get('file_count', 0)
            size_bytes = data.get('total_size', 0)
            file_types = data.get('file_types', {})
            
            total_files += file_count
            total_size += size_bytes
            
            # Format size
            size_mb = size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.1f} GB"
            
            # Format types
            types_str = ", ".join([f"{ext}: {cnt}" for ext, cnt in list(file_types.items())[:3]])
            
            item = QTreeWidgetItem([
                str(folder_path),
                str(file_count),
                size_str,
                types_str
            ])
            self.folder_tree.addTopLevelItem(item)
        
        # Update info label
        total_gb = total_size / (1024**3)
        self.source_info_label.setText(
            f"Total: {total_files} files, {total_gb:.1f} GB across "
            f"{self.folder_tree.topLevelItemCount()} folders"
        )
        
        # Update token estimate when source data changes
        self._update_token_estimate()

    def _estimate_tokens(self) -> tuple:
        """
        Estimate token count for the LLM prompt.
        
        Uses chars // 4 formula (same as generate_docstrings_with_llm.py).
        
        Returns:
            Tuple of (estimated_tokens, char_count, folder_count)
        """
        if not self.folder_structure:
            return (0, 0, 0)
        
        try:
            analyzer = LLMStructureAnalyzer()
            prompt = analyzer._build_analysis_prompt(self.folder_structure)
            char_count = len(prompt)
            estimated_tokens = char_count // 4
            
            # Count folders (excluding metadata keys)
            metadata_keys = {'project_name', 'scan_id', 'total_files'}
            folder_count = sum(
                1 for k in self.folder_structure.keys()
                if k not in metadata_keys and isinstance(self.folder_structure.get(k), dict)
            )
            
            return (estimated_tokens, char_count, folder_count)
        except Exception as e:
            logger.warning(f"Token estimation failed: {e}")
            return (0, 0, 0)
    
    def _update_token_estimate(self):
        """Update the token estimate label with current prompt size."""
        if not hasattr(self, 'lbl_token_estimate'):
            return
            
        tokens, chars, folders = self._estimate_tokens()
        
        if tokens == 0:
            self.lbl_token_estimate.setText("Token estimate: N/A (no data)")
            self.lbl_token_estimate.setStyleSheet("color: #888; font-style: italic;")
            return
        
        # Format size
        if chars >= 1_000_000:
            size_str = f"{chars / 1_000_000:.1f} MB"
        elif chars >= 1_000:
            size_str = f"{chars / 1_000:.1f} KB"
        else:
            size_str = f"{chars} bytes"
        
        text = f"📊 ~{tokens:,} tokens ({size_str}) • {folders:,} folders"
        
        # Warning color if exceeds 100K tokens (large context)
        if tokens > 100_000:
            self.lbl_token_estimate.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            text += " ⚠️ Large prompt - chunking recommended"
        elif tokens > 50_000:
            self.lbl_token_estimate.setStyleSheet("color: #ffa500; font-weight: bold;")
            text += " ⚠️ Large prompt"
        else:
            self.lbl_token_estimate.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        self.lbl_token_estimate.setText(text)

    # =========================================================================
    # Analysis Execution
    # =========================================================================
    
    def _on_mode_changed(self):
        """Handle analysis mode change."""
        mode_text = self.mode_combo.currentText()
        is_llm = "LLM" in mode_text or "Hybrid" in mode_text
        
        self.model_combo.setEnabled(is_llm)
        self.btn_refresh_models.setEnabled(is_llm)
        self.btn_preview.setEnabled(is_llm)

    def _refresh_models(self):
        """Refresh available LLM models from Poe API."""
        try:
            self._set_status("Fetching models...")
            client = PoeClient()
            models = client.get_available_models()
            
            if models:
                self.model_combo.clear()
                self.model_combo.addItems(models)
                self._set_status(f"Loaded {len(models)} models")
            else:
                self._set_status("No models available")
        except Exception as e:
            logger.error(f"Model refresh error: {e}", exc_info=True)
            QMessageBox.warning(self, "Model Refresh Failed", f"Could not fetch models:\n{e}")
    
    def _preview_prompt(self):
        """Preview the LLM prompt with human-readable and raw JSON tabs."""
        if not self.folder_structure:
            QMessageBox.warning(self, "No Data", "No scan data available.")
            return
        
        try:
            analyzer = LLMStructureAnalyzer()
            prompt = analyzer._build_analysis_prompt(self.folder_structure)
            
            # Calculate stats
            char_count = len(prompt)
            token_estimate = char_count // 4
            metadata_keys = {'project_name', 'scan_id', 'total_files'}
            folder_count = sum(
                1 for k in self.folder_structure.keys()
                if k not in metadata_keys and isinstance(self.folder_structure.get(k), dict)
            )
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Prompt Preview")
            dialog.resize(900, 700)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Tab widget for Human-Readable vs Raw JSON
            tab_widget = QTabWidget()
            
            # Tab 1: Human-Readable Summary
            human_tab = QWidget()
            human_layout = QVBoxLayout(human_tab)
            human_layout.setContentsMargins(8, 8, 8, 8)
            
            summary_label = QLabel(
                f"<b>Analysis will process {folder_count:,} folders</b><br>"
                f"Estimated tokens: ~{token_estimate:,} | Characters: {char_count:,}"
            )
            human_layout.addWidget(summary_label)
            
            # Folder table (human-readable)
            folder_table = QTableWidget()
            folder_table.setColumnCount(4)
            folder_table.setHorizontalHeaderLabels(["Folder Path", "Files", "Size", "File Types"])
            folder_table.setAlternatingRowColors(True)
            folder_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            folder_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            folder_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            
            # Populate folder table
            folder_items = [
                (k, v) for k, v in self.folder_structure.items()
                if k not in metadata_keys and isinstance(v, dict)
            ]
            folder_table.setRowCount(len(folder_items))
            
            for row, (folder_path, data) in enumerate(sorted(folder_items, key=lambda x: str(x[0]))):
                file_count = data.get('file_count', 0)
                size_bytes = data.get('total_size', 0)
                file_types = data.get('file_types', {})
                
                # Format size
                size_mb = size_bytes / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.1f} GB"
                
                # Format types
                types_list = [f"{ext}: {cnt}" for ext, cnt in list(file_types.items())[:5]]
                types_str = ", ".join(types_list)
                if len(file_types) > 5:
                    types_str += f" (+{len(file_types) - 5} more)"
                
                folder_table.setItem(row, 0, QTableWidgetItem(str(folder_path)))
                folder_table.setItem(row, 1, QTableWidgetItem(str(file_count)))
                folder_table.setItem(row, 2, QTableWidgetItem(size_str))
                folder_table.setItem(row, 3, QTableWidgetItem(types_str))
            
            human_layout.addWidget(folder_table)
            tab_widget.addTab(human_tab, "📋 Summary (Human-Readable)")
            
            # Tab 2: Raw JSON Prompt
            raw_tab = QWidget()
            raw_layout = QVBoxLayout(raw_tab)
            raw_layout.setContentsMargins(8, 8, 8, 8)
            
            raw_info = QLabel("Full JSON prompt that will be sent to the LLM:")
            raw_layout.addWidget(raw_info)
            
            text = QTextEdit()
            text.setReadOnly(True)
            text.setPlainText(prompt)
            text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;")
            raw_layout.addWidget(text)
            
            tab_widget.addTab(raw_tab, "🔧 Raw JSON Prompt")
            
            layout.addWidget(tab_widget, 1)
            
            # Buttons
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(8, 8, 8, 8)
            
            btn_copy = QPushButton("📋 Copy Prompt")
            btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(prompt))
            buttons_layout.addWidget(btn_copy)
            
            buttons_layout.addStretch()
            
            btn_close = QPushButton("Close")
            btn_close.clicked.connect(dialog.close)
            buttons_layout.addWidget(btn_close)
            
            layout.addLayout(buttons_layout)
            
            # Status bar at bottom
            status_bar = QStatusBar()
            status_text = f"~{token_estimate:,} tokens  |  {char_count:,} characters  |  {folder_count:,} folders"
            if token_estimate > 100_000:
                status_text += "  |  ⚠️ Large prompt - consider chunking"
                status_bar.setStyleSheet("background: #ffcccc;")
            elif token_estimate > 50_000:
                status_text += "  |  ⚠️ Large prompt"
                status_bar.setStyleSheet("background: #fff3cd;")
            status_bar.showMessage(status_text)
            layout.addWidget(status_bar)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Preview prompt error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate prompt:\n{e}")
    
    def _run_analysis(self):
        """Execute analysis using selected mode."""
        if not self.folder_structure:
            QMessageBox.warning(self, "No Data", "No scan data available.")
            return
        
        # Determine mode
        mode_text = self.mode_combo.currentText()
        if "LLM" in mode_text and "Hybrid" not in mode_text:
            mode = "llm"
        elif "Regex" in mode_text:
            mode = "regex"
        else:
            mode = "hybrid"
        
        model = self.model_combo.currentText()
        total = self.folder_structure.get('total_files', len(self.scanned_files))
        
        # Confirmation
        if mode == "llm":
            msg = f"Run LLM analysis with {model}?\n\nFiles: {total}\nTime: 30-60s\nCost: API charges"
        elif mode == "regex":
            msg = f"Run Regex analysis?\n\nFiles: {total}\nTime: <1s\nCost: FREE"
        else:
            msg = f"Run Hybrid analysis?\n\nFiles: {total}\nPhase 1: Regex (free)\nPhase 2: LLM for ambiguous"
        
        if QMessageBox.question(self, "Run Analysis", msg) != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI
        self._set_controls_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
            
        # Create worker
        try:
            if mode == "llm":
                self.analysis_worker = LLMAnalysisWorker(
                    folder_structure=self.folder_structure,
                    scanned_files=self.scanned_files,
                    model=model
                )
            elif mode == "regex":
                self.analysis_worker = RegexAnalysisWorker(
                    scanned_files=self.scanned_files
                )
            else:
                self.analysis_worker = HybridAnalysisWorker(
                    scanned_files=self.scanned_files,
                    folder_structure=self.folder_structure,
                    model=model
                )
            
            self.analysis_worker.progress.connect(self._on_analysis_progress)
            self.analysis_worker.finished.connect(self._on_analysis_finished)
            self.analysis_worker.error.connect(self._on_analysis_error)
            self.analysis_worker.start()
            
            logger.info(f"Started {mode} analysis")
            
        except Exception as e:
            logger.error(f"Failed to start analysis: {e}", exc_info=True)
            self._set_controls_enabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to start analysis:\n{e}")
    
    def _on_analysis_progress(self, status: str):
        """Handle progress updates."""
        self._set_status(status)

    def _on_analysis_finished(self, result: dict):
        """Handle analysis completion - run extrapolation."""
        self._set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        self.analysis_results = result
        self.detected_media = result.get('detected_media', [])
        
        # Update output section
        self._update_output_display(result)
        
        # Run extrapolation
        self._set_status("Extrapolating folder changes to file-level actions...")
        try:
            engine = ExtrapolationEngine(self.scanned_files)
            self.extrapolated_operations = engine.extrapolate(
                result.get('reorganization_plan', {}),
                self.detected_media
            )
            
            # Populate table
            self._populate_actions_table()
            
            # Save to database
            self._save_analysis_to_database(result)
            
            # Enable downstream actions
            self.btn_enrich.setEnabled(True)
            self.btn_send_to_review.setEnabled(len(self.extrapolated_operations) > 0)
            
            stats = engine.get_statistics()
            self._set_status(
                f"Analysis complete: {stats['total_files']} files, "
                f"{stats['move']} moves, {stats['review']} need review",
                success=True
            )
            
            # Expand output section
            self.output_section.setChecked(True)
            
        except Exception as e:
            logger.error(f"Extrapolation failed: {e}", exc_info=True)
            self._set_status(f"Extrapolation failed: {e}", error=True)

    def _on_analysis_error(self, error: str):
        """Handle analysis error."""
        self._set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        self._set_status(f"Analysis failed: {error}", error=True)
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed:\n{error}")

    def _update_output_display(self, result: dict):
        """Update the analysis output section."""
        # Detected media summary
        movies = [m for m in self.detected_media if m.get('type') == 'movie']
        shows = [m for m in self.detected_media if m.get('type') == 'tv_show']
        
        self.detected_media_label.setText(
            f"Detected: {len(movies)} movies, {len(shows)} TV shows, "
            f"{len(self.detected_media) - len(movies) - len(shows)} other"
        )
        self.detected_media_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        # Raw output/reasoning
        lines = []
        lines.append("=" * 60)
        lines.append("ANALYSIS RESULTS")
        lines.append("=" * 60)
        
        for media in self.detected_media[:5]:
            mtype = media.get('type', '?').upper()
            title = media.get('title', 'Unknown')
            year = media.get('year_estimate', '?')
            lines.append(f"[{mtype}] {title} ({year})")
        
        if len(self.detected_media) > 5:
            lines.append(f"... and {len(self.detected_media) - 5} more")
        
        lines.append("")
        lines.append("REORGANIZATION PLAN:")
        plan = result.get('reorganization_plan', {})
        lines.append(plan.get('summary', 'No summary'))
        
        lines.append("")
        lines.append("REASONING:")
        lines.append(result.get('reasoning', 'No reasoning provided'))
        
        self.output_text.setPlainText("\n".join(lines))

    # =========================================================================
    # Actions Table
    # =========================================================================
    
    def _populate_actions_table(self):
        """Populate the color-coded actions table."""
        self.actions_table.setRowCount(len(self.extrapolated_operations))
        
        for row, op in enumerate(self.extrapolated_operations):
            # Status checkbox
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(
                Qt.CheckState.Checked if op.user_approved is not False else Qt.CheckState.Unchecked
            )
            self.actions_table.setItem(row, 0, checkbox)
            
            # Original path
            src_item = QTableWidgetItem(str(op.source_path))
            self.actions_table.setItem(row, 1, src_item)
            
            # Proposed path
            dest_str = str(op.destination_path) if op.destination_path else "-"
            dest_item = QTableWidgetItem(dest_str)
            self.actions_table.setItem(row, 2, dest_item)
            
            # Action
            action_item = QTableWidgetItem(op.action_type.name)
            self.actions_table.setItem(row, 3, action_item)
            
            # Subtitles (from notes)
            subs = "Yes" if "Subtitle" in op.notes else "-"
            subs_item = QTableWidgetItem(subs)
            self.actions_table.setItem(row, 4, subs_item)
            
            # Confidence
            conf_item = QTableWidgetItem(op.confidence.name)
            self.actions_table.setItem(row, 5, conf_item)
            
            # Notes
            notes_item = QTableWidgetItem(op.notes)
            self.actions_table.setItem(row, 6, notes_item)
            
            # Apply row color based on confidence
            color = CONFIDENCE_COLORS.get(op.confidence, QColor(255, 255, 255))
            for col in range(self.actions_table.columnCount()):
                item = self.actions_table.item(row, col)
                if item:
                    item.setBackground(QBrush(color))
        
        # Update stats
        stats = self._calculate_table_stats()
        self.stats_label.setText(
            f"Total: {stats['total']} | "
            f"Move: {stats['move']} | Skip: {stats['skip']} | Review: {stats['review']} | "
            f"High: {stats['high']} | Medium: {stats['medium']} | Low: {stats['low']}"
        )
        self.stats_label.setStyleSheet("")

    def _calculate_table_stats(self) -> Dict[str, int]:
        """Calculate statistics from operations."""
        stats = {'total': 0, 'move': 0, 'skip': 0, 'review': 0, 'delete': 0,
                 'high': 0, 'medium': 0, 'low': 0}
        
        for op in self.extrapolated_operations:
            stats['total'] += 1
            stats[op.action_type.name.lower()] = stats.get(op.action_type.name.lower(), 0) + 1
            stats[op.confidence.name.lower()] = stats.get(op.confidence.name.lower(), 0) + 1
        
        return stats

    def _approve_selected(self):
        """Approve selected rows."""
        for row in self.actions_table.selectionModel().selectedRows():
            item = self.actions_table.item(row.row(), 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
                if row.row() < len(self.extrapolated_operations):
                    self.extrapolated_operations[row.row()].user_approved = True

    def _reject_selected(self):
        """Reject selected rows."""
        for row in self.actions_table.selectionModel().selectedRows():
            item = self.actions_table.item(row.row(), 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
                if row.row() < len(self.extrapolated_operations):
                    self.extrapolated_operations[row.row()].user_approved = False

    def _send_to_review(self):
        """Send approved operations to ReviewView."""
        approved = []
        for row in range(self.actions_table.rowCount()):
            item = self.actions_table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                if row < len(self.extrapolated_operations):
                    approved.append(self.extrapolated_operations[row])
        
        if not approved:
            QMessageBox.warning(self, "No Selection", "No operations are approved. Check the boxes to approve.")
            return
        
        reply = QMessageBox.question(
            self, "Send to Review",
            f"Send {len(approved)} approved operations to Review tab?\n\n"
            "You can make final adjustments there before execution."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.send_to_review.emit(approved)
            self._set_status(f"Sent {len(approved)} operations to Review", success=True)

    # =========================================================================
    # Snapshot & Metadata
    # =========================================================================
    
    def _create_snapshot(self):
        """Create a pre-operation snapshot using SnapshotManager."""
        try:
            from scripts._common.snapshot_manager import SnapshotManager
            
            if not self.scanned_files:
                QMessageBox.warning(self, "No Data", "No files to snapshot.")
                return
            
            # Get root folder from scanned files
            roots = set(f.parent_folder for f in self.scanned_files[:10])
            if not roots:
                QMessageBox.warning(self, "No Data", "Cannot determine media root.")
                return
            
            # Use common parent
            root = Path(list(roots)[0])
            while root.parent != root:
                if all(str(r).startswith(str(root)) for r in roots):
                    break
                root = root.parent
            
            self._set_status(f"Creating snapshot of {root}...")
            
            snapshot_id = SnapshotManager.create_snapshot(
                media_root=str(root),
                snapshot_type="pre_analysis"
            )
            
            self.snapshot_label.setText(f"Latest snapshot: {snapshot_id[:20]}...")
            self.snapshot_label.setStyleSheet("color: #2ecc71;")
            self.btn_restore_snapshot.setEnabled(True)
            
            self._set_status(f"Snapshot created: {snapshot_id}", success=True)
            
        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Snapshot Error", f"Failed to create snapshot:\n{e}")

    def _restore_snapshot(self):
        """Restore from the most recent snapshot."""
        try:
            from scripts._common.snapshot_manager import SnapshotManager
            
            reply = QMessageBox.question(
                self, "Restore Snapshot",
                "Restore files to their state before the last snapshot?\n\n"
                "This will undo any file operations since the snapshot."
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Get latest snapshot
            snapshots = SnapshotManager.list_snapshots()
            if not snapshots:
                QMessageBox.warning(self, "No Snapshots", "No snapshots available to restore.")
                return
            
            latest = snapshots[0]
            self._set_status(f"Restoring snapshot {latest}...")
            
            SnapshotManager.restore_snapshot(latest)
            
            self._set_status("Snapshot restored successfully", success=True)
            
        except Exception as e:
            logger.error(f"Snapshot restore failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Restore Error", f"Failed to restore snapshot:\n{e}")

    def _enrich_metadata(self):
        """Start metadata enrichment with TMDB/TVDB."""
        if not self.detected_media:
            QMessageBox.warning(self, "No Data", "Run analysis first to detect media.")
            return

        reply = QMessageBox.question(
            self, "Enrich Metadata",
            f"Query TMDB/TVDB for {len(self.detected_media)} detected media items?\n\n"
            "This will resolve official titles, years, and episode info."
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_enrich.setEnabled(False)
        self.progress_bar.setVisible(True)

        try:
            tmdb_key = os.getenv("TMDB_API_KEY")
            omdb_key = os.getenv("OMDB_API_KEY")

            self.metadata_worker = MetadataLookupWorker(
                detected_media=self.detected_media,
                scanned_files=self.scanned_files,
                tmdb_api_key=tmdb_key,
                omdb_api_key=omdb_key
            )
            
            self.metadata_worker.progress.connect(self._on_metadata_progress)
            self.metadata_worker.finished.connect(self._on_metadata_finished)
            self.metadata_worker.error.connect(self._on_metadata_error)
            self.metadata_worker.start()

        except Exception as e:
            self.btn_enrich.setEnabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to start metadata lookup:\n{e}")

    def _on_metadata_progress(self, status: str, current: int, total: int):
        """Handle metadata progress."""
        self._set_status(status)
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)

    def _on_metadata_finished(self, canonical_db: dict):
        """Handle metadata completion."""
        self.btn_enrich.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.canonical_database = canonical_db

        movies = len(canonical_db.get('movies', []))
        shows = len(canonical_db.get('tv_shows', []))
        
        self.metadata_status.setText(f"✓ {movies} movies, {shows} TV shows enriched")
        self.metadata_status.setStyleSheet("color: #2ecc71;")
        
        # Save to database
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE project_analyses SET metadata_json = ? WHERE id = ?
            ''', (json.dumps(canonical_db), self.current_analysis_id))
            conn.commit()
            conn.close()
            
            if self.current_analysis_id:
                self.metadata_built.emit(self.current_analysis_id)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}", exc_info=True)
        
        self._set_status("Metadata enrichment complete", success=True)

    def _on_metadata_error(self, error: str):
        """Handle metadata error."""
        self.btn_enrich.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._set_status(f"Metadata lookup failed: {error}", error=True)
        QMessageBox.critical(self, "Metadata Error", f"Metadata lookup failed:\n{error}")

    # =========================================================================
    # Database
    # =========================================================================
    
    def _save_analysis_to_database(self, result: dict):
        """Save analysis results to database."""
        try:
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            model = self.model_combo.currentText()
            scan_id = self.folder_structure.get('scan_id') if self.folder_structure else None
            
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
                json.dumps(result.get('reasoning', '')),
                json.dumps(result),
                'MEDIUM',
                len(self.extrapolated_operations)
            ))
            
            self.current_analysis_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            if self.current_analysis_id:
                self.analysis_saved.emit(self.current_analysis_id)
                
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}", exc_info=True)

    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _set_status(self, text: str, error: bool = False, success: bool = False):
        """Update status label."""
        self.status_label.setText(text)
        if error:
            self.status_label.setStyleSheet("color: #e74c3c; font-style: italic;")
        elif success:
            self.status_label.setStyleSheet("color: #2ecc71; font-style: italic;")
        else:
            self.status_label.setStyleSheet("font-style: italic;")

    def _set_controls_enabled(self, enabled: bool):
        """Enable/disable controls during operations."""
        self.btn_run.setEnabled(enabled)
        self.btn_preview.setEnabled(enabled)
        self.mode_combo.setEnabled(enabled)
        self.model_combo.setEnabled(enabled and "LLM" in self.mode_combo.currentText())
        self.btn_refresh_models.setEnabled(enabled and "LLM" in self.mode_combo.currentText())
        self.btn_snapshot.setEnabled(enabled)

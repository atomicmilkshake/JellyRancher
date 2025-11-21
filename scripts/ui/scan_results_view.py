#!/usr/bin/env python3
"""
Scan Results View - Dedicated view for reviewing scan results with pre-analysis filtering

Extracted from ScanView to provide focused results review in separate tab.
Displays file table, search/filter, export, folder overview, and duplicate detection.

NEW in Phase 33G-1: Pre-analysis filtering to reduce LLM costs and improve quality
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from collections import defaultdict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QGroupBox, QLineEdit, QMessageBox, QCheckBox,
    QSlider, QSpinBox, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from scripts.core.file_scanner import FileRecord, ScanStatistics
from scripts.core.project_manager import ProjectManager, Project
from scripts.core.inventory_repository import InventoryRepository
import sqlite3
import csv
import json

logger = logging.getLogger(__name__)


class ScanResultsView(QWidget):
    """
    Dedicated view for scan results review with pre-analysis filtering.
    
    Features:
    - Sortable/searchable results table
    - File type filters (Video, Subtitle, Image, Other)
    - Size range filter with slider
    - Duplicate detection filter (MD5)
    - Folder selection tree with checkboxes
    - Export filtered results to CSV
    - Send filtered data to Analysis
    
    Signals:
    - send_to_analysis: Emitted with filtered FileRecord list for analysis
    """
    
    # Signal to send filtered data to analysis
    send_to_analysis = pyqtSignal(list, dict)  # filtered_files, filter_config
    
    def __init__(self, project: Project, project_manager: ProjectManager, scan_session_id: int, parent=None):
        """
        Initialize the ScanResultsView widget.
        
        Creates a comprehensive view for reviewing media scan results with
        sortable tables, filtering, export capabilities, and duplicate detection.
        
        Args:
            project (Project): The current project containing scan configuration
            project_manager (ProjectManager): Manager for project operations
            scan_session_id (int): Database ID of the scan session to display
            parent (QWidget, optional): Parent widget for this view
            
        The initialization process:
        1. Sets up core dependencies (project, manager, repository)
        2. Initializes data structures for files, folders, and duplicates
        3. Creates the UI components with filter controls
        4. Loads scan results from the database
        5. Logs successful initialization
        
        Error Handling:
            If initialization fails, shows critical error dialog and re-raises
            the exception to prevent corrupted UI state.
        
        Data Structures:
            - scanned_files: List of all FileRecord objects from the scan
            - filtered_files: List of FileRecord objects after applying filters
            - folder_structure: Hierarchical dict of folder statistics
            - duplicate_groups: Dict mapping MD5 hashes to duplicate file lists
            - excluded_folders: Set of folder paths to exclude
            - excluded_files: Set of file paths to exclude
        """
        try:
            super().__init__(parent)

            self.project = project
            self.project_manager = project_manager
            self.inventory_repo = InventoryRepository()
            self.scan_session_id = scan_session_id

            self.scanned_files: List[FileRecord] = []
            self.filtered_files: List[FileRecord] = []
            self.folder_structure: Dict[Path, Dict[str, Any]] = {}
            self.duplicate_groups: Dict[str, List[FileRecord]] = {}
            
            # Filter state
            self.excluded_folders: Set[Path] = set()
            self.excluded_files: Set[Path] = set()
            
            # File type categories
            self.video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.ts', '.webm'}
            self.subtitle_extensions = {'.srt', '.sub', '.idx', '.ass', '.ssa', '.vtt'}
            self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

            self._init_ui()
            self._load_scan_results()
            logger.info(f"ScanResultsView initialized for session ID: {scan_session_id}")
        except Exception as e:
            logger.error(f"Failed to initialize ScanResultsView: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize scan results view:\n\n{str(e)}\n\nPlease check the logs for details.",
            )
            raise
    
    def _init_ui(self):
        """
        Initialize UI with sub-tabs for height optimization (Phase 37B).

        Replaces vertical VBox with QTabWidget (Filters | Files | Overview)
        to display one section at a time, reducing height by 60-70%.
        Each tab contains an existing groupbox; tables/trees scroll within tabs.

        Layout: Title + TabWidget (stretch=1).
        Tabs use 8px spacing/12px margins for compactness.
        Preserves all signals, methods, and error handling.
        """
        try:
            # Title (above tabs)
            title = QLabel(f"📊 Scan Results - Session #{self.scan_session_id}")
            title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            title.setStyleSheet("padding: 10px;")  # Color from stylesheet

            # NEW: TabWidget for reorganization (top tabs)
            tab_widget = QTabWidget()
            tab_widget.setTabPosition(QTabWidget.TabPosition.North)
            tab_widget.setMinimumHeight(400)  # Usable across tabs

            # Tab 1: Filters (compact)
            filters_widget = QWidget()
            filters_layout = QVBoxLayout(filters_widget)
            filters_layout.setSpacing(8)
            filters_layout.setContentsMargins(12, 12, 12, 12)
            filters_group = self._create_filter_section()
            filters_layout.addWidget(filters_group)
            
            # NEW: Analysis Preview below filters
            preview_group = self._create_filter_preview()
            filters_layout.addWidget(preview_group)
            filters_layout.addStretch()
            tab_widget.addTab(filters_widget, "🔍 Filters")

            # Tab 2: Files (table)
            files_widget = QWidget()
            files_layout = QVBoxLayout(files_widget)
            files_layout.setSpacing(8)
            files_layout.setContentsMargins(12, 12, 12, 12)
            files_group = self._create_results_section()
            files_layout.addWidget(files_group)
            tab_widget.addTab(files_widget, "📋 Files")

            # Tab 3: Overview (trees)
            overview_widget = QWidget()
            overview_layout = QVBoxLayout(overview_widget)
            overview_layout.setSpacing(8)
            overview_layout.setContentsMargins(12, 12, 12, 12)
            overview_group = self._create_overview_section()
            overview_layout.addWidget(overview_group)
            tab_widget.addTab(overview_widget, "📁 Overview")

            # Main layout: title + tabs (stretch)
            layout = QVBoxLayout(self)
            layout.setSpacing(0)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.addWidget(title)
            layout.addWidget(tab_widget, 1)
            self.setLayout(layout)

        except Exception as e:
            logger.error(f"Failed to initialize tabbed UI: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "UI Initialization Error",
                f"Failed to initialize scan results interface:\n\n{str(e)}\n\nPlease restart the application.",
            )
            raise
    
    def _create_filter_section(self) -> QGroupBox:
        """
        Create the filter controls section for pre-analysis filtering.
        
        Builds the filter area with controls for file type, size range,
        duplicate detection, and folder selection filtering.
        
        Returns:
            QGroupBox: Grouped container with all filter controls
            
        Filter Controls:
        1. File Type Filters: Checkboxes for Video, Subtitle, Image, Other
        2. Size Range: Spinboxes for min/max MB with slider
        3. Duplicate Filter: Checkbox to show/hide duplicates
        4. Action Buttons: Apply Filters, Reset Filters, Send to Analysis
        
        All filters are connected to _apply_filters() method for real-time updates.
        
        Error Handling:
            If section creation fails, logs error and re-raises exception.
        """
        try:
            group = QGroupBox("🔍 Pre-Analysis Filters")
            layout = QVBoxLayout()
            
            # File type filters
            type_layout = QHBoxLayout()
            type_layout.addWidget(QLabel("File Types:"))
            
            self.filter_video = QCheckBox("Video")
            self.filter_video.setChecked(True)
            self.filter_video.stateChanged.connect(self._apply_filters)
            type_layout.addWidget(self.filter_video)
            
            self.filter_subtitle = QCheckBox("Subtitle")
            self.filter_subtitle.setChecked(True)
            self.filter_subtitle.stateChanged.connect(self._apply_filters)
            type_layout.addWidget(self.filter_subtitle)
            
            self.filter_image = QCheckBox("Image")
            self.filter_image.setChecked(True)
            self.filter_image.stateChanged.connect(self._apply_filters)
            type_layout.addWidget(self.filter_image)
            
            self.filter_other = QCheckBox("Other")
            self.filter_other.setChecked(True)
            self.filter_other.stateChanged.connect(self._apply_filters)
            type_layout.addWidget(self.filter_other)
            
            type_layout.addStretch()
            layout.addLayout(type_layout)
            
            # Size range filters
            size_layout = QHBoxLayout()
            size_layout.addWidget(QLabel("Size Range (MB):"))
            
            self.size_min = QSpinBox()
            self.size_min.setRange(0, 100000)
            self.size_min.setValue(0)
            self.size_min.setSuffix(" MB")
            self.size_min.valueChanged.connect(self._apply_filters)
            size_layout.addWidget(QLabel("Min:"))
            size_layout.addWidget(self.size_min)
            
            self.size_max = QSpinBox()
            self.size_max.setRange(0, 100000)
            self.size_max.setValue(100000)
            self.size_max.setSuffix(" MB")
            self.size_max.valueChanged.connect(self._apply_filters)
            size_layout.addWidget(QLabel("Max:"))
            size_layout.addWidget(self.size_max)
            
            size_layout.addStretch()
            layout.addLayout(size_layout)
            
            # Duplicate filter
            duplicate_layout = QHBoxLayout()
            self.filter_duplicates = QCheckBox("Hide Duplicate Files (same MD5)")
            self.filter_duplicates.setChecked(False)
            self.filter_duplicates.stateChanged.connect(self._apply_filters)
            duplicate_layout.addWidget(self.filter_duplicates)
            duplicate_layout.addStretch()
            layout.addLayout(duplicate_layout)
            
            # Action buttons
            button_layout = QHBoxLayout()
            
            btn_reset = QPushButton("Reset Filters")
            btn_reset.clicked.connect(self._reset_filters)
            button_layout.addWidget(btn_reset)
            
            self.btn_send_to_analysis = QPushButton("➡️ Send to Analysis")
            self.btn_send_to_analysis.clicked.connect(self._send_to_analysis)
            self.btn_send_to_analysis.setMinimumHeight(35)
            self.btn_send_to_analysis.setEnabled(False)
            self.btn_send_to_analysis.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    font-size: 13px;
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
            button_layout.addWidget(self.btn_send_to_analysis)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            # Filter summary
            self.filter_summary = QLabel("No filters applied")
            self.filter_summary.setStyleSheet("color: #1abc9c; font-weight: bold; padding: 5px;")  # Bright teal
            layout.addWidget(self.filter_summary)
            
            group.setLayout(layout)
            return group
        except Exception as e:
            logger.error(f"Failed to create filter section: {e}", exc_info=True)
            raise

    def _create_filter_preview(self) -> QGroupBox:
        """
        Compact preview section for Filters tab (below filters).

        Shows: totals, reduction, types, dups, size avg, Jellyfin matches.
        Updates dynamically via _update_filter_preview().
        """
        group = QGroupBox("📈 Preview")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(10, 6, 10, 6)

        self.preview_totals = QLabel("--")
        layout.addWidget(self.preview_totals)

        self.preview_reduction = QLabel("--")
        self.preview_reduction.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.preview_reduction)

        self.preview_types = QLabel("--")
        layout.addWidget(self.preview_types)

        stats_layout = QHBoxLayout()
        self.preview_dups = QLabel("--")
        stats_layout.addWidget(self.preview_dups)
        self.preview_jf = QLabel("--")
        self.preview_jf.setToolTip('Files already in Jellyfin library (matched by provider IDs/metadata during scan).')
        stats_layout.addWidget(self.preview_jf)
        self.preview_size = QLabel("--")
        stats_layout.addStretch()
        stats_layout.addWidget(self.preview_size)
        layout.addLayout(stats_layout)

        group.setLayout(layout)
        group.setMaximumHeight(160)
        return group

    def _update_filter_preview(self):
        """Update preview labels with computed stats."""
        try:
            total = len(self.scanned_files)
            filtered = len(self.filtered_files)
            if total == 0:
                self.preview_totals.setText("No scan data")
                return

            total_gb = sum(r.size_bytes for r in self.scanned_files) / (1024**3)
            self.preview_totals.setText(f"{total} files | {total_gb:.2f} GB | #{self.scan_session_id}")

            red_pct = 100 * (1 - filtered / total)
            self.preview_reduction.setText(f"{filtered}/{total} ({red_pct:.1f}% reduction)")
            self.preview_reduction.setStyleSheet(f"font-weight: bold; color: %s;" % 
                ("#27ae60" if red_pct > 20 else "#f39c12" if red_pct > 5 else "#95a5a6"))

            # Types
            type_c = {"Video": 0, "Subtitle": 0, "Image": 0, "Other": 0}
            for r in self.filtered_files:
                ext = r.extension.lower()
                if ext in self.video_extensions: type_c["Video"] += 1
                elif ext in self.subtitle_extensions: type_c["Subtitle"] += 1
                elif ext in self.image_extensions: type_c["Image"] += 1
                else: type_c["Other"] += 1
            types_str = ", ".join(f"{k}:{v}" for k,v in type_c.items())
            self.preview_types.setText(types_str)

            # Dups
            dups = len(self.duplicate_groups)
            self.preview_dups.setText(f"Dups: {dups} groups")

            # Jellyfin
            jf_matched = sum(1 for r in self.filtered_files if getattr(r, 'jellyfin_matched', False))
            jf_pct = 100 * jf_matched / filtered if filtered else 0
            self.preview_jf.setText(f"JF: {jf_matched}/{filtered} ({jf_pct:.0f}%)")

            # Size avg
            sizes = [r.size_bytes for r in self.filtered_files if r.size_bytes]
            avg_mb = sum(sizes) / len(sizes) / (1024*1024) if sizes else 0
            self.preview_size.setText(f"Avg: {avg_mb:.0f} MB")

        except Exception as e:
            logger.warning(f"Preview update failed: {e}")
            self.preview_reduction.setText("Update error")

    def _create_results_section(self) -> QGroupBox:
        """
        Create the results section with table and controls.
        
        Builds the main results display area containing a sortable table
        of scanned files with search/filter capabilities and export functionality.
        
        Returns:
            QGroupBox: Grouped container with results table and controls
            
        The section includes:
        1. Search bar with real-time filtering
        2. Export button (enabled when files are loaded)
        3. Sortable table with columns for:
           - Filename: Base filename
           - Path: Full directory path
           - Size (MB): File size in megabytes
           - Type: Media type (movie/episode)
           - MD5: File hash for duplicate detection
           - Status: Filter status indicator
        4. Summary label showing file count and statistics
        
        Table Configuration:
            - Interactive column resizing
            - Pre-set column widths for optimal display
            - Sorting enabled on all columns
            - Minimum height of 200px
            - Color coding for filter status
        
        Error Handling:
            If section creation fails, logs error and re-raises exception.
        """
        try:
            group = QGroupBox("Scan Results")
            layout = QVBoxLayout()

            # Search and export bar
            search_layout = QHBoxLayout()

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search files...")
            self.search_input.textChanged.connect(self._filter_results)
            search_layout.addWidget(QLabel("Search:"))
            search_layout.addWidget(self.search_input)

            self.btn_export = QPushButton("Export Results")
            self.btn_export.clicked.connect(self._export_results)
            self.btn_export.setEnabled(False)
            search_layout.addWidget(self.btn_export)

            layout.addLayout(search_layout)

            # Results table
            self.results_table = QTableWidget()
            self.results_table.setMinimumHeight(200)
            self.results_table.setColumnCount(6)
            self.results_table.setHorizontalHeaderLabels([
                "Filename", "Path", "Size (MB)", "Type", "MD5", "Status"
            ])
            self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.results_table.setColumnWidth(0, 250)
            self.results_table.setColumnWidth(1, 300)
            self.results_table.setColumnWidth(2, 80)
            self.results_table.setColumnWidth(3, 60)
            self.results_table.setColumnWidth(4, 100)
            self.results_table.setColumnWidth(5, 80)
            self.results_table.setSortingEnabled(True)
            layout.addWidget(self.results_table)

            # Summary label
            self.lbl_summary = QLabel("No files loaded yet")
            self.lbl_summary.setStyleSheet("padding: 5px;")  # Color from stylesheet
            layout.addWidget(self.lbl_summary)

            group.setLayout(layout)
            return group
        except Exception as e:
            logger.error(f"Failed to create results section: {e}", exc_info=True)
            raise
    
    def _create_overview_section(self) -> QGroupBox:
        """
        Create hierarchical overview and duplicate summary section.
        
        Builds the overview area showing folder structure hierarchy and
        duplicate file detection results in expandable tree views.
        
        Returns:
            QGroupBox: Grouped container with overview trees and labels
            
        The section includes:
        1. Folder overview tree showing hierarchical directory structure
           with file counts and total sizes per folder
        2. Duplicate summary label showing MD5 group statistics
        3. Duplicate tree showing files grouped by MD5 hash with
           duplicate counts and example file paths
        
        Tree Configurations:
            - Folder tree: Columns for Folder, Files, Size (MB), Details
            - Duplicate tree: Columns for MD5 Hash, File Count, Example Paths
            - Pre-set column widths for optimal display
        
        Data Sources:
            - Folder structure computed from scanned files
            - Duplicate groups computed by MD5 hash analysis
        
        Error Handling:
            If section creation fails, logs error and re-raises exception.
        """
        try:
            group = QGroupBox("Folder Overview & Duplicate Detection")
            layout = QVBoxLayout()

            self.overview_tree = QTreeWidget()
            self.overview_tree.setHeaderLabels(["Folder", "Files", "Size (MB)", "Details"])
            self.overview_tree.setColumnWidth(0, 400)
            layout.addWidget(self.overview_tree)

            self.duplicate_summary_label = QLabel("MD5 duplicate groups: not computed yet.")
            layout.addWidget(self.duplicate_summary_label)

            self.duplicate_tree = QTreeWidget()
            self.duplicate_tree.setHeaderLabels(["MD5 Hash", "File Count", "Example Paths"])
            self.duplicate_tree.setColumnWidth(0, 260)
            self.duplicate_tree.setColumnWidth(1, 80)
            layout.addWidget(self.duplicate_tree)

            group.setLayout(layout)
            return group
        except Exception as e:
            logger.error(f"Failed to create overview section: {e}", exc_info=True)
            raise

    def _load_scan_results(self):
        """
        Load scan results from database by session ID.
        
        Retrieves scan session metadata and associated file records from
        the database, then populates the UI with the results.
        
        The loading process:
        1. Connects to media library database
        2. Retrieves session metadata (file count, total size, scan options)
        3. Loads FileRecord objects from inventory repository
        4. Computes folder structure hierarchy
        5. Populates results table with file data
        6. Updates overview trees and statistics
        7. Enables export and analysis functionality
        
        Data Validation:
            - Verifies session exists in database
            - Checks file count consistency between metadata and loaded records
            - Validates JSON scan options format
        
        Error Handling:
            - Database errors: Shows connection/query failure dialogs
            - JSON errors: Shows data corruption warnings
            - Session not found: Shows validation error dialogs
            - General errors: Shows generic load failure dialogs
        
        UI Updates:
            - Results table populated with sortable file data
            - Overview trees show folder hierarchy and duplicates
            - Summary label shows file count and total size
            - Export and analysis buttons enabled for successful loads
        """
        try:
            # Load session metadata
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_files, total_size_bytes, scan_options_json 
                FROM project_scan_sessions 
                WHERE id = ?
            ''', (self.scan_session_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Scan session {self.scan_session_id} not found")
            
            total_files, total_size_bytes, options_json = row
            options = json.loads(options_json) if options_json else {}
            
            conn.close()
            
            # Load FileRecords from inventory
            inventory_sessions = options.get('inventory_session_ids', [])
            self.scanned_files = []
            for session_id in inventory_sessions:
                self.scanned_files.extend(self.inventory_repo.get_all_files(session_id))
            
            if len(self.scanned_files) != total_files:
                logger.warning(f"Mismatch: DB reports {total_files} files, loaded {len(self.scanned_files)}")
            
            # Initialize filtered_files to all files
            self.filtered_files = self.scanned_files.copy()
            
            # Compute folder structure
            self._compute_folder_structure()
            
            # Populate UI
            self._populate_results_table(self.scanned_files)
            self._update_overview()
            self._update_filter_preview() # Call after _load_scan_results
            
            # Apply initial filters
            self._apply_filters()
            
            # Update summary
            total_size_gb = total_size_bytes / (1024 ** 3) if total_size_bytes else 0
            self.lbl_summary.setText(
                f"Loaded {len(self.scanned_files)} files ({total_size_gb:.2f} GB) "
                f"from session #{self.scan_session_id}"
            )
            
            self.btn_export.setEnabled(True)
            self.btn_send_to_analysis.setEnabled(True)
            logger.info(f"Loaded {len(self.scanned_files)} files for session {self.scan_session_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error loading scan results: {e}", exc_info=True)
            self.lbl_summary.setText(f"Database error loading results: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Failed to load scan results from database:\n\n{str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid scan options JSON: {e}", exc_info=True)
            self.lbl_summary.setText("Error: Invalid scan session data")
            QMessageBox.critical(self, "Data Error", f"Invalid scan session configuration:\n\n{str(e)}")
        except ValueError as e:
            logger.error(f"Scan session validation error: {e}", exc_info=True)
            self.lbl_summary.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Session Error", f"Scan session error:\n\n{str(e)}")
        except Exception as e:
            logger.error(f"Failed to load scan results: {e}", exc_info=True)
            self.lbl_summary.setText(f"Error loading results: {str(e)}")
            QMessageBox.critical(self, "Load Error", f"Failed to load scan results:\n\n{str(e)}")
    
    def _compute_folder_structure(self):
        """
        Compute folder structure from scanned files.
        
        Analyzes all scanned files to build a hierarchical folder structure
        with statistics for each directory including file counts, total sizes,
        and file type distributions.
        
        The computation process:
        1. Initializes folder statistics dictionary
        2. Iterates through all scanned files
        3. Groups files by parent directory
        4. Accumulates statistics per folder:
           - File count
           - Total size in bytes
           - File type counts by extension
        
        Data Structure:
            folder_structure: Dict[Path, Dict[str, Any]]
            - Key: Folder path
            - Value: Stats dict with file_count, total_size, file_types
        
        Error Handling:
            - Skips invalid file records with logging
            - Continues processing despite individual file errors
            - Shows warning dialog if entire computation fails
            - Falls back to empty structure on critical errors
        
        Performance:
            - O(n) complexity where n is number of files
            - Uses defaultdict for efficient accumulation
            - Processes files in single pass
        """
        try:
            self.folder_structure = {}
            folder_stats = defaultdict(lambda: {"file_count": 0, "total_size": 0, "file_types": defaultdict(int)})
            
            for record in self.scanned_files:
                try:
                    parent = record.absolute_path.parent
                    stats = folder_stats[parent]
                    stats["file_count"] += 1
                    stats["total_size"] += record.size_bytes
                    stats["file_types"][record.extension] += 1
                except AttributeError as e:
                    logger.warning(f"Invalid file record structure: {e}", exc_info=True)
                    continue
                except Exception as e:
                    logger.warning(f"Error processing file record: {e}", exc_info=True)
                    continue
            
            self.folder_structure = dict(folder_stats)
            logger.debug(f"Computed folder structure for {len(self.folder_structure)} folders")
            
        except Exception as e:
            logger.error(f"Failed to compute folder structure: {e}", exc_info=True)
            self.folder_structure = {}
            QMessageBox.warning(self, "Structure Error", f"Failed to compute folder structure:\n\n{str(e)}")
    
    def _apply_filters(self):
        """
        Apply all active filters to the scanned files.
        
        Filters the complete file list based on user-selected criteria:
        - File type (video, subtitle, image, other)
        - Size range (min/max MB)
        - Duplicate detection (MD5 hash)
        
        Updates the filtered_files list and refreshes the UI display.
        
        Filter Logic:
            - Files must pass ALL active filter criteria
            - Unchecked file types are excluded
            - Files outside size range are excluded
            - Duplicate files (by MD5) are excluded if filter enabled
        
        UI Updates:
            - Results table shows only filtered files with color coding
            - Filter summary shows count reduction
            - Send to Analysis button enabled with filtered count
        """
        try:
            # Start with all files
            self.filtered_files = []
            
            # Get filter states
            include_video = self.filter_video.isChecked()
            include_subtitle = self.filter_subtitle.isChecked()
            include_image = self.filter_image.isChecked()
            include_other = self.filter_other.isChecked()
            
            min_size_mb = self.size_min.value()
            max_size_mb = self.size_max.value()
            min_size_bytes = min_size_mb * 1024 * 1024
            max_size_bytes = max_size_mb * 1024 * 1024
            
            hide_duplicates = self.filter_duplicates.isChecked()
            
            # Build set of seen MD5 hashes for duplicate detection
            seen_md5 = set()
            
            for file_record in self.scanned_files:
                try:
                    # File type filter
                    ext = file_record.extension.lower()
                    if ext in self.video_extensions and not include_video:
                        continue
                    if ext in self.subtitle_extensions and not include_subtitle:
                        continue
                    if ext in self.image_extensions and not include_image:
                        continue
                    if (ext not in self.video_extensions and 
                        ext not in self.subtitle_extensions and 
                        ext not in self.image_extensions and 
                        not include_other):
                        continue
                    
                    # Size filter
                    if file_record.size_bytes < min_size_bytes or file_record.size_bytes > max_size_bytes:
                        continue
                    
                    # Duplicate filter
                    if hide_duplicates and file_record.md5_hash:
                        if file_record.md5_hash in seen_md5:
                            continue
                        seen_md5.add(file_record.md5_hash)
                    
                    # File passed all filters
                    self.filtered_files.append(file_record)
                    
                except AttributeError as e:
                    logger.warning(f"Invalid file record during filtering: {e}", exc_info=True)
                    continue
                except Exception as e:
                    logger.warning(f"Error filtering file record: {e}", exc_info=True)
                    continue
            
            # Update UI
            self._update_filter_summary()
            self._populate_results_table(self.filtered_files)
            self._update_filter_preview() # Call after _apply_filters
            
            logger.debug(f"Applied filters: {len(self.scanned_files)} → {len(self.filtered_files)} files")
            
        except Exception as e:
            logger.error(f"Failed to apply filters: {e}", exc_info=True)
            QMessageBox.warning(self, "Filter Error", f"Failed to apply filters:\n\n{str(e)}")
    
    def _reset_filters(self):
        """
        Reset all filters to default state (all files included).
        
        Restores filter controls to their initial state:
        - All file type checkboxes checked
        - Size range set to 0-100000 MB
        - Duplicate filter unchecked
        
        Then re-applies filters to show all files.
        """
        try:
            self.filter_video.setChecked(True)
            self.filter_subtitle.setChecked(True)
            self.filter_image.setChecked(True)
            self.filter_other.setChecked(True)
            self.size_min.setValue(0)
            self.size_max.setValue(100000)
            self.filter_duplicates.setChecked(False)
            
            # _apply_filters() will be called automatically via signal connections
            logger.info("Filters reset to default state")
            
        except Exception as e:
            logger.error(f"Failed to reset filters: {e}", exc_info=True)
            QMessageBox.warning(self, "Reset Error", f"Failed to reset filters:\n\n{str(e)}")
    
    def _update_filter_summary(self):
        """
        Update the filter summary label with current filter statistics.
        
        Shows:
        - Original file count
        - Filtered file count
        - Reduction percentage
        - Active filter descriptions
        """
        try:
            total = len(self.scanned_files)
            filtered = len(self.filtered_files)
            
            if total == filtered:
                self.filter_summary.setText("No filters applied - showing all files")
            else:
                reduction = 100 * (total - filtered) / total if total > 0 else 0
                self.filter_summary.setText(
                    f"Filtered: {filtered}/{total} files ({reduction:.1f}% reduction)"
                )
            
        except Exception as e:
            logger.error(f"Failed to update filter summary: {e}", exc_info=True)
    
    def _send_to_analysis(self):
        """
        Send filtered file list to Analysis view.
        
        Emits the send_to_analysis signal with the filtered files and filter configuration.
        This allows the Analysis view to work with only the user-selected subset of files.
        
        Filter configuration includes:
        - File type selections
        - Size range
        - Duplicate filter state
        - Excluded folders/files
        
        The signal is connected in jelly_rancher_studio.py to open/update the Analysis view.
        """
        try:
            if not self.filtered_files:
                QMessageBox.warning(
                    self,
                    "No Files",
                    "No files match the current filters.\n\n"
                    "Please adjust your filters and try again."
                )
                return
            
            # Build filter configuration
            filter_config = {
                "file_types": {
                    "video": self.filter_video.isChecked(),
                    "subtitle": self.filter_subtitle.isChecked(),
                    "image": self.filter_image.isChecked(),
                    "other": self.filter_other.isChecked(),
                },
                "size_range_mb": {
                    "min": self.size_min.value(),
                    "max": self.size_max.value(),
                },
                "hide_duplicates": self.filter_duplicates.isChecked(),
                "excluded_folders": list(str(p) for p in self.excluded_folders),
                "excluded_files": list(str(p) for p in self.excluded_files),
            }
            
            # Confirm with user
            reply = QMessageBox.question(
                self,
                "Send to Analysis",
                f"Send {len(self.filtered_files)} filtered files to Analysis?\n\n"
                f"Original: {len(self.scanned_files)} files\n"
                f"Filtered: {len(self.filtered_files)} files\n\n"
                f"This will reduce LLM token costs and improve analysis quality.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Emit signal with filtered data
                self.send_to_analysis.emit(self.filtered_files, filter_config)
                logger.info(f"Sent {len(self.filtered_files)} filtered files to analysis")
                
                QMessageBox.information(
                    self,
                    "Sent to Analysis",
                    f"Successfully sent {len(self.filtered_files)} files to Analysis view.\n\n"
                    f"The Analysis tab will now use your filtered data."
                )
            
        except Exception as e:
            logger.error(f"Failed to send to analysis: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Send Error",
                f"Failed to send files to analysis:\n\n{str(e)}"
            )
    
    def _populate_results_table(self, files: List[FileRecord]):
        """
        Populate the results table with scanned files.
        
        Fills the QTableWidget with file information from the provided files list,
        displaying filename, path, size, type, MD5 hash, and filter status.
        
        Args:
            files (List[FileRecord]): List of file records to display in the table
            
        Table Columns:
            0. Filename: Base filename from absolute path
            1. Path: Parent directory path
            2. Size (MB): File size in megabytes (formatted to 1 decimal)
            3. Type: File extension (media type indicator)
            4. MD5: First 8 characters of hash + "..." (or "N/A" if missing)
            5. Status: "✓ Included" or "✗ Filtered" with color coding
        
        Color Coding:
            - Green rows: Files included in filter
            - Gray rows: Files excluded by filter
        
        Error Handling:
            - Skips invalid records with logging and error row filling
            - Continues processing despite individual row errors
            - Shows warning dialog if entire table population fails
        
        Performance:
            - Processes all files in single pass
            - Handles large file lists efficiently
            - Uses QTableWidgetItem for each cell
        """
        try:
            self.results_table.setRowCount(len(files))
            
            for row, file_record in enumerate(files):
                try:
                    # Check if file is in filtered list
                    is_included = file_record in self.filtered_files
                    
                    # Filename
                    item = QTableWidgetItem(file_record.absolute_path.name)
                    if not is_included:
                        item.setForeground(QColor("#95a5a6"))
                    self.results_table.setItem(row, 0, item)
                    
                    # Path
                    item = QTableWidgetItem(str(file_record.absolute_path.parent))
                    if not is_included:
                        item.setForeground(QColor("#95a5a6"))
                    self.results_table.setItem(row, 1, item)
                    
                    # Size (MB)
                    size_mb = file_record.size_bytes / (1024 * 1024)
                    item = QTableWidgetItem(f"{size_mb:.1f}")
                    if not is_included:
                        item.setForeground(QColor("#95a5a6"))
                    self.results_table.setItem(row, 2, item)
                    
                    # Type
                    item = QTableWidgetItem(file_record.extension)
                    if not is_included:
                        item.setForeground(QColor("#95a5a6"))
                    self.results_table.setItem(row, 3, item)
                    
                    # MD5
                    md5_text = file_record.md5_hash[:8] + "..." if file_record.md5_hash else "N/A"
                    item = QTableWidgetItem(md5_text)
                    if not is_included:
                        item.setForeground(QColor("#95a5a6"))
                    self.results_table.setItem(row, 4, item)
                    
                    # Status
                    if is_included:
                        item = QTableWidgetItem("✓ Included")
                        item.setForeground(QColor("#27ae60"))
                    else:
                        item = QTableWidgetItem("✗ Filtered")
                        item.setForeground(QColor("#95a5a6"))
                    self.results_table.setItem(row, 5, item)
                    
                except AttributeError as e:
                    logger.warning(f"Invalid file record for table row {row}: {e}", exc_info=True)
                    # Fill with error indicators
                    for col in range(6):
                        self.results_table.setItem(row, col, QTableWidgetItem("ERROR"))
                except Exception as e:
                    logger.warning(f"Error populating table row {row}: {e}", exc_info=True)
                    continue
            
            logger.debug(f"Populated results table with {len(files)} files")
            
        except Exception as e:
            logger.error(f"Failed to populate results table: {e}", exc_info=True)
            QMessageBox.warning(self, "Table Error", f"Failed to populate results table:\n\n{str(e)}")
    
    def _filter_results(self, search_text: str):
        """
        Filter results table based on search text.
        
        Applies real-time filtering to the results table, showing only rows
        that contain the search text in filename or path columns.
        
        Args:
            search_text (str): Text to search for (case-insensitive)
            
        Filtering Logic:
            - If search_text is empty: Shows all rows
            - If search_text provided: Searches filename (col 0) and path (col 1)
            - Case-insensitive matching
            - Shows row if any searched column contains the text
        
        Performance:
            - Iterates through all table rows on each keystroke
            - Searches only filename and path columns for efficiency
            - Uses setRowHidden() to show/hide rows without removing data
        
        Error Handling:
            - Continues filtering despite individual cell access errors
            - Logs warnings for problematic rows/cells
            - Shows error dialog if entire filtering operation fails
        
        UI Integration:
            - Connected to search input's textChanged signal
            - Provides immediate visual feedback as user types
        """
        try:
            for row in range(self.results_table.rowCount()):
                show_row = False
                if not search_text:
                    show_row = True
                else:
                    # Search in filename and path
                    for col in [0, 1]:
                        try:
                            item = self.results_table.item(row, col)
                            if item and search_text.lower() in item.text().lower():
                                show_row = True
                                break
                        except Exception as e:
                            logger.warning(f"Error filtering row {row}, col {col}: {e}", exc_info=True)
                            continue
                
                self.results_table.setRowHidden(row, not show_row)
            
            logger.debug(f"Applied search filter '{search_text}' to results table")
            
        except Exception as e:
            logger.error(f"Failed to filter results: {e}", exc_info=True)
            QMessageBox.warning(self, "Filter Error", f"Failed to apply search filter:\n\n{str(e)}")
    
    def _export_results(self):
        """
        Export filtered scan results to CSV.
        
        Saves the current filtered results to a CSV file with comprehensive
        file information including paths, sizes, and metadata.
        
        The export process:
        1. Validates that scan results exist
        2. Opens file save dialog with timestamped default filename
        3. Writes CSV header row
        4. Exports each filtered file record as a data row
        5. Shows success confirmation with file path and filter stats
        
        CSV Format:
            - Filename: Base filename
            - Path: Parent directory path
            - Size (bytes): Exact file size in bytes
            - Extension: File extension/type
            - MD5: Full MD5 hash (or empty string if missing)
            - Status: "Included" or "Filtered"
        
        Filename Convention:
            scan_results_session_{session_id}_{timestamp}.csv
            
        Error Handling:
            - Permission errors: Shows access denied warnings
            - File system errors: Shows OS-specific error messages
            - Invalid records: Logs warnings and writes error rows
            - General errors: Shows export failure dialogs
        
        User Experience:
            - Cancel-safe (returns early if user cancels dialog)
            - Progress feedback through success/error dialogs
            - Shows filter statistics in confirmation
            - Comprehensive logging for troubleshooting
        """
        try:
            if not self.scanned_files:
                QMessageBox.information(self, "No Data", "No scan results to export.")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Scan Results",
                f"scan_results_session_{self.scan_session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not filename:
                return  # User cancelled
            
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Filename", "Path", "Size (bytes)", "Extension", "MD5", "Status"])
                    
                    for file_record in self.scanned_files:
                        try:
                            is_included = file_record in self.filtered_files
                            status = "Included" if is_included else "Filtered"
                            
                            writer.writerow([
                                file_record.absolute_path.name,
                                str(file_record.absolute_path.parent),
                                file_record.size_bytes,
                                file_record.extension,
                                file_record.md5_hash or "",
                                status
                            ])
                        except AttributeError as e:
                            logger.warning(f"Invalid file record during export: {e}", exc_info=True)
                            writer.writerow(["ERROR", "ERROR", 0, "ERROR", "ERROR", "ERROR"])
                        except Exception as e:
                            logger.warning(f"Error exporting file record: {e}", exc_info=True)
                            continue
                
                total = len(self.scanned_files)
                filtered = len(self.filtered_files)
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Results exported to:\n{filename}\n\n"
                    f"Total files: {total}\n"
                    f"Included (filtered): {filtered}\n"
                    f"Excluded: {total - filtered}"
                )
                logger.info(f"Exported scan results to: {filename}")
                
            except PermissionError as e:
                QMessageBox.critical(self, "Permission Error", f"Cannot write to file:\n{filename}\n\n{e}")
                logger.error(f"Export permission error: {e}")
            except OSError as e:
                QMessageBox.critical(self, "File Error", f"File system error:\n{e}")
                logger.error(f"Export file system error: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export:\n{e}")
                logger.error(f"Export error: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Failed to initiate export: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to start export:\n\n{str(e)}")
    
    def _update_overview(self):
        """
        Generate hierarchical overview and duplicate summary.
        
        Updates the overview trees with folder structure statistics and
        duplicate file detection results based on MD5 hash analysis.
        
        The update process:
        1. Validates folder structure data exists
        2. Clears and repopulates folder overview tree
        3. Computes duplicate groups by MD5 hash
        4. Updates duplicate summary label
        5. Populates duplicate tree with group details
        
        Folder Overview Tree:
            - Shows each folder with file count, total size, and type breakdown
            - Sorts folders alphabetically
            - Displays top 4 file types by count with counts
        
        Duplicate Detection:
            - Groups files by MD5 hash
            - Only shows groups with 2+ files (true duplicates)
            - Sorts groups by size (largest first)
            - Shows MD5 hash, file count, and example paths
        
        Data Structures Updated:
            - overview_tree: QTreeWidget with folder hierarchy
            - duplicate_groups: Dict mapping MD5 to file lists
            - duplicate_summary_label: Statistics text
            - duplicate_tree: QTreeWidget with duplicate groups
        
        Error Handling:
            - Continues processing despite individual item errors
            - Logs warnings for data structure issues
            - Shows error messages for critical failures
            - Graceful degradation if components fail
        """
        try:
            if not self.folder_structure:
                logger.debug("No folder structure available for overview update")
                return

            # Folder overview
            try:
                self.overview_tree.clear()
                for folder_path, data in sorted(self.folder_structure.items()):
                    try:
                        path_str = str(folder_path)
                        size_mb = data["total_size"] / (1024 * 1024)
                        
                        sorted_types = sorted(data["file_types"].items(), key=lambda x: x[1], reverse=True)
                        details = ", ".join([f"{ext}: {count}" for ext, count in sorted_types[:4]])
                        
                        item = QTreeWidgetItem([
                            path_str,
                            str(data["file_count"]),
                            f"{size_mb:.1f}",
                            details,
                        ])
                        self.overview_tree.addTopLevelItem(item)
                    except KeyError as e:
                        logger.warning(f"Missing folder data key: {e}", exc_info=True)
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing folder {folder_path}: {e}", exc_info=True)
                        continue
                
                logger.debug(f"Updated overview tree with {len(self.folder_structure)} folders")
                
            except Exception as e:
                logger.error(f"Failed to update folder overview: {e}", exc_info=True)

            # Duplicate detection
            try:
                self.duplicate_tree.clear()
                self.duplicate_groups = {}
                md5_map = defaultdict(list)
                
                for record in self.scanned_files:
                    try:
                        md5_value = getattr(record, "md5_hash", None)
                        if md5_value:
                            md5_map[md5_value].append(record)
                    except Exception as e:
                        logger.warning(f"Error processing record for duplicates: {e}", exc_info=True)
                        continue

                for md5_value, records in md5_map.items():
                    if len(records) >= 2:
                        self.duplicate_groups[md5_value] = records

                if not self.duplicate_groups:
                    self.duplicate_summary_label.setText("MD5 duplicate groups: none detected.")
                else:
                    total_files = sum(len(v) for v in self.duplicate_groups.values())
                    self.duplicate_summary_label.setText(
                        f"MD5 duplicate groups: {len(self.duplicate_groups)} groups, {total_files} files."
                    )

                    for md5_value, records in sorted(
                        self.duplicate_groups.items(), key=lambda x: len(x[1]), reverse=True
                    ):
                        try:
                            example_paths = [str(rec.absolute_path) for rec in records[:3]]
                            item = QTreeWidgetItem([
                                md5_value,
                                str(len(records)),
                                "; ".join(example_paths),
                            ])
                            self.duplicate_tree.addTopLevelItem(item)
                        except AttributeError as e:
                            logger.warning(f"Invalid record in duplicate group {md5_value}: {e}", exc_info=True)
                            continue
                        except Exception as e:
                            logger.warning(f"Error processing duplicate group {md5_value}: {e}", exc_info=True)
                            continue
                
                logger.debug(f"Updated duplicate analysis: {len(self.duplicate_groups)} groups found")
                
            except Exception as e:
                logger.error(f"Failed to update duplicate analysis: {e}", exc_info=True)
                self.duplicate_summary_label.setText("Error: Failed to analyze duplicates")
                
        except Exception as e:
            logger.error(f"Failed to update overview: {e}", exc_info=True)
            QMessageBox.warning(self, "Overview Error", f"Failed to update overview:\n\n{str(e)}")

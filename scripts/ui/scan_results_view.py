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
    QSlider, QSpinBox, QFileDialog, QTabWidget, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from scripts.core.file_scanner import FileRecord, ScanStatistics
from scripts.core.project_manager import ProjectManager, Project
from scripts.core.inventory_repository import InventoryRepository
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.workers import ScanResultsLoadWorker
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

            # Get Round-Up database path if using adapter pattern
            self.roundup_db_path: Optional[Path] = None
            print(f"DEBUG: hasattr(project, 'roundup') = {hasattr(project, 'roundup')}")
            print(f"DEBUG: project.roundup = {getattr(project, 'roundup', 'NOT SET')}")
            if hasattr(project, 'roundup') and project.roundup:
                self.roundup_db_path = project.roundup.path / "data.db"
                print(f"DEBUG: roundup_db_path = {self.roundup_db_path}")
                print(f"DEBUG: roundup_db_path.exists() = {self.roundup_db_path.exists()}")
                logger.info(f"Round-Up database path: {self.roundup_db_path}")
            else:
                print(f"DEBUG: Not using Round-Up mode - project.roundup is None or not set")

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

            # Worker reference for async loading
            self.load_worker: Optional[ScanResultsLoadWorker] = None

            self._init_ui()
            self._load_scan_results_async()
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

            # Progress bar for async loading (hidden by default)
            self.progress_container = QWidget()
            progress_layout = QVBoxLayout(self.progress_container)
            progress_layout.setContentsMargins(10, 5, 10, 5)
            progress_layout.setSpacing(4)

            self.progress_status = QLabel("Loading scan results...")
            self.progress_status.setStyleSheet("font-weight: bold;")
            progress_layout.addWidget(self.progress_status)

            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(4)  # 4 steps in loading
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            progress_layout.addWidget(self.progress_bar)

            self.progress_container.setVisible(False)  # Hidden until loading starts

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

            # Main layout: title + progress + tabs (stretch)
            layout = QVBoxLayout(self)
            layout.setSpacing(0)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.addWidget(title)
            layout.addWidget(self.progress_container)
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
        Rich statistics preview section for Filters tab.

        Shows comprehensive scan statistics:
        - Total files and size
        - File type breakdown with counts and percentages
        - Size distribution (min, max, avg, median)
        - Folder statistics
        - Duplicate information
        - Jellyfin matches
        - Extension breakdown (top 10)
        - Filter reduction impact

        Updates dynamically via _update_filter_preview().
        """
        group = QGroupBox("📊 Scan Statistics")
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(12, 10, 12, 10)

        # Row 1: Totals (bold header)
        self.preview_totals = QLabel("--")
        self.preview_totals.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.preview_totals)

        # Row 2: Filter reduction
        self.preview_reduction = QLabel("--")
        self.preview_reduction.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.preview_reduction)

        # Separator
        sep1 = QLabel("─" * 40)
        sep1.setStyleSheet("color: #555;")
        layout.addWidget(sep1)

        # Row 3: File Types breakdown
        types_header = QLabel("📁 File Types:")
        types_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(types_header)
        self.preview_types = QLabel("--")
        layout.addWidget(self.preview_types)

        # Row 4: Size Distribution
        size_header = QLabel("📏 Size Distribution:")
        size_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(size_header)
        self.preview_size_stats = QLabel("--")
        layout.addWidget(self.preview_size_stats)

        # Row 5: Folder Statistics
        folder_header = QLabel("📂 Folder Statistics:")
        folder_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(folder_header)
        self.preview_folders = QLabel("--")
        layout.addWidget(self.preview_folders)

        # Row 6: Duplicates and Jellyfin
        extras_layout = QHBoxLayout()
        self.preview_dups = QLabel("--")
        extras_layout.addWidget(self.preview_dups)
        self.preview_jf = QLabel("--")
        self.preview_jf.setToolTip('Files already in Jellyfin library (matched by provider IDs/metadata during scan).')
        extras_layout.addWidget(self.preview_jf)
        extras_layout.addStretch()
        layout.addLayout(extras_layout)

        # Row 7: Top Extensions
        ext_header = QLabel("🏷️ Top Extensions:")
        ext_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(ext_header)
        self.preview_extensions = QLabel("--")
        self.preview_extensions.setWordWrap(True)
        layout.addWidget(self.preview_extensions)

        # Legacy compatibility
        self.preview_types_legacy = self.preview_types
        self.preview_size = QLabel("")  # Hidden, for compatibility

        group.setLayout(layout)
        group.setMinimumHeight(280)
        return group

    def _update_filter_preview(self):
        """Update preview labels with comprehensive scan statistics."""
        try:
            total = len(self.scanned_files)
            filtered = len(self.filtered_files)

            if total == 0:
                self.preview_totals.setText("No scan data - run a scan first")
                self.preview_reduction.setText("--")
                self.preview_types.setText("--")
                self.preview_size_stats.setText("--")
                self.preview_folders.setText("--")
                self.preview_dups.setText("--")
                self.preview_jf.setText("--")
                self.preview_extensions.setText("--")
                return

            # === TOTALS ===
            total_bytes = sum(r.size_bytes for r in self.scanned_files)
            total_gb = total_bytes / (1024**3)
            self.preview_totals.setText(
                f"🔢 {total:,} files | {total_gb:.2f} GB total | Session #{self.scan_session_id}"
            )

            # === FILTER REDUCTION ===
            red_pct = 100 * (1 - filtered / total) if total > 0 else 0
            filtered_bytes = sum(r.size_bytes for r in self.filtered_files)
            filtered_gb = filtered_bytes / (1024**3)
            color = "#27ae60" if red_pct > 20 else "#f39c12" if red_pct > 5 else "#95a5a6"
            self.preview_reduction.setText(
                f"🎯 After filters: {filtered:,}/{total:,} files ({filtered_gb:.2f} GB) — {red_pct:.1f}% reduction"
            )
            self.preview_reduction.setStyleSheet(f"font-weight: bold; color: {color};")

            # === FILE TYPES BREAKDOWN ===
            type_counts = {"Video": 0, "Subtitle": 0, "Image": 0, "Other": 0}
            type_sizes = {"Video": 0, "Subtitle": 0, "Image": 0, "Other": 0}
            for r in self.scanned_files:
                ext = r.extension.lower()
                size = r.size_bytes or 0
                if ext in self.video_extensions:
                    type_counts["Video"] += 1
                    type_sizes["Video"] += size
                elif ext in self.subtitle_extensions:
                    type_counts["Subtitle"] += 1
                    type_sizes["Subtitle"] += size
                elif ext in self.image_extensions:
                    type_counts["Image"] += 1
                    type_sizes["Image"] += size
                else:
                    type_counts["Other"] += 1
                    type_sizes["Other"] += size

            types_parts = []
            for typ in ["Video", "Subtitle", "Image", "Other"]:
                count = type_counts[typ]
                if count > 0:
                    pct = 100 * count / total
                    size_mb = type_sizes[typ] / (1024**2)
                    types_parts.append(f"{typ}: {count:,} ({pct:.1f}%, {size_mb:.0f} MB)")
            self.preview_types.setText(" | ".join(types_parts) if types_parts else "No files")

            # === SIZE DISTRIBUTION ===
            sizes = [r.size_bytes for r in self.scanned_files if r.size_bytes and r.size_bytes > 0]
            if sizes:
                min_mb = min(sizes) / (1024**2)
                max_mb = max(sizes) / (1024**2)
                avg_mb = sum(sizes) / len(sizes) / (1024**2)
                sorted_sizes = sorted(sizes)
                median_mb = sorted_sizes[len(sorted_sizes) // 2] / (1024**2)

                # Format sizes appropriately
                def fmt_size(mb):
                    if mb >= 1024:
                        return f"{mb/1024:.1f} GB"
                    elif mb >= 1:
                        return f"{mb:.0f} MB"
                    else:
                        return f"{mb*1024:.0f} KB"

                self.preview_size_stats.setText(
                    f"Min: {fmt_size(min_mb)} | Max: {fmt_size(max_mb)} | "
                    f"Avg: {fmt_size(avg_mb)} | Median: {fmt_size(median_mb)}"
                )
            else:
                self.preview_size_stats.setText("No size data available")

            # === FOLDER STATISTICS ===
            unique_folders = set()
            depth_counts = {}
            for r in self.scanned_files:
                try:
                    parent = r.absolute_path.parent
                    unique_folders.add(parent)
                    depth = len(parent.parts)
                    depth_counts[depth] = depth_counts.get(depth, 0) + 1
                except Exception:
                    pass

            if unique_folders:
                max_depth = max(depth_counts.keys()) if depth_counts else 0
                min_depth = min(depth_counts.keys()) if depth_counts else 0
                self.preview_folders.setText(
                    f"{len(unique_folders):,} unique folders | "
                    f"Depth: {min_depth}-{max_depth} levels | "
                    f"Avg files/folder: {total / len(unique_folders):.1f}"
                )
            else:
                self.preview_folders.setText("No folder data")

            # === DUPLICATES ===
            dups = len(self.duplicate_groups)
            dup_files = sum(len(files) for files in self.duplicate_groups.values())
            if dups > 0:
                dup_size = sum(
                    sum(r.size_bytes for r in files[1:])  # Skip first (keep one)
                    for files in self.duplicate_groups.values()
                )
                dup_gb = dup_size / (1024**3)
                self.preview_dups.setText(f"🔁 Dups: {dups} groups ({dup_files} files, {dup_gb:.2f} GB recoverable)")
            else:
                self.preview_dups.setText("🔁 Dups: None detected")

            # === JELLYFIN MATCHES ===
            jf_matched = sum(1 for r in self.scanned_files if getattr(r, 'jellyfin_matched', False))
            jf_pct = 100 * jf_matched / total if total > 0 else 0
            if jf_matched > 0:
                self.preview_jf.setText(f"📺 Jellyfin: {jf_matched:,}/{total:,} ({jf_pct:.0f}%)")
            else:
                # Check Jellyfin config to provide informative message
                try:
                    jf_config = JellyfinConfigManager()
                    if not jf_config.is_configured():
                        self.preview_jf.setText("📺 Jellyfin: Not configured")
                        self.preview_jf.setToolTip("Configure Jellyfin server in Tools → Settings to enable cross-reference")
                    elif not jf_config.is_enabled():
                        self.preview_jf.setText("📺 Jellyfin: Disabled")
                        self.preview_jf.setToolTip("Jellyfin integration is disabled in settings")
                    else:
                        self.preview_jf.setText("📺 Jellyfin: 0 matches")
                        self.preview_jf.setToolTip("Jellyfin configured but no scanned files matched library items")
                except Exception:
                    self.preview_jf.setText("📺 Jellyfin: No matches")

            # === TOP EXTENSIONS ===
            ext_counts = {}
            for r in self.scanned_files:
                ext = r.extension.lower() or "(none)"
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

            sorted_exts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ext_parts = [f".{ext}: {count:,}" for ext, count in sorted_exts]
            self.preview_extensions.setText(" | ".join(ext_parts) if ext_parts else "No extensions")

        except Exception as e:
            logger.warning(f"Preview update failed: {e}", exc_info=True)
            self.preview_totals.setText(f"Error computing statistics: {e}")

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

    def _load_scan_results_async(self):
        """
        Start async loading of scan results from database.

        Creates a ScanResultsLoadWorker to load data in background thread,
        preventing UI freezing for large scan sessions (5000+ files).

        Shows progress bar during loading, hides on completion.
        """
        try:
            # Show progress UI
            self.progress_container.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_status.setText("Starting load...")
            self.lbl_summary.setText("Loading scan results...")

            # Create and configure worker
            # Pass Round-Up database path for Round-Up mode (preferred)
            # Falls back to legacy mode if not available
            # Also pass roundup_manager and roundup for caching support
            roundup_manager = None
            roundup = None
            if hasattr(self.project, 'roundup') and self.project.roundup:
                roundup = self.project.roundup
                roundup_manager = self.project.manager

            self.load_worker = ScanResultsLoadWorker(
                scan_session_id=self.scan_session_id,
                inventory_repo=self.inventory_repo,
                roundup_db_path=self.roundup_db_path,
                roundup_manager=roundup_manager,
                roundup=roundup,
            )

            # Connect signals
            self.load_worker.progress.connect(self._on_load_progress)
            self.load_worker.finished.connect(self._on_load_finished)
            self.load_worker.error.connect(self._on_load_error)

            # Start background loading
            self.load_worker.start()
            logger.info(f"Started async load for session {self.scan_session_id}")

        except Exception as e:
            logger.error(f"Failed to start async load: {e}", exc_info=True)
            self.progress_container.setVisible(False)
            self.lbl_summary.setText(f"Error: {str(e)}")
            QMessageBox.critical(
                self, "Load Error", f"Failed to start loading:\n\n{str(e)}"
            )

    def _on_load_progress(self, message: str, current: int, total: int):
        """
        Handle progress updates from the load worker.

        Args:
            message: Status message to display
            current: Current step (0-based)
            total: Total number of steps
        """
        try:
            self.progress_status.setText(message)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        except Exception as e:
            logger.warning(f"Error updating progress: {e}")

    def _on_load_finished(
        self,
        scanned_files: List[FileRecord],
        folder_structure: Dict[Path, Dict[str, Any]],
        duplicate_groups: Dict[str, List[FileRecord]],
    ):
        """
        Handle successful completion of async load.

        Populates UI with loaded data on the main thread.

        Args:
            scanned_files: List of loaded FileRecord objects
            folder_structure: Computed folder hierarchy
            duplicate_groups: MD5-keyed duplicate file groups
        """
        try:
            # Hide progress UI
            self.progress_container.setVisible(False)

            # Store loaded data
            self.scanned_files = scanned_files
            self.folder_structure = folder_structure
            self.duplicate_groups = duplicate_groups

            # Initialize filtered files
            self.filtered_files = self.scanned_files.copy()

            # Populate UI (must happen on main thread)
            self._populate_results_table(self.scanned_files)
            self._update_overview()
            self._update_filter_preview()

            # Apply initial filters
            self._apply_filters()

            # Update summary
            total_size_bytes = sum(r.size_bytes for r in self.scanned_files)
            total_size_gb = total_size_bytes / (1024**3) if total_size_bytes else 0
            self.lbl_summary.setText(
                f"Loaded {len(self.scanned_files)} files ({total_size_gb:.2f} GB) "
                f"from session #{self.scan_session_id}"
            )

            # Enable buttons
            self.btn_export.setEnabled(True)
            self.btn_send_to_analysis.setEnabled(True)

            logger.info(
                f"Async load complete: {len(self.scanned_files)} files, "
                f"{len(self.folder_structure)} folders, "
                f"{len(self.duplicate_groups)} duplicate groups"
            )

        except Exception as e:
            logger.error(f"Error handling load completion: {e}", exc_info=True)
            self.lbl_summary.setText(f"Error displaying results: {str(e)}")
            QMessageBox.warning(
                self, "Display Error", f"Failed to display loaded results:\n\n{str(e)}"
            )

    def _on_load_error(self, error_message: str):
        """
        Handle error from the load worker.

        Args:
            error_message: Error description from worker
        """
        try:
            # Hide progress UI
            self.progress_container.setVisible(False)

            # Show error
            self.lbl_summary.setText(f"Load error: {error_message}")
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load scan results:\n\n{error_message}",
            )
            logger.error(f"Async load failed: {error_message}")

        except Exception as e:
            logger.error(f"Error handling load error: {e}", exc_info=True)
    
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
            - Batches updates with setUpdatesEnabled(False)
            - Uses set for O(1) filter membership lookup
            - Processes all files in single pass
        """
        try:
            # Disable updates for performance during bulk insert
            self.results_table.setUpdatesEnabled(False)
            self.results_table.setSortingEnabled(False)
            
            # Build set for O(1) lookup instead of O(n) list scan
            filtered_set = set(id(f) for f in self.filtered_files)
            
            self.results_table.setRowCount(len(files))
            gray_color = QColor("#95a5a6")
            green_color = QColor("#27ae60")
            
            for row, file_record in enumerate(files):
                try:
                    # O(1) lookup using object id
                    is_included = id(file_record) in filtered_set
                    row_color = None if is_included else gray_color
                    
                    # Filename
                    item = QTableWidgetItem(file_record.absolute_path.name)
                    if row_color:
                        item.setForeground(row_color)
                    self.results_table.setItem(row, 0, item)
                    
                    # Path
                    item = QTableWidgetItem(str(file_record.absolute_path.parent))
                    if row_color:
                        item.setForeground(row_color)
                    self.results_table.setItem(row, 1, item)
                    
                    # Size (MB)
                    size_mb = file_record.size_bytes / (1024 * 1024)
                    item = QTableWidgetItem(f"{size_mb:.1f}")
                    if row_color:
                        item.setForeground(row_color)
                    self.results_table.setItem(row, 2, item)
                    
                    # Type
                    item = QTableWidgetItem(file_record.extension)
                    if row_color:
                        item.setForeground(row_color)
                    self.results_table.setItem(row, 3, item)
                    
                    # MD5
                    md5_text = file_record.md5_hash[:8] + "..." if file_record.md5_hash else "N/A"
                    item = QTableWidgetItem(md5_text)
                    if row_color:
                        item.setForeground(row_color)
                    self.results_table.setItem(row, 4, item)
                    
                    # Status
                    if is_included:
                        item = QTableWidgetItem("✓ Included")
                        item.setForeground(green_color)
                    else:
                        item = QTableWidgetItem("✗ Filtered")
                        item.setForeground(gray_color)
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
        finally:
            # Re-enable updates after bulk insert (always runs)
            self.results_table.setSortingEnabled(True)
            self.results_table.setUpdatesEnabled(True)
    
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

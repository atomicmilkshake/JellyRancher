#!/usr/bin/env python3
"""
JellyBase View - Comprehensive Jellyfin Library Management Tool

Provides complete visibility and control over Jellyfin library:
- Dashboard with statistics and overview
- Items management with filtering and batch operations
- Collections management with auto-grouping
- Validation with enhanced checks
- Tools for adding/removing items and library operations

NOT part of Round-Up workflow - standalone library management tool.
"""

import logging
import time
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar, QGroupBox,
    QHeaderView, QCheckBox, QComboBox, QTabWidget, QLineEdit,
    QTextEdit, QSpinBox, QFileDialog
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QThread

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.file_scanner import FileScanner
from scripts.core.jellyfin_validator import JellyfinValidator, ValidationResult
from scripts.core.jellyfin_collections import (
    create_collection_by_genre, create_collection_by_year, create_collection_by_series
)
from scripts.core.jellyfin_batch import (
    batch_add_items, batch_remove_items, batch_update_metadata
)

logger = logging.getLogger(__name__)

# Valid video extensions
VIDEO_EXTENSIONS = FileScanner.DEFAULT_VIDEO_EXTENSIONS

# Validation status constants (Issue #12: Replace magic strings)
STATUS_VALID = 'VALID'
STATUS_INVALID = 'INVALID'
STATUS_MISSING = 'MISSING'
STATUS_DUPLICATE = 'DUPLICATE'


class ValidationWorker(QThread):
    """Background worker for validating Jellyfin library entries using enhanced validator."""

    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(list)  # list of result dicts
    error = pyqtSignal(str)  # error message

    def __init__(self, validator: JellyfinValidator, media_types: List[str],
                 check_metadata: bool = True, check_quality: bool = True, check_subtitles: bool = True):
        super().__init__()
        self.validator = validator
        self.media_types = media_types
        self.check_metadata = check_metadata
        self.check_quality = check_quality
        self.check_subtitles = check_subtitles

    def run(self):
        """Validate all Jellyfin items using enhanced validator."""
        try:
            self.progress.emit("Fetching items from Jellyfin...", 0, 1)
            results = self.validator.validate_library(
                media_types=self.media_types,
                check_metadata=self.check_metadata,
                check_quality=self.check_quality,
                check_subtitles=self.check_subtitles
            )

            if not results:
                self.finished.emit([])
                return

            total = len(results)
            logger.info(f"Validating {total} Jellyfin items...")

            # Convert ValidationResult objects to dicts for compatibility
            result_dicts = []
            for i, result in enumerate(results):
                # Convert to dict format expected by UI
                result_dict = {
                    'jellyfin_id': result.jellyfin_id,
                    'title': result.title,
                    'path': result.jellyfin_path,
                    'type': result.item.get('Type', 'Unknown'),
                    'status': STATUS_VALID if result.valid else STATUS_INVALID,
                    'issue': '; '.join([issue.message for issue in result.issues]) if result.issues else '',
                    'file_size': result.file_size,
                    'resolution': result.resolution,
                    'codec': result.codec,
                    'has_subtitles': result.has_subtitles,
                    'subtitle_languages': ', '.join(result.subtitle_languages),
                    'issues': result.issues  # Keep full issue objects for detailed view
                }
                
                # Determine status based on issues
                if result.issues:
                    critical_issues = [i for i in result.issues if i.severity == 'critical']
                    if critical_issues:
                        if 'does not exist' in critical_issues[0].message.lower():
                            result_dict['status'] = STATUS_MISSING
                        else:
                            result_dict['status'] = STATUS_INVALID
                    elif any(i.category == 'duplicate' for i in result.issues):
                        result_dict['status'] = STATUS_DUPLICATE
                
                result_dicts.append(result_dict)

                # Emit progress every 10 items or 1 second
                if (i + 1) % 10 == 0 or (i + 1) == total:
                    self.progress.emit(
                        f"Validating items: {i + 1}/{total}",
                        i + 1,
                        total
                    )

            # Detect duplicates (if needed)
            self.progress.emit("Detecting duplicates...", total, total)
            # Duplicate detection would go here if needed

            logger.info(f"Validation complete: {len(result_dicts)} items processed")
            self.finished.emit(result_dicts)

        except Exception as e:
            logger.error(f"Validation worker error: {e}", exc_info=True)
            self.error.emit(f"Validation failed: {str(e)}")


class JellyBaseView(QWidget):
    """
    JellyBase View - Comprehensive library management tool.
    
    Provides tabbed interface with:
    - Dashboard: Statistics and overview
    - Items: Comprehensive item management
    - Collections: Collection management and auto-grouping
    - Validation: Enhanced validation results
    - Tools: Add/remove items, refresh library
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.jellyfin_client = None
        self.validator = None
        self.validation_worker = None
        self.all_results = []
        self.filtered_results = []
        self.all_items = []  # Cache of all items for Items tab
        self.statistics = {}  # Cache of statistics
        self.connection_test_result = None  # Store connection test result (True/False/None)
        self.connection_test_message = ""  # Store connection test message

        self._init_ui()
        self._test_jellyfin_connection()

        logger.info("JellyBaseView initialized")

    def _init_ui(self):
        """Initialize the user interface with tabbed layout."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("JellyBase - Jellyfin Library Management")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Connection section
        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout()

        self.conn_status_label = QLabel("● Status: Not connected")
        self.conn_status_label.setFont(QFont("Segoe UI", 12))
        conn_layout.addWidget(self.conn_status_label)

        btn_layout = QHBoxLayout()
        btn_test = QPushButton("Test Connection")
        btn_test.clicked.connect(self._test_jellyfin_connection)
        btn_config = QPushButton("Configure Jellyfin")
        btn_config.clicked.connect(self._open_jellyfin_settings)
        btn_layout.addWidget(btn_test)
        btn_layout.addWidget(btn_config)
        btn_layout.addStretch()
        conn_layout.addLayout(btn_layout)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # Tabbed interface
        self.tabs = QTabWidget()
        
        # Create tabs
        self.dashboard_tab = self._create_dashboard_tab()
        self.items_tab = self._create_items_tab()
        self.collections_tab = self._create_collections_tab()
        self.validation_tab = self._create_validation_tab()
        self.tools_tab = self._create_tools_tab()
        
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.items_tab, "Items")
        self.tabs.addTab(self.collections_tab, "Collections")
        self.tabs.addTab(self.validation_tab, "Validation")
        self.tabs.addTab(self.tools_tab, "Tools")
        
        # Connect tab change to auto-load items when Items tab is selected
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _create_dashboard_tab(self) -> QWidget:
        """Create Dashboard tab with statistics and overview."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Statistics section
        stats_group = QGroupBox("Library Statistics")
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel("Click 'Refresh Statistics' to load library data")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        btn_refresh_stats = QPushButton("Refresh Statistics")
        btn_refresh_stats.clicked.connect(self._refresh_statistics)
        stats_layout.addWidget(btn_refresh_stats)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Health score
        health_group = QGroupBox("Library Health")
        health_layout = QVBoxLayout()
        
        self.health_score_label = QLabel("Click 'Calculate Health Score' to analyze library health")
        self.health_score_label.setWordWrap(True)
        health_layout.addWidget(self.health_score_label)
        
        btn_health = QPushButton("Calculate Health Score")
        btn_health.clicked.connect(self._calculate_health_score)
        health_layout.addWidget(btn_health)
        
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)

        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        
        btn_validate = QPushButton("Run Full Validation")
        btn_validate.clicked.connect(self._quick_validate)
        actions_layout.addWidget(btn_validate)
        
        btn_refresh_lib = QPushButton("Refresh Library")
        btn_refresh_lib.clicked.connect(self._quick_refresh_library)
        actions_layout.addWidget(btn_refresh_lib)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_items_tab(self) -> QWidget:
        """Create Items tab with comprehensive item management."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Search and filter
        filter_group = QGroupBox("Search & Filter")
        filter_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.items_search = QLineEdit()
        self.items_search.setPlaceholderText("Search by title, genre, year...")
        self.items_search.textChanged.connect(self._filter_items)
        search_layout.addWidget(self.items_search)
        filter_layout.addLayout(search_layout)
        
        # Filter options
        filter_options = QHBoxLayout()
        filter_options.addWidget(QLabel("Type:"))
        self.items_type_filter = QComboBox()
        self.items_type_filter.addItems(["All", "Movie", "Episode", "Series"])
        self.items_type_filter.currentTextChanged.connect(self._filter_items)
        filter_options.addWidget(self.items_type_filter)
        
        filter_options.addWidget(QLabel("Library:"))
        self.items_library_filter = QComboBox()
        self.items_library_filter.addItem("All")
        self.items_library_filter.currentTextChanged.connect(self._filter_items)
        filter_options.addWidget(self.items_library_filter)
        
        # Populate library filter when connection is established
        self._populate_library_filter()
        
        filter_layout.addLayout(filter_options)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "☑", "Title", "Type", "Year", "Genre", "Library", "Path", "ID"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSortingEnabled(True)
        self.items_table.setMinimumHeight(400)
        layout.addWidget(self.items_table)
        
        # Load items button
        btn_load_items = QPushButton("Load Items from Jellyfin")
        btn_load_items.clicked.connect(self._load_items)
        layout.addWidget(btn_load_items)

        # Batch actions
        batch_group = QGroupBox("Batch Actions")
        batch_layout = QHBoxLayout()
        
        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self._items_select_all)
        batch_layout.addWidget(btn_select_all)
        
        btn_deselect_all = QPushButton("Deselect All")
        btn_deselect_all.clicked.connect(self._items_deselect_all)
        batch_layout.addWidget(btn_deselect_all)
        
        batch_layout.addStretch()
        
        btn_refresh_metadata = QPushButton("Refresh Metadata")
        btn_refresh_metadata.clicked.connect(self._batch_refresh_metadata)
        batch_layout.addWidget(btn_refresh_metadata)
        
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        widget.setLayout(layout)
        return widget

    def _create_collections_tab(self) -> QWidget:
        """Create Collections tab with collection management."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Collections list
        collections_group = QGroupBox("Collections")
        collections_layout = QVBoxLayout()
        
        self.collections_table = QTableWidget()
        self.collections_table.setColumnCount(4)
        self.collections_table.setHorizontalHeaderLabels([
            "Name", "Item Count", "Type", "ID"
        ])
        self.collections_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.collections_table.setSortingEnabled(True)
        self.collections_table.setMinimumHeight(300)
        collections_layout.addWidget(self.collections_table)
        
        btn_refresh_collections = QPushButton("Refresh Collections")
        btn_refresh_collections.clicked.connect(self._refresh_collections)
        collections_layout.addWidget(btn_refresh_collections)
        
        collections_group.setLayout(collections_layout)
        layout.addWidget(collections_group)

        # Auto-grouping
        grouping_group = QGroupBox("Auto-Grouping")
        grouping_layout = QVBoxLayout()
        
        genre_layout = QHBoxLayout()
        genre_layout.addWidget(QLabel("Genre:"))
        self.group_genre_input = QLineEdit()
        self.group_genre_input.setPlaceholderText("Enter genre name")
        genre_layout.addWidget(self.group_genre_input)
        btn_group_genre = QPushButton("Create Collection")
        btn_group_genre.clicked.connect(self._group_by_genre)
        genre_layout.addWidget(btn_group_genre)
        grouping_layout.addLayout(genre_layout)
        
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.group_year_input = QSpinBox()
        self.group_year_input.setRange(1900, 2100)
        self.group_year_input.setValue(2024)
        year_layout.addWidget(self.group_year_input)
        btn_group_year = QPushButton("Create Collection")
        btn_group_year.clicked.connect(self._group_by_year)
        year_layout.addWidget(btn_group_year)
        grouping_layout.addLayout(year_layout)
        
        series_layout = QHBoxLayout()
        series_layout.addWidget(QLabel("Series:"))
        self.group_series_input = QLineEdit()
        self.group_series_input.setPlaceholderText("Enter series name")
        series_layout.addWidget(self.group_series_input)
        btn_group_series = QPushButton("Create Collection")
        btn_group_series.clicked.connect(self._group_by_series)
        series_layout.addWidget(btn_group_series)
        grouping_layout.addLayout(series_layout)
        
        grouping_group.setLayout(grouping_layout)
        layout.addWidget(grouping_group)

        widget.setLayout(layout)
        return widget

    def _create_validation_tab(self) -> QWidget:
        """Create Validation tab with enhanced validation results."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Options
        options_group = QGroupBox("Validation Options")
        options_layout = QVBoxLayout()
        
        media_layout = QHBoxLayout()
        self.chk_movies = QCheckBox("Movies")
        self.chk_movies.setChecked(True)
        self.chk_episodes = QCheckBox("Episodes")
        self.chk_episodes.setChecked(True)
        media_layout.addWidget(QLabel("Media Types:"))
        media_layout.addWidget(self.chk_movies)
        media_layout.addWidget(self.chk_episodes)
        media_layout.addStretch()
        options_layout.addLayout(media_layout)
        
        check_layout = QHBoxLayout()
        self.chk_metadata = QCheckBox("Check Metadata")
        self.chk_metadata.setChecked(True)
        self.chk_quality = QCheckBox("Check Quality")
        self.chk_quality.setChecked(True)
        self.chk_subtitles = QCheckBox("Check Subtitles")
        self.chk_subtitles.setChecked(True)
        check_layout.addWidget(self.chk_metadata)
        check_layout.addWidget(self.chk_quality)
        check_layout.addWidget(self.chk_subtitles)
        check_layout.addStretch()
        options_layout.addLayout(check_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Action buttons
        action_layout = QHBoxLayout()
        
        self.btn_scan = QPushButton("▶ Run Validation")
        self.btn_scan.setMinimumHeight(40)
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_scan.clicked.connect(self._start_validation)
        
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_csv)
        
        action_layout.addWidget(self.btn_scan)
        action_layout.addWidget(self.btn_export)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout()
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Items",
            "Issues Only (Missing/Invalid/Duplicate)",
            "Valid Only",
            "Missing Only",
            "Duplicates Only",
            "Metadata Issues",
            "Quality Issues",
            "Subtitle Issues"
        ])
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        results_layout.addLayout(filter_layout)
        
        # Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(9)
        self.results_table.setHorizontalHeaderLabels([
            "☑", "Status", "Title", "Path", "ID", "Size", "Resolution", "Codec", "Issues"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSortingEnabled(True)
        self.results_table.setMinimumHeight(300)
        results_layout.addWidget(self.results_table)
        
        # Summary
        self.summary_label = QLabel("No results yet")
        results_layout.addWidget(self.summary_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)

        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        action_btn_layout = QHBoxLayout()
        btn_select_issues = QPushButton("Select All Issues")
        btn_select_issues.clicked.connect(self._select_all_issues)
        btn_deselect = QPushButton("Deselect All")
        btn_deselect.clicked.connect(self._deselect_all)
        action_btn_layout.addWidget(btn_select_issues)
        action_btn_layout.addWidget(btn_deselect)
        action_btn_layout.addStretch()
        actions_layout.addLayout(action_btn_layout)
        
        delete_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Delete Selected from Jellyfin")
        self.btn_delete.setMinimumHeight(35)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_selected)
        
        self.chk_dry_run = QCheckBox("Dry Run (preview only, no changes)")
        self.chk_dry_run.setChecked(True)
        self.chk_dry_run.setStyleSheet("font-weight: bold;")
        
        delete_layout.addWidget(self.btn_delete)
        delete_layout.addWidget(self.chk_dry_run)
        delete_layout.addStretch()
        actions_layout.addLayout(delete_layout)
        
        warning_label = QLabel("⚠ Note: Physical files will NOT be deleted, only Jellyfin database entries")
        warning_label.setStyleSheet("color: #e67e22; font-weight: bold;")
        actions_layout.addWidget(warning_label)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        widget.setLayout(layout)
        return widget

    def _create_tools_tab(self) -> QWidget:
        """Create Tools tab for adding/removing items and library operations."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add items
        add_group = QGroupBox("Add Items")
        add_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Path:"))
        self.add_path_input = QLineEdit()
        self.add_path_input.setPlaceholderText("Enter filesystem path to scan")
        path_layout.addWidget(self.add_path_input)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_add_path)
        path_layout.addWidget(btn_browse)
        add_layout.addLayout(path_layout)
        
        btn_add = QPushButton("Scan Path and Add to Library")
        btn_add.clicked.connect(self._add_items_by_path)
        add_layout.addWidget(btn_add)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # Remove items
        remove_group = QGroupBox("Remove Items")
        remove_layout = QVBoxLayout()
        remove_layout.addWidget(QLabel("Use the Items or Validation tab to select and remove items"))
        remove_group.setLayout(remove_layout)
        layout.addWidget(remove_group)

        # Refresh library
        refresh_group = QGroupBox("Refresh Library")
        refresh_layout = QVBoxLayout()
        
        btn_full_refresh = QPushButton("Full Library Refresh")
        btn_full_refresh.clicked.connect(self._full_refresh_library)
        refresh_layout.addWidget(btn_full_refresh)
        
        path_refresh_layout = QHBoxLayout()
        path_refresh_layout.addWidget(QLabel("Path:"))
        self.refresh_path_input = QLineEdit()
        self.refresh_path_input.setPlaceholderText("Enter path for targeted refresh")
        path_refresh_layout.addWidget(self.refresh_path_input)
        btn_path_refresh = QPushButton("Refresh Path")
        btn_path_refresh.clicked.connect(self._refresh_library_path)
        path_refresh_layout.addWidget(btn_path_refresh)
        refresh_layout.addLayout(path_refresh_layout)
        
        refresh_group.setLayout(refresh_layout)
        layout.addWidget(refresh_group)

        # Export/Import
        export_group = QGroupBox("Export/Import")
        export_layout = QVBoxLayout()
        
        btn_export_library = QPushButton("Export Library Data (JSON)")
        btn_export_library.clicked.connect(self._export_library_data)
        export_layout.addWidget(btn_export_library)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # Tab management
    def _on_tab_changed(self, index: int):
        """Handle tab change - auto-load data when needed."""
        tab_name = self.tabs.tabText(index)
        if tab_name == "Items" and not self.all_items:
            # Auto-load items when Items tab is first opened
            self._load_items()
        elif tab_name == "Collections":
            # Auto-refresh collections when Collections tab is opened
            if self.jellyfin_client:
                self._refresh_collections()
    
    # Connection and initialization methods
    def _set_status(self, message: str):
        """Set status message in main window's status bar."""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(message)
        except Exception:
            logger.warning(f"Could not set status: {message}")

    def closeEvent(self, event):
        """
        Clean up resources on close (Commandment #7: Resource Safety).
        
        Disconnects ValidationWorker signals and stops worker thread gracefully
        to prevent memory leaks.
        """
        if self.validation_worker and self.validation_worker.isRunning():
            # Disconnect signals to prevent memory leaks
            try:
                self.validation_worker.progress.disconnect()
                self.validation_worker.finished.disconnect()
                self.validation_worker.error.disconnect()
            except TypeError:
                # Signals already disconnected or never connected
                pass

            # Stop worker gracefully
            self.validation_worker.quit()
            if not self.validation_worker.wait(5000):  # 5 second timeout (positional arg for PyQt6)
                logger.warning("ValidationWorker did not stop within timeout, terminating")
                self.validation_worker.terminate()
                self.validation_worker.wait()

            logger.info("ValidationWorker cleaned up")

        super().closeEvent(event)

    def _test_jellyfin_connection(self):
        """Test connection to Jellyfin server and store result."""
        try:
            config_mgr = JellyfinConfigManager()
            if not config_mgr.is_enabled():
                self.conn_status_label.setText("● Status: Not configured")
                self.conn_status_label.setStyleSheet("color: #e67e22;")
                self._set_status("⚠ Jellyfin not configured. Click 'Configure Jellyfin' to set up.")
                self.connection_test_result = False
                self.connection_test_message = "Not configured"
                return

            server_url = config_mgr.get_server_url()
            api_key = config_mgr.get_api_key()

            if not server_url or not api_key:
                self.conn_status_label.setText("● Status: Missing URL or API key")
                self.conn_status_label.setStyleSheet("color: #e74c3c;")
                self._set_status("✗ Jellyfin: Missing server URL or API key")
                self.connection_test_result = False
                self.connection_test_message = "Missing URL or API key"
                return

            self.jellyfin_client = JellyfinClient(server_url=server_url, api_key=api_key)

            if self.jellyfin_client.test_connection():
                self.conn_status_label.setText(f"● Status: Connected to {server_url}")
                self.conn_status_label.setStyleSheet("color: #27ae60;")
                self._set_status(f"✓ Connected to Jellyfin: {server_url}")
                self.validator = JellyfinValidator(self.jellyfin_client)
                self._populate_library_filter()
                self.connection_test_result = True
                self.connection_test_message = f"Connected to {server_url}"
                logger.info(f"Connected to Jellyfin: {server_url}")
            else:
                self.conn_status_label.setText("● Status: Connection failed")
                self.conn_status_label.setStyleSheet("color: #e74c3c;")
                self._set_status("✗ Jellyfin connection test failed")
                self.jellyfin_client = None
                self.connection_test_result = False
                self.connection_test_message = "Connection test failed"
                logger.warning("Jellyfin connection test failed")

        except Exception as e:
            logger.error(f"Connection test error: {e}", exc_info=True)
            self.conn_status_label.setText("● Status: Error")
            self.conn_status_label.setStyleSheet("color: #e74c3c;")
            self._set_status(f"✗ Jellyfin connection error: {e}")
            self.jellyfin_client = None
            self.connection_test_result = False
            self.connection_test_message = f"Error: {str(e)}"

    def _open_jellyfin_settings(self):
        """Open Jellyfin settings dialog and reload connection if settings were saved."""
        try:
            from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog
            from PyQt6.QtWidgets import QDialog
            dialog = JellyfinSettingsDialog(self)
            # Check if dialog was accepted (settings were saved)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Settings were saved - reload Jellyfin connection
                logger.info("Jellyfin settings changed - reloading connection")
                self._test_jellyfin_connection()
                self._set_status("✓ Jellyfin settings updated - connection reloaded")
        except Exception as e:
            logger.error(f"Failed to open settings dialog: {e}", exc_info=True)
            self._set_status(f"✗ Failed to open settings: {e}")
    
    def _populate_library_filter(self):
        """Populate library filter dropdown."""
        if not self.jellyfin_client:
            return

        try:
            libraries = self.jellyfin_client.get_libraries()
            # Block signals while populating to prevent filter cascade
            self.items_library_filter.blockSignals(True)
            self.items_library_filter.clear()
            self.items_library_filter.addItem("All")
            for lib in libraries:
                self.items_library_filter.addItem(lib.get('Name', 'Unknown'))
            self.items_library_filter.blockSignals(False)
        except Exception as e:
            self.items_library_filter.blockSignals(False)
            logger.warning(f"Could not populate library filter: {e}")

    # Dashboard methods
    def _refresh_statistics(self):
        """Refresh library statistics for dashboard."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            self._set_status("Loading library statistics...")
            stats = self.jellyfin_client.get_item_statistics()
            self.statistics = stats
            
            # Format statistics display
            stats_text = f"""
<b>Library Statistics</b><br><br>
<b>Total Items:</b> {stats['total_items']}<br>
<b>Total Size:</b> {self._format_size(stats['total_size'])}<br><br>
<b>By Type:</b><br>
"""
            for item_type, count in stats['by_type'].items():
                stats_text += f"  • {item_type}: {count}<br>"
            
            stats_text += "<br><b>By Library:</b><br>"
            for library, count in stats['by_library'].items():
                stats_text += f"  • {library}: {count}<br>"
            
            self.stats_label.setText(stats_text)
            self._set_status("✓ Statistics loaded")
            logger.info("Statistics refreshed")
        except Exception as e:
            logger.error(f"Error refreshing statistics: {e}", exc_info=True)
            self._set_status(f"✗ Error loading statistics: {e}")

    def _quick_validate(self):
        """Quick validation from dashboard."""
        self.tabs.setCurrentIndex(3)  # Switch to Validation tab
        self._start_validation()

    def _quick_refresh_library(self):
        """Quick library refresh from dashboard."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            self._set_status("Refreshing library...")
            if self.jellyfin_client.refresh_library():
                self._set_status("✓ Library refresh triggered")
                logger.info("Library refresh triggered from dashboard")
            else:
                self._set_status("✗ Library refresh failed")
        except Exception as e:
            logger.error(f"Error refreshing library: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")
    
    def _calculate_health_score(self):
        """Calculate and display library health score."""
        if not self.jellyfin_client or not self.validator:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            self._set_status("Calculating library health score...")
            from scripts.core.jellybase_analyzer import calculate_health_score
            
            # Get sample of items for health score calculation
            items = self.jellyfin_client.get_all_items()
            if not items:
                self.health_score_label.setText("No items found in library")
                return
            
            score = calculate_health_score(self.validator, items)
            
            # Format health score display
            if score >= 80:
                color = "#27ae60"  # Green
                status = "Excellent"
            elif score >= 60:
                color = "#f39c12"  # Orange
                status = "Good"
            elif score >= 40:
                color = "#e67e22"  # Dark orange
                status = "Fair"
            else:
                color = "#e74c3c"  # Red
                status = "Poor"
            
            health_text = f"""
<b>Library Health Score: <span style="color: {color}; font-size: 24px;">{score}/100</span></b><br>
<b>Status:</b> {status}<br><br>
<b>Factors:</b><br>
• File Validity (40%)<br>
• Metadata Completeness (30%)<br>
• Subtitle Coverage (20%)<br>
• Duplicate Count (10%)<br>
"""
            self.health_score_label.setText(health_text)
            self._set_status(f"✓ Health score calculated: {score}/100")
            logger.info(f"Health score: {score}/100")
        except Exception as e:
            logger.error(f"Error calculating health score: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")
            self.health_score_label.setText(f"Error calculating health score: {e}")

    # Items tab methods
    def _load_items(self):
        """Load items from Jellyfin library."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            self._set_status("Loading items from Jellyfin...")
            self.all_items = self.jellyfin_client.get_all_items()
            
            # Update library filter
            libraries = self.jellyfin_client.get_libraries()
            self.items_library_filter.clear()
            self.items_library_filter.addItem("All")
            for lib in libraries:
                self.items_library_filter.addItem(lib.get('Name', 'Unknown'))
            
            self._populate_items_table()
            self._set_status(f"✓ Loaded {len(self.all_items)} items")
            logger.info(f"Loaded {len(self.all_items)} items")
        except Exception as e:
            logger.error(f"Error loading items: {e}", exc_info=True)
            self._set_status(f"✗ Error loading items: {e}")
    
    def _populate_items_table(self):
        """Populate items table with all items."""
        items_to_show = self.all_items
        
        # Apply filters
        filters = {}
        type_filter = self.items_type_filter.currentText()
        if type_filter != "All":
            filters['item_types'] = [type_filter]
        
        library_filter = self.items_library_filter.currentText()
        if library_filter != "All":
            # Find library ID
            libraries = self.jellyfin_client.get_libraries() if self.jellyfin_client else []
            library_id = None
            for lib in libraries:
                if lib.get('Name') == library_filter:
                    library_id = lib.get('Id')
                    break
            if library_id:
                filters['libraries'] = [library_id]
        
        search_text = self.items_search.text().strip()
        if search_text:
            filters['search'] = search_text
        
        # Apply filters
        if filters:
            from scripts.core.jellybase_manager import JellyBaseManager
            manager = JellyBaseManager()
            items_to_show = manager.apply_filters(self.all_items, filters)
        
        # Populate table
        self.items_table.setSortingEnabled(False)
        self.items_table.setRowCount(len(items_to_show))

        # Cache libraries lookup ONCE before the loop (not per-row!)
        cached_libraries = []
        if self.jellyfin_client:
            try:
                cached_libraries = self.jellyfin_client.get_libraries()
            except Exception:
                pass

        for row, item in enumerate(items_to_show):
            try:
                # Checkbox
                checkbox = QCheckBox()
                self.items_table.setCellWidget(row, 0, checkbox)
                
                # Title
                title_item = QTableWidgetItem(item.get('Name', 'Unknown'))
                self.items_table.setItem(row, 1, title_item)
                
                # Type
                type_item = QTableWidgetItem(item.get('Type', 'Unknown'))
                self.items_table.setItem(row, 2, type_item)
                
                # Year
                year_item = QTableWidgetItem(str(item.get('ProductionYear', '')))
                self.items_table.setItem(row, 3, year_item)
                
                # Genre
                genres = ', '.join(item.get('Genres', []))
                genre_item = QTableWidgetItem(genres)
                self.items_table.setItem(row, 4, genre_item)
                
                # Library (look up from cached libraries - NOT per-row API call!)
                library_name = 'N/A'
                parent_id = item.get('ParentId')
                for lib in cached_libraries:
                    if lib.get('Id') == parent_id:
                        library_name = lib.get('Name', 'Unknown')
                        break
                library_item = QTableWidgetItem(library_name)
                self.items_table.setItem(row, 5, library_item)
                
                # Path
                path_item = QTableWidgetItem(item.get('Path', ''))
                self.items_table.setItem(row, 6, path_item)
                
                # ID
                id_item = QTableWidgetItem(item.get('Id', 'N/A'))
                self.items_table.setItem(row, 7, id_item)
                
            except Exception as e:
                logger.error(f"Failed to populate items row {row}: {e}", exc_info=True)
        
        self.items_table.setSortingEnabled(True)
    
    def _filter_items(self):
        """Filter items table based on search and filters."""
        if not self.all_items:
            # Load items first
            self._load_items()
        else:
            self._populate_items_table()

    def _items_select_all(self):
        """Select all items in items table."""
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def _items_deselect_all(self):
        """Deselect all items in items table."""
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def _batch_refresh_metadata(self):
        """Batch refresh metadata for selected items."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        # Get selected item IDs
        selected_ids = []
        for row in range(self.items_table.rowCount()):
            checkbox = self.items_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                id_item = self.items_table.item(row, 7)  # ID column
                if id_item:
                    selected_ids.append(id_item.text())
        
        if not selected_ids:
            self._set_status("⚠ No items selected")
            return
        
        try:
            self._set_status(f"Refreshing metadata for {len(selected_ids)} items...")
            # Use batch operation
            result = batch_update_metadata(self.jellyfin_client, selected_ids, {})
            # Actually trigger refresh for each item
            for item_id in selected_ids:
                self.jellyfin_client.refresh_item(item_id)
            self._set_status(f"✓ Metadata refresh triggered for {len(selected_ids)} items")
        except Exception as e:
            logger.error(f"Error refreshing metadata: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    # Collections tab methods
    def _refresh_collections(self):
        """Refresh collections list."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            self._set_status("Loading collections...")
            collections = self.jellyfin_client.get_collections()
            
            self.collections_table.setRowCount(len(collections))
            for row, collection in enumerate(collections):
                self.collections_table.setItem(row, 0, QTableWidgetItem(collection.get('Name', 'Unknown')))
                self.collections_table.setItem(row, 1, QTableWidgetItem(str(collection.get('ChildCount', 0))))
                self.collections_table.setItem(row, 2, QTableWidgetItem(collection.get('Type', 'Unknown')))
                self.collections_table.setItem(row, 3, QTableWidgetItem(collection.get('Id', 'N/A')))
            
            self._set_status(f"✓ Loaded {len(collections)} collections")
            logger.info(f"Loaded {len(collections)} collections")
        except Exception as e:
            logger.error(f"Error loading collections: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    def _group_by_genre(self):
        """Create collection grouped by genre."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        genre = self.group_genre_input.text().strip()
        if not genre:
            self._set_status("⚠ Please enter a genre name")
            return
        
        try:
            self._set_status(f"Creating collection for genre: {genre}...")
            collection_id = create_collection_by_genre(self.jellyfin_client, genre)
            if collection_id:
                self._set_status(f"✓ Created collection for genre: {genre}")
                self.group_genre_input.clear()
                self._refresh_collections()
            else:
                self._set_status(f"✗ Failed to create collection for genre: {genre}")
        except Exception as e:
            logger.error(f"Error creating genre collection: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    def _group_by_year(self):
        """Create collection grouped by year."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        year = self.group_year_input.value()
        
        try:
            self._set_status(f"Creating collection for year: {year}...")
            collection_id = create_collection_by_year(self.jellyfin_client, year)
            if collection_id:
                self._set_status(f"✓ Created collection for year: {year}")
                self._refresh_collections()
            else:
                self._set_status(f"✗ Failed to create collection for year: {year}")
        except Exception as e:
            logger.error(f"Error creating year collection: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    def _group_by_series(self):
        """Create collection grouped by series."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        series = self.group_series_input.text().strip()
        if not series:
            self._set_status("⚠ Please enter a series name")
            return
        
        try:
            self._set_status(f"Creating collection for series: {series}...")
            collection_id = create_collection_by_series(self.jellyfin_client, series)
            if collection_id:
                self._set_status(f"✓ Created collection for series: {series}")
                self.group_series_input.clear()
                self._refresh_collections()
            else:
                self._set_status(f"✗ Failed to create collection for series: {series}")
        except Exception as e:
            logger.error(f"Error creating series collection: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    # Validation tab methods
    def _start_validation(self):
        """Start validation scan with proper cleanup of previous worker."""
        if not self.jellyfin_client or not self.validator:
            self._set_status("✗ Not connected to Jellyfin")
            return

        # Cleanup old worker before creating new one (Commandment #7: Resource Safety)
        if self.validation_worker:
            if self.validation_worker.isRunning():
                self._set_status("⚠ Validation already running")
                return
            
            # Disconnect old signals to prevent memory leaks
            try:
                self.validation_worker.progress.disconnect()
                self.validation_worker.finished.disconnect()
                self.validation_worker.error.disconnect()
            except TypeError:
                # Signals already disconnected or never connected
                pass

        # Get selected media types
        media_types = []
        if self.chk_movies.isChecked():
            media_types.append("Movie")
        if self.chk_episodes.isChecked():
            media_types.append("Episode")

        if not media_types:
            self._set_status("⚠ Please select at least one media type")
            return

        # Start validation worker
        self.validation_worker = ValidationWorker(
            self.validator,
            media_types,
            check_metadata=self.chk_metadata.isChecked(),
            check_quality=self.chk_quality.isChecked(),
            check_subtitles=self.chk_subtitles.isChecked()
        )
        self.validation_worker.progress.connect(self._on_validation_progress)
        self.validation_worker.finished.connect(self._on_validation_finished)
        self.validation_worker.error.connect(self._on_validation_error)

        self.btn_scan.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_status("Validating Jellyfin library...")

        self.validation_worker.start()
        logger.info(f"Started validation for: {media_types}")

    def _on_validation_progress(self, message: str, current: int, total: int):
        """Handle validation progress updates."""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        self._set_status(message)

    def _on_validation_finished(self, results: List[Dict]):
        """Handle validation completion."""
        self.all_results = results
        self.filtered_results = results

        self.progress_bar.setVisible(False)
        self.btn_scan.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_delete.setEnabled(True)

        self._populate_validation_table()
        self._update_validation_summary()

        self._set_status(f"✓ Validation complete: {len(results)} items validated")
        logger.info(f"Validation complete: {len(results)} items")
        
        # Clean up worker signals after completion (Commandment #7: Resource Safety)
        if self.validation_worker:
            try:
                self.validation_worker.progress.disconnect()
                self.validation_worker.finished.disconnect()
                self.validation_worker.error.disconnect()
            except TypeError:
                # Signals already disconnected
                pass

    def _on_validation_error(self, error_msg: str):
        """Handle validation error."""
        self.progress_bar.setVisible(False)
        self.btn_scan.setEnabled(True)
        self._set_status(f"✗ {error_msg}")
        logger.error(f"Validation error: {error_msg}")
        
        # Clean up worker signals after error (Commandment #7: Resource Safety)
        if self.validation_worker:
            try:
                self.validation_worker.progress.disconnect()
                self.validation_worker.finished.disconnect()
                self.validation_worker.error.disconnect()
            except TypeError:
                # Signals already disconnected
                pass

    def _apply_filter(self):
        """Apply filter to validation results."""
        filter_text = self.filter_combo.currentText()

        if filter_text == "All Items":
            self.filtered_results = self.all_results
        elif filter_text == "Issues Only (Missing/Invalid/Duplicate)":
            self.filtered_results = [r for r in self.all_results if r['status'] != STATUS_VALID]
        elif filter_text == "Valid Only":
            self.filtered_results = [r for r in self.all_results if r['status'] == STATUS_VALID]
        elif filter_text == "Missing Only":
            self.filtered_results = [r for r in self.all_results if r['status'] == STATUS_MISSING]
        elif filter_text == "Duplicates Only":
            self.filtered_results = [r for r in self.all_results if r['status'] == STATUS_DUPLICATE]
        elif filter_text == "Metadata Issues":
            self.filtered_results = [r for r in self.all_results if 'metadata' in r.get('issue', '').lower()]
        elif filter_text == "Quality Issues":
            self.filtered_results = [r for r in self.all_results if 'quality' in r.get('issue', '').lower()]
        elif filter_text == "Subtitle Issues":
            self.filtered_results = [r for r in self.all_results if 'subtitle' in r.get('issue', '').lower()]

        self._populate_validation_table()
        self._update_validation_summary()

    def _populate_validation_table(self):
        """Populate the validation results table."""
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(len(self.filtered_results))

        for row, result in enumerate(self.filtered_results):
            try:
                # Checkbox
                checkbox = QCheckBox()
                self.results_table.setCellWidget(row, 0, checkbox)

                # Status
                status_item = QTableWidgetItem(result['status'])
                if result['status'] == STATUS_VALID:
                    status_item.setBackground(QColor(39, 174, 96, 50))  # Green
                elif result['status'] == STATUS_MISSING:
                    status_item.setBackground(QColor(231, 76, 60, 50))  # Red
                elif result['status'] == STATUS_DUPLICATE:
                    status_item.setBackground(QColor(243, 156, 18, 50))  # Orange
                else:  # INVALID
                    status_item.setBackground(QColor(255, 235, 59, 50))  # Yellow
                self.results_table.setItem(row, 1, status_item)

                # Title
                title_item = QTableWidgetItem(result['title'])
                self.results_table.setItem(row, 2, title_item)

                # Path
                path_item = QTableWidgetItem(result['path'])
                self.results_table.setItem(row, 3, path_item)

                # ID
                id_item = QTableWidgetItem(result['jellyfin_id'])
                self.results_table.setItem(row, 4, id_item)

                # Size
                size_str = self._format_size(result['file_size']) if result.get('file_size') else '-'
                size_item = QTableWidgetItem(size_str)
                self.results_table.setItem(row, 5, size_item)

                # Resolution
                resolution_item = QTableWidgetItem(result.get('resolution', '-'))
                self.results_table.setItem(row, 6, resolution_item)

                # Codec
                codec_item = QTableWidgetItem(result.get('codec', '-'))
                self.results_table.setItem(row, 7, codec_item)

                # Issues
                issue_item = QTableWidgetItem(result.get('issue', ''))
                self.results_table.setItem(row, 8, issue_item)

            except Exception as e:
                logger.error(f"Failed to populate row {row}: {e}", exc_info=True)

        self.results_table.setSortingEnabled(True)

    def _update_validation_summary(self):
        """Update validation summary statistics."""
        total = len(self.all_results)
        valid = sum(1 for r in self.all_results if r['status'] == STATUS_VALID)
        missing = sum(1 for r in self.all_results if r['status'] == STATUS_MISSING)
        invalid = sum(1 for r in self.all_results if r['status'] == STATUS_INVALID)
        duplicates = sum(1 for r in self.all_results if r['status'] == STATUS_DUPLICATE)
        issues = total - valid

        filtered_count = len(self.filtered_results)

        summary = (
            f"Total: {total} | Valid: {valid} | Issues: {issues} "
            f"(Missing: {missing}, Invalid: {invalid}, Duplicates: {duplicates}) | "
            f"Showing: {filtered_count}"
        )
        self.summary_label.setText(summary)

    def _select_all_issues(self):
        """Select all rows with issues."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                status_item = self.results_table.item(row, 1)
                if status_item and status_item.text() != STATUS_VALID:
                    checkbox.setChecked(True)

    def _deselect_all(self):
        """Deselect all rows."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def _delete_selected(self):
        """Delete selected items from Jellyfin."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return

        # Get selected items
        selected_ids = []
        selected_titles = []

        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                id_item = self.results_table.item(row, 4)
                title_item = self.results_table.item(row, 2)
                if id_item:
                    selected_ids.append(id_item.text())
                    selected_titles.append(title_item.text() if title_item else "Unknown")

        if not selected_ids:
            self._set_status("⚠ No items selected")
            return

        # Dry run mode
        if self.chk_dry_run.isChecked():
            self._set_status(f"⚠ DRY RUN: Would delete {len(selected_ids)} items (no changes made)")
            logger.info(f"Dry run: would delete {len(selected_ids)} items")
            logger.info(f"Items: {selected_titles}")
            return

        # Real deletion
        self._set_status(f"Deleting {len(selected_ids)} items from Jellyfin...")
        self.btn_delete.setEnabled(False)

        deleted = 0
        failed = 0

        for item_id, title in zip(selected_ids, selected_titles):
            try:
                if self.jellyfin_client.delete_item(item_id):
                    deleted += 1
                    logger.info(f"Deleted: {title} (ID: {item_id})")
                else:
                    failed += 1
                    logger.warning(f"Failed to delete: {title} (ID: {item_id})")
            except Exception as e:
                failed += 1
                logger.error(f"Error deleting {title}: {e}", exc_info=True)

        self.btn_delete.setEnabled(True)
        self._set_status(f"✓ Deleted {deleted} items, {failed} failed")

        # Re-scan to update table
        if deleted > 0:
            self._start_validation()

    def _export_csv(self):
        """Export validation results to CSV."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                f"jellybase_validation_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if not filename:
                return

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Status', 'Title', 'Path', 'Jellyfin ID', 'Size', 'Resolution', 'Codec', 'Issues'])

                for result in self.filtered_results:
                    size_str = self._format_size(result['file_size']) if result.get('file_size') else ''
                    writer.writerow([
                        result['status'],
                        result['title'],
                        result['path'],
                        result['jellyfin_id'],
                        size_str,
                        result.get('resolution', ''),
                        result.get('codec', ''),
                        result.get('issue', '')
                    ])

            self._set_status(f"✓ Exported {len(self.filtered_results)} items to {filename}")
            logger.info(f"Exported to: {filename}")

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            self._set_status(f"✗ Export failed: {e}")

    # Tools tab methods
    def _browse_add_path(self):
        """Browse for path to add."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Scan",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.add_path_input.setText(folder)

    def _add_items_by_path(self):
        """Add items by scanning a path."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        path = self.add_path_input.text().strip()
        if not path:
            self._set_status("⚠ Please enter a path")
            return
        
        try:
            self._set_status(f"Scanning path: {path}...")
            if self.jellyfin_client.add_item_by_path(path):
                self._set_status(f"✓ Scan triggered for path: {path}")
                self.add_path_input.clear()
            else:
                self._set_status(f"✗ Failed to trigger scan for path: {path}")
        except Exception as e:
            logger.error(f"Error adding items by path: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    def _full_refresh_library(self):
        """Trigger full library refresh."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            self._set_status("Refreshing library...")
            if self.jellyfin_client.refresh_library():
                self._set_status("✓ Library refresh triggered")
                logger.info("Full library refresh triggered")
            else:
                self._set_status("✗ Library refresh failed")
        except Exception as e:
            logger.error(f"Error refreshing library: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    def _refresh_library_path(self):
        """Trigger targeted library refresh for a path."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        path = self.refresh_path_input.text().strip()
        if not path:
            self._set_status("⚠ Please enter a path")
            return
        
        try:
            self._set_status(f"Refreshing library path: {path}...")
            if self.jellyfin_client.refresh_library_by_path(path):
                self._set_status(f"✓ Library refresh triggered for path: {path}")
                self.refresh_path_input.clear()
            else:
                self._set_status(f"✗ Failed to refresh path: {path}")
        except Exception as e:
            logger.error(f"Error refreshing library path: {e}", exc_info=True)
            self._set_status(f"✗ Error: {e}")

    def _export_library_data(self):
        """Export library data to JSON."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return
        
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Library Data",
                f"jellybase_library_{time.strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )

            if not filename:
                return

            # Get all items
            self._set_status("Loading library data...")
            items = self.jellyfin_client.get_all_items()
            stats = self.jellyfin_client.get_item_statistics()
            
            data = {
                'export_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'statistics': stats,
                'items': items
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            self._set_status(f"✓ Exported {len(items)} items to {filename}")
            logger.info(f"Exported library data to: {filename}")

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            self._set_status(f"✗ Export failed: {e}")

    # Utility methods
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


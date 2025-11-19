#!/usr/bin/env python3
"""
Scan Results View - Dedicated view for reviewing scan results

Extracted from ScanView to provide focused results review in separate tab.
Displays file table, search/filter, export, folder overview, and duplicate detection.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from collections import defaultdict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QGroupBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt
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
    Dedicated view for scan results review.
    
    Features:
    - Sortable/searchable results table
    - Export to CSV
    - Hierarchical folder overview
    - Duplicate detection summary
    """
    
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
        3. Creates the UI components
        4. Loads scan results from the database
        5. Logs successful initialization
        
        Error Handling:
            If initialization fails, shows critical error dialog and re-raises
            the exception to prevent corrupted UI state.
        
        Data Structures:
            - scanned_files: List of all FileRecord objects from the scan
            - folder_structure: Hierarchical dict of folder statistics
            - duplicate_groups: Dict mapping MD5 hashes to duplicate file lists
        """
        try:
            super().__init__(parent)

            self.project = project
            self.project_manager = project_manager
            self.inventory_repo = InventoryRepository()
            self.scan_session_id = scan_session_id

            self.scanned_files: List[FileRecord] = []
            self.folder_structure: Dict[Path, Dict[str, Any]] = {}
            self.duplicate_groups: Dict[str, List[FileRecord]] = {}

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
        Initialize the user interface components.
        
        Creates the main layout and UI structure for the scan results view,
        including title, results table section, and overview statistics section.
        
        The UI layout consists of:
        1. Title label with session ID
        2. Results section (expandable table with search/filter/export)
        3. Overview section (summary statistics and folder structure)
        
        Layout Configuration:
            - Vertical box layout with 10px spacing and margins
            - Title with large, bold font and styled background
            - Results section gets stretch factor 1 (takes available space)
            - Overview section has fixed height
        
        Error Handling:
            If UI initialization fails, shows critical error dialog and re-raises
            exception to prevent corrupted interface state.
        """
        try:
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)

            # Title
            title = QLabel(f"Scan Results - Session #{self.scan_session_id}")
            title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            title.setStyleSheet("color: #2c3e50; padding: 10px;")
            layout.addWidget(title)

            # Results section
            results_group = self._create_results_section()
            layout.addWidget(results_group, 1)  # Stretch to fill space

            # Overview section
            overview_group = self._create_overview_section()
            layout.addWidget(overview_group)

            self.setLayout(layout)
        except Exception as e:
            logger.error(f"Failed to initialize scan results UI: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "UI Initialization Error",
                f"Failed to initialize scan results interface:\n\n{str(e)}\n\nPlease restart the application.",
            )
            raise
    
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
           - Metadata: Additional file information
        4. Summary label showing file count and statistics
        
        Table Configuration:
            - Interactive column resizing
            - Pre-set column widths for optimal display
            - Sorting enabled on all columns
            - Minimum height of 200px
        
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
            self.btn_export.setEnabled(bool(self.scanned_files))
            search_layout.addWidget(self.btn_export)

            layout.addLayout(search_layout)

            # Results table
            self.results_table = QTableWidget()
            self.results_table.setMinimumHeight(200)
            self.results_table.setColumnCount(6)
            self.results_table.setHorizontalHeaderLabels([
                "Filename", "Path", "Size (MB)", "Type", "MD5", "Metadata"
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
            self.lbl_summary.setStyleSheet("color: #566573; padding: 5px;")
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
        7. Enables export functionality
        
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
            - Export button enabled for successful loads
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
            
            # Load FileRecords from inventory (assuming session_id foreign key)
            self.scanned_files = self.inventory_repo.get_files_by_session(self.scan_session_id)
            
            if len(self.scanned_files) != total_files:
                logger.warning(f"Mismatch: DB reports {total_files} files, loaded {len(self.scanned_files)}")
            
            # Load folder structure (recompute or from options if cached)
            self._compute_folder_structure()
            
            # Populate UI
            self._populate_results_table(self.scanned_files)
            self._update_overview()
            
            # Update summary
            total_size_gb = total_size_bytes / (1024 ** 3) if total_size_bytes else 0
            self.lbl_summary.setText(
                f"Loaded {len(self.scanned_files)} files ({total_size_gb:.2f} GB) "
                f"from session #{self.scan_session_id}"
            )
            
            self.btn_export.setEnabled(True)
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
    
    def _populate_results_table(self, files: List[FileRecord]):
        """
        Populate the results table with scanned files.
        
        Fills the QTableWidget with file information from the scanned files list,
        displaying filename, path, size, type, MD5 hash, and metadata status.
        
        Args:
            files (List[FileRecord]): List of file records to display in the table
            
        Table Columns:
            0. Filename: Base filename from absolute path
            1. Path: Parent directory path
            2. Size (MB): File size in megabytes (formatted to 1 decimal)
            3. Type: File extension (media type indicator)
            4. MD5: First 8 characters of hash + "..." (or "N/A" if missing)
            5. Metadata: Status indicator ("✓" for extracted, placeholder)
        
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
                    # Filename
                    self.results_table.setItem(row, 0, QTableWidgetItem(file_record.absolute_path.name))
                    
                    # Path
                    self.results_table.setItem(row, 1, QTableWidgetItem(str(file_record.absolute_path.parent)))
                    
                    # Size (MB)
                    size_mb = file_record.size_bytes / (1024 * 1024)
                    self.results_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.1f}"))
                    
                    # Type
                    self.results_table.setItem(row, 3, QTableWidgetItem(file_record.extension))
                    
                    # MD5
                    md5_text = file_record.md5_hash[:8] + "..." if file_record.md5_hash else "N/A"
                    self.results_table.setItem(row, 4, QTableWidgetItem(md5_text))
                    
                    # Metadata (placeholder)
                    self.results_table.setItem(row, 5, QTableWidgetItem("✓"))  # Assume extracted
                    
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
            
            logger.debug(f"Applied filter '{search_text}' to results table")
            
        except Exception as e:
            logger.error(f"Failed to filter results: {e}", exc_info=True)
            QMessageBox.warning(self, "Filter Error", f"Failed to apply filter:\n\n{str(e)}")
    
    def _export_results(self):
        """
        Export scan results to CSV.
        
        Saves the current scan results to a CSV file with comprehensive
        file information including paths, sizes, and metadata.
        
        The export process:
        1. Validates that scan results exist
        2. Opens file save dialog with timestamped default filename
        3. Writes CSV header row
        4. Exports each file record as a data row
        5. Shows success confirmation with file path
        
        CSV Format:
            - Filename: Base filename
            - Path: Parent directory path
            - Size (bytes): Exact file size in bytes
            - Extension: File extension/type
            - MD5: Full MD5 hash (or empty string if missing)
        
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
                    writer.writerow(["Filename", "Path", "Size (bytes)", "Extension", "MD5"])
                    
                    for file_record in self.scanned_files:
                        try:
                            writer.writerow([
                                file_record.absolute_path.name,
                                str(file_record.absolute_path.parent),
                                file_record.size_bytes,
                                file_record.extension,
                                file_record.md5_hash or ""
                            ])
                        except AttributeError as e:
                            logger.warning(f"Invalid file record during export: {e}", exc_info=True)
                            writer.writerow(["ERROR", "ERROR", 0, "ERROR", "ERROR"])
                        except Exception as e:
                            logger.warning(f"Error exporting file record: {e}", exc_info=True)
                            continue
                
                QMessageBox.information(self, "Export Complete", f"Results exported to:\n{filename}")
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

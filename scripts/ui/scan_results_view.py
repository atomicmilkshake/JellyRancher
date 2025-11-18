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
    
    def _init_ui(self):
        """Initialize the UI.""" 
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
    
    def _create_results_section(self) -> QGroupBox:
        """Create the results section.""" 
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
    
    def _create_overview_section(self) -> QGroupBox:
        """Create hierarchical overview and duplicate summary section."""
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

    def _load_scan_results(self):
        """Load scan results from database by session ID."""
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
            
        except Exception as e:
            logger.error(f"Failed to load scan results: {e}")
            self.lbl_summary.setText(f"Error loading results: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load scan results:\n{e}")
    
    def _compute_folder_structure(self):
        """Compute folder structure from scanned files."""
        self.folder_structure = {}
        folder_stats = defaultdict(lambda: {"file_count": 0, "total_size": 0, "file_types": defaultdict(int)})
        
        for record in self.scanned_files:
            parent = record.absolute_path.parent
            stats = folder_stats[parent]
            stats["file_count"] += 1
            stats["total_size"] += record.size_bytes
            stats["file_types"][record.extension] += 1
        
        self.folder_structure = dict(folder_stats)
    
    def _populate_results_table(self, files: List[FileRecord]):
        """Populate the results table with scanned files."""
        self.results_table.setRowCount(len(files))
        
        for row, file_record in enumerate(files):
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
    
    def _filter_results(self, search_text: str):
        """Filter results table based on search text."""
        for row in range(self.results_table.rowCount()):
            show_row = False
            if not search_text:
                show_row = True
            else:
                # Search in filename and path
                for col in [0, 1]:
                    item = self.results_table.item(row, col)
                    if item and search_text.lower() in item.text().lower():
                        show_row = True
                        break
            
            self.results_table.setRowHidden(row, not show_row)
    
    def _export_results(self):
        """Export scan results to CSV."""
        if not self.scanned_files:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scan Results",
            f"scan_results_session_{self.scan_session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Filename", "Path", "Size (bytes)", "Extension", "MD5"])
                    
                    for file_record in self.scanned_files:
                        writer.writerow([
                            file_record.absolute_path.name,
                            str(file_record.absolute_path.parent),
                            file_record.size_bytes,
                            file_record.extension,
                            file_record.md5_hash or ""
                        ])
                
                QMessageBox.information(self, "Export Complete", f"Results exported to:\n{filename}")
                logger.info(f"Exported scan results to: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export:\n{e}")
                logger.error(f"Export error: {e}")
    
    def _update_overview(self):
        """Generate hierarchical overview and duplicate summary."""
        if not self.folder_structure:
            return

        # Folder overview
        self.overview_tree.clear()
        for folder_path, data in sorted(self.folder_structure.items()):
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

        # Duplicate detection
        self.duplicate_tree.clear()
        self.duplicate_groups = {}
        md5_map = defaultdict(list)
        for record in self.scanned_files:
            md5_value = getattr(record, "md5_hash", None)
            if md5_value:
                md5_map[md5_value].append(record)

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
                example_paths = [str(rec.absolute_path) for rec in records[:3]]
                item = QTreeWidgetItem([
                    md5_value,
                    str(len(records)),
                    "; ".join(example_paths),
                ])
                self.duplicate_tree.addTopLevelItem(item)

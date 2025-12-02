#!/usr/bin/env python3
"""
Log Viewer Widget - Real-time display of master log file.

Provides a dockable log viewer window that displays the master log file
in real-time with auto-scroll, filtering, and search capabilities.
"""

import logging
import re
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QComboBox, QLineEdit, QCheckBox, QGroupBox
)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PyQt6.QtCore import Qt, QTimer, QFileSystemWatcher, pyqtSignal

from scripts._common.logger import MasterLogger

logger = logging.getLogger(__name__)


class LogViewerWindow(QWidget):
    """
    Real-time log viewer widget that displays the master log file.
    
    Features:
    - Real-time file tailing with auto-scroll
    - Level filtering (DEBUG/INFO/WARNING/ERROR)
    - Search/find functionality
    - Clear button
    - Pause/resume button
    - Color coding for log levels
    - Monospace font for readability
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the log viewer window.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.master_logger = MasterLogger()
        self.log_file_path = self.master_logger.get_log_path()
        self.last_position = 0
        self.is_paused = False
        self.auto_scroll = True
        self.current_filter_level = logging.DEBUG
        
        # File watcher for log file changes
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self._on_file_changed)
        
        # Timer for periodic file checks (fallback if file watcher fails)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_file_changes)
        self.check_timer.start(500)  # Check every 500ms
        
        self._init_ui()
        self._load_initial_log()
        
        # Start watching the log file
        if self.log_file_path.exists():
            self.file_watcher.addPath(str(self.log_file_path))
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Level filter
        toolbar.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setCurrentText("ALL")
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(self.level_combo)
        
        toolbar.addSpacing(10)
        
        # Search
        toolbar.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search log...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_edit)
        
        toolbar.addSpacing(10)
        
        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.toggled.connect(self._on_auto_scroll_toggled)
        toolbar.addWidget(self.auto_scroll_check)
        
        toolbar.addSpacing(10)
        
        # Pause button
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._toggle_pause)
        toolbar.addWidget(self.pause_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_log)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Log display
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Log file will appear here...")
        
        # Monospace font
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_text.setFont(font)
        
        # Set up color formatting
        self._setup_color_formats()
        
        layout.addWidget(self.log_text)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def _setup_color_formats(self):
        """Set up color formats for different log levels."""
        self.color_formats = {
            'DEBUG': QTextCharFormat(),
            'INFO': QTextCharFormat(),
            'WARNING': QTextCharFormat(),
            'ERROR': QTextCharFormat(),
            'CRITICAL': QTextCharFormat(),
        }
        
        # Set colors
        self.color_formats['DEBUG'].setForeground(QColor("#888888"))  # Gray
        self.color_formats['INFO'].setForeground(QColor("#000000"))  # Black
        self.color_formats['WARNING'].setForeground(QColor("#FF8800"))  # Orange
        self.color_formats['ERROR'].setForeground(QColor("#CC0000"))  # Red
        self.color_formats['CRITICAL'].setForeground(QColor("#FF0000"))  # Bright red
    
    def _load_initial_log(self):
        """Load existing log content."""
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.log_text.setPlainText(content)
                    self.last_position = len(content)
                    
                    # Scroll to bottom
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.log_text.setTextCursor(cursor)
                    
                    self.status_label.setText(f"Loaded {len(content)} characters from log file")
            else:
                self.log_text.setPlainText("Log file not found. Waiting for log entries...")
                self.status_label.setText("Log file not found")
        except Exception as e:
            logger.error(f"Failed to load initial log: {e}", exc_info=True)
            self.status_label.setText(f"Error loading log: {e}")
    
    def _on_file_changed(self, path: str):
        """Handle file change notification."""
        if not self.is_paused:
            self._read_new_content()
    
    def _check_file_changes(self):
        """Periodic check for file changes (fallback)."""
        if not self.is_paused and self.log_file_path.exists():
            try:
                current_size = self.log_file_path.stat().st_size
                if current_size > self.last_position:
                    self._read_new_content()
            except Exception as e:
                logger.debug(f"Error checking file changes: {e}")
    
    def _read_new_content(self):
        """Read new content from log file."""
        try:
            if not self.log_file_path.exists():
                return
            
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to last known position
                f.seek(self.last_position)
                new_content = f.read()
                
                if new_content:
                    # Apply filtering
                    filtered_lines = self._filter_lines(new_content.split('\n'))
                    
                    if filtered_lines:
                        # Append to log display
                        cursor = self.log_text.textCursor()
                        cursor.movePosition(QTextCursor.MoveOperation.End)
                        
                        for line in filtered_lines:
                            if line.strip():
                                # Determine log level for coloring
                                level = self._extract_log_level(line)
                                
                                # Apply color format
                                cursor.insertText(line + '\n', self.color_formats.get(level, self.color_formats['INFO']))
                        
                        # Update position
                        self.last_position = f.tell()
                        
                        # Auto-scroll if enabled
                        if self.auto_scroll:
                            cursor.movePosition(QTextCursor.MoveOperation.End)
                            self.log_text.setTextCursor(cursor)
                        
                        # Update status
                        self.status_label.setText(f"Last updated: {len(new_content)} new characters")
        except Exception as e:
            logger.error(f"Error reading new log content: {e}", exc_info=True)
            self.status_label.setText(f"Error reading log: {e}")
    
    def _extract_log_level(self, line: str) -> str:
        """Extract log level from log line."""
        # Look for [LEVEL] pattern
        match = re.search(r'\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\]', line.upper())
        if match:
            return match.group(1)
        return 'INFO'  # Default
    
    def _filter_lines(self, lines: list) -> list:
        """Filter lines based on level and search criteria."""
        filtered = []
        search_text = self.search_edit.text().lower()
        
        for line in lines:
            # Level filtering
            if self.level_combo.currentText() != "ALL":
                level = self._extract_log_level(line)
                level_map = {
                    'DEBUG': logging.DEBUG,
                    'INFO': logging.INFO,
                    'WARNING': logging.WARNING,
                    'ERROR': logging.ERROR,
                    'CRITICAL': logging.CRITICAL
                }
                required_level = level_map.get(self.level_combo.currentText(), logging.INFO)
                line_level = level_map.get(level, logging.INFO)
                
                if line_level < required_level:
                    continue
            
            # Search filtering
            if search_text and search_text not in line.lower():
                continue
            
            filtered.append(line)
        
        return filtered
    
    def _on_level_changed(self, level: str):
        """Handle level filter change."""
        # Reload and re-filter entire log
        self._load_initial_log()
        self.status_label.setText(f"Filter: {level}")
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        # For now, just update status
        # Full re-filtering happens on next update
        if text:
            self.status_label.setText(f"Searching for: {text}")
        else:
            self.status_label.setText("Ready")
    
    def _on_auto_scroll_toggled(self, checked: bool):
        """Handle auto-scroll toggle."""
        self.auto_scroll = checked
        if checked:
            # Scroll to bottom
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
    
    def _toggle_pause(self):
        """Toggle pause/resume."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setText("▶ Resume")
            self.status_label.setText("Paused")
        else:
            self.pause_btn.setText("⏸ Pause")
            self.status_label.setText("Resumed")
            # Read any new content immediately
            self._read_new_content()
    
    def _clear_log(self):
        """Clear the log display."""
        self.log_text.clear()
        self.last_position = 0
        self.status_label.setText("Log cleared")
        # Reload from file
        self._load_initial_log()
    
    def refresh_log(self):
        """Manually refresh the log display."""
        self._load_initial_log()
        self.status_label.setText("Log refreshed")
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.check_timer.stop()
        if self.log_file_path.exists():
            try:
                self.file_watcher.removePath(str(self.log_file_path))
            except Exception:
                pass
        event.accept()


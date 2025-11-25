#!/usr/bin/env python3
"""
Welcome Screen - Launch screen for JellyRancher Studio.

Shows on app startup when no Round-Up is loaded. Provides options to:
- Create a new Round-Up
- Open an existing Round-Up
- Resume a recent Round-Up

Design follows the Round-Up specification from master-prompt.md Section VII.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialog, QLineEdit, QTextEdit,
    QDialogButtonBox, QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from scripts.core.roundup_manager import RoundUpManager, RoundUp

logger = logging.getLogger(__name__)


class NewRoundUpDialog(QDialog):
    """Dialog for creating a new Round-Up."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Round-Up")
        self.setModal(True)
        self.resize(500, 250)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Round-Up name
        name_label = QLabel("Round-Up Name:")
        name_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My TV Library, Movie Collection 2024")
        self.name_input.setFont(QFont("Segoe UI", 11))
        self.name_input.setMinimumHeight(35)
        layout.addWidget(self.name_input)

        # Source folders (optional at creation)
        folders_label = QLabel("Source Folders (optional - can add later):")
        folders_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(folders_label)

        folders_layout = QHBoxLayout()
        self.folders_input = QLineEdit()
        self.folders_input.setPlaceholderText("Click 'Browse' to select folders...")
        self.folders_input.setReadOnly(True)
        folders_layout.addWidget(self.folders_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folders)
        folders_layout.addWidget(browse_btn)

        layout.addLayout(folders_layout)

        # Store selected folders
        self.selected_folders: List[str] = []

        # Spacer
        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Focus on name input
        self.name_input.setFocus()

    def _browse_folders(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Source Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            if folder not in self.selected_folders:
                self.selected_folders.append(folder)
            self.folders_input.setText("; ".join(self.selected_folders))

    def _validate_and_accept(self):
        """Validate input before accepting."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Please enter a name for your Round-Up."
            )
            self.name_input.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        """Get the entered data."""
        return {
            'name': self.name_input.text().strip(),
            'source_folders': self.selected_folders
        }


class RoundUpListItem(QListWidgetItem):
    """Custom list item for displaying Round-Up info."""

    def __init__(self, roundup: RoundUp):
        super().__init__()
        self.roundup = roundup

        # Format display text
        step_text = f"Step {roundup.current_step}/8"
        if roundup.current_step == 8 and roundup.is_step_completed(8):
            step_text = "Complete ✓"

        # Format time ago
        time_ago = self._format_time_ago(roundup.last_modified)

        # Set display text
        display_text = f"{roundup.name}\n{step_text} • {time_ago}"
        self.setText(display_text)

        # Store roundup reference
        self.setData(Qt.ItemDataRole.UserRole, roundup)

    def _format_time_ago(self, iso_timestamp: str) -> str:
        """Format timestamp as relative time (e.g., '2 hours ago')."""
        if not iso_timestamp:
            return "Unknown"

        try:
            then = datetime.fromisoformat(iso_timestamp)
            now = datetime.now()
            diff = now - then

            seconds = diff.total_seconds()
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes}m ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours}h ago"
            elif seconds < 604800:
                days = int(seconds / 86400)
                return f"{days}d ago"
            elif seconds < 2592000:
                weeks = int(seconds / 604800)
                return f"{weeks}w ago"
            else:
                return then.strftime("%Y-%m-%d")
        except Exception:
            return "Unknown"


class WelcomeScreen(QWidget):
    """
    Welcome Screen widget for JellyRancher Studio.

    Displayed on app startup when no Round-Up is loaded.
    Provides access to create, open, and resume Round-Ups.

    Signals:
        roundup_opened: Emitted when a Round-Up is successfully opened
        roundup_created: Emitted when a new Round-Up is created
    """

    # Signals
    roundup_opened = pyqtSignal(object)   # Emits RoundUp instance
    roundup_created = pyqtSignal(object)  # Emits RoundUp instance

    def __init__(self, roundup_manager: RoundUpManager, parent=None):
        super().__init__(parent)
        self.roundup_manager = roundup_manager
        self._init_ui()
        self._refresh_recent_list()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("JellyRancher Studio")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Media Library Organization Made Easy")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("padding-bottom: 20px;")
        layout.addWidget(subtitle)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)

        # Left side: Action buttons
        actions_widget = self._create_actions_panel()
        content_layout.addWidget(actions_widget)

        # Vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(separator)

        # Right side: Recent Round-Ups
        recent_widget = self._create_recent_panel()
        content_layout.addWidget(recent_widget, stretch=1)

        layout.addLayout(content_layout)

        # Footer
        footer = QLabel("Press F1 for help • Round-Ups stored in ~/JellyRancher/roundups/")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("padding-top: 20px;")
        layout.addWidget(footer)

        self.setLayout(layout)

    def _create_actions_panel(self) -> QWidget:
        """Create the left panel with action buttons."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # New Round-Up button
        btn_new = QPushButton("📁 New Round-Up")
        btn_new.setFont(QFont("Segoe UI", 14))
        btn_new.setMinimumHeight(60)
        btn_new.setMinimumWidth(250)
        btn_new.setToolTip("Create a new media organization project")
        btn_new.clicked.connect(self._on_new_clicked)
        layout.addWidget(btn_new)

        # Open Round-Up button
        btn_open = QPushButton("📂 Open Round-Up...")
        btn_open.setFont(QFont("Segoe UI", 14))
        btn_open.setMinimumHeight(60)
        btn_open.setMinimumWidth(250)
        btn_open.setToolTip("Browse and open an existing Round-Up")
        btn_open.clicked.connect(self._on_open_clicked)
        layout.addWidget(btn_open)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_recent_panel(self) -> QWidget:
        """Create the right panel with recent Round-Ups list."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Header
        header = QLabel("Recent Round-Ups:")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # List widget
        self.recent_list = QListWidget()
        self.recent_list.setFont(QFont("Segoe UI", 11))
        self.recent_list.setAlternatingRowColors(True)
        self.recent_list.setSpacing(5)
        self.recent_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
        self.recent_list.setMinimumWidth(350)
        self.recent_list.setMinimumHeight(300)
        layout.addWidget(self.recent_list)

        # Empty state label
        self.empty_label = QLabel(
            "No recent Round-Ups.\n\n"
            "Click 'New Round-Up' to get started!"
        )
        self.empty_label.setFont(QFont("Segoe UI", 10))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("padding: 40px;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

        # Action buttons for selected item
        btn_layout = QHBoxLayout()

        self.btn_open_selected = QPushButton("Open Selected")
        self.btn_open_selected.setEnabled(False)
        self.btn_open_selected.clicked.connect(self._on_open_selected_clicked)
        btn_layout.addWidget(self.btn_open_selected)

        self.btn_delete_selected = QPushButton("Delete")
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.clicked.connect(self._on_delete_selected_clicked)
        btn_layout.addWidget(self.btn_delete_selected)

        layout.addLayout(btn_layout)

        # Connect selection change
        self.recent_list.itemSelectionChanged.connect(self._on_selection_changed)

        widget.setLayout(layout)
        return widget

    def _refresh_recent_list(self):
        """Refresh the recent Round-Ups list."""
        self.recent_list.clear()

        try:
            recent = self.roundup_manager.list_all()

            if not recent:
                self.recent_list.setVisible(False)
                self.empty_label.setVisible(True)
                self.btn_open_selected.setEnabled(False)
                self.btn_delete_selected.setEnabled(False)
            else:
                self.recent_list.setVisible(True)
                self.empty_label.setVisible(False)

                for roundup in recent:
                    item = RoundUpListItem(roundup)
                    self.recent_list.addItem(item)

        except Exception as e:
            logger.error(f"Failed to refresh recent list: {e}", exc_info=True)
            self.empty_label.setText(f"Error loading Round-Ups:\n{e}")
            self.empty_label.setVisible(True)
            self.recent_list.setVisible(False)

    def _on_selection_changed(self):
        """Handle selection change in recent list."""
        has_selection = len(self.recent_list.selectedItems()) > 0
        self.btn_open_selected.setEnabled(has_selection)
        self.btn_delete_selected.setEnabled(has_selection)

    def _on_new_clicked(self):
        """Handle New Round-Up button click."""
        dialog = NewRoundUpDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            try:
                roundup = self.roundup_manager.create(
                    name=data['name'],
                    source_folders=data['source_folders']
                )
                logger.info(f"Created new Round-Up: {roundup.name}")
                self.roundup_created.emit(roundup)

            except ValueError as e:
                QMessageBox.critical(
                    self,
                    "Cannot Create Round-Up",
                    str(e)
                )
            except Exception as e:
                logger.error(f"Failed to create Round-Up: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create Round-Up:\n{e}"
                )

    def _on_open_clicked(self):
        """Handle Open Round-Up button click."""
        # Show file dialog to select .roundup directory
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Round-Up",
            str(self.roundup_manager.roundups_dir),
            QFileDialog.Option.ShowDirsOnly
        )

        if folder and folder.endswith(".roundup"):
            self._open_roundup(folder)
        elif folder:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select a .roundup folder.\n\n"
                f"Round-Ups are stored in:\n{self.roundup_manager.roundups_dir}"
            )

    def _on_recent_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on recent Round-Up."""
        roundup = item.data(Qt.ItemDataRole.UserRole)
        if roundup:
            self._open_roundup(str(roundup.path))

    def _on_open_selected_clicked(self):
        """Handle Open Selected button click."""
        selected = self.recent_list.selectedItems()
        if selected:
            roundup = selected[0].data(Qt.ItemDataRole.UserRole)
            if roundup:
                self._open_roundup(str(roundup.path))

    def _on_delete_selected_clicked(self):
        """Handle Delete button click."""
        selected = self.recent_list.selectedItems()
        if not selected:
            return

        roundup = selected[0].data(Qt.ItemDataRole.UserRole)
        if not roundup:
            return

        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Delete Round-Up?",
            f"Are you sure you want to delete '{roundup.name}'?\n\n"
            f"This will permanently remove all data including:\n"
            f"• Scan results\n"
            f"• Analysis data\n"
            f"• Review table edits\n"
            f"• Execution logs\n\n"
            f"This cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            try:
                self.roundup_manager.delete(roundup, confirm=True)
                logger.info(f"Deleted Round-Up: {roundup.name}")
                self._refresh_recent_list()
            except Exception as e:
                logger.error(f"Failed to delete Round-Up: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete Round-Up:\n{e}"
                )

    def _open_roundup(self, path: str):
        """Open a Round-Up by path."""
        try:
            roundup = self.roundup_manager.load(path)

            if roundup:
                # Validate the Round-Up
                validation = self.roundup_manager.validate_roundup(roundup)

                if not validation['valid']:
                    # Show validation issues
                    issues_text = "\n".join(f"• {issue}" for issue in validation['issues'])
                    result = QMessageBox.warning(
                        self,
                        "Round-Up Issues Detected",
                        f"The Round-Up '{roundup.name}' has issues:\n\n"
                        f"{issues_text}\n\n"
                        f"Would you like to attempt recovery?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if result == QMessageBox.StandardButton.Yes:
                        roundup = self.roundup_manager.attempt_recovery(roundup.path)
                        if not roundup:
                            QMessageBox.critical(
                                self,
                                "Recovery Failed",
                                "Could not recover the Round-Up."
                            )
                            return
                    else:
                        return

                logger.info(f"Opened Round-Up: {roundup.name}")
                self.roundup_opened.emit(roundup)

            else:
                QMessageBox.critical(
                    self,
                    "Cannot Open Round-Up",
                    f"Failed to load Round-Up from:\n{path}"
                )

        except Exception as e:
            logger.error(f"Failed to open Round-Up {path}: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Round-Up:\n{e}"
            )

    def refresh(self):
        """Refresh the welcome screen (call after returning from workspace)."""
        self._refresh_recent_list()

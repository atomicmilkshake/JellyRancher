#!/usr/bin/env python3
"""
Application Settings Dialog

Provides comprehensive UI for configuring JellyRancher application settings
including destination paths, reorganization strategies, and user preferences.

Features:
- Destination base path configuration for Movies and TV Shows
- Reorganization strategy selection
- Duplicate handling strategy configuration
- Auto-approval settings
- Subtitle display preferences
- MD5 verification settings
- Folder browser dialogs for path selection
- Configuration validation and help text
- Save/cancel with confirmation

Usage:
    from dialogs.app_settings_dialog import AppSettingsDialog

    dialog = AppSettingsDialog(parent)
    if dialog.exec():
        # Settings were saved
        pass
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QFormLayout,
    QComboBox, QCheckBox, QTextEdit, QFileDialog, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.core.app_config import AppConfigManager


class AppSettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.config_manager = AppConfigManager()

        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self._init_ui()
        self._load_config()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("JellyRancher Application Settings")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        # Destination Paths group
        paths_group = QGroupBox("Destination Base Paths")
        paths_layout = QFormLayout()

        # Movies base path
        self.movies_path_input = QLineEdit()
        self.movies_path_input.setPlaceholderText("e.g., V:/Movies or /media/movies")
        movies_path_layout = QHBoxLayout()
        movies_path_layout.addWidget(self.movies_path_input)

        self.movies_browse_button = QPushButton("Browse...")
        self.movies_browse_button.clicked.connect(lambda: self._browse_path(self.movies_path_input, "Select Movies Base Directory"))
        movies_path_layout.addWidget(self.movies_browse_button)

        movies_container = QWidget()
        movies_container.setLayout(movies_path_layout)
        paths_layout.addRow("Movies Base Path:", movies_container)

        # TV Shows base path
        self.tv_path_input = QLineEdit()
        self.tv_path_input.setPlaceholderText("e.g., V:/TV Shows or /media/tvshows")
        tv_path_layout = QHBoxLayout()
        tv_path_layout.addWidget(self.tv_path_input)

        self.tv_browse_button = QPushButton("Browse...")
        self.tv_browse_button.clicked.connect(lambda: self._browse_path(self.tv_path_input, "Select TV Shows Base Directory"))
        tv_path_layout.addWidget(self.tv_browse_button)

        tv_container = QWidget()
        tv_container.setLayout(tv_path_layout)
        paths_layout.addRow("TV Shows Base Path:", tv_container)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        layout.addSpacing(10)

        # Strategy Settings group
        strategy_group = QGroupBox("Reorganization Strategies")
        strategy_layout = QFormLayout()

        # Reorganization strategy
        self.reorg_strategy_combo = QComboBox()
        self.reorg_strategy_combo.addItems([
            "user_choice - Manual selection for each item",
            "llm - Follow LLM reorganization proposal",
            "canonical - Use canonical database paths only",
            "hybrid - Combine LLM and canonical approaches"
        ])
        strategy_layout.addRow("Reorganization Strategy:", self.reorg_strategy_combo)

        # Duplicate strategy
        self.duplicate_strategy_combo = QComboBox()
        self.duplicate_strategy_combo.addItems([
            "jellyfin_first - Prefer files already in Jellyfin",
            "largest_file - Keep largest file in each duplicate group",
            "manual - Manual review of all duplicates"
        ])
        strategy_layout.addRow("Duplicate Handling:", self.duplicate_strategy_combo)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        layout.addSpacing(10)

        # Auto-Approval Settings group
        approval_group = QGroupBox("Auto-Approval Settings")
        approval_layout = QVBoxLayout()

        self.auto_approve_high_confidence = QCheckBox(
            "Auto-approve operations with ≥95% confidence (recommended)"
        )
        self.auto_approve_high_confidence.setChecked(True)
        approval_layout.addWidget(self.auto_approve_high_confidence)

        self.subtitle_auto_approve = QCheckBox(
            "Auto-approve subtitle operations that follow video files"
        )
        self.subtitle_auto_approve.setChecked(True)
        approval_layout.addWidget(self.subtitle_auto_approve)

        approval_group.setLayout(approval_layout)
        layout.addWidget(approval_group)

        layout.addSpacing(10)

        # UI Preferences group
        ui_group = QGroupBox("User Interface Preferences")
        ui_layout = QVBoxLayout()

        self.show_subtitles_in_table = QCheckBox(
            "Show subtitle files in action review table (greyed out, auto-approved)"
        )
        self.show_subtitles_in_table.setChecked(True)
        ui_layout.addWidget(self.show_subtitles_in_table)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        layout.addSpacing(10)

        # Verification Settings group
        verification_group = QGroupBox("Safety & Verification")
        verification_layout = QVBoxLayout()

        self.md5_verify_operations = QCheckBox(
            "Enable MD5 verification for all file operations (recommended)"
        )
        self.md5_verify_operations.setChecked(True)
        verification_layout.addWidget(self.md5_verify_operations)

        verification_group.setLayout(verification_layout)
        layout.addWidget(verification_group)

        layout.addSpacing(10)

        # Help text group
        help_group = QGroupBox("Help & Information")
        help_layout = QVBoxLayout()

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setHtml("""
        <p><b>Destination Base Paths:</b> Root directories where reorganized media will be placed.</p>

        <p><b>Reorganization Strategies:</b></p>
        <ul>
            <li><b>User Choice:</b> Maximum control - review each item individually</li>
            <li><b>LLM:</b> Follow AI reorganization proposal automatically</li>
            <li><b>Canonical:</b> Use metadata database paths only</li>
            <li><b>Hybrid:</b> Combine AI and database approaches</li>
        </ul>

        <p><b>Duplicate Handling:</b> Determines which file to keep when duplicates are found.</p>

        <p><b>Auto-approval:</b> High-confidence operations skip manual review.</p>
        """)
        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)

        layout.addStretch()

        # Buttons at bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.accept)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_config(self):
        """Load existing configuration."""
        # Load base paths
        movies_base = self.config_manager.get_movies_base()
        if movies_base:
            self.movies_path_input.setText(str(movies_base))

        tv_base = self.config_manager.get_tv_base()
        if tv_base:
            self.tv_path_input.setText(str(tv_base))

        # Load strategies
        reorg_strategy = self.config_manager.get_reorganization_strategy()
        strategy_map = {
            "user_choice": 0,
            "llm": 1,
            "canonical": 2,
            "hybrid": 3
        }
        self.reorg_strategy_combo.setCurrentIndex(strategy_map.get(reorg_strategy, 0))

        duplicate_strategy = self.config_manager.get_duplicate_strategy()
        duplicate_map = {
            "jellyfin_first": 0,
            "largest_file": 1,
            "manual": 2
        }
        self.duplicate_strategy_combo.setCurrentIndex(duplicate_map.get(duplicate_strategy, 0))

        # Load checkboxes
        self.auto_approve_high_confidence.setChecked(
            self.config_manager.is_auto_approve_high_confidence()
        )
        self.subtitle_auto_approve.setChecked(
            self.config_manager.is_subtitle_auto_approve()
        )
        self.show_subtitles_in_table.setChecked(
            self.config_manager.is_show_subtitles_in_table()
        )
        self.md5_verify_operations.setChecked(
            self.config_manager.is_md5_verify_operations()
        )

    def _browse_path(self, input_field: QLineEdit, title: str):
        """Open folder browser dialog for path selection."""
        current_path = input_field.text().strip()

        # Start from current path if valid, otherwise from user home
        start_path = current_path if Path(current_path).exists() else str(Path.home())

        path = QFileDialog.getExistingDirectory(
            self,
            title,
            start_path,
            QFileDialog.Option.ShowDirsOnly
        )

        if path:
            input_field.setText(path)

    def _validate_paths(self) -> bool:
        """Validate that base paths are configured and exist."""
        movies_path = self.movies_path_input.text().strip()
        tv_path = self.tv_path_input.text().strip()

        errors = []

        if not movies_path:
            errors.append("Movies base path is required")
        elif not Path(movies_path).exists():
            errors.append(f"Movies path does not exist: {movies_path}")

        if not tv_path:
            errors.append("TV Shows base path is required")
        elif not Path(tv_path).exists():
            errors.append(f"TV Shows path does not exist: {tv_path}")

        if movies_path and tv_path and movies_path == tv_path:
            errors.append("Movies and TV Shows paths must be different")

        if errors:
            QMessageBox.warning(
                self,
                "Configuration Errors",
                "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
            )
            return False

        return True

    def accept(self):
        """Save settings and close dialog."""
        # Validate paths first
        if not self._validate_paths():
            return

        try:
            # Save base paths
            movies_path = self.movies_path_input.text().strip()
            tv_path = self.tv_path_input.text().strip()

            self.config_manager.set_movies_base(movies_path)
            self.config_manager.set_tv_base(tv_path)

            # Save strategies
            strategy_values = ["user_choice", "llm", "canonical", "hybrid"]
            reorg_strategy = strategy_values[self.reorg_strategy_combo.currentIndex()]
            self.config_manager.set_reorganization_strategy(reorg_strategy)

            duplicate_values = ["jellyfin_first", "largest_file", "manual"]
            duplicate_strategy = duplicate_values[self.duplicate_strategy_combo.currentIndex()]
            self.config_manager.set_duplicate_strategy(duplicate_strategy)

            # Save checkbox settings
            self.config_manager.set_auto_approve_high_confidence(
                self.auto_approve_high_confidence.isChecked()
            )
            self.config_manager.set_subtitle_auto_approve(
                self.subtitle_auto_approve.isChecked()
            )
            self.config_manager.set_show_subtitles_in_table(
                self.show_subtitles_in_table.isChecked()
            )
            self.config_manager.set_md5_verify_operations(
                self.md5_verify_operations.isChecked()
            )

            # Show success message
            QMessageBox.information(
                self,
                "Settings Saved",
                "Application settings have been saved successfully."
            )

            super().accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save settings: {str(e)}"
            )

    def get_config_summary(self) -> dict:
        """
        Get current configuration summary.

        Returns:
            Dict with current dialog settings
        """
        strategy_values = ["user_choice", "llm", "canonical", "hybrid"]
        duplicate_values = ["jellyfin_first", "largest_file", "manual"]

        return {
            'movies_base': self.movies_path_input.text().strip(),
            'tv_base': self.tv_path_input.text().strip(),
            'reorganization_strategy': strategy_values[self.reorg_strategy_combo.currentIndex()],
            'duplicate_strategy': duplicate_values[self.duplicate_strategy_combo.currentIndex()],
            'auto_approve_high_confidence': self.auto_approve_high_confidence.isChecked(),
            'subtitle_auto_approve': self.subtitle_auto_approve.isChecked(),
            'show_subtitles_in_table': self.show_subtitles_in_table.isChecked(),
            'md5_verify': self.md5_verify_operations.isChecked(),
        }


if __name__ == "__main__":
    """Test the dialog."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = AppSettingsDialog()
    if dialog.exec():
        config = dialog.get_config_summary()
        print("Settings saved:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    else:
        print("Settings cancelled")

    sys.exit(0)

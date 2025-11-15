#!/usr/bin/env python3
"""
Jellyfin Settings Dialog

Provides UI for configuring Jellyfin integration.

Features:
- Server URL configuration (defaults to local server)
- API key configuration with password field
- Test connection button
- Enable/disable integration checkbox
- Help text with API key generation instructions

Usage:
    from dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog

    dialog = JellyfinSettingsDialog(parent)
    if dialog.exec():
        # Settings were saved
        config = dialog.get_config()
"""

import sys
from pathlib import Path
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QFormLayout,
    QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from jellyfin_config import JellyfinConfigManager
from jellyfin_client import JellyfinClient


class JellyfinTestWorker(QThread):
    """Worker thread for testing Jellyfin connection."""

    # Signals
    test_complete = pyqtSignal(bool, str)  # Success flag, message

    def __init__(self, server_url: str, api_key: str):
        super().__init__()
        self.server_url = server_url
        self.api_key = api_key

    def run(self):
        """Execute connection test."""
        try:
            client = JellyfinClient(
                server_url=self.server_url,
                api_key=self.api_key
            )

            if client.test_connection():
                # Get server info for display
                import requests
                response = requests.get(f"{self.server_url}/System/Info", headers={
                    'X-Emby-Token': self.api_key
                }, timeout=10)

                if response.ok:
                    info = response.json()
                    server_name = info.get('ServerName', 'Unknown')
                    version = info.get('Version', 'Unknown')
                    message = f"Connected successfully!\n\nServer: {server_name}\nVersion: {version}"
                    self.test_complete.emit(True, message)
                else:
                    self.test_complete.emit(False, "Connection failed: Invalid response")
            else:
                self.test_complete.emit(False, "Connection failed: Could not reach server")

        except Exception as e:
            self.test_complete.emit(False, f"Connection failed: {str(e)}")


class JellyfinSettingsDialog(QDialog):
    """Dialog for configuring Jellyfin integration."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.config_manager = JellyfinConfigManager()
        self.test_worker = None

        self.setWindowTitle("Jellyfin Integration Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._init_ui()
        self._load_config()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Enable/Disable checkbox at top
        self.enable_checkbox = QCheckBox("Enable Jellyfin Integration")
        self.enable_checkbox.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.enable_checkbox.toggled.connect(self._on_enable_toggled)
        layout.addWidget(self.enable_checkbox)

        layout.addSpacing(10)

        # Connection settings group
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout()

        # Server URL
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("http://127.0.0.1:8096")
        self.server_url_input.setText("http://127.0.0.1:8096")  # Default to local server
        conn_layout.addRow("Server URL:", self.server_url_input)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your Jellyfin API key")
        conn_layout.addRow("API Key:", self.api_key_input)

        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        conn_layout.addRow("", self.test_button)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        layout.addSpacing(10)

        # Help text group
        help_group = QGroupBox("How to Get an API Key")
        help_layout = QVBoxLayout()

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(200)
        help_text.setHtml("""
        <p><b>To generate a Jellyfin API key:</b></p>
        <ol>
            <li>Open your Jellyfin web interface (usually <a href="http://127.0.0.1:8096">http://127.0.0.1:8096</a>)</li>
            <li>Log in as an administrator</li>
            <li>Go to <b>Dashboard</b> (top right menu)</li>
            <li>Click <b>Advanced</b> in the left sidebar</li>
            <li>Click <b>API Keys</b></li>
            <li>Click the <b>+</b> button to create a new API key</li>
            <li>Enter "JellyRancher" as the application name</li>
            <li>Copy the generated API key and paste it above</li>
        </ol>
        <p><b>Note:</b> If Jellyfin is running on a different machine, change the server URL to match (e.g., http://192.168.1.100:8096)</p>
        """)
        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)

        layout.addStretch()

        # Buttons at bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_config(self):
        """Load existing configuration."""
        # Load enabled state
        self.enable_checkbox.setChecked(self.config_manager.is_enabled())

        # Load server URL (default to localhost if not set)
        server_url = self.config_manager.get_server_url()
        if server_url:
            self.server_url_input.setText(server_url)

        # Load API key
        api_key = self.config_manager.get_api_key()
        if api_key:
            self.api_key_input.setText(api_key)

        # Set initial enabled state
        self._on_enable_toggled(self.enable_checkbox.isChecked())

    def _on_enable_toggled(self, checked: bool):
        """Handle enable/disable checkbox toggle."""
        # Enable/disable input fields
        self.server_url_input.setEnabled(checked)
        self.api_key_input.setEnabled(checked)
        self.test_button.setEnabled(checked)

    def _test_connection(self):
        """Test connection to Jellyfin server."""
        server_url = self.server_url_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not server_url:
            QMessageBox.warning(
                self,
                "Missing Server URL",
                "Please enter the Jellyfin server URL."
            )
            return

        if not api_key:
            QMessageBox.warning(
                self,
                "Missing API Key",
                "Please enter the Jellyfin API key."
            )
            return

        # Disable button during test
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing...")

        # Start worker thread
        self.test_worker = JellyfinTestWorker(server_url, api_key)
        self.test_worker.test_complete.connect(self._on_test_complete)
        self.test_worker.start()

    def _on_test_complete(self, success: bool, message: str):
        """Handle connection test completion."""
        # Re-enable button
        self.test_button.setEnabled(True)
        self.test_button.setText("Test Connection")

        # Show result
        if success:
            QMessageBox.information(
                self,
                "Connection Successful",
                message
            )
        else:
            QMessageBox.warning(
                self,
                "Connection Failed",
                message
            )

    def accept(self):
        """Save settings and close dialog."""
        # Save enabled state
        self.config_manager.set_enabled(self.enable_checkbox.isChecked())

        # Only save connection details if enabled
        if self.enable_checkbox.isChecked():
            server_url = self.server_url_input.text().strip()
            api_key = self.api_key_input.text().strip()

            if not server_url:
                QMessageBox.warning(
                    self,
                    "Missing Server URL",
                    "Please enter the Jellyfin server URL or disable integration."
                )
                return

            if not api_key:
                QMessageBox.warning(
                    self,
                    "Missing API Key",
                    "Please enter the Jellyfin API key or disable integration."
                )
                return

            self.config_manager.set_server_url(server_url)
            self.config_manager.set_api_key(api_key)

        super().accept()

    def get_config(self) -> Dict[str, any]:
        """
        Get the current configuration.

        Returns:
            Dict with enabled, server_url, api_key
        """
        return {
            'enabled': self.enable_checkbox.isChecked(),
            'server_url': self.server_url_input.text().strip(),
            'api_key': self.api_key_input.text().strip()
        }


if __name__ == "__main__":
    """Test the dialog."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = JellyfinSettingsDialog()
    if dialog.exec():
        config = dialog.get_config()
        print("Settings saved:")
        print(f"  Enabled: {config['enabled']}")
        print(f"  Server URL: {config['server_url']}")
        print(f"  API Key: {'*' * len(config['api_key'])} (masked)")
    else:
        print("Settings cancelled")

    sys.exit(0)

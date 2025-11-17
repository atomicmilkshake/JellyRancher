#!/usr/bin/env python3
"""
JellyRancher Studio - Modern QSS Stylesheet

Professional, clean styling for the entire application.
"""

# Main application stylesheet
STUDIO_STYLESHEET = """
/* =================================================================== */
/* GLOBAL STYLES */
/* =================================================================== */

QWidget {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 10pt;
    color: #2c3e50;
}

QMainWindow {
    background-color: #ecf0f1;
}

/* =================================================================== */
/* MENU BAR */
/* =================================================================== */

QMenuBar {
    background-color: #34495e;
    color: white;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 3px;
}

QMenuBar::item:selected {
    background-color: #2c3e50;
}

QMenuBar::item:pressed {
    background-color: #1a252f;
}

QMenu {
    background-color: white;
    border: 1px solid #bdc3c7;
    padding: 4px;
}

QMenu::item {
    padding: 6px 30px 6px 20px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #bdc3c7;
    margin: 4px 0px;
}

/* =================================================================== */
/* STATUS BAR */
/* =================================================================== */

QStatusBar {
    background-color: #34495e;
    color: white;
    padding: 4px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: white;
    padding: 2px 8px;
}

/* =================================================================== */
/* TAB WIDGET */
/* =================================================================== */

QTabWidget::pane {
    border: 1px solid #bdc3c7;
    background-color: white;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #ecf0f1;
    color: #2c3e50;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover {
    background-color: #d5dbdb;
}

QTabBar::close-button {
    image: url(none);  /* Will use default X */
    subcontrol-position: right;
}

/* =================================================================== */
/* BUTTONS */
/* =================================================================== */

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}

/* =================================================================== */
/* GROUP BOXES */
/* =================================================================== */

QGroupBox {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: white;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 8px;
    background-color: white;
    color: #2c3e50;
    font-weight: bold;
}

/* =================================================================== */
/* TABLES */
/* =================================================================== */

QTableWidget {
    background-color: white;
    alternate-background-color: #f8f9fa;
    selection-background-color: #3498db;
    selection-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    gridline-color: #ecf0f1;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #34495e;
    color: white;
    padding: 6px;
    border: none;
    border-right: 1px solid #2c3e50;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #2c3e50;
}

/* =================================================================== */
/* TREE WIDGET */
/* =================================================================== */

QTreeWidget {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    selection-background-color: #3498db;
    selection-color: white;
}

QTreeWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QTreeWidget::item:hover {
    background-color: #ecf0f1;
}

QTreeWidget::branch {
    background-color: white;
}

/* =================================================================== */
/* TEXT EDIT / LINE EDIT */
/* =================================================================== */

QTextEdit, QPlainTextEdit {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 4px;
    selection-background-color: #3498db;
    selection-color: white;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3498db;
}

QLineEdit {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 6px;
    selection-background-color: #3498db;
    selection-color: white;
}

QLineEdit:focus {
    border: 1px solid #3498db;
}

/* =================================================================== */
/* COMBO BOX */
/* =================================================================== */

QComboBox {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 6px;
    min-width: 150px;
}

QComboBox:hover {
    border: 1px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(none);  /* Will use default arrow */
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #bdc3c7;
    selection-background-color: #3498db;
    selection-color: white;
}

/* =================================================================== */
/* PROGRESS BAR */
/* =================================================================== */

QProgressBar {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    text-align: center;
    background-color: #ecf0f1;
}

QProgressBar::chunk {
    background-color: #3498db;
    border-radius: 3px;
}

/* =================================================================== */
/* SCROLL BAR */
/* =================================================================== */

QScrollBar:vertical {
    background-color: #ecf0f1;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #ecf0f1;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* =================================================================== */
/* CHECKBOXES */
/* =================================================================== */

QCheckBox {
    spacing: 6px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #bdc3c7;
    border-radius: 3px;
    background-color: white;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
    border-color: #3498db;
}

QCheckBox::indicator:hover {
    border-color: #3498db;
}

/* =================================================================== */
/* LABELS */
/* =================================================================== */

QLabel {
    color: #2c3e50;
}

QLabel[class="title"] {
    font-size: 18pt;
    font-weight: bold;
    color: #2c3e50;
    padding: 10px;
}

QLabel[class="subtitle"] {
    font-size: 12pt;
    color: #7f8c8d;
}

QLabel[class="status"] {
    color: #7f8c8d;
    font-style: italic;
    padding: 5px;
}

/* =================================================================== */
/* DIALOGS */
/* =================================================================== */

QDialog {
    background-color: #ecf0f1;
}

QDialogButtonBox {
    button-layout: 0;  /* Windows style */
}

/* =================================================================== */
/* TOOLTIPS */
/* =================================================================== */

QToolTip {
    background-color: #34495e;
    color: white;
    border: 1px solid #2c3e50;
    padding: 4px;
    border-radius: 3px;
}
"""


def apply_stylesheet(app, dark_mode: bool = False):
    """
    Apply the studio stylesheet to the application.

    Args:
        app: QApplication instance
        dark_mode: If True, apply dark mode stylesheet. If False, use light mode.
    """
    if dark_mode:
        # Load dark mode stylesheet
        from pathlib import Path
        dark_qss_path = Path(__file__).parent / "dark_mode.qss"
        if dark_qss_path.exists():
            with open(dark_qss_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
        else:
            # Fallback to light mode if dark_mode.qss not found
            app.setStyleSheet(STUDIO_STYLESHEET)
    else:
        # Apply light mode stylesheet
        app.setStyleSheet(STUDIO_STYLESHEET)


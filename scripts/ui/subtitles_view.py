#!/usr/bin/env python3
"""
Subtitles View - Workflow Steps 8-9

Provides a placeholder interface for subtitle coverage evaluation and
download actions to maintain feature parity with the legacy GUI. Future
phases will integrate SubtitleCoverageAnalyzer and SubtitleDownloader
for full automation.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QTextEdit,
    QGroupBox,
)
from PyQt6.QtGui import QFont

from scripts.core.project_manager import ProjectManager, Project


class SubtitlesView(QWidget):
    """Placeholder UI for subtitle coverage and download steps."""

    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project = project
        self.project_manager = project_manager

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Subtitle Coverage & Downloads")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Coverage section
        coverage_group = QGroupBox("Step 8: Subtitle Coverage Evaluation")
        coverage_layout = QVBoxLayout()
        coverage_layout.addWidget(QLabel("Scan for embedded and external English subtitles:"))
        btn_check = QPushButton("Check Subtitle Coverage")
        btn_check.clicked.connect(self._check_subtitles_placeholder)
        coverage_layout.addWidget(btn_check)

        self.coverage_list = QListWidget()
        coverage_layout.addWidget(QLabel("Files Missing English Subtitles:"))
        coverage_layout.addWidget(self.coverage_list)

        coverage_group.setLayout(coverage_layout)
        layout.addWidget(coverage_group)

        # Download section
        download_group = QGroupBox("Step 9: Subtitle Acquisition")
        download_layout = QVBoxLayout()
        download_layout.addWidget(QLabel("Download subtitles from OpenSubtitles, Podnapisi, etc.:"))
        btn_download = QPushButton("Download Missing Subtitles")
        btn_download.clicked.connect(self._download_subtitles_placeholder)
        download_layout.addWidget(btn_download)

        self.download_log = QTextEdit()
        self.download_log.setReadOnly(True)
        self.download_log.setPlaceholderText("Download log will appear here...")
        download_layout.addWidget(self.download_log)

        download_group.setLayout(download_layout)
        layout.addWidget(download_group)

        self.setLayout(layout)

    def _check_subtitles_placeholder(self):
        """Placeholder subtitle coverage results."""
        self.coverage_list.clear()
        self.coverage_list.addItems([
            "Movie1.mkv - No English subtitles found",
            "TVShow.S01E05.mkv - No English subtitles found",
            "Movie2.mkv - Has embedded English subtitles ✓",
            "TVShow.S01E06.mkv - Has external .srt file ✓",
        ])

    def _download_subtitles_placeholder(self):
        """Placeholder download log."""
        self.download_log.setPlainText(
            "📥 Downloading Subtitles (Placeholder)\n\n"
            "Using subliminal library to download from:\n"
            "- OpenSubtitles\n"
            "- Podnapisi\n"
            "- TVsubtitles\n"
            "- Addic7ed\n\n"
            "Process:\n"
            "1. Hash-based matching (most accurate)\n"
            "2. Fallback to filename fuzzy matching\n"
            "3. Download both regular and forced subtitles\n"
            "4. Save alongside video files\n\n"
            "Example:\n"
            "✓ Movie1.mkv → Downloaded from OpenSubtitles\n"
            "✓ TVShow.S01E05.mkv → Downloaded from Podnapisi\n\n"
            "TODO: Integrate SubtitleCoverageAnalyzer and SubtitleDownloader."
        )


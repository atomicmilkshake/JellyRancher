#!/usr/bin/env python3
"""
Analysis View - LLM-powered folder structure analysis

Implements Point 2-3 from plan.md: LLM Analysis and Metadata Lookup
Allows users to analyze folder structure and get reorganization recommendations.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QMessageBox, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from scripts.core.project_manager import ProjectManager, Project

logger = logging.getLogger(__name__)


class AnalysisView(QWidget):
    """
    Analysis View - LLM analysis interface.
    
    Features:
    - Model selection
    - Prompt preview
    - Run analysis
    - View results
    - Compare multiple analyses (Phase 32C)
    """
    
    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        
        self.project = project
        self.project_manager = project_manager
        
        self._init_ui()
        
        logger.info(f"AnalysisView initialized for project: {project.name}")
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("LLM Analysis")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout()
        
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Claude-3.7-Sonnet", "GPT-4", "Gemini-2.5-Pro"])
        model_row.addWidget(self.model_combo)
        
        btn_refresh = QPushButton("Refresh Models")
        btn_refresh.clicked.connect(self._refresh_models)
        model_row.addWidget(btn_refresh)
        model_row.addStretch()
        
        model_layout.addLayout(model_row)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        btn_preview = QPushButton("Preview Prompt")
        btn_preview.clicked.connect(self._preview_prompt)
        button_layout.addWidget(btn_preview)
        
        btn_run = QPushButton("▶ Run Analysis")
        btn_run.clicked.connect(self._run_analysis)
        btn_run.setMinimumHeight(40)
        btn_run.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        button_layout.addWidget(btn_run)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)
        
        self.setLayout(layout)
    
    def _refresh_models(self):
        """Refresh available models from Poe API."""
        QMessageBox.information(
            self,
            "Refresh Models",
            "Model refresh functionality coming in Phase 32C!"
        )
    
    def _preview_prompt(self):
        """Preview the prompt that will be sent to LLM."""
        QMessageBox.information(
            self,
            "Preview Prompt",
            "Prompt preview functionality coming in Phase 32C!"
        )
    
    def _run_analysis(self):
        """Run LLM analysis."""
        QMessageBox.information(
            self,
            "Run Analysis",
            "LLM analysis functionality coming in Phase 32C!\n\n"
            "This will analyze your scanned files and provide reorganization recommendations."
        )


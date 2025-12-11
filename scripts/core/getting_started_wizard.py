"""
Getting Started Wizard for JellyRancher

Provides initial guidance for new users on how to use the application.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QTextEdit, QCheckBox, QWizard,
    QWizardPage, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


class WelcomeWizard(QWizard):
    """Multi-page wizard to guide users through initial setup."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to JellyRancher!")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 400)  # Reduced by 20% from 500px
        
        # Add pages
        self.addPage(self.create_welcome_page())
        self.addPage(self.create_workflow_overview_page())
        self.addPage(self.create_quick_start_page())
        self.addPage(self.create_final_page())
        
        # Store user selections
        self.selected_quick_action = None
    
    def create_welcome_page(self):
        """Create the welcome page."""
        page = QWizardPage()
        page.setTitle("Welcome to JellyRancher!")
        
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_label = QLabel(
            "<h2>🍫 Media Organization Made Simple</h2>"
            "<p>JellyRancher helps you organize your media library with ease.</p>"
            "<br>"
            "<p><b>What can JellyRancher do?</b></p>"
            "<ul>"
            "<li>📁 <b>Organize</b> movies and TV shows into proper folder structures</li>"
            "<li>🔍 <b>Scan</b> and analyze your existing media collection</li>"
            "<li>📝 <b>Generate</b> metadata and NFO files for media servers</li>"
            "<li>💬 <b>Download</b> subtitles in multiple languages</li>"
            "<li>🔄 <b>Batch process</b> multiple operations with AI assistance</li>"
            "<li>📊 <b>Track</b> and analyze your library statistics</li>"
            "</ul>"
            "<br>"
            "<p>This wizard will guide you through the basics.</p>"
        )
        welcome_label.setWordWrap(True)
        welcome_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(welcome_label)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def create_workflow_overview_page(self):
        """Explain the workflow tab."""
        page = QWizardPage()
        page.setTitle("Understanding the Workflow")
        
        layout = QVBoxLayout()
        
        overview = QLabel(
            "<h3>🚀 The Workflow Tab: Your Main Tool</h3>"
            "<p>The <b>Workflow tab</b> guides you through organizing media step-by-step:</p>"
            "<br>"
            "<table style='width: 100%; border-collapse: collapse;'>"
            "<tr><td style='padding: 8px;'><b>Step 1-2:</b></td><td style='padding: 8px;'>Add folders and scan your media</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 3:</b></td><td style='padding: 8px;'>AI analyzes your folder structure</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 4:</b></td><td style='padding: 8px;'>Lookup metadata (titles, years, etc.)</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 5:</b></td><td style='padding: 8px;'>Generate reorganization plan</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 6:</b></td><td style='padding: 8px;'>Review and adjust the plan</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 7:</b></td><td style='padding: 8px;'>Create snapshot backup</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 8:</b></td><td style='padding: 8px;'>Execute the reorganization</td></tr>"
            "<tr><td style='padding: 8px;'><b>Step 9:</b></td><td style='padding: 8px;'>Analyze subtitle coverage</td></tr>"
            "</table>"
            "<br>"
            "<p><b>💡 Pro Tip:</b> Each step builds on the previous one. You must complete steps in order!</p>"
        )
        overview.setWordWrap(True)
        overview.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(overview)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def create_quick_start_page(self):
        """Offer quick start options."""
        page = QWizardPage()
        page.setTitle("Quick Start Guide")
        
        layout = QVBoxLayout()
        
        label = QLabel(
            "<h3>Choose Your Path</h3>"
            "<p>What would you like to do first?</p>"
        )
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)
        
        # Quick action selection
        self.quick_action_group = QButtonGroup()
        
        actions = [
            ("organize_movies", "🎬 Organize Movies", 
             "Scan and organize movie files into proper folders"),
            ("organize_tv", "📺 Organize TV Shows", 
             "Scan and organize TV show episodes by season"),
            ("download_subs", "💬 Download Subtitles", 
             "Add subtitles to your existing media collection"),
            ("just_explore", "🔍 Just Let Me Explore", 
             "I'll figure it out myself, thanks!")
        ]
        
        for i, (action_id, title, description) in enumerate(actions):
            radio = QRadioButton(f"{title}\n   {description}")
            radio.setProperty("action_id", action_id)
            self.quick_action_group.addButton(radio, i)
            layout.addWidget(radio)
            
            if i == 0:
                radio.setChecked(True)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def create_final_page(self):
        """Final tips and start button."""
        page = QWizardPage()
        page.setTitle("You're Ready!")
        
        layout = QVBoxLayout()
        
        # Get selected action
        final_text = QLabel()
        final_text.setWordWrap(True)
        final_text.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(final_text)
        
        # Update text based on selection when page is shown
        def update_text():
            selected_button = self.quick_action_group.checkedButton()
            if selected_button:
                action_id = selected_button.property("action_id")
                self.selected_quick_action = action_id
                
                if action_id == "organize_movies":
                    text = (
                        "<h3>🎬 Organizing Movies</h3>"
                        "<p><b>Here's what to do next:</b></p>"
                        "<ol>"
                        "<li>Go to the <b>Workflow tab</b> (first tab)</li>"
                        "<li>Click <b>'Add Folder'</b> in Step 1 and select your movie folder</li>"
                        "<li>Click <b>'Start Scan'</b> in Step 2</li>"
                        "<li>Follow the steps sequentially - each button will activate as you complete the previous step</li>"
                        "</ol>"
                        "<p><b>💡 Quick Tip:</b> The <b>Organization tab</b> offers a simplified version if you just want to organize without the full workflow.</p>"
                    )
                elif action_id == "organize_tv":
                    text = (
                        "<h3>📺 Organizing TV Shows</h3>"
                        "<p><b>Here's what to do next:</b></p>"
                        "<ol>"
                        "<li>Go to the <b>Workflow tab</b></li>"
                        "<li>Add your TV shows folder in Step 1</li>"
                        "<li>Make sure to select <b>'TV Shows'</b> as media type in Step 5</li>"
                        "<li>The system will automatically organize episodes by season</li>"
                        "</ol>"
                    )
                elif action_id == "download_subs":
                    text = (
                        "<h3>💬 Downloading Subtitles</h3>"
                        "<p><b>Two ways to do this:</b></p>"
                        "<ol>"
                        "<li><b>Subtitles Tab:</b> Quick subtitle downloads for a specific folder</li>"
                        "<li><b>Workflow Tab (Step 9):</b> Analyze coverage and download missing subtitles after organizing</li>"
                        "</ol>"
                        "<p>Start with the <b>Subtitles tab</b> if you just want to add subtitles to existing media.</p>"
                    )
                else:  # just_explore
                    text = (
                        "<h3>🔍 Explore at Your Own Pace</h3>"
                        "<p><b>Key Things to Know:</b></p>"
                        "<ul>"
                        "<li>Hover over any control for helpful tooltips</li>"
                        "<li>Click the <b>❓ Help</b> buttons for detailed documentation</li>"
                        "<li>The <b>Organization tab</b> is the most powerful but also most complex</li>"
                        "<li>The <b>Organization tab</b> is great for quick, simple tasks</li>"
                        "<li>Settings are in the last tab</li>"
                        "</ul>"
                        "<p><b>⚠️ Important:</b> Operations create backups, but always test with a small folder first!</p>"
                    )
                
                final_text.setText(text)
        
        page.initializePage = update_text
        
        # Checkbox for "don't show again"
        self.dont_show_again = QCheckBox("Don't show this wizard on startup")
        layout.addWidget(self.dont_show_again)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def get_selected_action(self):
        """Return the selected quick action."""
        return self.selected_quick_action
    
    def should_show_again(self):
        """Return False if user doesn't want to see wizard again."""
        return not self.dont_show_again.isChecked()


class QuickStartDialog(QDialog):
    """Simple quick start dialog for users who dismissed the wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Start Guide")
        self.setMinimumSize(500, 320)  # Reduced by 20% from 400px
        
        layout = QVBoxLayout()
        
        title = QLabel("<h2>🍫 JellyRancher Quick Start</h2>")
        title.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(title)
        
        guide = QTextEdit()
        guide.setReadOnly(True)
        guide.setHtml("""
            <h3>Common Tasks:</h3>
            
            <p><b>🎬 Organize Movies:</b></p>
            <ol>
                <li>Go to <b>Organization tab</b></li>
                <li>Add folder → Start Scan → Follow steps 1-8</li>
            </ol>
            
            <p><b>📺 Organize TV Shows:</b></p>
            <ol>
                <li>Same as movies, but select "TV Shows" in Step 5</li>
            </ol>
            
            <p><b>💬 Download Subtitles:</b></p>
            <ol>
                <li>Go to <b>Subtitles tab</b></li>
                <li>Select folder → Detect Coverage → Download</li>
            </ol>
            
            <p><b>🔍 Simple Organization:</b></p>
            <ol>
                <li>Go to <b>Organization tab</b> for quick operations</li>
                <li>Select media type → Browse folder → Organize</li>
            </ol>
            
            <h3>Need More Help?</h3>
            <p>Click the <b>❓ Help</b> button in any tab for detailed guidance.</p>
        """)
        layout.addWidget(guide)
        
        close_btn = QPushButton("Got It!")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

"""
JellyRancher Help System
Context-sensitive help for all application features
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QTabWidget, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class JellyRancherHelpDialog(QDialog):
    """Context-sensitive help dialog for JellyRancher."""

    def __init__(self, parent=None, topic="general"):
        super().__init__(parent)
        self.topic = topic
        self.setWindowTitle("JellyRancher Help")
        self.setModal(True)
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize the help dialog UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("JellyRancher Help System")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Help content tabs
        self.help_tabs = QTabWidget()

        # Overview tab
        overview_tab = self.create_overview_tab()
        self.help_tabs.addTab(overview_tab, "📖 Overview")

        # Feature-specific tabs
        features_tab = self.create_features_tab()
        self.help_tabs.addTab(features_tab, "🔧 Features")

        # Troubleshooting tab
        troubleshooting_tab = self.create_troubleshooting_tab()
        self.help_tabs.addTab(troubleshooting_tab, "🔧 Troubleshooting")

        # FAQ tab
        faq_tab = self.create_faq_tab()
        self.help_tabs.addTab(faq_tab, "❓ FAQ")

        layout.addWidget(self.help_tabs)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

        # Show relevant tab based on topic
        self.show_relevant_tab()

    def create_overview_tab(self):
        """Create the overview help tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Welcome to JellyRancher</h2>

        <p><strong>JellyRancher</strong> is a unified media organization platform that combines all your media management tools into a single, professional application.</p>

        <h3>Key Features:</h3>
        <ul>
        <li><strong>📁 Media Organization</strong>: Intelligent file organization for Movies, TV Shows, and Anime</li>
        <li><strong>📺 Subtitle Management</strong>: Download and manage subtitles from multiple providers</li>
        <li><strong>⚙️ Batch Processing</strong>: AI-powered bulk operations with RavenMaven integration</li>
        <li><strong>🔍 Code Analysis</strong>: Quality metrics and analysis with CodeCop</li>
        <li><strong>📊 Analytics</strong>: Comprehensive reporting and statistics</li>
        <li><strong>🧠 Memory Search</strong>: Semantic search through project knowledge</li>
        <li><strong>🔒 Security</strong>: Immutable audit trails and secure credential management</li>
        </ul>

        <h3>Getting Started:</h3>
        <ol>
        <li>Configure your media paths in the Settings tab</li>
        <li>Set up API credentials for AI features</li>
        <li>Use the Organization tab to structure your media library</li>
        <li>Explore other tabs for additional features</li>
        </ol>

        <h3>Safety First:</h3>
        <p>JellyRancher includes comprehensive safety features:</p>
        <ul>
        <li>Dry-run mode for safe testing</li>
        <li>Immutable audit trails</li>
        <li>Snapshot backups</li>
        <li>File integrity verification</li>
        </ul>
        """)
        layout.addWidget(content)

        tab.setLayout(layout)
        return tab

    def create_features_tab(self):
        """Create the features help tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Feature Guide</h2>

        <h3>📁 Organization Tab</h3>
        <p>Organize your media files with intelligent naming and folder structure.</p>
        <ul>
        <li><strong>Media Type</strong>: Choose between Movies, TV Shows, Anime, or All</li>
        <li><strong>Source Folder</strong>: Select the folder containing your media files</li>
        <li><strong>Options</strong>: Enable dry-run mode and integrity verification</li>
        <li><strong>Scan Folder</strong>: Analyze files before organizing</li>
        <li><strong>Organize</strong>: Apply the organization structure</li>
        </ul>

        <h3>📺 Subtitles Tab</h3>
        <p>Download and manage subtitles for your media collection.</p>
        <ul>
        <li><strong>Media Folder</strong>: Select folder with video files</li>
        <li><strong>Language</strong>: Choose subtitle language</li>
        <li><strong>Providers</strong>: Select subtitle providers to use</li>
        <li><strong>Detect Coverage</strong>: Check which files need subtitles</li>
        <li><strong>Download Subtitles</strong>: Download missing subtitles</li>
        </ul>

        <h3>⚙️ Batch Processing Tab</h3>
        <p>AI-powered bulk operations using RavenMaven.</p>
        <ul>
        <li><strong>Source Directory</strong>: Select folder to process</li>
        <li><strong>AI Configuration</strong>: Choose LLM model and custom prompts</li>
        <li><strong>Processing Options</strong>: Set chunk size and safety options</li>
        <li><strong>AI Analysis</strong>: Get AI recommendations for processing</li>
        <li><strong>Execute Batch</strong>: Run the batch processing operation</li>
        </ul>

        <h3>🔍 Code Analysis Tab</h3>
        <p>Analyze code quality with CodeCop metrics.</p>
        <ul>
        <li><strong>Analysis Scope</strong>: Choose what to analyze</li>
        <li><strong>Analysis Options</strong>: Select analysis types</li>
        <li><strong>Run Analysis</strong>: Perform the code quality check</li>
        <li><strong>Generate Report</strong>: Create detailed analysis report</li>
        </ul>

        <h3>📊 Analytics Tab</h3>
        <p>View comprehensive statistics and reports.</p>
        <ul>
        <li><strong>System Statistics</strong>: Overview of your media library</li>
        <li><strong>Organization Report</strong>: Media organization details</li>
        <li><strong>Subtitle Report</strong>: Subtitle coverage information</li>
        <li><strong>Timeline</strong>: Historical activity view</li>
        <li><strong>Export Report</strong>: Generate printable reports</li>
        </ul>

        <h3>🧠 Memory Tab</h3>
        <p>Semantic search through project knowledge.</p>
        <ul>
        <li><strong>Semantic Search</strong>: Natural language queries</li>
        <li><strong>Search Results</strong>: Relevant information and context</li>
        <li><strong>AI Suggestions</strong>: Intelligent recommendations</li>
        </ul>

        <h3>⚙️ Settings Tab</h3>
        <p>Configure application preferences and credentials.</p>
        <ul>
        <li><strong>Media Paths</strong>: Set default folder locations</li>
        <li><strong>API Credentials</strong>: Configure AI service keys</li>
        <li><strong>Preferences</strong>: Set default behavior options</li>
        </ul>
        """)
        layout.addWidget(content)

        tab.setLayout(layout)
        return tab

    def create_troubleshooting_tab(self):
        """Create the troubleshooting help tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Troubleshooting Guide</h2>

        <h3>🚫 Application Won't Start</h3>
        <ul>
        <li><strong>Python Version</strong>: Ensure Python 3.10+ is installed</li>
        <li><strong>Dependencies</strong>: Run <code>pip install -r requirements-jelly-rancher.txt</code></li>
        <li><strong>Permissions</strong>: Check file/folder access permissions</li>
        <li><strong>Virtual Environment</strong>: Try running without venv first</li>
        </ul>

        <h3>🤖 AI Features Not Working</h3>
        <ul>
        <li><strong>API Keys</strong>: Verify credentials in Settings tab</li>
        <li><strong>Internet Connection</strong>: Check network connectivity</li>
        <li><strong>Rate Limits</strong>: Wait if you've exceeded API limits</li>
        <li><strong>Model Availability</strong>: Confirm selected model is accessible</li>
        </ul>

        <h3>🐌 Performance Issues</h3>
        <ul>
        <li><strong>Chunk Size</strong>: Reduce batch processing chunk size</li>
        <li><strong>Dry-run Mode</strong>: Enable for testing without actual changes</li>
        <li><strong>System Resources</strong>: Close other applications</li>
        <li><strong>Disk Space</strong>: Ensure adequate free space</li>
        </ul>

        <h3>📁 File Operation Errors</h3>
        <ul>
        <li><strong>Permissions</strong>: Run as administrator if needed</li>
        <li><strong>File Locks</strong>: Close files/applications using the media</li>
        <li><strong>Path Length</strong>: Windows has 260-character path limits</li>
        <li><strong>Network Drives</strong>: Local drives work better than network</li>
        </ul>

        <h3>🔒 Security/Audit Issues</h3>
        <ul>
        <li><strong>Audit Logs</strong>: Check <code>audit/audit-trail.json</code></li>
        <li><strong>Snapshots</strong>: Use rollback feature if needed</li>
        <li><strong>Credentials</strong>: Re-enter API keys if corrupted</li>
        </ul>

        <h3>📊 Getting Help</h3>
        <ul>
        <li><strong>Logs</strong>: Check <code>logs/jelly_rancher_master_YYYYMMDD.log</code> for errors</li>
        <li><strong>Verbose Mode</strong>: Enable detailed logging in settings</li>
        <li><strong>Community</strong>: Visit the JellyRancher community forum</li>
        <li><strong>Support</strong>: Contact support@jellyrancher.dev</li>
        </ul>
        """)
        layout.addWidget(content)

        tab.setLayout(layout)
        return tab

    def create_faq_tab(self):
        """Create the FAQ help tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Frequently Asked Questions</h2>

        <h3>🧠 What is JellyRancher?</h3>
        <p>JellyRancher is a unified media organization platform that combines multiple specialized tools into a single, professional GUI application. It includes media organization, subtitle management, AI-powered batch processing, code analysis, analytics, and semantic search capabilities.</p>

        <h3>💰 Is JellyRancher free?</h3>
        <p>Yes, JellyRancher is free and open-source software. However, some features require API keys for external services (OpenAI, Anthropic, Google AI) which may have associated costs.</p>

        <h3>🔧 What are the system requirements?</h3>
        <p>JellyRancher requires Python 3.10+, 4GB RAM (8GB recommended), and works best on Windows 10/11. Some features benefit from faster processors and more RAM for large media libraries.</p>

        <h3>🛡️ Is my data safe?</h3>
        <p>JellyRancher includes multiple safety features: dry-run mode, immutable audit trails, snapshot backups, and file integrity verification. API keys are encrypted and stored securely.</p>

        <h3>🤖 How does AI integration work?</h3>
        <p>JellyRancher integrates with multiple AI providers (GPT-4, Claude-3, Gemini Pro) for intelligent processing. You provide your own API keys, and JellyRancher uses them to enhance batch processing, code analysis, and semantic search.</p>

        <h3>📁 What file formats are supported?</h3>
        <p>JellyRancher supports common video formats (MP4, MKV, AVI, MOV) and can organize based on metadata. Subtitle support includes SRT, ASS, and VTT formats from multiple providers.</p>

        <h3>🔄 Can I undo operations?</h3>
        <p>Yes! JellyRancher creates snapshots before major operations and maintains an immutable audit trail. You can review all changes and rollback if needed.</p>

        <h3>🌐 Does it work with network drives?</h3>
        <p>Network drives are supported but local drives provide better performance and reliability. Some features may be slower or have limitations on network storage.</p>

        <h3>📊 How do I export reports?</h3>
        <p>Use the Analytics tab to generate comprehensive reports. You can export system statistics, organization details, subtitle coverage, and activity timelines in various formats.</p>

        <h3>🧠 What is semantic memory?</h3>
        <p>Semantic memory allows you to search through all project documentation and context using natural language queries. It's powered by OpenMemory and helps you find relevant information quickly.</p>

        <h3>⚡ How fast is batch processing?</h3>
        <p>Processing speed depends on file size, complexity, and AI model used. Typical batch operations process 50-200 files per hour, with dynamic chunking optimizing performance.</p>

        <h3>🔍 Can I analyze my own code?</h3>
        <p>Yes! The Code Analysis tab (CodeCop integration) can analyze your Python projects for quality metrics, complexity, documentation coverage, and potential issues.</p>

        <h3>🎯 What's the difference from other media organizers?</h3>
        <p>JellyRancher uniquely combines media organization with AI-powered processing, code analysis, semantic search, and comprehensive audit trails - all in one unified interface.</p>
        """)
        layout.addWidget(content)

        tab.setLayout(layout)
        return tab

    def show_relevant_tab(self):
        """Show the most relevant tab based on the help topic."""
        topic_map = {
            "general": 0,
            "overview": 0,
            "Organization": 1,
            "Subtitles": 1,
            "Batch": 1,
            "Code": 1,
            "Analytics": 1,
            "Memory": 1,
            "Settings": 1,
            "troubleshooting": 2,
            "faq": 3
        }

        tab_index = topic_map.get(self.topic, 0)
        self.help_tabs.setCurrentIndex(tab_index)


def show_help_dialog(parent, topic="general"):
    """Show the help dialog for a specific topic."""
    dialog = JellyRancherHelpDialog(parent, topic)
    dialog.exec()

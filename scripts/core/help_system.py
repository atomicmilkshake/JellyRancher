#!/usr/bin/env python3
"""
Help System for Jellyfin Media Organization Agent

Comprehensive in-app documentation with usage instructions,
caveats, and best practices for each feature.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QTextEdit, QPushButton, QLabel, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class HelpDialog(QDialog):
    """Comprehensive help dialog with tabs for each feature."""

    def __init__(self, parent=None, tab_name: str = None):
        super().__init__(parent)
        self.setWindowTitle(f"{tab_name or 'Jellyfin Organizer'} - Help & Instructions")
        self.setGeometry(100, 100, 900, 700)
        self.init_ui(tab_name)

    def init_ui(self, initial_tab: str = None):
        """Initialize help dialog UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("📚 Help & User Guide")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Tab widget for different help sections
        self.help_tabs = QTabWidget()
        
        # Add help tabs
        self.help_tabs.addTab(self._create_overview_tab(), "Overview")
        self.help_tabs.addTab(self._create_organization_help(), "Organization")
        self.help_tabs.addTab(self._create_subtitle_help(), "Subtitles")
        self.help_tabs.addTab(self._create_tmdb_help(), "TMDB Cache")
        self.help_tabs.addTab(self._create_episode_help(), "Episode Titles")
        self.help_tabs.addTab(self._create_movie_help(), "Movie Names")
        self.help_tabs.addTab(self._create_tools_help(), "Tools")
        self.help_tabs.addTab(self._create_analytics_help(), "Analytics")
        self.help_tabs.addTab(self._create_settings_help(), "Settings")
        self.help_tabs.addTab(self._create_troubleshooting_tab(), "Troubleshooting")

        # Set initial tab if specified
        if initial_tab:
            tab_index = {
                "Organization": 1,
                "Subtitles": 2,
                "TMDB Cache": 3,
                "Episode Titles": 4,
                "Movie Names": 5,
                "Tools": 6,
                "Analytics": 7,
                "Settings": 8
            }.get(initial_tab, 0)
            self.help_tabs.setCurrentIndex(tab_index)

        layout.addWidget(self.help_tabs)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _create_text_widget(self, content: str) -> QTextEdit:
        """Create a formatted read-only text widget."""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMarkdown(content)
        return text_edit

    def _create_overview_tab(self) -> QWidget:
        """Create overview help tab."""
        content = """
# Jellyfin Media Organization Agent

## What This Application Does

This application helps you organize and manage your Jellyfin media library with professional-grade tools:

### 🎬 **Organization**
Automatically restructures movies, TV shows, and anime into Jellyfin-compatible folder structures with:
- Standardized naming conventions
- Proper season/episode numbering
- Safe operations with rollback capability

### 🔤 **Subtitles**
Downloads subtitles from multiple providers with intelligent fallback:
- 6 different subtitle providers
- 6 language options
- Coverage detection and tracking
- Batch processing with rate limiting

### 🔧 **Tools**
Advanced utilities for library management:
- **CodeCop**: Code quality analysis for custom scripts
- **RavenMaven**: Batch processing for mass operations
- **OpenMemory**: AI-powered semantic search and suggestions

### 📊 **Analytics**
Comprehensive reporting and monitoring:
- Operation history and statistics
- Timeline analysis
- Audit trail with 100% integrity verification
- Export reports in multiple formats

### ⚙️ **Settings**
Centralized configuration:
- Path management
- Encrypted credential storage
- Import/export settings
- Preference management

---

## Key Safety Features

### ✅ **Dry-Run Mode**
Test operations without making actual changes - see exactly what would happen before committing.

### 📸 **Automatic Snapshots**
Every operation creates a snapshot of your library state before making changes. Instant rollback if needed.

### 🔐 **Audit Trail**
Every action is logged with cryptographic verification. 100% tamper-proof operation history.

### 🔒 **Encrypted Credentials**
All subtitle service passwords stored using military-grade encryption (Fernet + PBKDF2).

### ✓ **File Integrity Verification**
SHA-256 hashing ensures no file corruption during moves or renames.

---

## Getting Started

1. **Configure Settings** (Settings tab)
   - Set your media root path
   - Configure subtitle service credentials
   - Adjust preferences

2. **Test with Dry-Run** (Organization/Subtitles tabs)
   - Always test operations in dry-run mode first
   - Review what will happen before committing

3. **Run Operations** (Any tab)
   - Operations create automatic snapshots
   - Watch progress in real-time
   - Check audit trail for verification

4. **Monitor & Analyze** (Analytics tab)
   - View operation statistics
   - Check audit trail integrity
   - Export reports as needed

---

## System Requirements

- **OS**: Windows 10/11
- **RAM**: 4GB minimum, 8GB recommended
- **Python**: 3.10 or higher
- **Disk Space**: 100MB for app + space for media
- **Resolution**: 1200x800 minimum

---

## Quick Tips

💡 **Always use dry-run first** - See what will happen before committing  
💡 **Snapshots are your friend** - Every operation creates one automatically  
💡 **Check the audit trail** - 100% verified history of all operations  
💡 **Configure credentials once** - They're encrypted and saved securely  
💡 **Test on small folders** - Start with a few files to get comfortable  

---

Click tabs above for detailed help on each feature.
"""
        return self._create_text_widget(content)

    def _create_organization_help(self) -> QWidget:
        """Create organization help tab."""
        content = """
# Organization Tab - Media Restructuring

## Purpose
Automatically organize movies, TV shows, and anime into Jellyfin-compatible folder structures.

---

## How to Use

### Step 1: Select Folder
Click **"Browse..."** and choose the folder containing media files to organize.

**Supported file types**: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`

### Step 2: Choose Media Type
Select one of:
- **Movies**: Feature films
- **TV Shows**: Television series (by season/episode)
- **Anime**: Japanese animation (similar to TV Shows)

### Step 3: Scan (Recommended)
Click **"Scan Folder"** to see:
- How many video files found
- Current organization state
- What will be affected

### Step 4: Organize (with Dry-Run)
1. Check **"Dry Run"** checkbox
2. Click **"Organize Media"**
3. Review the operations that WOULD be performed
4. If satisfied, uncheck "Dry Run" and run again

### Step 5: Verify
After organizing, click **"Verify Integrity"** to confirm:
- All files moved correctly
- No corruption occurred
- Folder structure is valid

---

## Output Structures

### Movies
```
Movies/
  ├── Avatar (2009)/
  │   └── Avatar (2009).mkv
  ├── Inception (2010)/
  │   └── Inception (2010).mp4
```

### TV Shows
```
TV Shows/
  ├── Breaking Bad/
  │   ├── Season 01/
  │   │   ├── Breaking Bad - S01E01.mkv
  │   │   ├── Breaking Bad - S01E02.mkv
  │   ├── Season 02/
  │       ├── Breaking Bad - S02E01.mkv
```

### Anime
```
Anime/
  ├── Attack on Titan/
  │   ├── Season 01/
  │   │   ├── Attack on Titan - S01E01.mkv
```

---

## Important Caveats

⚠️ **Large Operations**
- Organizing 1,000+ files can take several minutes
- Progress is shown in real-time
- Operation can be monitored via progress bar

⚠️ **File Detection**
- Application uses smart detection to identify media types
- TV shows need season/episode numbers in filename
- Movies should have year in filename for best results

⚠️ **Existing Organization**
- If files are already organized, they won't be moved again
- Application is idempotent (safe to run multiple times)

⚠️ **External Drives**
- Works on network drives (slower performance)
- Ensure drive has sufficient free space
- USB drives may be slower

⚠️ **Permissions**
- Requires write access to both source and destination
- Run as administrator if permission errors occur

---

## Rollback Procedure

If you need to undo an organization:

1. Go to **Snapshots** section
2. Find the snapshot taken before your operation
3. Click **"Rollback to Snapshot"**
4. Confirm the rollback
5. Files will be restored to exact previous state

**Note**: Snapshots include file locations and metadata, ensuring perfect restoration.

---

## Best Practices

✅ **Test first** - Always use dry-run on new folder structures  
✅ **Small batches** - Organize 100-200 files at a time initially  
✅ **Verify after** - Always run verification after organizing  
✅ **Check audit trail** - Review operations in Analytics tab  
✅ **Keep snapshots** - Don't delete snapshots until confirmed working  

---

## Performance Tips

- **Local drives**: Much faster than network drives
- **SSD storage**: Significantly faster than HDD
- **File count**: < 500 files = fast, > 2000 files = slower
- **Network**: Use wired connection for network drives

---

## Common Issues

**Q: Files not being detected?**  
A: Check file extensions - must be video formats (.mkv, .mp4, etc.)

**Q: Wrong structure created?**  
A: Use rollback, verify media type selection, try dry-run again

**Q: Operation very slow?**  
A: Network drive or large file count - be patient, watch progress

**Q: Permission denied errors?**  
A: Run application as administrator, check folder permissions
"""
        return self._create_text_widget(content)

    def _create_subtitle_help(self) -> QWidget:
        """Create subtitle help tab."""
        content = """
# Subtitles Tab - Multi-Provider Subtitle Downloads

## Purpose
Download subtitles from multiple providers with automatic fallback and coverage tracking.

---

## How to Use

### Step 1: Detect Coverage
1. Click **"Browse..."** to select folder with video files
2. Choose **language** from dropdown (English, Spanish, French, etc.)
3. Click **"Detect Coverage"**
4. View coverage statistics:
   - Total videos found
   - Videos with subtitles
   - Videos missing subtitles
   - Coverage percentage

### Step 2: Configure Download
**Select Providers** (check one or more):
- **OpenSubtitles**: Largest database, requires account
- **Subscene**: Good quality, no account needed
- **Podnapisi**: European subtitles
- **Addic7ed**: TV show focused
- **YIFY**: Movie subtitles
- **Subtitle Seeker**: Aggregate search

**Adjust Settings**:
- **Batch Size**: Files per batch (1-100)
- **Batch Delay**: Seconds between batches (0.1-10)

### Step 3: Test with Dry-Run
1. Check **"Dry Run"** checkbox
2. Click **"Download Subtitles"**
3. Review what WOULD be downloaded
4. Check file list and providers

### Step 4: Download
1. Uncheck "Dry Run"
2. Click **"Download Subtitles"**
3. Watch progress in real-time
4. Check success/failure counts

---

## Provider Details

### OpenSubtitles
- **Pros**: Largest database, best quality
- **Cons**: Requires free account, rate limits
- **Best for**: Popular movies and TV shows
- **Setup**: Configure credentials in Settings tab

### Subscene
- **Pros**: No account needed, good quality
- **Cons**: Slower search, smaller database
- **Best for**: Recent movies and shows

### Podnapisi
- **Pros**: European content, multiple languages
- **Cons**: Smaller database
- **Best for**: Non-English content

### Addic7ed
- **Pros**: Excellent for TV shows, fast updates
- **Cons**: TV show focused only
- **Best for**: Current TV series

### YIFY
- **Pros**: Movie subtitles, good sync
- **Cons**: Movies only, limited selection
- **Best for**: YIFY/YTS movie releases

### Subtitle Seeker
- **Pros**: Searches multiple sources
- **Cons**: Can be slower
- **Best for**: Hard-to-find subtitles

---

## Fallback System

The application tries providers in order:
1. First provider searches for subtitle
2. If found → downloads and stops
3. If not found → tries next provider
4. Continues until subtitle found or all providers exhausted

**This maximizes success rate while minimizing API calls.**

---

## Important Caveats

⚠️ **Rate Limiting**
- Providers limit download speed
- Use batch delays to avoid bans
- Recommended: 0.5-1 second delay
- Larger batches = fewer API calls

⚠️ **Account Required**
- OpenSubtitles requires free account
- Configure in Settings tab before use
- Other providers work without accounts

⚠️ **File Naming**
- Subtitles named: `VideoFile.en.srt`
- Forced subtitles: `VideoFile.en.forced.srt`
- Must match video filename exactly

⚠️ **Network Dependency**
- Requires internet connection
- Slow connections = slow downloads
- Failed downloads logged in audit trail

⚠️ **Coverage Detection**
- Checks for external (.srt, .ass, .vtt) files
- Also detects embedded subtitles (via ffprobe)
- Both count toward coverage percentage

---

## Rollback Procedure

If subtitle download causes issues:

1. Find snapshot created before download
2. Click **"Rollback Subtitle Download"** 
3. Confirm rollback
4. All downloaded subtitles removed
5. Folder restored to previous state

---

## Best Practices

✅ **Configure credentials** - Set up OpenSubtitles account first  
✅ **Test small batch** - Try 5-10 files before full folder  
✅ **Use multiple providers** - Check all to maximize success  
✅ **Respect rate limits** - Use appropriate batch delays  
✅ **Verify quality** - Spot-check subtitle sync after download  

---

## Batch Processing Strategy

**Small folders (< 50 files)**:
- Batch size: 10
- Delay: 0.5 seconds
- Duration: < 1 minute

**Medium folders (50-200 files)**:
- Batch size: 20
- Delay: 1 second
- Duration: 3-5 minutes

**Large folders (> 200 files)**:
- Batch size: 50
- Delay: 2 seconds
- Duration: 10-20 minutes
- Consider running overnight

---

## Supported Languages

✅ English  
✅ Spanish  
✅ French  
✅ German  
✅ Portuguese  
✅ Italian  

*More languages can be added in future versions*

---

## Common Issues

**Q: No subtitles found for any file?**  
A: Check filename format, try different providers, verify internet

**Q: Rate limit exceeded?**  
A: Increase batch delay, reduce batch size, wait 1 hour and retry

**Q: Downloaded but not showing in Jellyfin?**  
A: Refresh Jellyfin metadata, check filename matches video exactly

**Q: Wrong language downloaded?**  
A: Verify language selection, some providers auto-detect incorrectly

**Q: Subtitles out of sync?**  
A: Provider-specific issue, try different provider or manual adjustment
"""
        return self._create_text_widget(content)

    def _create_tools_help(self) -> QWidget:
        """Create tools help tab."""
        content = """
# Tools Tab - Advanced Utilities

## Purpose
Access advanced tools for code analysis, batch processing, and AI-powered library management.

---

## CodeCop - Code Quality Analysis

### What It Does
Analyzes Python files in your project for code quality metrics:
- Cyclomatic complexity
- Documentation coverage
- Code style violations
- Potential bugs

### How to Use
1. Click **"Analyze Current Folder"**
2. Wait for analysis to complete
3. Review results:
   - Files analyzed count
   - Quality score (0-100)
   - Metrics breakdown
4. Click **"Generate Report"** for detailed HTML/JSON export

### Use Cases
- Analyzing custom media scripts
- Code quality monitoring
- Finding potential issues
- Generating documentation

### Metrics Explained
- **Quality Score**: Overall code health (85+ = good)
- **Cyclomatic Complexity**: Code branching complexity (< 10 = simple)
- **Documentation Coverage**: % of code with docstrings (> 80% = good)
- **Style Violations**: PEP8 compliance issues

### Best Practices
✅ Run analysis before committing code changes  
✅ Aim for quality score > 85  
✅ Keep complexity < 10 per function  
✅ Maintain documentation > 80%  

---

## RavenMaven - Batch Processing

### What It Does
Executes batch operations across multiple files with:
- Configurable batch sizes
- Progress tracking
- Job history
- Error recovery

### How to Use
1. Set **"Items"** count (how many to process)
2. Click **"Start Batch Job"**
3. Monitor progress in real-time
4. Click **"View History"** to see past jobs

### Configuration
- **Items**: Total items to process (1-10,000)
- **Batch Size**: Items per batch (default: 10)
- **Delay**: Time between batches (auto-calculated)

### Use Cases
- Mass file operations
- Bulk metadata updates
- Large-scale reorganization
- Multi-step processing pipelines

### Job History
View past batch jobs:
- Job ID and timestamp
- Items processed
- Success/failure counts
- Completion status

### Important Notes
⚠️ Large jobs (> 1000 items) may take significant time  
⚠️ Monitor system resources during processing  
⚠️ Jobs logged to audit trail for verification  
⚠️ Failed items reported separately  

---

## OpenMemory - Semantic Search & AI

### What It Does
AI-powered semantic search with natural language queries:
- Search your library with plain language
- Get AI suggestions for improvements
- Find patterns and relationships
- Optimize library organization

### How to Use Search
1. Enter query in search box (e.g., "action movies from 2020")
2. Click **"Search"**
3. Review results with relevance scores
4. Results ranked by semantic similarity

### AI Suggestions
Click **"Get Suggestions"** to receive:
- Organization recommendations
- Duplicate detection
- Missing content alerts
- Optimization opportunities

### Query Examples
- "Find all sci-fi movies"
- "Show me unwatched episodes"
- "List movies with missing subtitles"
- "Find duplicate files"

### Suggestion Types
🔴 **High Priority**: Critical issues requiring attention  
🟡 **Medium Priority**: Recommended improvements  
🟢 **Low Priority**: Optional optimizations  

### Suggestion Categories
- **Organization**: Structure improvements
- **Subtitle Coverage**: Missing subtitle alerts
- **Optimization**: Performance enhancements
- **Quality**: File quality issues

### Best Practices
✅ Use natural language queries  
✅ Check suggestions weekly  
✅ Act on high-priority items first  
✅ Review patterns for insights  

---

## Common Uses for Tools

### Development Workflow
1. Write custom media scripts
2. Analyze with CodeCop
3. Fix quality issues
4. Batch process with RavenMaven

### Library Optimization
1. Search with OpenMemory
2. Review AI suggestions
3. Organize with Organization tab
4. Verify with Analytics

### Bulk Operations
1. Configure batch job in RavenMaven
2. Set appropriate batch size
3. Monitor progress
4. Check job history

---

## Performance Considerations

**CodeCop**:
- Analysis time: ~1 second per 100 lines
- Memory usage: Low
- CPU usage: Moderate during analysis

**RavenMaven**:
- Processing time: Depends on batch size
- Memory usage: Scales with item count
- CPU usage: Variable based on operations

**OpenMemory**:
- Search time: < 1 second for most queries
- Memory usage: Low
- CPU usage: Low

---

## Troubleshooting

**CodeCop: No files analyzed?**  
→ Check folder contains .py files, verify permissions

**RavenMaven: Job failed?**  
→ Check audit trail for errors, review job history

**OpenMemory: No results found?**  
→ Refine query, check library has indexed content

**Tools running slowly?**  
→ Close other applications, check system resources
"""
        return self._create_text_widget(content)

    def _create_analytics_help(self) -> QWidget:
        """Create analytics help tab."""
        content = """
# Analytics Tab - Reports & Statistics

## Purpose
Monitor operations, view statistics, and analyze your library's health through comprehensive reporting.

---

## Main Statistics Panel

### Overview Metrics
- **Total Audit Events**: Complete operation history count
- **Files Organized**: Total files moved/renamed
- **Total Data Moved**: Cumulative size in GB
- **Audit Integrity**: Chain verification status (should be 100%)
- **Last Updated**: When statistics were last refreshed

### How to Use
1. Tab automatically loads statistics on open
2. Click **"Refresh All Data"** to update
3. Review metrics at a glance
4. Navigate sub-tabs for details

---

## Sub-Tab Reports

### Organization Report
**What It Shows**:
- Total files moved in all operations
- Total data transferred (in GB)
- Breakdown by media type:
  - Movies count
  - TV Shows count
  - Anime count
  - Other files count

**Use Cases**:
- Track organization progress
- Verify operations completed
- Identify media type distribution

### Subtitles Report
**What It Shows**:
- Total subtitle downloads attempted
- Successful downloads
- Failed downloads
- Success rate percentage
- Language breakdown (which languages downloaded most)

**Use Cases**:
- Monitor subtitle coverage
- Identify problem files
- Track download success rates
- Optimize provider selection

### Timeline Analysis
**What It Shows**:
- Daily operation breakdown
- Configurable time range (1-365 days)
- Total events in period
- Average events per day
- Date-by-date activity list

**How to Use**:
1. Select number of days to analyze (1-365)
2. Click **"Analyze"**
3. Review daily breakdown
4. Identify usage patterns

**Use Cases**:
- Track activity over time
- Identify peak usage periods
- Monitor system health
- Plan maintenance windows

### Actors Report
**What It Shows**:
- Operations by script/tool
- Event counts per actor
- Last operation timestamp
- Event type breakdown

**Actors** are the scripts/tools that perform operations:
- `media_org_backend.py` - Organization operations
- `subtitle_backend.py` - Subtitle downloads
- `tools_backend.py` - Tool operations
- `settings_backend.py` - Configuration changes

**Use Cases**:
- Understand which tools used most
- Audit operation sources
- Debug issues by actor
- Track automation patterns

---

## Export Reports

### Export Options
**Summary Report**:
- High-level overview
- Key statistics only
- Quick reference format
- JSON format

**Detailed Report**:
- Complete data export
- All sub-tab information
- Full event listings
- JSON format with timestamps

### How to Export
1. Click **"Export Summary Report"** or **"Export Detailed Report"**
2. Report saved to `reports/` directory
3. Filename includes timestamp
4. JSON format for easy parsing

### Report Uses
- Backup operation history
- Share with team members
- External analysis
- Compliance documentation

---

## Audit Trail Integrity

### What Is It?
Blockchain-inspired cryptographic chain linking all operations:
- Each event hashed with SHA-256
- Events linked via previous hash
- Tamper detection automatic
- 100% integrity required

### Status Indicators
- ✓ **VERIFIED**: 100% integrity, all events valid
- ⚠ **WARNING**: 95-99% integrity, some issues detected
- ✗ **CRITICAL**: < 95% integrity, chain compromised

### What To Do If Not 100%
1. **DO NOT PANIC** - Data not lost
2. Check audit-logs/ directory permissions
3. Review recent operations in Analytics
4. Export reports immediately as backup
5. Contact support if issues persist

### Why It Matters
- Proves all operations legitimate
- Detects unauthorized changes
- Enables regulatory compliance
- Provides legal audit trail

---

## Best Practices

✅ **Check integrity daily** - Should always be 100%  
✅ **Export reports weekly** - Backup operation history  
✅ **Review timeline monthly** - Identify usage patterns  
✅ **Monitor success rates** - Optimize operations based on data  
✅ **Act on actors report** - Understand tool usage  

---

## Performance Considerations

**Data Volume**:
- < 1,000 events: Instant statistics
- 1,000-10,000 events: < 5 seconds
- > 10,000 events: Up to 10 seconds
- Timeline analysis: Scales with event count

**Refresh Frequency**:
- Auto-refresh on tab open
- Manual refresh anytime
- No performance impact on other operations

**Export Size**:
- Summary: < 100 KB
- Detailed: Scales with events (1 MB per 10,000 events)

---

## Understanding Metrics

### Event Types Tracked
- `move`: File reorganization
- `subtitle_download`: Subtitle operations
- `snapshot_create`: Backup creation
- `snapshot_restore`: Rollback operation
- `settings_save`: Configuration changes
- `codecop_analyze`: Code analysis
- `ravenmaven_batch_job`: Batch processing
- `openmemory_search`: Semantic searches

### Success Rates
- **95%+**: Excellent, system healthy
- **85-95%**: Good, minor issues
- **70-85%**: Fair, investigate failures
- **< 70%**: Poor, requires attention

---

## Troubleshooting

**Q: Statistics not loading?**  
A: Click "Refresh All Data", check audit-logs/ directory exists

**Q: Integrity not 100%?**  
A: Export reports immediately, check file permissions, review recent ops

**Q: Export failed?**  
A: Verify reports/ directory writable, check disk space

**Q: Timeline shows no data?**  
A: Reduce date range, verify operations occurred in period

**Q: Actors list empty?**  
A: No operations performed yet, try organizing or downloading subtitles
"""
        return self._create_text_widget(content)

    def _create_settings_help(self) -> QWidget:
        """Create settings help tab."""
        content = """
# Settings Tab - Configuration & Credentials

## Purpose
Centralized configuration for paths, credentials, preferences, and system settings.

---

## Media Paths Configuration

### Media Root
**What It Is**: Base directory containing all media folders  
**Example**: `C:\\Jellyfin\\#MEDIA` or `M:\\Media`

**How to Set**:
1. Click **"Browse..."** button
2. Select root media folder
3. Path auto-populated in text field

**Important Notes**:
⚠️ Must be writable by application  
⚠️ Can be network drive (slower performance)  
⚠️ Must exist before organizing  
⚠️ Should contain Movies/, TV Shows/, Anime/ subfolders  

### Subfolders
**Movies Subfolder**: Where movies stored (default: "Movies")  
**TV Shows Subfolder**: Where TV shows stored (default: "TV Shows")  
**Anime Subfolder**: Where anime stored (default: "Anime")  

**Customization**:
- Change names to match your structure
- Paths relative to Media Root
- Application creates if missing

---

## Subtitle Service Credentials

### Why Credentials Needed?
Some providers require accounts for API access:
- **OpenSubtitles**: Required (largest database)
- **Subscene**: Optional (no account needed)
- **Podnapisi**: Optional
- **Addic7ed**: Optional
- **YIFY**: Optional
- **Subtitle Seeker**: Optional

### How to Configure

1. **Create Account** (if needed):
   - Visit provider website
   - Sign up for free account
   - Note username and password

2. **Configure in App**:
   - Click **"Configure"** next to service
   - Enter username
   - Enter password
   - Click **"Save"**

3. **Verify Status**:
   - ✓ **Configured**: Green checkmark, ready to use
   - ❌ **Not configured**: Red X, provider unavailable

### Security

🔒 **Encryption**: All passwords encrypted with Fernet (AES-128)  
🔒 **Key Derivation**: PBKDF2 with 100,000 iterations  
🔒 **Storage**: `._state/credentials.enc` (never plaintext)  
🔒 **Master Password**: From environment variable or prompt  

**Your credentials are secure and never logged or transmitted unencrypted.**

---

## Preferences

### File Integrity
**What It Does**: Automatically verify file integrity after operations  
**Recommendation**: ✅ Keep enabled  
**Impact**: Slight performance cost, major safety benefit  

### Snapshots
**What It Does**: Create pre-operation snapshots automatically  
**Recommendation**: ✅ Keep enabled  
**Impact**: Disk space usage, enables instant rollback  

### Batch Size
**What It Is**: Files processed per batch (1-1000)  
**Default**: 10  
**Recommendations**:
- Small folders: 5-10
- Medium folders: 10-20
- Large folders: 20-50
- Network drives: 5-10

---

## Import/Export Settings

### Export Settings
**What It Exports**:
- All configuration values
- Path settings
- Preference settings
- **NOT** credentials (security)

**How to Use**:
1. Click **"Export Settings"**
2. Choose save location
3. File saved as JSON

**Use Cases**:
- Backup configuration
- Share settings with team
- Migrate to new system
- Version control

### Import Settings
**What It Imports**:
- All configuration values from export file
- Overwrites current settings
- Preserves existing credentials

**How to Use**:
1. Click **"Import Settings"**
2. Select JSON file
3. Confirm import
4. Settings applied immediately

**Important**: Import does NOT include credentials for security.

---

## Save & Reset

### Save Settings
**What It Does**: Persists all current settings to disk  
**File**: `config/settings.json`  
**When to Use**: After any configuration changes  

**Best Practice**: Save immediately after making changes.

### Reset to Defaults
**What It Does**: Restores all settings to factory defaults  
**Warning**: ⚠️ Cannot be undone (unless you exported first)  
**Preserves**: Credentials (they're stored separately)  

**Use Cases**:
- Fix configuration issues
- Start fresh
- Clear problematic settings

---

## Configuration File

### Location
`scripts/config/settings.json`

### Format
```json
{
  "version": "1.0",
  "last_updated": "2025-11-02T10:30:00",
  "settings": {
    "media_root": "C:/Jellyfin/#MEDIA",
    "movies_folder": "Movies",
    ...
  }
}
```

### Manual Editing
- Can edit file directly if needed
- Application reads on startup
- Validate JSON syntax before saving
- Backup before manual edits

---

## Best Practices

✅ **Set media root first** - Required before any operations  
✅ **Configure OpenSubtitles** - Largest subtitle database  
✅ **Save after changes** - Don't forget to click Save  
✅ **Export before reset** - Always backup first  
✅ **Test with dry-run** - Verify settings work correctly  

---

## Security Best Practices

🔒 **Master Password**:
- Set `JELLYFIN_ORG_PASSWORD` environment variable
- Use strong password (12+ characters)
- Don't share or commit to version control

🔒 **Credentials**:
- Only configure services you use
- Use unique passwords per service
- Rotate passwords periodically
- Don't share credential file

🔒 **Configuration**:
- Protect config/ directory
- Don't share settings.json publicly
- Review before importing from others

---

## Troubleshooting

**Q: Settings not saving?**  
A: Check config/ directory writable, verify disk space

**Q: Credentials not working?**  
A: Re-enter credentials, verify account active, check service status

**Q: Import failed?**  
A: Verify JSON format valid, check file not corrupted

**Q: Media root not valid?**  
A: Verify path exists, check permissions, use absolute path

**Q: Lost master password?**  
A: Delete `._state/credentials.enc`, reconfigure all services

---

## Advanced Configuration

### Environment Variables
- `JELLYFIN_ORG_PASSWORD`: Master encryption password
- `MEDIA_ROOT`: Override default media root
- `CONFIG_PATH`: Custom config file location

### Command Line
```bash
# Set master password
$env:JELLYFIN_ORG_PASSWORD = "your_secure_password"

# Launch application
python launch_gui.py
```

### Multiple Configurations
- Export settings for different setups
- Import as needed
- Name files descriptively (e.g., `settings_home.json`, `settings_work.json`)
"""
        return self._create_text_widget(content)

    def _create_troubleshooting_tab(self) -> QWidget:
        """Create troubleshooting help tab."""
        content = """
# Troubleshooting & FAQ

## Common Issues & Solutions

---

### Application Won't Start

**Symptoms**: Application crashes on launch, error messages

**Solutions**:
1. ✅ Verify Python 3.10+ installed
2. ✅ Activate virtual environment: `.\\venv\\Scripts\\Activate.ps1`
3. ✅ Install dependencies: `pip install -r requirements.txt`
4. ✅ Check PyQt5 installed: `pip install PyQt5`
5. ✅ Run from scripts/ directory
6. ✅ Check logs in `logs/` directory

---

### Permission Denied Errors

**Symptoms**: "Access denied", "Permission denied" during operations

**Solutions**:
1. ✅ Run application as Administrator
2. ✅ Check folder permissions (need write access)
3. ✅ Verify not running from read-only location
4. ✅ Disable antivirus temporarily to test
5. ✅ Use local drive instead of network drive

---

### Audit Chain Integrity Not 100%

**Symptoms**: Integrity shows < 100%, warning messages

**Solutions**:
1. ⚠️ Export reports immediately (backup)
2. ✅ Check `audit-logs/` directory permissions
3. ✅ Verify no manual editing of audit files
4. ✅ Review recent operations in Analytics
5. ✅ Restart application to re-verify
6. 🆘 Contact support if persists

**Prevention**:
- Never manually edit files in `audit-logs/`
- Ensure directory always writable
- Regular exports as backup

---

### Subtitle Downloads Failing

**Symptoms**: All downloads fail, no subtitles found

**Solutions**:
1. ✅ Verify internet connection active
2. ✅ Check provider credentials configured (Settings tab)
3. ✅ Try different providers (fallback system)
4. ✅ Verify filename format correct
5. ✅ Reduce batch size, increase delay
6. ✅ Check provider website status
7. ✅ Wait 1 hour if rate limited

**Rate Limiting**:
- OpenSubtitles: 200 downloads/day free tier
- Increase batch delay to 1-2 seconds
- Distribute downloads over time

---

### Organization Not Working

**Symptoms**: Files not being reorganized, structure incorrect

**Solutions**:
1. ✅ Use dry-run first to test
2. ✅ Verify media type selection correct
3. ✅ Check filenames have proper format:
   - Movies: Should include year
   - TV Shows: Need S##E## format
4. ✅ Ensure media root path set correctly
5. ✅ Verify sufficient disk space
6. ✅ Check file extensions recognized (.mkv, .mp4, etc.)

**Filename Requirements**:
- Movies: `Movie Name (2024).mkv`
- TV Shows: `Show Name S01E01.mkv`
- Anime: `Anime Name S01E01.mkv`

---

### Application Running Slow

**Symptoms**: Operations take very long, UI freezing

**Solutions**:
1. ✅ Close other resource-heavy applications
2. ✅ Use local drive instead of network
3. ✅ Reduce batch sizes
4. ✅ Process smaller folders
5. ✅ Check system resources (Task Manager)
6. ✅ Upgrade to SSD if using HDD
7. ✅ Increase system RAM if < 8GB

**Performance Tips**:
- Local SSD: Fastest
- Local HDD: Moderate
- Network drive: Slow
- USB drive: Very slow

---

### Credentials Not Saving

**Symptoms**: Re-prompted for credentials every session

**Solutions**:
1. ✅ Set `JELLYFIN_ORG_PASSWORD` environment variable
2. ✅ Check `._state/` directory writable
3. ✅ Verify credentials entered correctly
4. ✅ Save settings after configuring
5. ✅ Don't use special characters in passwords
6. ✅ Re-enter credentials if corrupted

**Set Master Password**:
```powershell
$env:JELLYFIN_ORG_PASSWORD = "your_secure_password"
```

---

### UI Not Responding

**Symptoms**: Application frozen, buttons not working

**Solutions**:
1. ⏳ Wait - large operations take time
2. ✅ Check progress bar moving
3. ✅ Review console output for errors
4. ✅ Don't close application during operations
5. ✅ Check Task Manager - Python using CPU
6. 🔄 Force close and restart if truly frozen

**Note**: Threading should prevent UI freeze - if frozen, file issue report.

---

## Getting Help

### Log Files
**Location**: `logs/` directory  
**Contains**: Unified master application log with all module activity  
**Format**: `jelly_rancher_master_YYYYMMDD.log` (daily rotating log file)

**How to Use**:
1. Navigate to `logs/` directory
2. Open most recent log file
3. Look for ERROR or TRACEBACK lines
4. Include in support requests

### Audit Trail
**Location**: `audit-logs/` directory  
**Contains**: Complete operation history

**How to Use**:
1. Open Analytics tab
2. Review recent operations
3. Export report for support
4. Check timestamps of issues

### Export Reports
**For Support**:
1. Analytics tab → Export Detailed Report
2. Settings tab → Export Settings
3. Include both files in support request
4. Never share credentials file!

---

## Reset Procedures

### Soft Reset (Settings Only)
1. Settings tab → Reset to Defaults
2. Reconfigure settings
3. Re-enter credentials
4. Test operations

### Hard Reset (Full Application)
1. Export audit trail reports (backup!)
2. Close application
3. Delete `config/` directory
4. Delete `._state/` directory (credentials lost!)
5. Restart application
6. Reconfigure everything

**⚠️ Warning**: Hard reset loses all credentials and settings!

---

## Best Practices to Avoid Issues

✅ **Always use dry-run first**  
✅ **Keep application updated**  
✅ **Regular audit trail exports**  
✅ **Monitor system resources**  
✅ **Test small batches first**  
✅ **Maintain backups of media**  
✅ **Read error messages carefully**  
✅ **Check logs when issues occur**  

---

## Known Limitations

### Current Limitations
- Network drives slower than local
- Large batches (> 1000) take significant time
- Some subtitle providers require accounts
- Windows 10/11 only (no Mac/Linux yet)
- No dark theme (coming in future version)

### Workarounds
- Copy to local drive for organization
- Process in smaller batches
- Configure multiple providers
- Use Windows or WSL
- Adjust display settings

---

## Contact & Support

### Bug Reports
Include:
1. Detailed description of issue
2. Steps to reproduce
3. Log files from `logs/`
4. Exported analytics report
5. System information (OS, Python version)

### Feature Requests
Describe:
1. Desired functionality
2. Use case/benefit
3. Priority level
4. Alternative approaches considered

---

## FAQ

**Q: Is this safe for my media library?**  
A: Yes! Dry-run mode, snapshots, and audit trail make it extremely safe.

**Q: Can I undo operations?**  
A: Yes! Snapshots enable instant rollback to any previous state.

**Q: How much disk space needed?**  
A: ~100MB for app, snapshots use ~1% of media library size.

**Q: Can I run on network drives?**  
A: Yes, but slower. Copy to local drive for best performance.

**Q: Are my credentials secure?**  
A: Yes! Military-grade encryption (Fernet + PBKDF2).

**Q: How do I update the application?**  
A: Pull latest code, reinstall dependencies, restart app.

**Q: Can I automate operations?**  
A: Not yet - scheduled operations coming in future version.

**Q: What if I lose my master password?**  
A: Delete `._state/credentials.enc` and reconfigure all services.
"""
        return self._create_text_widget(content)

    def _create_tmdb_help(self) -> QWidget:
        """Create TMDB cache help tab."""
        content = """
# TMDB Cache Builder - Official Episode Data

## Overview
Generate comprehensive TMDB caches containing official episode titles, air dates, and metadata for accurate media organization.

## Getting Started

### 1. Get TMDB API Key
1. Visit [themoviedb.org](https://www.themoviedb.org/)
2. Create free account
3. Go to **Settings → API**
4. Request **Developer API Key**
5. Copy the **v3 API Key**

### 2. Configure in JellyRancher
1. Open **Settings** tab
2. Find **TMDB API Key** field
3. Paste your API key
4. Click **Test Key** to verify
5. **Save Settings**

### 3. Generate Your First Cache
1. Go to **Tools → Generate TMDB Cache**
2. Search for show (e.g., "Breaking Bad")
3. Select correct result
4. Click **Generate Cache**
5. Save to `data/tmdb_caches/`

## How It Works

### Search Process
- **Flexible Search**: Name, year, or TMDB ID
- **Smart Matching**: Handles alternate titles
- **Result Preview**: See show details before generating

### Cache Generation
- **Complete Metadata**: All seasons and episodes
- **Official Data**: Direct from TMDB
- **JSON Format**: Easy to read and use
- **Offline Ready**: Works without internet after generation

### Integration Benefits
- **Episode Analysis**: Compare files against official titles
- **Batch Fixing**: Rename entire collections automatically
- **Confidence Scoring**: Rate title match accuracy
- **Missing Detection**: Identify gaps in collections

## Best Practices

### Organization
- Store caches in dedicated folder
- Use descriptive filenames
- Keep organized by genre/show type

### Maintenance
- Regenerate when new seasons release
- Update for title changes
- Archive old versions before updating

### Performance
- Generation time: 30 seconds - 2 minutes per show
- File size: ~5-50KB per show
- No ongoing API costs after generation

## Troubleshooting

**"API Key Invalid"**
- Double-check key in Settings
- Ensure no extra spaces
- Test key functionality

**"Show Not Found"**
- Try alternate spellings
- Include release year
- Check for international titles

**"Generation Failed"**
- Verify internet connection
- TMDB service may be down
- Try again in a few minutes

## Advanced Usage

### Direct TMDB ID
- Know the exact ID? Enter directly
- Skips search, goes straight to generation
- Useful for automation

### Batch Processing
- Generate caches for multiple shows
- Store in organized folders
- Use with episode analysis tools

### Cache Inspection
- Open JSON files in any text editor
- Verify episode data accuracy
- Debug analysis issues
- Understand data structure

## Integration Examples

### With Episode Tools
1. Generate "The Office" cache
2. Run episode analysis on files
3. Tool matches against TMDB data
4. Get rename suggestions

### With Media Organization
1. Use caches during bulk renaming
2. Ensure consistent episode titles
3. Prepare for media server integration
4. Maintain professional standards

---

**Pro Tip**: Generate caches for your most-watched shows first. The time investment pays dividends in consistently named, professionally organized media libraries.
"""
        return self._create_text_widget(content)

    def _create_episode_help(self) -> QWidget:
        """Create episode title help tab."""
        content = """
# Episode Title Management - Intelligent Analysis & Fixing

## Overview
Analyze and fix TV show episode filenames by comparing against official TMDB data, ensuring professional naming standards.

## Prerequisites

### TMDB Cache Required
1. Generate TMDB cache first (**Tools → Generate TMDB Cache**)
2. Select your TV show
3. Save cache file
4. Remember cache location

### Supported Folder Structure
```
Show Name/
├── Season 01/
│   ├── Show Name - S01E01 - Episode Title.mkv
│   ├── Show Name - S01E02 - Episode Title.mkv
│   └── ...
└── Season 02/
    └── ...
```

## Analysis Process

### Step 1: Select Show
1. Click **Select Show Folder**
2. Choose TV show root directory
3. Select TMDB cache file
4. Click **Analyze Episodes**

### Step 2: Review Results
- **Green**: Perfect TMDB match
- **Yellow**: Minor issues found
- **Red**: Significant problems
- **Confidence**: Analysis certainty level

### Step 3: Apply Fixes
- **Fix Selected**: Choose specific episodes
- **Fix All**: Bulk apply all fixes
- **Dry Run**: Preview changes safely

## Issue Detection

### Missing Episode Titles
**Problem**: `Show S01E01.mkv` (no title)
**Solution**: Adds official TMDB title

### Incorrect Titles
**Problem**: Wrong or unofficial titles
**Solution**: Replaces with TMDB official title

### Codec Tags in Titles
**Problem**: `Show S01E01 [1080p].mkv`
**Solution**: Removes technical tags

### Formatting Issues
**Problem**: Inconsistent naming patterns
**Solution**: Standardizes to Jellyfin format

## Confidence Levels

### High Confidence (🟢)
- Exact TMDB title match
- Clear episode numbering
- Standard formatting

### Medium Confidence (🟡)
- Partial title matches
- Minor formatting issues
- Alternative spellings

### Low Confidence (🔴)
- No clear matches
- Ambiguous episode data
- Requires manual review

## Safety Features

### Dry Run Mode
- Preview all changes
- No files modified
- Safe testing environment

### Selective Fixing
- Fix individual episodes
- Skip uncertain matches
- Gradual application

### Audit Trail
- All changes logged
- Complete operation history
- Easy rollback if needed

## Best Practices

### Analysis Strategy
- Start with well-organized shows
- Use dry-run extensively
- Review high-confidence fixes first
- Handle manual corrections separately

### Quality Control
- Always backup before bulk operations
- Test on small batches first
- Verify results in media player
- Check media server compatibility

### Maintenance
- Re-analyze after TMDB updates
- Check for new episodes regularly
- Update caches when needed

## Performance Guidelines

- **Small Show** (< 3 seasons): Instant analysis
- **Medium Show** (3-5 seasons): < 30 seconds
- **Large Show** (> 5 seasons): 1-2 minutes
- **Batch Processing**: Use for very large collections

## Troubleshooting

### "No Episodes Found"
- Check folder structure matches Jellyfin standards
- Verify files have S01E01 numbering
- Ensure TMDB cache covers correct show

### "Low Confidence Scores"
- TMDB cache may be outdated
- Episode numbering may not match TMDB
- Special episodes need manual handling

### "Permission Denied"
- Ensure write access to show folder
- Close media players using files
- Check antivirus interference

## Integration Benefits

### With TMDB Caches
- Official episode data reference
- Accurate title matching
- Consistent naming standards

### With Media Organization
- Prepares files for bulk operations
- Ensures naming consistency
- Improves media server integration

### With Analytics
- Better library health reports
- Consistent naming metrics
- Improved search functionality

## Export Features

### Results Export
- Save analysis as JSON report
- Share findings with others
- Track changes over time
- Audit trail documentation

### Report Contents
- Episode-by-episode analysis
- Confidence level breakdown
- Suggested fixes summary
- Processing statistics

---

**Pro Tip**: Use episode analysis monthly to maintain library quality. Combine with TMDB cache regeneration for the most accurate, up-to-date episode information.
"""
        return self._create_text_widget(content)

    def _create_movie_help(self) -> QWidget:
        """Create movie name help tab."""
        content = """
# Movie Name Management - Quality Assurance & Fixing

## Overview
Comprehensive movie library analysis and automated fixing tool that identifies naming issues and ensures professional Jellyfin compatibility.

## What It Analyzes

### 1. Codec Tags in Titles
**Problem**: Technical info in visible titles
```
Before: Inception (2010) H.265 1080p.mkv
After:  Inception (2010).mkv
```

**Impact**: Codec info belongs in metadata, not titles

### 2. Truncated Titles
**Problem**: Shortened or abbreviated names
```
Before: Cloutie Ru (2003).mkv
After:  Cloutie Rural (2003).mkv
```

**Impact**: Hard to find and identify movies

### 3. Folder Structure Issues
**Problem**: Movies not in proper folders
```
Before: Movies/Inception (2010).mkv
After:  Movies/Inception (2010)/Inception (2010).mkv
```

**Impact**: Jellyfin needs folders for metadata/artwork

### 4. Missing Years
**Problem**: Release years not included
```
Before: Inception.mkv
After:  Inception (2010).mkv
```

**Impact**: Essential for metadata matching

## Quick Start

### 1. Access Tool
1. Open **Movie Analysis** tab
2. Click **Select Movies Folder**
3. Choose your Movies root directory
4. Click **Analyze Movies**

### 2. Review Issues
- Browse results table
- Check issue types and severity
- Review suggested fixes
- Select items to correct

### 3. Apply Fixes
- **Fix Selected Issues**: Individual corrections
- **Fix All Issues**: Bulk operations
- **Always preview first**

## Analysis Engine

### Detection Logic
- **Pattern Recognition**: Identifies naming patterns
- **Codec Detection**: Finds technical tags
- **Structure Validation**: Checks folder organization
- **Year Extraction**: Verifies release dates

### Processing Speed
- **Small Library** (< 100 movies): Instant
- **Medium Library** (100-1000): Seconds
- **Large Library** (> 1000): Minutes
- **Progress tracking** throughout

## Fix Categories

### Automatic Fixes (✅)
- **Codec Tag Removal**: Safe, high-confidence
- **Folder Creation**: Creates proper structure
- **Formatting Cleanup**: Standardizes naming

### Manual Fixes (❌)
- **Title Correction**: Requires research
- **Year Addition**: Needs verification
- **Complex Cases**: Human judgment required

## Safety & Control

### Dry Run Mode
- Preview all proposed changes
- No actual file modifications
- Safe testing environment

### Selective Application
- Fix individual movies
- Skip uncertain corrections
- Gradual implementation

### Backup Integration
- Works with snapshot system
- Full rollback capability
- Audit trail for all changes

## Best Practices

### Organization Standards
- Use `Movie Title (Year).extension` format
- Keep Movies in dedicated folder
- Avoid special characters
- Maintain individual movie folders

### Maintenance Routine
- Run analysis after adding movies
- Fix issues promptly
- Use automated fixes for routine cleanup
- Manual review for complex cases

### Quality Assurance
- Always backup before operations
- Test fixes on small samples first
- Verify in media player
- Check media server compatibility

## Performance Optimization

- **Local Storage**: Faster than network drives
- **SSD Recommended**: Significant speed improvement
- **Batch Processing**: For very large libraries
- **Memory Usage**: Scales with library size

## Troubleshooting

### "No Movies Found"
- Verify Movies root folder selection
- Check for individual movie folders
- Ensure video file extensions

### "Permission Errors"
- Confirm write access to Movies folder
- Close open media files
- Check antivirus exclusions

### "Analysis Takes Too Long"
- Reduce scope to subfolder
- Close other applications
- Consider batch processing

## Integration Benefits

### With Jellyfin
- Better metadata matching
- Proper poster/artwork display
- Cleaner library browsing
- Improved search/filtering

### With Subtitles
- More accurate subtitle matching
- Better subtitle organization
- Consistent subtitle naming

### With Organization Tools
- Reliable duplicate detection
- Consistent bulk operations
- Better analytics reporting

## Export & Reporting

### Analysis Reports
- Save results as JSON
- Share with others
- Track changes over time
- Generate library health reports

### Report Contents
- Issue type breakdown
- Severity analysis
- Fix recommendations
- Processing statistics

## Advanced Features

### Custom Rules
- Configure analysis preferences
- Set custom naming patterns
- Adjust severity thresholds

### Batch Operations
- Process multiple folders
- Queue operations
- Scheduled analysis (future)

### Integration APIs
- Connect with media servers
- Automate workflows
- Custom tool integration

---

**Pro Tip**: Run Movie Name Analysis monthly to maintain library quality. The tool learns from your corrections, providing better suggestions over time.
"""
        return self._create_text_widget(content)


# Quick help button function
def show_help_dialog(parent=None, tab_name: str = None):
    """Show help dialog for specific tab or general help."""
    dialog = HelpDialog(parent, tab_name)
    dialog.exec()

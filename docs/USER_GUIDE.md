# JellyRancher User Guide

## 🎯 Quick Start

When you first launch JellyRancher, you'll see a **Welcome Wizard** that guides you through the basics. If you dismissed it, you can access it anytime:

- Press **F1** or go to **File → Quick Start Guide**
- Click the **🎯 Quick Start** button in the toolbar

## 📚 Common Tasks

### 🎬 Organize Movies (Full Workflow)

**Best for:** Complete organization with metadata and proper naming

1. **Go to the Workflow Tab** (first tab: 🚀 Workflow)
2. **STEP 1:** Add folders using "➕ Add Folder" button
3. **STEP 2:** Click "🔍 STEP 1-2: Start Scan" to analyze your media
4. **STEP 3:** Click "🤖 STEP 3: Analyze with LLM" for AI-powered structure detection
5. **STEP 4A:** Click "🔍 STEP 4A: Lookup Metadata" to fetch movie titles/years
6. **STEP 4B:** (Optional) Click "📄 STEP 4B: Generate NFO Files" for multi-part episodes
7. **STEP 5:** Click "📋 STEP 5: Generate Reorganization Plan" to see proposed changes
8. **STEP 6:** Click "📸 STEP 6: Create Snapshot" for backup/rollback capability
9. **STEP 7:** Click "▶️ STEP 7: Execute Reorganization" to reorganize your files
10. **STEP 8:** Analyze subtitle coverage (optional)
11. **STEP 9:** Download missing subtitles (optional)

**💡 Tip:** Each button is clearly numbered! Just follow the sequence from 1-2 through 9.

---

### 📁 Simple Organization (Quick Mode)

**Best for:** Quick organization without full analysis

1. **Go to the Organization Tab** (📁 Organization)
2. **Select media type** (Movies, TV Shows, or Anime)
3. **Browse** to select your source folder
4. **Choose options:**
   - ✅ Dry Run Mode (preview without moving files)
   - ✅ File Verification (check integrity)
5. **Click "Scan Folder"** to see what will be organized
6. **Click "Organize Media"** to execute

**⚠️ Important:** Simple mode organizes based on existing folder structure. For best results, use the full workflow.

---

### 💬 Download Subtitles

**Method 1: Subtitles Tab (Quick)**

1. **Go to the Subtitles Tab** (📺 Subtitles)
2. **Browse** to select folder with video files
3. **Click "Detect Coverage"** to see missing subtitles
4. **Select languages** you want to download
5. **Click "Download Subtitles"**

**Method 2: Workflow Tab (After Organization)**

1. Complete Steps 1-8 in Workflow tab
2. **Step 9:** Click "Analyze Coverage" to see subtitle status
3. Review missing subtitles
4. Click "Download Missing" to fetch them

---

### 🔍 Quick Actions Toolbar

The toolbar at the top provides shortcuts to common tasks:

- **🎯 Quick Start** - Show the getting started guide
- **🔍 Scan Folder** - Quick scan (goes to Organization tab)
- **📁 Organize Media** - Quick organize (must have folder selected)
- **💬 Get Subtitles** - Jump to Subtitles tab
- **🚀 Full Workflow** - Switch to Workflow tab

---

## 📖 Tab Overview

### 🚀 Workflow Tab
**Most Powerful** - Complete 9-step media organization workflow
- Scanning, AI analysis, metadata lookup, planning, execution
- Best for initial library organization
- Follow steps sequentially

### 📁 Organization Tab
**Quick & Simple** - Direct media organization
- Choose media type, scan, organize
- Snapshot management for rollback
- Episode/Movie name analyzers

### 📺 Subtitles Tab
**Subtitle Management** - Download and manage subtitles
- Multi-provider support
- Coverage detection
- Language selection

### 📝 NFO Files Tab
**Metadata Generation** - Create NFO files for media servers
- Auto-detect media type
- TMDB integration
- Jellyfin/Plex compatible

### 🤖 Batch Processing Tab
**AI-Powered** - RavenMaven batch operations
- Queue management
- AI assistance
- Bulk operations

### 🔍 Code Analysis Tab
**CodeCop** - Code quality metrics
- Project analysis
- Quality reports
- Technical debt tracking

### 📊 Analytics Tab
**Statistics** - Library analytics and reports
- File counts and sizes
- Media type breakdown
- Export capabilities

### 🧠 Memory Tab
**Semantic Search** - Query ChromaDB memory
- Natural language search
- Historical context
- Smart suggestions

### ⚙️ Settings Tab
**Configuration** - Application settings
- Credentials management
- Paths and preferences
- Save/reset options

---

## 💡 Pro Tips

### Before You Start

1. **Always test with a small folder first** - Make sure you understand the process
2. **Enable Dry Run Mode** - Preview changes before executing
3. **Create snapshots** - In Workflow Step 7 or Organization tab
4. **Check the help** - Hover over controls or click ❓ buttons

### Understanding the Workflow

- **Steps 1-2:** Information gathering (scan your media)
- **Steps 3-4:** Analysis and enrichment (AI + metadata)
- **Steps 5-6:** Planning (review before execution)
- **Step 7:** Safety (backup snapshot)
- **Step 8:** Execution (actual reorganization)
- **Step 9:** Enhancement (subtitles)

### Hover Help System

**Every control has contextual help!**
- Hover your mouse over any button, checkbox, or input field
- The right-side help panel updates with detailed information
- No need to guess what a control does

### Keyboard Shortcuts

- **F1** - Quick Start Guide
- **Ctrl+S** - Quick Scan
- **Ctrl+O** - Quick Organize
- **Ctrl+T** - TMDB Cache Generator
- **Ctrl+E** - Episode Analyzer
- **Ctrl+M** - Movie Analyzer
- **Ctrl+Shift+M** - Memory Query
- **Ctrl+Q** - Exit

---

## ⚠️ Important Safety Notes

### Backups
- **Workflow Step 7** creates automatic snapshots
- **Organization tab** has snapshot management section
- Snapshots can verify/restore file states
- Last 10 snapshots are kept automatically

### Rollback
1. Go to Organization tab
2. Find "Snapshots & Rollback" section
3. Click "🔄 Refresh" to see available snapshots
4. Select a snapshot and click "↩️ Restore" to verify
5. Click "🗑️ Delete" to remove old snapshots

### Testing
- Always use **Dry Run Mode** first
- Start with a **copy of your media** if unsure
- Review the **proposed plan** before executing
- Check **log messages** for any warnings

---

## 🆘 Need More Help?

### In-App Help
- Press **F1** for Quick Start Guide
- Click **❓ Help** buttons in each tab
- Hover over controls for tooltips
- Check **File → Help → Documentation**

### Tab-Specific Help
Each tab has a dedicated help button that explains:
- What the tab does
- When to use it
- Step-by-step instructions
- Common pitfalls to avoid

### Status Bar
- Bottom of window shows current operation status
- Displays success/error messages
- Shows progress for long operations

---

## 🎓 Learning Path

### Beginner
1. Start with **Organization Tab** for simple tasks
2. Use **Dry Run Mode** to preview changes
3. Organize one small folder at a time
4. Get comfortable with the interface

### Intermediate
1. Try the **Full Workflow** on a test folder
2. Complete all 9 steps sequentially
3. Review the generated plan before executing
4. Use **Subtitles Tab** to enhance your library

### Advanced
1. Explore **Batch Processing** with AI
2. Use **NFO Generation** for media servers
3. Leverage **Analytics** for library insights
4. Query **Memory** for semantic search

---

## 🔧 Troubleshooting

### "I don't know what to click first"
→ Press **F1** or click **🎯 Quick Start** in toolbar

### "The Workflow steps are confusing"
→ Follow them in order: 1→2→3→4→5→6→7→8→9
→ Each step enables the next one

### "I want something simpler"
→ Use the **Organization Tab** instead of Workflow
→ Or use **Quick Actions** from the toolbar

### "How do I undo changes?"
→ Go to Organization tab → Snapshots section
→ Refresh, select snapshot, and restore

### "Nothing is happening when I click"
→ Check if you need to complete a previous step first
→ Look for error messages in the status bar
→ Make sure you've selected a folder

---

**Happy organizing! 🍫**

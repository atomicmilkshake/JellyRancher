# JellyRancher UX Redesign Master Plan

**Status:** Approved for Implementation  
**Created:** 2025-11-17  
**Version:** 1.0  
**Target:** Phase 32 Implementation

---

## Executive Summary

### The Problem
The current `jelly_rancher_clean.py` GUI (2,445 lines) implements a rigid, linear 9-step wizard that:
- Forces users through steps sequentially even when they want to skip/revisit
- Loses all state when closed (no save/resume capability)
- Provides poor feedback and limited interactivity
- Feels "janky and counterintuitive and rigid/inflexible"

### The Solution: Project-Centric Workflow Canvas
Transform JellyRancher from a **wizard** into a **studio** - a flexible, project-based workspace where users can:
- **Save and resume** work at any point
- **Work non-linearly** - jump between steps, compare analyses, iterate
- **See everything** - project state, dependencies, progress at a glance
- **Stay in control** - preview, tweak, approve with full visibility

**Think:** Photoshop/Premiere/VSCode, not Windows installer wizard.

---

## Core UX Principles

### 1. Project-Centric
Everything revolves around **projects**. A project contains:
- Scanned folders and file inventory
- LLM analyses (multiple versions for comparison)
- Action plans (approved/rejected operations)
- Execution history and transaction logs
- User preferences and settings

### 2. Task-Based, Not Step-Based
Instead of "Step 3 of 9", show:
- **"What do you want to do?"**
- Available actions based on current state
- Clear requirements for locked actions
- Smart suggestions for next steps

### 3. Always Visible Context
Users should always see:
- Current project name and state
- What's been done, what's pending
- Performance metrics and estimates
- Quick access to logs and history

### 4. Flexible Workflow
Users can:
- Skip optional steps
- Redo previous steps
- Compare multiple analyses side-by-side
- Export/import at any stage

### 5. Professional Polish
- Modern, clean visual design
- Responsive interactions
- Contextual help and tooltips
- Keyboard shortcuts
- Undo/redo where applicable

---

## Main Window Layout: "The Studio"

```
┌─────────────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help              [Project: My Media Library ▼]│
├───────────┬─────────────────────────────────────────────────────────────┤
│           │                                                               │
│ PROJECT   │                    WORKSPACE                                 │
│ EXPLORER  │                                                               │
│           │  ┌─────────────────────────────────────────────────────┐    │
│ 📁 Scans  │  │                                                     │    │
│  ├─ Scan1 │  │         [Active View: Scan Results]                │    │
│  └─ Scan2 │  │                                                     │    │
│           │  │   - OR -                                            │    │
│ 🤖 Analyses│ │                                                     │    │
│  ├─ GPT4  │  │   [Split View: Compare Two Analyses]               │    │
│  └─ Claude│  │                                                     │    │
│           │  │   - OR -                                            │    │
│ 📋 Plans  │  │                                                     │    │
│  └─ Plan1 │  │   [Action Plan Review Table]                       │    │
│           │  │                                                     │    │
│ ⚙️ Execute│  │   - OR -                                            │    │
│  └─ Logs  │  │                                                     │    │
│           │  │   [Execution Progress & Logs]                      │    │
│ 📊 Reports│  │                                                     │    │
│           │  └─────────────────────────────────────────────────────┘    │
│           │                                                               │
│ [Actions] │  ┌─────────────────────────────────────────────────────┐    │
│ ▶ Scan    │  │ CONTEXT PANEL (collapsible)                        │    │
│ ▶ Analyze │  │ - Details about selected item                       │    │
│ ▶ Review  │  │ - Quick stats                                       │    │
│ ▶ Execute │  │ - Related actions                                   │    │
│           │  └─────────────────────────────────────────────────────┘    │
├───────────┴─────────────────────────────────────────────────────────────┤
│ ⚡ Ready  │  📁 1,234 files scanned  │  🤖 2 analyses  │  ⏱️ 00:26.7s   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layout Components

#### A. Top Bar
- **Menu Bar:** File, Edit, View, Tools, Help
- **Project Selector:** Dropdown showing current project + recent projects
- **Quick Actions:** New Project, Save, Settings

#### B. Left Sidebar: Project Explorer (250px, resizable)
**Hierarchical tree view of project contents:**

1. **📁 Scans** - All scan sessions
   - Each scan shows: date, folder count, file count
   - Click to view scan results
   - Right-click: Re-scan, Delete, Export

2. **🤖 Analyses** - LLM analysis results
   - Each analysis shows: model, date, confidence
   - Click to view full analysis
   - Right-click: Re-analyze, Compare, Export

3. **📋 Action Plans** - Generated plans
   - Shows: total operations, approved count, rejected count
   - Click to open review table
   - Right-click: Edit, Export, Duplicate

4. **⚙️ Execution** - Transaction logs
   - Shows: execution status, progress
   - Click to view detailed log
   - Right-click: Rollback, Export

5. **📊 Reports** - Generated reports
   - Metadata summaries
   - Duplicate analysis
   - Collection suggestions

**Bottom of sidebar:**
- **[Action Buttons]** - Context-aware buttons for next logical steps

#### C. Center: Workspace (flexible, multi-document)
**Tabbed interface supporting multiple simultaneous views:**

- **Scan Results View**
- **Analysis View** (single or split for comparison)
- **Action Plan Review Table** (Excel-like)
- **Execution Monitor**
- **Metadata Browser**
- **Settings Panel**

Users can open multiple tabs and arrange them side-by-side.

#### D. Right Panel: Context Panel (300px, collapsible)
**Shows details about currently selected item:**
- Properties
- Statistics
- Related items
- Quick actions
- Help text

#### E. Bottom: Status Bar
- **Left:** Current operation status
- **Center:** Key metrics (files, size, time)
- **Right:** Performance indicators, log access

---

## Key Views & Interactions

### View 1: Scan Configuration & Results

**Purpose:** Select folders, configure scan options, view inventory

**Layout:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ SCAN CONFIGURATION                                    [▶ Start Scan] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Selected Folders:                                    [+ Add Folder]  │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │ Path                    │ Included │ Excluded │ Actions        │   │
│ ├───────────────────────────────────────────────────────────────┤   │
│ │ D:\Media\Movies         │ 245      │ 12       │ [Edit] [Remove]│   │
│ │ E:\TV Shows             │ 1,023    │ 5        │ [Edit] [Remove]│   │
│ └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
│ Options:                                                              │
│ ☑ Calculate MD5 hashes (slower, enables duplicate detection)         │
│ ☑ Extract metadata from filenames                                    │
│ ☐ Deep scan (analyze file contents)                                  │
│                                                                       │
│ Estimated time: ~30 seconds for 1,268 files (1.3 TB)                 │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│ SCAN RESULTS                                                          │
├─────────────────────────────────────────────────────────────────────┤
│ [Search: ___________] [Filter ▼] [Group By: Type ▼] [Export]        │
│                                                                       │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │ Filename        │ Path      │ Size  │ Type │ MD5      │ Meta   │   │
│ ├───────────────────────────────────────────────────────────────┤   │
│ │ Movie.mkv       │ D:\Media\ │ 4.2GB │ MKV  │ a3f2... │ ✓      │   │
│ │ Show.S01E01.mkv │ E:\TV\    │ 1.8GB │ MKV  │ b7e9... │ ✓      │   │
│ │ ...             │           │       │      │         │        │   │
│ └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
│ Showing 1,268 files │ Total: 1.3 TB │ Duplicates: 3 │ Issues: 12    │
└─────────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- **Add Folder:** Opens `FolderContentSelectionDialog` (existing)
- **Edit:** Re-opens selection dialog to adjust inclusions/exclusions
- **Start Scan:** Runs scan with progress overlay
- **Table:** Sortable, filterable, resizable columns
- **Right-click row:** Quick actions (open location, view metadata, mark as reviewed)

---

### View 2: LLM Analysis

**Purpose:** Configure and run LLM analysis, view results, compare multiple analyses

**Single Analysis View:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ LLM ANALYSIS                                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Model: [Claude-3.7-Sonnet ▼]  [Refresh Models]  [Preview Prompt]    │
│                                                                       │
│ Analysis Type:                                                        │
│ ● Folder Structure Analysis (recommend reorganization)               │
│ ○ Metadata Enhancement (suggest missing metadata)                    │
│ ○ Duplicate Detection (find similar content)                         │
│                                                                       │
│ Options:                                                              │
│ ☑ Include file samples in prompt                                     │
│ ☑ Request confidence scores                                          │
│ ☐ Use extended context (slower, more accurate)                       │
│                                                                       │
│ Estimated cost: ~$0.15 │ Time: ~30s                [▶ Run Analysis]  │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│ ANALYSIS RESULTS                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Analysis: GPT-4 Analysis (2025-11-17 14:32)                          │
│ Status: ✓ Complete │ Confidence: High │ Issues Found: 23             │
│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ SUMMARY                                                           │ │
│ │                                                                   │ │
│ │ The current structure mixes movies and TV shows in inconsistent  │ │
│ │ hierarchies. Recommended reorganization:                         │ │
│ │                                                                   │ │
│ │ • Separate /Movies and /TV Shows top-level directories           │ │
│ │ • Standardize naming: "Title (Year)" for movies                  │ │
│ │ • TV shows: "Show Name/Season XX/Episode files"                  │ │
│ │ • 23 files need renaming for Jellyfin compatibility              │ │ │
│ │                                                                   │ │
│ │ [View Full Analysis] [Export JSON] [Compare with Another]        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│ [Generate Action Plan from This Analysis]                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Comparison View (Side-by-Side):**
```
┌─────────────────────────────────────────────────────────────────────┐
│ COMPARE ANALYSES                                                      │
├──────────────────────────────────┬──────────────────────────────────┤
│ GPT-4 (2025-11-17 14:32)         │ Claude (2025-11-17 14:45)        │
│ Confidence: High                 │ Confidence: Medium               │
├──────────────────────────────────┼──────────────────────────────────┤
│ Issues Found: 23                 │ Issues Found: 31                 │
│                                  │                                  │
│ Recommends:                      │ Recommends:                      │
│ • Separate Movies/TV             │ • Separate Movies/TV             │
│ • Standardize naming             │ • Standardize naming             │
│ • 23 renames                     │ • 31 renames + 8 moves           │
│                                  │                                  │
│ [View Full]                      │ [View Full]                      │
├──────────────────────────────────┴──────────────────────────────────┤
│ DIFFERENCES:                                                          │
│ • Claude identified 8 additional multi-part episodes                 │
│ • GPT-4 has higher confidence scores overall                         │
│ • Both agree on core structure recommendations                       │
│                                                                       │
│ [Generate Merged Action Plan] [Export Comparison]                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- **Preview Prompt:** Shows full prompt in dialog (existing functionality)
- **Run Analysis:** Executes with progress indicator
- **Compare:** Opens split view with two selected analyses
- **Generate Action Plan:** Creates new plan in Project Explorer

---

### View 3: Action Plan Review (The Excel-Like Table)

**Purpose:** Review, approve/reject, edit proposed operations

```
┌─────────────────────────────────────────────────────────────────────┐
│ ACTION PLAN REVIEW                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Plan: From GPT-4 Analysis (23 operations)                            │
│ Status: 15 approved, 3 rejected, 5 pending review                    │
│                                                                       │
│ [Search: ___________] [Filter ▼] [Group By: Type ▼]                  │
│ [Select All] [Approve Selected] [Reject Selected] [Bulk Edit]        │
│                                                                       │
│ ┌───────────────────────────────────────────────────────────────────┐│
│ │☑│Type  │Current Path      │Proposed Path     │Confidence│Approve││ │
│ ├─┼──────┼──────────────────┼──────────────────┼──────────┼───────┤│ │
│ │☑│RENAME│Movie 2023.mkv    │Movie (2023).mkv  │ HIGH ●   │  ☑    ││ │
│ │☑│MOVE  │D:\Mix\Show.mkv   │E:\TV\Show\S01\.. │ HIGH ●   │  ☑    ││ │
│ │☐│RENAME│OldName.avi       │NewName.avi       │ MED  ◐   │  ☐    ││ │
│ │☑│NFO   │Multi-part.mkv    │[Create NFO]      │ HIGH ●   │  ☑    ││ │
│ │...                                                                ││ │
│ └───────────────────────────────────────────────────────────────────┘│
│                                                                       │
│ [👁️ Preview Changes] [💾 Save Plan] [▶ Execute Approved]              │
│                                                                       │
│ ⚠️  Dry Run Available: Test without making actual changes            │
└─────────────────────────────────────────────────────────────────────┘
```

**Advanced Features:**
- **Search:** Real-time filtering across all columns
- **Group By:** Type, Confidence, Status, Source Folder
- **Bulk Edit:** Select multiple rows, apply action
- **Inline Editing:** Double-click paths to manually adjust
- **Drag & Drop:** Reorder operations (respects dependencies)
- **Color Coding:**
  - Green: Approved
  - Red: Rejected
  - Yellow: Pending review
  - Gray: Blocked (dependency not met)
- **Right-click menu:**
  - Edit operation
  - View file details
  - Open file location
  - Add to exceptions
  - View similar operations

**Preview Changes Modal:**
Shows before/after folder structure as tree view with diffs highlighted.

---

### View 4: Execution Monitor

**Purpose:** Real-time execution progress, transaction log, rollback capability

```
┌─────────────────────────────────────────────────────────────────────┐
│ EXECUTION MONITOR                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Executing: Action Plan 1 (15 operations approved)                    │
│                                                                       │
│ Progress: ████████████████░░░░░░░░░░  60% (9/15)                     │
│ Elapsed: 00:12.4s │ Remaining: ~00:08s │ Speed: 0.7 ops/sec          │
│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ TRANSACTION LOG                                                   │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ ✓ [14:52:01] RENAME: Movie.mkv → Movie (2023).mkv               │ │
│ │ ✓ [14:52:03] MOVE: Show.mkv → E:\TV\Show\S01\Show.S01E01.mkv    │ │
│ │ ✓ [14:52:05] NFO: Created Show.S01E01.nfo                        │ │
│ │ ⏳ [14:52:07] RENAME: Processing...                              │ │
│ │ ⏸️ [Pending] MOVE: Waiting for dependency...                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│ [⏸️ Pause] [⏹️ Stop] [↩️ Rollback All] [💾 Export Log]                │
│                                                                       │
│ ⚠️  Rollback available: All operations are reversible                │
└─────────────────────────────────────────────────────────────────────┘
```

**Post-Execution Summary:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ EXECUTION COMPLETE                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ ✓ Successfully completed 15 operations in 00:20.8s                   │
│                                                                       │
│ Summary:                                                              │
│ • 8 files renamed                                                     │
│ • 5 files moved                                                       │
│ • 2 NFO files created                                                 │
│ • 0 errors                                                            │
│                                                                       │
│ Next Steps:                                                           │
│ ☐ Trigger Jellyfin library refresh                                   │
│ ☐ Verify changes in Jellyfin                                         │
│ ☐ Generate completion report                                         │
│                                                                       │
│ [🔄 Refresh Jellyfin] [📊 View Report] [✓ Close]                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Management

### File Menu
```
File
├─ New Project...              Ctrl+N
├─ Open Project...             Ctrl+O
├─ Open Recent                 →
│  ├─ My Media Library
│  ├─ TV Shows Reorganization
│  └─ Movie Collection 2024
├─ Save Project                Ctrl+S
├─ Save Project As...          Ctrl+Shift+S
├─ Close Project               Ctrl+W
├─────────────────────
├─ Import...                   →
│  ├─ Import Scan Results
│  ├─ Import Action Plan
│  └─ Import from JSON
├─ Export...                   →
│  ├─ Export Current View
│  ├─ Export Full Project
│  └─ Export Report
├─────────────────────
├─ Settings...                 Ctrl+,
└─ Exit                        Alt+F4
```

### Project Structure (Database)

**Table: `projects`**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_opened TIMESTAMP,
    state TEXT DEFAULT 'active',  -- active, archived, template
    settings_json TEXT  -- Project-specific settings
);
```

**Table: `project_scan_sessions`**
```sql
CREATE TABLE project_scan_sessions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    scan_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_end TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    scan_options_json TEXT,  -- MD5 enabled, deep scan, etc.
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**Table: `project_analyses`**
```sql
CREATE TABLE project_analyses (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    scan_session_id INTEGER,
    model_name TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prompt_text TEXT,
    response_text TEXT,
    parsed_json TEXT,
    confidence TEXT,  -- HIGH, MEDIUM, LOW
    issues_found INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (scan_session_id) REFERENCES project_scan_sessions(id)
);
```

**Table: `project_action_plans`**
```sql
CREATE TABLE project_action_plans (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    analysis_id INTEGER,
    plan_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_operations INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    executed BOOLEAN DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (analysis_id) REFERENCES project_analyses(id)
);
```

**Table: `project_operations`**
```sql
CREATE TABLE project_operations (
    id INTEGER PRIMARY KEY,
    action_plan_id INTEGER NOT NULL,
    operation_type TEXT NOT NULL,  -- RENAME, MOVE, NFO, etc.
    current_path TEXT,
    proposed_path TEXT,
    current_md5 TEXT,
    proposed_md5 TEXT,
    confidence TEXT,
    user_approved BOOLEAN DEFAULT NULL,  -- NULL=pending, 0=rejected, 1=approved
    executed BOOLEAN DEFAULT 0,
    execution_timestamp TIMESTAMP,
    rollback_data_json TEXT,  -- For undo capability
    FOREIGN KEY (action_plan_id) REFERENCES project_action_plans(id)
);
```

**Table: `project_state`**
```sql
CREATE TABLE project_state (
    project_id INTEGER PRIMARY KEY,
    current_view TEXT,  -- Last active view
    ui_state_json TEXT,  -- Window size, splitter positions, etc.
    last_scan_session_id INTEGER,
    last_analysis_id INTEGER,
    last_action_plan_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Save/Load Behavior

**On Save (Auto-save every 30s + manual save):**
1. Persist all scan results to `scanned_files` table
2. Save all analyses to `project_analyses`
3. Save action plan state (approved/rejected) to `project_operations`
4. Save UI state (window position, splitter sizes, active tab) to `project_state`
5. Update `last_opened` timestamp

**On Load:**
1. Restore scan results from database
2. Populate Project Explorer with all saved items
3. Restore UI state (window, splitters, last active view)
4. Show "Resume from last session?" if work was in progress

**On Close:**
1. Prompt to save if unsaved changes exist
2. Auto-save project state
3. Close cleanly (no data loss)

---

## Smart Dependency Handling

Instead of hard-blocking users, provide **smart guidance**:

### Example: User Tries to Generate Action Plan Without Scan

**Current (Bad):**
```
❌ Error: You must complete a scan first.
[OK]
```

**New (Good):**
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  Action Plan Requires Scan Results                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ To generate an action plan, you need:                            │
│ ✓ Scanned files (required)                                       │
│ ✗ LLM analysis (recommended but optional)                        │
│                                                                   │
│ Options:                                                          │
│ 1. [▶ Run Scan Now] - Quick scan with default settings (~30s)    │
│ 2. [📂 Load Previous Scan] - Use existing scan from this project │
│ 3. [📥 Import Scan Results] - Import from another project        │
│                                                                   │
│ [Cancel]                                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Example: User Tries to Execute Without Approvals

**New (Good):**
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  No Operations Approved                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Your action plan has 23 operations, but none are approved yet.   │
│                                                                   │
│ Quick Actions:                                                    │
│ • [✓ Approve All High Confidence] (15 operations)                │
│ • [👁️ Review in Table] - Manually select operations              │
│ • [🤖 Auto-Approve by Rules] - Set approval criteria              │
│                                                                   │
│ [Cancel]                                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Visual Design System

### Color Palette
```
Primary:   #2c3e50  (Dark blue-gray) - Headers, primary buttons
Secondary: #3498db  (Bright blue) - Links, accents
Success:   #27ae60  (Green) - Approved, completed
Warning:   #f39c12  (Orange) - Pending, caution
Danger:    #e74c3c  (Red) - Rejected, errors
Info:      #9b59b6  (Purple) - Info, help

Background: #ecf0f1  (Light gray)
Surface:    #ffffff  (White)
Border:     #bdc3c7  (Medium gray)
Text:       #2c3e50  (Dark)
Text-Light: #7f8c8d  (Gray)
```

### Typography
```
Headings:  Segoe UI, 18pt, Bold
Body:      Segoe UI, 10pt, Regular
Mono:      Consolas, 9pt (for paths, logs)
```

### Spacing
```
Padding:   10px (standard), 20px (sections)
Margins:   10px (between elements)
Borders:   1px solid #bdc3c7
Radius:    4px (buttons, panels)
```

### Icons
Use **Material Design Icons** or **Font Awesome** for consistency:
- 📁 Folder
- 🤖 AI/Analysis
- 📋 Action Plan
- ⚙️ Settings/Execute
- 📊 Reports
- ✓ Success
- ⚠️ Warning
- ❌ Error

---

## Keyboard Shortcuts

### Global
- `Ctrl+N` - New Project
- `Ctrl+O` - Open Project
- `Ctrl+S` - Save Project
- `Ctrl+W` - Close Project
- `Ctrl+,` - Settings
- `Ctrl+Q` - Quit
- `F1` - Help
- `F5` - Refresh current view

### Navigation
- `Ctrl+1` through `Ctrl+9` - Jump to Project Explorer sections
- `Ctrl+Tab` - Next workspace tab
- `Ctrl+Shift+Tab` - Previous workspace tab
- `Alt+Left` - Back
- `Alt+Right` - Forward

### Actions
- `Ctrl+R` - Run/Execute current action
- `Ctrl+P` - Preview
- `Space` - Toggle checkbox (in tables)
- `Ctrl+A` - Select all (in tables)
- `Delete` - Remove selected item

### Table-Specific
- `Ctrl+F` - Search/Filter
- `Ctrl+G` - Group by
- `Ctrl+E` - Export
- `↑↓` - Navigate rows
- `Enter` - Edit selected row
- `Esc` - Cancel edit

---

## Implementation Phases

### Phase 32A: Foundation (Week 1)
**Goal:** Project management infrastructure + basic UI shell

**Tasks:**
1. **Database Schema** (Day 1)
   - Create all project management tables
   - Migration script from current schema
   - Test save/load with existing data

2. **Project Manager Class** (Day 2)
   - `ProjectManager` class for CRUD operations
   - Auto-save functionality (every 30s)
   - Import/export utilities

3. **Main Window Shell** (Day 3-4)
   - Create main window with menu bar
   - Implement left sidebar (Project Explorer tree)
   - Add tabbed workspace area
   - Status bar with metrics

4. **Project Explorer** (Day 5)
   - Tree widget with icons
   - Context menus
   - Drag-and-drop (basic)
   - Double-click to open views

**Deliverable:** Users can create/save/load projects, see project structure in sidebar

---

### Phase 32B: Core Views (Week 2)
**Goal:** Implement the 4 main views with full functionality

**Tasks:**
1. **Scan View** (Day 1-2)
   - Migrate existing scan UI to new view
   - Add folder table with include/exclude
   - Integrate existing `FolderContentSelectionDialog`
   - Results table with search/filter

2. **Analysis View** (Day 3-4)
   - Single analysis view with model selector
   - Integrate existing prompt preview
   - Split comparison view
   - Save multiple analyses per project

3. **Action Plan Review** (Day 5-6)
   - Excel-like table with all features:
     - Search, filter, group by
     - Inline editing
     - Bulk operations
     - Color coding
   - Preview changes modal

4. **Execution Monitor** (Day 7)
   - Real-time progress display
   - Transaction log viewer
   - Pause/resume/rollback controls

**Deliverable:** All 9 workflow points accessible as flexible views

---

### Phase 32C: Polish & Advanced Features (Week 3)
**Goal:** Professional polish, advanced features, user delight

**Tasks:**
1. **Visual Design** (Day 1-2)
   - Apply QSS stylesheet for modern look
   - Consistent icons throughout
   - Smooth animations (fade, slide)
   - Dark mode support

2. **Smart Interactions** (Day 3-4)
   - Contextual help tooltips
   - Smart dependency dialogs
   - Keyboard shortcuts
   - Undo/redo where applicable

3. **Advanced Features** (Day 5-6)
   - Analysis comparison diff view
   - Bulk edit operations
   - Custom filters and saved views
   - Export to various formats

4. **Testing & Refinement** (Day 7)
   - User testing with real workflows
   - Performance optimization
   - Bug fixes
   - Documentation

**Deliverable:** Production-ready, polished application

---

## Migration Strategy

### Approach: Parallel Development + Gradual Cutover

**Step 1: Keep `jelly_rancher_clean.py` Working**
- Don't break existing functionality
- New code in separate files: `jelly_rancher_studio.py` (new main), `ui/` directory

**Step 2: Extract Reusable Components**
- Move worker classes to `scripts/workers/`
- Keep existing `FileScanner`, `LLMStructureAnalyzer`, etc.
- Create new UI components in `scripts/ui/`

**Step 3: Build New UI Alongside**
- Develop `jelly_rancher_studio.py` as separate application
- Test thoroughly before switching
- Allow users to choose which to launch

**Step 4: Data Migration**
- Script to migrate existing `scanned_files` to new project schema
- One-time migration on first launch of new UI
- Keep old data intact (no data loss)

**Step 5: Deprecate Old UI**
- After new UI is stable, mark old UI as legacy
- Eventually remove after user feedback period

---

## Success Criteria

### User Experience
- ✅ Users can save and resume work at any point
- ✅ Users can work non-linearly (skip, revisit, compare)
- ✅ Users understand current state at a glance
- ✅ Users feel in control (preview, approve, rollback)
- ✅ UI feels modern and professional

### Performance
- ✅ Project save/load < 2 seconds for typical project
- ✅ UI remains responsive during all operations
- ✅ Table with 10,000+ rows remains smooth

### Functionality
- ✅ All 9 workflow points accessible and functional
- ✅ No data loss on crash or unexpected close
- ✅ Full rollback capability for all operations
- ✅ Multiple analyses can be compared side-by-side

### Code Quality
- ✅ Clean separation of concerns (UI, logic, data)
- ✅ Comprehensive error handling
- ✅ Centralized logging
- ✅ Unit tests for core functionality
- ✅ Documentation for all major components

---

## Risk Mitigation

### Risk 1: Scope Creep
**Mitigation:** Strict phase boundaries. Phase 32A must be complete before 32B starts.

### Risk 2: Database Performance
**Mitigation:** Index all foreign keys. Test with 100,000+ file projects early.

### Risk 3: UI Complexity
**Mitigation:** Start with simple layouts. Add advanced features incrementally.

### Risk 4: User Adoption
**Mitigation:** Keep old UI available. Provide migration guide. Gather feedback early.

### Risk 5: Breaking Changes
**Mitigation:** Comprehensive testing. Parallel development. Gradual rollout.

---

## Appendix: Wireframe Details

### New Project Dialog
```
┌─────────────────────────────────────────────────────────────┐
│ Create New Project                                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Project Name: [_________________________________]             │
│                                                               │
│ Description:  ┌─────────────────────────────────┐            │
│               │                                 │            │
│               │                                 │            │
│               └─────────────────────────────────┘            │
│                                                               │
│ Location: [C:\Users\...\JellyRancher\projects\] [Browse]     │
│                                                               │
│ Template:                                                     │
│ ● Blank Project                                              │
│ ○ From Existing Scan                                         │
│ ○ Duplicate Existing Project                                │
│                                                               │
│                                    [Cancel]  [Create Project] │
└─────────────────────────────────────────────────────────────┘
```

### Settings Dialog (Expanded)
```
┌─────────────────────────────────────────────────────────────────────┐
│ Settings                                                              │
├───────────┬─────────────────────────────────────────────────────────┤
│           │                                                           │
│ General   │ Application Settings                                     │
│ Scanning  │                                                           │
│ LLM       │ Theme: [Light ▼]                                         │
│ Execution │ Language: [English ▼]                                    │
│ Jellyfin  │ Auto-save interval: [30] seconds                         │
│ Advanced  │ ☑ Check for updates on startup                           │
│           │ ☑ Send anonymous usage statistics                        │
│           │                                                           │
│           │ Default Paths                                             │
│           │ Projects: [C:\Users\...\projects\] [Browse]              │
│           │ Logs: [C:\Users\...\logs\] [Browse]                      │
│           │ Temp: [C:\Users\...\temp\] [Browse]                      │
│           │                                                           │
├───────────┼─────────────────────────────────────────────────────────┤
│           │                                    [Cancel]  [Apply]  [OK]│
└───────────┴─────────────────────────────────────────────────────────┘
```

---

## Next Steps: Implementation Kickoff

### Immediate Actions (Today)
1. ✅ **Document this plan** - `docs/UX_REDESIGN_MASTER_PLAN.md`
2. ✅ **Update journal** - Record Phase 32 planning completion
3. ✅ **Commit to Git** - Save this milestone

### Tomorrow: Start Phase 32A
1. **Create database migration script**
   - Add new tables to `scripts/database/schema.sql`
   - Write migration function in `scripts/database/migrations.py`
   - Test with existing `media_library.db`

2. **Create `ProjectManager` class**
   - File: `scripts/core/project_manager.py`
   - Methods: `create_project()`, `load_project()`, `save_project()`, `list_projects()`
   - Auto-save timer integration

3. **Start new main window**
   - File: `jelly_rancher_studio.py`
   - Basic window with menu bar
   - Empty Project Explorer sidebar
   - Tabbed workspace area

### Week 1 Goal
By end of Week 1, users should be able to:
- Create a new project
- Save and load projects
- See project structure in sidebar
- Open basic views in workspace

---

**End of Master Plan**

*This document is the authoritative reference for Phase 32 implementation.*  
*All development should align with this plan.*  
*Updates to this plan require user approval.*


# JellyRancher Bootstrap Guide for LLM Coding Assistants

## 🚨 PRIME DIRECTIVE: Virtual Environment

**ALWAYS USE THE VIRTUAL ENVIRONMENT FOR ALL PYTHON OPERATIONS**

### Critical Rules:
1. **NEVER run `python` directly** - it uses system Python 3.14 which breaks ChromaDB
2. **ALWAYS use `.venv\Scripts\python.exe`** - this is Python 3.10 with correct dependencies
3. **CHECK before every Python command** - verify you're using the venv

### Correct Usage:
```bash
# ✅ CORRECT - Use venv Python
.venv\Scripts\python.exe script.py
.venv\Scripts\python.exe -m pip install package
.venv\Scripts\python.exe -c "import sys; print(sys.executable)"

# ❌ WRONG - Do not use system Python
python script.py              # Uses Python 3.14 - breaks ChromaDB!
pip install package           # Installs to wrong Python!
python -c "..."              # Uses wrong interpreter!
```

### Why This Matters:
- System Python 3.14 is **incompatible with ChromaDB** (Pydantic v1 issues)
- Venv Python 3.10 has all correct dependencies installed
- Using wrong Python causes cryptic errors: "unable to infer type for attribute 'chroma_db_impl'"

### Quick Verification:
```bash
# Check which Python you're using
.venv\Scripts\python.exe --version  # Should show: Python 3.10.0
python --version                     # Shows: Python 3.14.0 (WRONG!)
```

## Quick Start

When a user says "bootstrap", run the comprehensive verification script:

```bash
.venv\Scripts\python.exe bootstrap.py
```

This script performs all necessary checks automatically and provides detailed feedback.

### Manual Verification (if needed):

1. **Verify Virtual Environment**
   ```bash
   .venv/Scripts/python.exe --version
   # Should show: Python 3.10+
   ```

2. **Run Comprehensive Bootstrap Check**
   ```bash
   .venv/Scripts/python.exe bootstrap.py
   # Provides complete environment verification
   ```

3. **Query ChromaDB for Project Context**
   - ALWAYS query ChromaDB before starting ANY task
   - ChromaDB contains ALL project documentation, history, and decisions
   - Use semantic search to find relevant information

## 🚨 CRITICAL: ChromaDB is the Sole Source of Truth

### What This Means

**ChromaDB contains EVERYTHING:**
- ✅ Project documentation (README, guides, workflows)
- ✅ Development journal (all sessions, all decisions)
- ✅ Feature implementations (what works, what's been tried)
- ✅ Architecture decisions (why things are built this way)
- ✅ Troubleshooting guides (known issues and solutions)
- ✅ API documentation (how to use all components)
- ✅ Project roadmap (what's planned, what's completed)
- ✅ Git changelog (all commits are reflected in ChromaDB)

**Loose documentation files are ARCHIVED:**
- All markdown files (except this bootstrap.md) are in `archive/documentation_YYYY-MM-DD/`
- These are historical artifacts only
- **NEVER read from archived docs** - always query ChromaDB instead

## 🚨 CRITICAL: GUI Entry Point Directive

### Official GUI Launcher

**`launch_gui.py` (root directory) is the ONLY authorized GUI entry point for JellyRancher.**

**What This Means:**
- ✅ `launch_gui.py` (root) - **SOLE OFFICIAL LAUNCHER**
- ❌ `scripts/core/launch_gui.py` - **LEGACY, DO NOT USE**
- ❌ All other GUI files (`jelly_rancher_main.py`, `jelly_rancher_main_jellyfin.py`, etc.) - **REFERENCE ONLY**
- ❌ Batch files, shortcuts, or other launchers - **NOT AUTHORIZED**

**When to Use:**
- ✅ User says "launch the GUI" → run `.venv\Scripts\python.exe launch_gui.py`
- ✅ User says "start the application" → run `.venv\Scripts\python.exe launch_gui.py`
- ✅ Testing GUI functionality → run `.venv\Scripts\python.exe launch_gui.py`
- ✅ Any GUI-related task → run `.venv\Scripts\python.exe launch_gui.py`

**Implementation Details:**
- Root `launch_gui.py` imports `main()` from `scripts.core.jelly_rancher_main`
- `scripts/core/jelly_rancher_main.py` contains the complete unified GUI application
- All other GUI files exist for historical reference only
- This directive supersedes all previous launch methods

## How to Use ChromaDB

### 1. Query for Project Information

```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend

mem = ChromaMemoryBackend('./chroma_db')

# Semantic search - finds relevant information
results = mem.query_memory("how to implement TMDB integration", limit=5)

# Show results
for result in results:
    print(result['content'])
    print(result.get('metadata', {}))
```

### 2. Query Before Every Task

**ALWAYS follow this pattern:**

```python
# Before implementing feature X, query:
context = mem.query_memory("feature X implementation architecture", limit=10)

# Before fixing bug Y, query:
context = mem.query_memory("bug Y troubleshooting known issues", limit=10)

# Before refactoring Z, query:
context = mem.query_memory("component Z architecture decisions", limit=10)
```

### 3. Document Everything in ChromaDB

**After completing ANY task, log to ChromaDB:**

```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
from datetime import datetime

mem = ChromaMemoryBackend('./chroma_db')

# Document your activity
mem.add_memory(
    content="""# Task: [Brief Title]
Date: [YYYY-MM-DD]
Type: [feature_implementation|bug_fix|refactor|documentation|session_log]
Status: [completed|in_progress|blocked]

## What Was Done
[Detailed description of work performed]

## Changes Made
- File: path/to/file.py (lines X-Y)
- Added: [features/functions/classes]
- Modified: [what changed and why]
- Deleted: [what was removed and why]

## Implementation Details
[Technical details, patterns used, architectural decisions]

## Testing
[How it was tested, results]

## Issues Encountered
[Problems faced and how they were solved]

## Next Steps
[What should be done next, if anything]
""",
    user_id='llm_assistant',
    metadata={
        'type': 'session_log',  # or 'feature_implementation', 'bug_fix', etc.
        'date': datetime.now().strftime('%Y-%m-%d'),
        'component': 'gui',  # which part of codebase
        'feature': 'contextual_help',  # specific feature/bug
        'status': 'completed',
        'tags': 'gui,help_system,enhancement',  # comma-separated
        'files_modified': 'scripts/core/jelly_rancher_main.py',
        'lines_changed': 324
    }
)

print('[OK] Activity documented in ChromaDB')
```

### 4. Rebuild ALL Indexes After Code Changes

**CRITICAL: After adding/modifying/deleting ANY functions or GUI controls, rebuild ALL indexes:**

```bash
# Enhanced rebuild (auto-generates docstrings for new functions with LLM)
.venv/Scripts/python.exe build_function_index_enhanced.py --enhance-new

# Then rebuild GUI and help indexes
.venv/Scripts/python.exe build_gui_control_index.py
.venv/Scripts/python.exe build_help_index.py
```

**ENHANCED INDEXER ONLY:**
- `build_function_index_enhanced.py` auto-generates comprehensive docstrings with Grok LLM
- Use `--enhance-new` flag to only enhance new/modified functions (recommended)
- Use `--enhance` flag to enhance all functions (slower)
- See `ENHANCED_INDEXER_GUIDE.md` for details

**Why ALL Indexes Are Required:**

1. **Function Index** (`function_index.json`)
   - Project's API reference with 1,773 functions
   - 1,757 functions have LLM-enhanced docstrings (99% coverage)
   - Signatures, comprehensive docstrings, parameters, return types
   - Stored in JSON + ChromaDB
   - Can auto-generate docstrings for new functions via `build_function_index_enhanced.py`

2. **GUI Control Index** (`gui_control_index.json`)
   - Maps EVERY GUI control to its connected function
   - **Prevents LLMs from creating STUB implementations**
   - **Enforces function accountability**
   - Detects unconnected controls and stub functions
   - Health status: FAIL if any stubs or unconnected controls found

3. **Help Index** (`help_index.json`)
   - Links GUI controls to function docstrings
   - Generates tooltips from function documentation
   - When user hovers mouse over control, shows help from connected function
   - **MUST be synchronized** with GUI Control Index and Function Index

**When to Rebuild:**
- ✅ After adding/modifying/deleting functions
- ✅ After modifying function signatures or docstrings
- ✅ After adding/modifying/deleting GUI controls (buttons, inputs, etc.)
- ✅ After connecting controls to functions
- ✅ After updating tooltips
- ✅ **ALWAYS before committing** to ensure no stubs or unconnected controls

**Example Workflow:**
```bash
# 1. Make code changes (add/modify functions or GUI controls)

# 2. Document in ChromaDB
.venv/Scripts/python.exe -c "from scripts.core.chroma_memory_backend import ChromaMemoryBackend; ..."

# 3. Rebuild ALL indexes
.venv/Scripts/python.exe build_function_index.py
.venv/Scripts/python.exe build_gui_control_index.py
.venv/Scripts/python.exe build_help_index.py

# 4. Check health status
# GUI Control Index: Health Status should be PASS
# Help Index: Help coverage should be >90%
# If FAIL: Fix stubs, connect controls, add docstrings

# 5. Git commit mentioning all index updates
git add function_index.json gui_control_index.json help_index.json chroma_db/
git commit -m "feat: Add new feature X

## Changes
- Added 3 new functions to module Y
- Added 2 GUI controls (connected to functions)
- Updated all indexes:
  - Function index: 1,750 functions
  - GUI control index: PASS (no stubs)
  - Help index: 95% coverage
..."
```

## Development Workflow

### Step 1: Bootstrap
```bash
# User types: "bootstrap"
# You respond: verify environment, check ChromaDB
```

### Step 2: Query ChromaDB for Context
```python
# User asks to implement feature X
# FIRST: Query ChromaDB about feature X
results = mem.query_memory("feature X architecture implementation", limit=10)

# Read the results to understand:
# - Has this been tried before?
# - What patterns should be followed?
# - What are known issues?
# - How does it fit into existing architecture?
```

### Step 3: Perform Work
```python
# Implement the feature/fix following patterns from ChromaDB
# Use existing code as reference
# Follow architectural decisions documented in ChromaDB
```

### Step 4: Document in ChromaDB
```python
# Log everything you did
mem.add_memory(content=detailed_log, metadata=...)
```

### Step 5: Rebuild ALL Indexes (if functions or GUI controls changed)
```bash
# If you added/modified/deleted ANY functions or GUI controls
.venv/Scripts/python.exe build_function_index_enhanced.py --enhance-new
.venv/Scripts/python.exe build_gui_control_index.py
.venv/Scripts/python.exe build_help_index.py

# Check health status - must be PASS before committing
```

### Step 6: Git Commit with ChromaDB-Based Changelog
```bash
# Git commit message should reflect ChromaDB content
git commit -m "$(cat <<'EOF'
feat: Brief description of change

## Summary
[What was done, based on ChromaDB documentation]

## Changes Made
[List of changes, from ChromaDB log]

## Files Modified
[Files changed, from ChromaDB metadata]

Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Common ChromaDB Queries

### Project Overview
```python
results = mem.query_memory("project overview architecture components", limit=5)
```

### Feature Implementation
```python
results = mem.query_memory("feature_name implementation how to use", limit=10)
```

### Troubleshooting
```python
results = mem.query_memory("error_message troubleshooting solution", limit=5)
```

### Integration Roadmap
```python
results = mem.query_memory("integration roadmap todo tasks phases", limit=10)
```

### Recent Activity
```python
# Get recent work (last few days)
results = mem.query_memory("2025-11-09 session implementation", limit=10)
```

### API Usage
```python
results = mem.query_memory("component_name API how to use methods", limit=5)
```

## Rules for LLM Assistants

### ✅ ALWAYS DO

1. **Query ChromaDB first** before any task
2. **Document everything** you do in ChromaDB
3. **Read ChromaDB** for project history and decisions
4. **Trust ChromaDB** - it contains tested, verified information
5. **Update ChromaDB** after every significant change
6. **Use semantic search** - ChromaDB finds relevant info even if keywords don't match exactly
7. **Include metadata** when adding memories (makes searching easier)
8. **Rebuild ALL indexes** after any function or GUI control changes
9. **Check health status** - GUI Control Index must be PASS (no stubs/unconnected controls)
10. **Connect every GUI control to a function** - NO STUBS ALLOWED
11. **Add docstrings to all functions** - for help tooltip generation
12. **Commit all index files** (function_index.json, gui_control_index.json, help_index.json)
13. **Mention index updates** in git commit messages with health status
14. **Commit with ChromaDB-based changelogs** - git reflects ChromaDB

### ❌ NEVER DO

1. **NEVER create new documentation files** (markdown, txt, etc.)
2. **NEVER read from archived documentation** - use ChromaDB instead
3. **NEVER skip ChromaDB queries** before implementing features
4. **NEVER forget to document** your work in ChromaDB
5. **NEVER assume** - if unsure, query ChromaDB for context
6. **NEVER duplicate documentation** - ChromaDB is the single source
7. **NEVER work in isolation** - ChromaDB connects all sessions
8. **NEVER skip rebuilding indexes** after changing functions or GUI controls
9. **NEVER create GUI controls without connecting to functions** - NO STUBS
10. **NEVER create stub implementations** - always implement full functionality
11. **NEVER leave controls unconnected** - every control must have a function
12. **NEVER commit with FAIL health status** - fix stubs and connections first
13. **NEVER commit without updating all indexes** if functions/controls changed
14. **NEVER forget docstrings** - they generate help tooltips

## Function Index System

The JellyRancher project maintains a comprehensive function index that must be kept up-to-date.

### What Is the Function Index?

- **File**: `function_index.json`
- **Builder**: `build_function_index_enhanced.py` - LLM-enhanced function indexer
- **Current Size**: 1,773 functions across 211 Python files
- **Enhanced**: 1,757 functions (99%) have LLM-generated comprehensive docstrings
- **Storage**: Both JSON file (2.3MB) and ChromaDB for semantic search

### What It Contains

For every function in the codebase:
- Function name and signature
- File path and line number
- Docstring/description
- Parameters with type annotations
- Return type annotation
- Whether it's a class method or module-level function
- Parent class name (if applicable)

### Why It's Critical

1. **API Reference**: The function index is the project's complete API reference
2. **Discoverability**: Makes all 1,747+ functions searchable via semantic queries
3. **Documentation**: Serves as living documentation of all code
4. **Integration**: Stored in ChromaDB for cross-session context
5. **Onboarding**: New LLM sessions can quickly understand available functionality

### When to Rebuild

**ALWAYS rebuild after:**
- Adding new functions
- Modifying function signatures
- Changing parameters or return types
- Updating docstrings
- Deleting functions
- Renaming functions

**Commands:**
```bash
# Standard rebuild (fast, no enhancement)
.venv/Scripts/python.exe build_function_index.py

# Enhanced rebuild (auto-generates docstrings for new functions)
.venv/Scripts/python.exe build_function_index_enhanced.py --enhance-new
```

**See also:** `ENHANCED_INDEXER_GUIDE.md` for complete docstring enhancement documentation

### Commit Requirements

When committing changes that affect functions:

```bash
# 1. Make code changes
# 2. Rebuild function index
.venv/Scripts/python.exe build_function_index_enhanced.py --enhance-new

# 3. Stage both code and index
git add scripts/your_file.py function_index.json chroma_db/

# 4. Commit with clear message
git commit -m "feat: Add new feature

## Changes
- Added 3 new functions to scripts/core/module.py
- Modified 2 function signatures
- Updated function index (1,750 total functions)

Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>
"
```

### Searching the Function Index

Use ChromaDB semantic search to find functions:

```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
mem = ChromaMemoryBackend('./chroma_db')

# Find functions by purpose
results = mem.query_memory("subtitle download implementation", limit=5)

# Find functions by component
results = mem.query_memory("TMDB cache API functions", limit=5)

# Find functions by name
results = mem.query_memory("analyze episode titles function", limit=5)
```

## GUI Control Index System

The JellyRancher project maintains a comprehensive GUI control index that **PREVENTS LLMs FROM CREATING STUBS**.

### What Is the GUI Control Index?

- **File**: `gui_control_index.json`
- **Builder**: `build_gui_control_index.py`
- **Purpose**: Map EVERY GUI control to its connected function
- **Storage**: Both JSON file and ChromaDB for semantic search

### Critical Requirements

🚨 **NO STUBS ALLOWED** - Every GUI control MUST be connected to a fully implemented function.

The indexer detects:
- Unconnected controls (buttons with no function)
- Stub implementations (functions with pass/TODO/NotImplementedError)
- Health status: **FAIL** if ANY stubs or unconnected controls found

### What It Contains

For every GUI control:
- Control variable name and type (QPushButton, QLineEdit, etc.)
- Control label and tooltip
- File path and line number
- Connected function name
- Connection line number
- Stub detection status
- Health status

### When to Rebuild

**ALWAYS rebuild after:**
- Adding new GUI controls
- Modifying control connections
- Deleting controls
- Changing control types
- Adding/removing signal connections

**Command:**
```bash
.venv/Scripts/python.exe build_gui_control_index.py
```

### Health Status Requirements

Before committing:
- **Health Status**: MUST be PASS
- **Connected**: 100% of controls must be connected to functions
- **Stubs**: 0 stub implementations allowed
- **Unconnected**: 0 unconnected controls allowed

### Example Output

```
================================================================================
GUI CONTROL HEALTH REPORT
================================================================================
Total Controls: 150
Connected: 150 (100%)
Unconnected: 0
Stub Implementations: 0
Health Status: PASS
================================================================================
```

## Help Index System

The help index links GUI controls to their help tooltips derived from function docstrings.

### What Is the Help Index?

- **File**: `help_index.json`
- **Builder**: `build_help_index.py`
- **Purpose**: Generate help tooltips from function docstrings
- **Integration**: GUI Control → Function → Docstring → Tooltip

### How It Works

1. **User hovers mouse over GUI control**
2. **Tooltip displays help from connected function's docstring**
3. **Help text is derived from function documentation**

This ensures:
- Every control has contextual help
- Help text stays synchronized with code
- Function docstrings serve dual purpose (API docs + user help)

### What It Contains

For every GUI control:
- Current tooltip text
- Connected function name
- Function docstring
- Suggested tooltip (generated from docstring)
- Help coverage status
- Update requirements

### When to Rebuild

**ALWAYS rebuild after:**
- Updating function docstrings
- Changing control connections
- Modifying tooltips
- GUI control index changes

**Command:**
```bash
# Must run after function index and GUI control index
.venv/Scripts/python.exe build_help_index.py
```

### Health Status Requirements

Before committing:
- **Help Coverage**: >90% of controls should have help
- **Missing Help**: Minimize controls without docstrings
- **Tooltip Updates**: Review suggested tooltip updates

### Synchronization Requirements

**CRITICAL**: All three indexes must be synchronized:
1. **Function Index** → Provides function signatures and docstrings
2. **GUI Control Index** → Maps controls to functions (no stubs!)
3. **Help Index** → Generates tooltips from docstrings

When you change ANY of these, rebuild ALL THREE indexes.

## ChromaDB API Reference

### Initialize Connection
```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
mem = ChromaMemoryBackend('./chroma_db')
```

### Add Memory
```python
memory_id = mem.add_memory(
    content="Your documentation text here",
    user_id='llm_assistant',  # or 'documentation_system', 'user', etc.
    metadata={
        'type': 'feature_implementation',
        'date': '2025-11-09',
        'tags': 'comma,separated,tags',
        # ... other metadata fields
    }
)
```

### Query Memory
```python
results = mem.query_memory(
    query="your search query",
    user_id=None,  # optional filter by user
    limit=5,  # number of results
    include_metadata=False  # whether to include full metadata
)

# Results structure:
# [
#   {
#     'content': 'The memory content',
#     'metadata': {...},  # if include_metadata=True
#   },
#   ...
# ]
```

### Get Statistics
```python
stats = mem.get_memory_stats()
# Returns:
# {
#   'total_memories': 1152,
#   'collection_name': 'jellyfin_memories'
# }
```

## Project Structure

```
JellyRancher/
├── bootstrap.md                          # This file (only loose doc)
├── chroma_db/                            # ChromaDB database (source of truth)
├── scripts/
│   ├── core/
│   │   ├── jelly_rancher_main.py           # Main GUI application
│   │   ├── chroma_memory_backend.py     # ChromaDB interface
│   │   └── ...
│   ├── media/                           # Media organization backends
│   ├── utils/                           # Utility modules
│   └── tests/                           # Test suite
├── archive/
│   └── documentation_YYYY-MM-DD/        # Archived docs (DO NOT USE)
├── document_to_chromadb.py              # Helper script for documentation
├── ingest_docs_to_chromadb.py           # Bulk doc ingestion
└── requirements-jelly-rancher.txt          # Python dependencies
```

## Example Session

```python
# 1. Bootstrap
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
mem = ChromaMemoryBackend('./chroma_db')
print(f"ChromaDB ready: {mem.get_memory_stats()['total_memories']} memories")

# 2. User asks: "Add feature X to the GUI"

# 3. Query ChromaDB first
gui_context = mem.query_memory("GUI architecture PyQt5 patterns", limit=5)
feature_context = mem.query_memory("feature X implementation", limit=5)

# 4. Read results, understand existing patterns

# 5. Implement feature X following discovered patterns

# 6. Document in ChromaDB
mem.add_memory(
    content="""# Feature X Implementation
Date: 2025-11-09
Status: Completed

## Implementation
- Added feature X to GUI following existing PyQt5 patterns
- Modified: scripts/core/jelly_rancher_main.py
- Pattern used: [discovered from ChromaDB query]

## Testing
- Launched GUI, feature works correctly
- No errors in audit log
""",
    user_id='llm_assistant',
    metadata={
        'type': 'feature_implementation',
        'date': '2025-11-09',
        'component': 'gui',
        'feature': 'feature_x',
        'status': 'completed',
        'tags': 'gui,feature_x,enhancement'
    }
)

# 7. Git commit with ChromaDB-based message
# (commit message reflects ChromaDB documentation)
```

## Getting Help

All project information is in ChromaDB. Use semantic search:

```python
# How do I...?
results = mem.query_memory("how to implement X", limit=5)

# What is...?
results = mem.query_memory("what is component Y architecture", limit=5)

# Why does...?
results = mem.query_memory("why was decision Z made", limit=5)

# When was...?
results = mem.query_memory("when was feature X added 2025", limit=5)
```

## Summary

**ChromaDB = Single Source of Truth**

- 📖 All documentation is in ChromaDB
- 📝 All development journals are in ChromaDB
- 🗺️ Project roadmap is in ChromaDB
- 🔧 All implementation details are in ChromaDB
- 🐛 All troubleshooting guides are in ChromaDB
- 📊 All changelogs are in ChromaDB
- 🔍 Complete function index (1,773 functions, 99% with enhanced docstrings) is in ChromaDB

**Your Workflow:**
1. Query ChromaDB for context
2. Implement based on ChromaDB patterns
3. Document everything in ChromaDB
4. **Rebuild ALL indexes if functions or GUI controls changed**
5. **Check health status - must be PASS before committing**
6. Git commit reflects ChromaDB content and all index updates

**Never:**
- Create loose documentation files
- Read from archived docs
- Work without querying ChromaDB first
- Skip documenting in ChromaDB
- **Create stub implementations - NO STUBS ALLOWED**
- **Leave GUI controls unconnected**
- **Commit with FAIL health status**
- **Forget to rebuild indexes after changes**
- **Commit without updating ALL indexes**

ChromaDB connects all development sessions, maintains project memory, and serves as the permanent knowledge base for JellyRancher.

The three synchronized indexes ensure:
- **Function Index**: All code is discoverable and documented
- **GUI Control Index**: NO STUBS - every control connected to real function
- **Help Index**: Every control has contextual help from function docstrings

One last thing, dickhead.  If I ask you a QUESTION in agent mode, you must ANSWER IT using VERBAL HUMAN LANGUAGE before your start making tool calls and modifying or writing code.  Capische?
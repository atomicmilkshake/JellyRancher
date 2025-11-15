# 🚀 JellyRancher LLM Assistant Bootstrap Guide

## Welcome to JellyRancher! 🤖

This guide will get you up and running as a coding assistant for the JellyRancher project. JellyRancher is a comprehensive media organization platform that unifies multiple tools into a single professional GUI application.

---

## ⚡ Quick Start (3 Steps)

### 1. Activate Virtual Environment
```powershell
# Always start here - NEVER work outside the virtual environment
cd "V:\JellyRancher"
.venv\Scripts\Activate.ps1
```

### 2. Bootstrap ChromaDB Knowledge Base
```powershell
# This ingests the ENTIRE project into ChromaDB for complete knowledge
python scripts/ai/bootstrap_chroma.py
```
**This is mandatory for new assistants!** It creates your complete knowledge base.

### 3. Launch the Application
```powershell
# Test that everything works
python scripts/core/jelly_rancher_main.py
```

---

## 🧠 ChromaDB: Your Sole Source of Truth

### Why ChromaDB?
- **Complete project knowledge** - all code, docs, and context
- **Semantic search** - find anything by meaning, not just keywords
- **Persistent memory** - knowledge accumulates across sessions
- **Activity documentation** - all work is logged and searchable

### How to Use ChromaDB

#### Query Project Knowledge
```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
memory = ChromaMemoryBackend()

# Search for anything
results = memory.query_memory("how does subtitle downloading work?", n_results=5)
for result in results:
    print(f"File: {result['metadata']['file_path']}")
    print(f"Summary: {result['metadata']['summary']}")
    print(f"Content: {result['document'][:200]}...")
```

#### Document Your Activities
```python
# ALWAYS document what you do
memory.add_memory(
    content="Fixed bug in media scanner - added null check for file paths",
    user_id="your_assistant_name",
    metadata={
        "activity": "bug_fix",
        "files_modified": ["scripts/media/media_scanner.py"],
        "lines_changed": "45-52",
        "testing": "ran unit tests, all pass"
    }
)
```

#### Search Examples
- `"how does the GUI work?"` - Find interface documentation
- `"subtitle backend implementation"` - Find specific functionality
- `"testing framework"` - Find test setup and usage
- `"configuration options"` - Find settings and config files
- `"recent changes to media organizer"` - Find recent modifications

---

## 📋 Development Workflow

### 1. Always Start with Virtual Environment
```powershell
# FIRST COMMAND EVERY SESSION
cd "V:\JellyRancher"
.venv\Scripts\Activate.ps1
```

### 2. Query ChromaDB Before Starting
```python
# Check existing knowledge first
memory = ChromaMemoryBackend()
results = memory.query_memory("similar feature already exists?", n_results=3)
```

### 3. Document Your Work Plan
```python
memory.add_memory(
    content="Planning to implement feature X. Will modify files A, B, C. Expected completion: 2 hours.",
    user_id="your_name",
    metadata={"activity": "planning", "feature": "X", "estimated_time": "2h"}
)
```

### 4. Implement and Test
- Write code following project patterns
- Test thoroughly (unit tests, integration tests)
- Run the application to verify functionality

### 5. Document Completion
```python
memory.add_memory(
    content="Completed feature X implementation. Added Y functionality, fixed Z bugs. All tests pass.",
    user_id="your_name",
    metadata={
        "activity": "completion",
        "feature": "X",
        "status": "completed",
        "test_results": "all_pass",
        "files_modified": ["A.py", "B.py", "C.py"]
    }
)
```

---

## 🏗️ Project Structure

```
JellyRancher/
├── scripts/                    # All organized scripts
│   ├── core/                   # Main application (18 files)
│   ├── media/                  # Media processing (29 files)
│   ├── ai/                     # AI/LLM integration (17 files)
│   ├── utils/                  # Utilities (57 files)
│   ├── tests/                  # Test suites (18 files)
│   ├── batch/                  # Automation scripts (10 files)
│   ├── docs/                   # Documentation (4 files)
│   ├── tools/                  # Specialized tools (322 files)
│   ├── _common/                # Shared modules (23 files)
│   └── config/                 # Configuration (1 file)
├── data/                       # Data files (15 files)
├── logs/                       # Log files (12 files)
├── chroma_db/                  # Your knowledge base
├── docs.md                     # Main documentation
└── run_jelly_rancher.bat         # Launcher script
```

---

## 🔧 Key Commands

### Environment Setup
```powershell
# Activate virtual environment (REQUIRED)
.venv\Scripts\Activate.ps1

# Install/update dependencies
pip install -r requirements-jelly-rancher.txt
```

### Knowledge Base Management
```powershell
# Bootstrap complete knowledge (first time only)
python scripts/ai/bootstrap_chroma.py

# Query knowledge base
python -c "from scripts.core.chroma_memory_backend import ChromaMemoryBackend; m=ChromaMemoryBackend(); print(m.query_memory('search query', n_results=3))"
```

### Development
```powershell
# Run main application
python scripts/core/jelly_rancher_main.py

# Run tests
python -m pytest scripts/tests/

# Check code quality
python scripts/tools/code_cop/audit.py
```

### Documentation
```powershell
# Update ChromaDB with your work
python -c "
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
m = ChromaMemoryBackend()
m.add_memory('Completed task X', user_id='your_name', metadata={'activity': 'completion'})
"
```

---

## 📚 Available Functionality

### Core Features
- **Media Organization**: Movies, TV shows, anime with intelligent naming
- **Subtitle Management**: Multi-provider downloads and synchronization
- **AI Batch Processing**: GPT-4, Claude-3, Gemini Pro integration
- **Code Quality Analysis**: Complexity, coverage, security scanning
- **Analytics & Reporting**: System statistics and performance metrics
- **Semantic Memory**: ChromaDB-powered knowledge base

### Key Components
- `scripts/core/jelly_rancher_main.py` - Main GUI application
- `scripts/media/media_org_backend.py` - Media organization engine
- `scripts/media/subtitle_backend.py` - Subtitle management
- `scripts/ai/ravenmaven_client.py` - AI processing client
- `scripts/core/chroma_memory_backend.py` - Knowledge base

---

## 🐛 Troubleshooting

### Virtual Environment Issues
```powershell
# If activation fails
python -m venv .venv --clear
.venv\Scripts\Activate.ps1
pip install -r requirements-jelly-rancher.txt
```

### ChromaDB Issues
```powershell
# If ChromaDB fails to load
# Delete and recreate the database
Remove-Item -Recurse -Force chroma_db
python scripts/ai/bootstrap_chroma.py
```

### Import Errors
```powershell
# If imports fail, check you're in the right directory
cd "V:\JellyRancher"
.venv\Scripts\Activate.ps1
python scripts/core/jelly_rancher_main.py
```

---

## 📝 Documentation Standards

### Code Documentation
- All functions need docstrings
- Complex logic needs inline comments
- New features need usage examples

### ChromaDB Documentation
- Document ALL activities immediately
- Include file paths, line numbers, and test results
- Use consistent metadata tags
- Write searchable summaries

### Commit Messages
- Start with action verb (Add, Fix, Update, Remove)
- Include component name
- Reference issue numbers when applicable

---

## 🎯 Best Practices

### 1. **Always Use Virtual Environment**
Never work outside `.venv` - it ensures consistent dependencies.

### 2. **Query Before Implementing**
```python
# Check if feature exists
results = memory.query_memory("similar functionality", n_results=5)
```

### 3. **Document Everything**
Every change, decision, and test result goes into ChromaDB.

### 4. **Test Thoroughly**
- Unit tests for new functions
- Integration tests for new features
- Manual testing of GUI changes

### 5. **Follow Project Patterns**
- Use existing code structure
- Follow naming conventions
- Maintain error handling patterns

### 6. **Keep Knowledge Base Updated**
- Bootstrap new assistants with `bootstrap_chroma.py`
- Document breaking changes immediately
- Update guides when workflows change

---

## 🚨 Critical Rules

### ✅ DO
- Use virtual environment for ALL work
- Document every activity in ChromaDB
- Query ChromaDB before making assumptions
- Test changes thoroughly
- Follow existing code patterns
- Update documentation for new features

### ❌ DON'T
- Work outside virtual environment
- Make changes without ChromaDB documentation
- Assume knowledge - always query first
- Skip testing
- Break existing functionality
- Ignore import errors

---

## 📞 Getting Help

### ChromaDB Queries
```python
# Find similar issues
memory.query_memory("similar problem", n_results=5)

# Find implementation examples
memory.query_memory("how to implement X", n_results=3)

# Find testing patterns
memory.query_memory("testing approach for Y", n_results=3)
```

### Project Resources
- `docs.md` - Main project documentation
- `scripts/docs/` - Additional guides
- `scripts/_common/` - Shared utilities
- `scripts/tests/` - Testing examples

---

## 🎉 You're Ready!

With ChromaDB bootstrapped and this guide, you have:
- ✅ Complete project knowledge
- ✅ Proper development environment
- ✅ Documentation standards
- ✅ Testing procedures
- ✅ Troubleshooting guides

**Welcome to the JellyRancher development team!** 🎊

*Remember: ChromaDB is your brain - keep it updated, query it often, and it will make you an exceptional coding assistant.*
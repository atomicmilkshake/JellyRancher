# OpenMemory Ingestion Guide

Both ingestion scripts work seamlessly with Rich formatting on Windows, Mac, and Linux.

## Quick Start

### 1. Start the OpenMemory Backend
```bash
cd V:\Jellyfin Organizer\OpenMemory\backend
npm run dev
```

The backend should show:
```
Server listening on port 8080
```

### 2. Run Ingestion (Choose One)

#### Option A: Full-featured version with Rich formatting (Recommended)
```bash
cd V:\Jellyfin Organizer\scripts
python openmemory_ingest_all.py
```

**Features:**
- Beautiful Rich formatting with colors, tables, and progress bars
- Works on Windows, Mac, and Linux
- Automatic UTF-8 encoding on Windows
- Falls back to plain text if Rich unavailable
- Shows semantic search examples after ingestion

#### Option B: Simple version (Lightweight)
```bash
cd V:\Jellyfin Organizer\scripts
python openmemory_ingest_simple.py
```

**Features:**
- Minimal dependencies
- Plain text output
- Lightweight and fast
- No Rich library needed
- Same ingestion results as full version

## Technical Details

### UTF-8 Encoding Fix (Windows)

Both scripts now include automatic UTF-8 encoding configuration:

```python
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Reconfigure stdout/stderr for UTF-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

This solves the Unicode encoding errors that were preventing Rich from working on Windows PowerShell.

### Rich Console Configuration

Both scripts use intelligent Rich initialization:

```python
try:
    from rich.console import Console
    
    # Try modern approach with force_unicode
    console = Console(
        width=100,
        force_terminal=True,
        force_unicode=True,
        legacy_windows=False
    )
except TypeError:
    # Fallback for older Rich versions
    console = Console(width=100, force_terminal=True)
    
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
```

### Graceful Fallback

Both scripts check if Rich is available and fall back to plain text:

```python
if RICH_AVAILABLE and console:
    console.print(colored_formatted_text)
else:
    print(plain_text)
```

## What Gets Ingested

Both scripts ingest:

- **92 documentation files** (.md files)
  - Guides, decisions, architecture, procedures
  
- **114 Python source files** (.py files)
  - Code with full docstrings
  - Includes test files and utilities
  
- **8 configuration files** (.json files)
  - Settings and configurations
  
- **Total: 213 files** (~3M+ characters)

## Expected Output

### With Rich (Full-featured)
```
═════════════════════════════════════════════════
  OpenMemory Project Foundation Builder
═════════════════════════════════════════════════

✓ OpenMemory backend online

📂 Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

⏳ Ingesting documentation... ████████░░ 85%
⏳ Ingesting Python code... ████████░░ 92%
⏳ Ingesting configurations... ░░░░░░░░░░ 0%

┌─ Ingestion Summary ──────────────────────────────┐
│ Category                 Count                   │
├──────────────────────────────────────────────────┤
│ Documentation Files         92                   │
│ Python Files               114                   │
│ Config Files                 8                   │
│ Total Characters       3,245,189                 │
├──────────────────────────────────────────────────┤
│ Total Files Ingested       214                   │
└──────────────────────────────────────────────────┘

🔍 Testing Semantic Search...

Q: How do we organize TV shows?
  [89%] MASTER_PROMPT.md: The system organizes media into standardized...
  [87%] media_utils.py: TV show organization follows standard patterns...

[... more search results ...]

═════════════════════════════════════════════════
  Success!
═════════════════════════════════════════════════
OpenMemory is now the foundation of this project.
AI agents can now query project context semantically.
═════════════════════════════════════════════════
```

### Without Rich (Plain text)
```
============================================================
  OpenMemory Project Foundation Builder
============================================================

[OK] OpenMemory backend online

[SCAN] Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

Ingesting documentation files...
[OK] Ingesting Python code files...
[OK] Ingesting configuration files...
[OK]

============================================================
Ingestion Summary
============================================================
Documentation Files:  92
Python Files:        114
Config Files:          8
Total Characters:     3,245,189
────────────────────────────────────────────────────────────
Total Files Ingested: 214
============================================================

Q: How do we organize TV shows?
  [89%] MASTER_PROMPT.md: The system organizes media into...
  [87%] media_utils.py: TV show organization follows standard...

[... more search results ...]

============================================================
SUCCESS!
============================================================
OpenMemory is now the foundation of this project.
AI agents can now query project context semantically.
============================================================
```

## Troubleshooting

### Problem: "OpenMemory backend not running"

**Solution:** Start the backend first:
```bash
cd V:\Jellyfin Organizer\OpenMemory\backend
npm run dev
```

Wait for: `Server listening on port 8080`

### Problem: Unicode encoding errors

**Solution:** Both scripts now handle this automatically. If you still see errors:

1. Ensure you're using Python 3.7+
2. Try running from VS Code terminal instead of PowerShell
3. Set `PYTHONIOENCODING=utf-8` manually:
   ```bash
   $env:PYTHONIOENCODING = 'utf-8'
   ```

### Problem: "OpenMemory SDK not found"

**Solution:** Install the SDK:
```bash
cd V:\Jellyfin Organizer\OpenMemory\sdk-py
pip install -e .
```

### Problem: Script hangs during ingestion

**Solution:** This is normal for large projects. The first run ingests 213 files and can take 2-5 minutes.

Monitor progress in the terminal - you should see file counts advancing.

## Scripts Comparison

| Feature | `openmemory_ingest_all.py` | `openmemory_ingest_simple.py` |
|---------|----------------------------|-------------------------------|
| Rich Formatting | ✅ Yes (with UTF-8 fix) | ⚠️ Optional |
| Windows Compatible | ✅ Yes | ✅ Yes |
| Ingestion Speed | Normal | Normal |
| Dependencies | Rich (optional) | None |
| Fallback Output | Plain text | Plain text |
| Semantic Search Tests | ✅ Included | ⚠️ Minimal |
| Progress Bars | ✅ Yes | Simple counter |
| File Size | 550 lines | 235 lines |

**Recommendation:** Use `openmemory_ingest_all.py` for the full experience. Both work identically for ingestion; the difference is just presentation.

## Next Steps

After successful ingestion, the system is ready to use with OpenMemory context:

1. **Verify ingestion** - Check that semantic search is working
2. **Test queries** - Try querying project knowledge
3. **Use in AI agents** - All scripts can now access OpenMemory context
4. **Maintain** - Re-run ingestion after major code changes

## API Usage

Both scripts use the same OpenMemory API:

```python
from openmemory import OpenMemory

om = OpenMemory(base_url="http://localhost:8080")

# Ingest a file
om.ingest(
    content="file contents here",
    tags=["documentation", "guide"],
    metadata={
        "file_name": "example.md",
        "type": "markdown"
    }
)

# Query the index
results = om.query(query="How do we organize media?", k=3)
for item in results["items"]:
    print(f"{item['metadata']['file_name']}: {item['content']}")
```

## Support

If you encounter issues:

1. Check that backend is running (`curl http://localhost:8080/health`)
2. Verify Python environment is activated
3. Review error messages in terminal
4. Check `backend_error.log` if backend fails

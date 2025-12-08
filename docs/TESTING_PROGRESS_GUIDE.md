# Testing with Real-Time Progress Reporting

## 🎯 Recommended: pytest-sugar (Native Progress Bar)

**pytest-sugar** is the standard community solution for real-time test progress visualization. It provides:
- ✅ Green progress bar with test counts
- ✅ Elapsed time display
- ✅ Instant failure reporting (no buffering)
- ✅ Native Python integration (no PowerShell piping needed)
- ✅ Works on all platforms (Windows, Linux, macOS)

**Installation:**
```bash
.venv\Scripts\python.exe -m pip install pytest-sugar
```

**Usage:**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

pytest-sugar activates automatically - no special flags needed! Just run pytest normally with `-v` for verbose output.

**Benefits:**
- No PowerShell `Select-Object` piping needed
- No custom wrapper scripts
- Zero buffering issues
- Standard community solution

## Quick Start Commands

**Non-GUI tests (fast, ~10 seconds):**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -m "not requires_gui" -v
```

**All tests:**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

**GUI tests only:**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -m "requires_gui" -v
```

**Parallel execution (faster):**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -n auto -v
```

## Alternative: Rich Library Progress (Advanced)

If you want even more detailed progress with colors, percentages, and ETA, the Rich library hooks in `tests/conftest.py` provide:
- Colorful animated progress bar
- Real-time test names as they run
- Percentage completion (0-100%)
- Pass/Fail/Skip counts with colors
- Time elapsed and ETA
- Beautiful summary table at end

Rich progress is automatically enabled when using `-v` flag (if Rich is installed).

## Parallel Execution

**Auto-detect CPU cores:**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -n auto -v
```

**Specify number of workers:**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -n 4 -v
```

**Note:** GUI tests work with parallel execution, but each worker creates its own QApplication instance.

## Test Counts

- **Total tests:** 560 (362 non-GUI + 185 GUI + 13 validation)
- **Non-GUI tests:** 362 (fast, ~10 seconds)
- **GUI tests:** 185 (slow, ~5-10 minutes)

## Performance Tips

1. **Run non-GUI tests by default** (fast feedback)
2. **Run GUI tests separately** when needed
3. **Use parallel execution** for both (speeds up significantly)
4. **Skip slow tests** unless needed: `-m "not slow"`

## Other Output Options

### Quiet Mode (minimal output)
```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```

### HTML Report (after completion)
```powershell
.venv\Scripts\python.exe -m pytest tests/ --html=report.html --self-contained-html
```

## Troubleshooting

**If you see buffering issues:**
- Use pytest-sugar (recommended) - it handles output natively
- Avoid PowerShell `Select-Object -Last N` piping (causes buffering)
- Use `-v` flag for verbose output

**If pytest-sugar doesn't show progress:**
- Ensure pytest-sugar is installed: `pip list | findstr pytest-sugar`
- Check that you're using `-v` flag
- pytest-sugar activates automatically when installed

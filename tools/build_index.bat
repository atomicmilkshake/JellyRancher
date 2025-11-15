@echo off
REM Build JellyRancher Function Index using venv Python 3.10
REM This ensures ChromaDB compatibility (Python 3.14+ breaks ChromaDB)

echo Building function index with Python 3.10 (venv)...
.venv\Scripts\python.exe build_function_index_enhanced.py %*

if errorlevel 1 (
    echo.
    echo ERROR: Function indexing failed!
    echo Make sure you're using the venv Python 3.10
    pause
    exit /b 1
)

echo.
echo Function index built successfully!
pause

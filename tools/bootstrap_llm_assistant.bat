@echo off
REM JellyRancher LLM Assistant Bootstrap Launcher
REM This script sets up the development environment and bootstraps ChromaDB knowledge

echo ===========================================
echo   JellyRancher LLM Assistant Bootstrap
echo ===========================================
echo.

echo Step 1: Activating virtual environment...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\activate ^& pip install -r requirements-jelly-rancher.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

echo ✓ Virtual environment activated
echo.

echo Step 2: Verifying dependencies...
echo.

REM Check critical ChromaDB dependencies
python -c "import overrides" 2>nul
if errorlevel 1 (
    echo ⚠️  Missing ChromaDB dependencies detected
    echo Installing required packages: overrides, posthog, onnxruntime, pydantic-settings...
    pip install overrides posthog onnxruntime pydantic-settings
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    echo ✓ Dependencies installed
    echo.
) else (
    echo ✓ All dependencies present
    echo.
)

echo Step 3: Checking ChromaDB knowledge base...
echo.

REM Check if ChromaDB database exists
if exist "chroma_db" (
    echo ✓ ChromaDB database found
    echo.
    
    REM Verify ChromaDB loads correctly
    python -c "from chroma_memory_backend import ChromaMemoryBackend; mem = ChromaMemoryBackend('./chroma_db'); print('✓ ChromaDB verified and ready')" 2>nul
    if errorlevel 1 (
        echo ⚠️  ChromaDB verification failed
        echo You may need to run: python scripts/ai/bootstrap_chroma.py
        echo.
    )
    echo.
    echo If you need to refresh the knowledge base, run:
    echo python scripts/ai/bootstrap_chroma.py
    echo.
) else (
    echo ⚠️  ChromaDB database not found
    echo.
    echo Step 4: Bootstrapping complete project knowledge...
    echo This will ingest ALL project files into ChromaDB.
    echo This may take several minutes...
    echo.
    python scripts/ai/bootstrap_chroma.py
    if errorlevel 1 (
        echo ERROR: Bootstrap failed!
        pause
        exit /b 1
    )
)

echo.
echo ===========================================
echo        BOOTSTRAP COMPLETE! 🎉
echo ===========================================
echo.
echo Your ChromaDB knowledge base is ready!
echo.
echo Next steps:
echo 1. Review INTEGRATION_TODO_LIST.md for feature roadmap
echo 2. Query ChromaDB for project context before starting work
echo 3. Launch the application: python jelly_rancher_main.py
echo 4. Document all activities in ChromaDB
echo.
echo IMPORTANT: Integration Roadmap Available
echo - File: INTEGRATION_TODO_LIST.md
echo - Contains: 94 tasks across 7 phases (31-33 hours)
echo - Purpose: Integrate 2,891 lines of high-value unused code
echo - Start with: Phase 1 (TMDB Cache Builder) - Quick win!
echo.
echo Read the full guide: bootstrap.md
echo.

REM Keep terminal open
pause
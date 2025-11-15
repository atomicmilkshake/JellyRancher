@echo off
REM JellyRancher - Unified Media Organization Platform Launcher
REM This script launches the unified JellyRancher GUI application

echo ========================================
echo    JellyRancher - Unified Media Platform
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists and has required packages
if exist ".venv" (
    echo Checking virtual environment for required packages...
    call .venv\Scripts\activate.bat
    python -c "import PyQt5" >nul 2>&1
    if errorlevel 1 (
        echo Required packages not found in virtual environment. Using global environment...
        call .venv\Scripts\deactivate.bat
    ) else (
        echo Using virtual environment...
    )
) else (
    echo No virtual environment found. Using global Python environment...
)

REM Install/update requirements if needed (commented out since already installed)
REM echo Checking dependencies...
REM pip install -r requirements-jelly-rancher.txt --quiet

REM Launch the application
echo.
echo Starting JellyRancher...
echo.
cd scripts\core
python jelly_rancher_main.py

REM Deactivate virtual environment if it was activated and we're still in it
if exist ".venv" (
    if defined VIRTUAL_ENV (
        if "%VIRTUAL_ENV%"=="%CD%\.venv" (
            call .venv\Scripts\deactivate.bat
        )
    )
)

echo.
echo JellyRancher application closed.
pause
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

REM Check if virtual environment exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Installing dependencies globally...
)

REM Install/update requirements if needed
echo Checking dependencies...
pip install -r requirements-jelly-rancher.txt --quiet

REM Launch the application
echo.
echo Starting JellyRancher...
echo.
python scripts\jelly_rancher_main.py

REM Deactivate virtual environment if it was activated
if exist "venv" (
    call venv\Scripts\deactivate.bat
)

echo.
echo JellyRancher application closed.
pause
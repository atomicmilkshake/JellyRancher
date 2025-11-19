@echo off
REM JellyRancher Studio Launcher
REM Activates virtual environment and starts the application

echo ========================================
echo   JellyRancher Studio Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first: setup_and_run.ps1
    echo.
    pause
    exit /b 1
)

REM Start JellyRancher Studio using venv Python directly
echo Starting JellyRancher Studio...
echo.
.venv\Scripts\python.exe jelly_rancher_studio.py

REM Check if launch succeeded
if errorlevel 1 (
    echo.
    echo ERROR: Studio failed to start
    echo Check error messages above
)

echo.
echo Studio closed.
pause

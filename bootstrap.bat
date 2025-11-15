@echo off
REM JellyRancher Quick Bootstrap Batch File
REM Provides fast environment verification

echo ==================================================
echo 🍫 JELLYRANCHER QUICK BOOTSTRAP
echo ==================================================

echo 📁 Working Directory: %CD%

echo.
echo 🔍 Checking Virtual Environment...
.venv\Scripts\python.exe --version
if %errorlevel% neq 0 (
    echo ❌ Python check failed!
    pause
    exit /b 1
)

echo.
echo 🔍 Running Comprehensive Bootstrap Check...
.venv\Scripts\python.exe bootstrap.py

echo.
echo ==================================================
echo 💡 Quick Commands:
echo    GUI: .venv\Scripts\python.exe jelly_rancher_clean.py
echo ==================================================

pause
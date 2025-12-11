@echo off
cd /d "%~dp0"
echo Running backup script...
.venv\Scripts\python.exe tools\create_backup.py
echo.
echo Checking for backup file...
dir /B v:\JellyRancher_backup_*.zip 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Backup file found!
) else (
    echo No backup file found.
)
pause



















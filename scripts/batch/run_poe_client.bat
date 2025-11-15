@echo off
REM Poe Client GUI Launcher
REM Launches the Poe.com batch file processor GUI

echo Starting Poe Client GUI...
echo.
echo Make sure OPENAI_API_KEY is set in your environment!
echo.

python RavenMaven\ravenmaven_gui.py

if errorlevel 1 (
    echo.
    echo Error launching GUI. Make sure Python is installed and OPENAI_API_KEY is set.
    pause
)

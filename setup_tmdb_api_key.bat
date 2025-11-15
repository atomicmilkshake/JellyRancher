@echo off
REM Setup TMDB API Key for JellyRancher
REM This sets the environment variable for the current session

echo ============================================================
echo Setting up TMDB API Key
echo ============================================================
echo.

REM Set the TMDB API key
set TMDB_API_KEY=a71ed25dc11e509b52067f0c10df1af4

echo [OK] TMDB_API_KEY set to: %TMDB_API_KEY%
echo.
echo This environment variable is set for the current session only.
echo.
echo To make it permanent, add it to System Environment Variables:
echo   1. Right-click 'This PC' ^> Properties
echo   2. Advanced system settings ^> Environment Variables
echo   3. Add new User variable: TMDB_API_KEY = a71ed25dc11e509b52067f0c10df1af4
echo.
echo ============================================================
echo Ready to run JellyRancher!
echo ============================================================
echo.
echo Starting JellyRancher GUI...
echo.

REM Activate virtual environment and run the application
call .venv\Scripts\Activate.ps1
python jelly_rancher_clean.py




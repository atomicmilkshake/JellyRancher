@echo off
REM Dot-source session env loader then run GUI in PowerShell so env vars are available
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '%~dp0scripts\load_system_env.ps1'; python '%~dp0tools\audit\codecop_gui.py'; Read-Host 'Press Enter to exit' }"
@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
if errorlevel 1 exit /b 2
python scripts\build_original_v1_daily_status.py --check
if errorlevel 1 exit /b 2
rem Prints the evidence-selected task. It never silently dispatches a model edit.
python scripts\select_original_v1_next_action.py
exit /b %errorlevel%

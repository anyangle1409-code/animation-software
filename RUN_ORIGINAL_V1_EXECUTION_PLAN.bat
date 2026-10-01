@echo off
setlocal
cd /d "%~dp0"
call RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
if errorlevel 1 exit /b 2
python scripts\build_original_v1_daily_status.py --check
if errorlevel 1 exit /b 2
if "%~1"=="" (
  python scripts\original_v1_execution_orchestration.py
) else (
  python scripts\original_v1_execution_orchestration.py --json --json-out "%~1"
)
exit /b %ERRORLEVEL%

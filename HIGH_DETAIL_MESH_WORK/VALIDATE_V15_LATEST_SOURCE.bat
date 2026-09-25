@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  python scripts\run_v15_latest_source_validation.py
) else (
  python scripts\run_v15_latest_source_validation.py --version %~1
)
exit /b %errorlevel%

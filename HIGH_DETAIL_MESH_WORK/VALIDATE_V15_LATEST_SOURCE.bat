@echo off
setlocal
cd /d "%~dp0"
python scripts\run_v15_latest_source_validation.py
exit /b %errorlevel%

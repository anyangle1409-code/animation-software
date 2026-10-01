@echo off
setlocal
cd /d "%~dp0"
python scripts\original_v1_progress_summary.py %*
exit /b %ERRORLEVEL%

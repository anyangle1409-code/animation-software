@echo off
setlocal
cd /d "%~dp0"
python scripts\check_prepared_tooling.py
exit /b %errorlevel%

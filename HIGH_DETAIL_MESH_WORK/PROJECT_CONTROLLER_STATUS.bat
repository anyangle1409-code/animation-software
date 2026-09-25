@echo off
setlocal
cd /d "%~dp0"
python scripts\project_controller_status.py
exit /b %errorlevel%

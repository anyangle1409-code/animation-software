@echo off
setlocal
cd /d "%~dp0"
python scripts\start_project_controller.py
exit /b %errorlevel%

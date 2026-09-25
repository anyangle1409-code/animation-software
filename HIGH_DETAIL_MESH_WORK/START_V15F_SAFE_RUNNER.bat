@echo off
setlocal
cd /d "%~dp0"
python scripts\start_v15f_safe_runner.py
exit /b %errorlevel%

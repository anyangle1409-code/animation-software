@echo off
setlocal
cd /d "%~dp0"
python scripts\v15f_status.py
exit /b %errorlevel%

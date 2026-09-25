@echo off
setlocal
cd /d "%~dp0"
python scripts\preflight_v15.py
exit /b %errorlevel%

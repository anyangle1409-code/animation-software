@echo off
setlocal
cd /d "%~dp0"
python scripts\v15_attempts.py
exit /b %errorlevel%

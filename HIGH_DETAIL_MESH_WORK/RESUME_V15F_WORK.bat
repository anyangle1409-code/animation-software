@echo off
setlocal
cd /d "%~dp0"
python scripts\resume_v15f_work.py
exit /b %errorlevel%

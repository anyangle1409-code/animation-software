@echo off
setlocal
cd /d "%~dp0"
python scripts\print_v15f_work_prompt.py
exit /b %errorlevel%

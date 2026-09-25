@echo off
setlocal
cd /d "%~dp0"
python scripts\begin_next_work_task.py
exit /b %errorlevel%

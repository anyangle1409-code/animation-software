@echo off
setlocal
cd /d "%~dp0"
python scripts\prepare_next_work_task.py
set RC=%errorlevel%
echo.
echo Task card: NEXT_WORK_TASK_CARD.md
exit /b %RC%

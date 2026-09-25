@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: FINISH_WORK_TASK.bat window_after [week_after] [notes]
  echo Example: FINISH_WORK_TASK.bat 72 84 "ring L complete"
  exit /b 2
)
python scripts\finish_work_task.py %~1 %~2 --notes "%~3"
exit /b %errorlevel%

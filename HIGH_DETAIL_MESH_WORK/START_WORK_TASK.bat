@echo off
setlocal
cd /d "%~dp0"
if "%~3"=="" (
  echo Usage: START_WORK_TASK.bat task_class model before_percent [notes]
  exit /b 2
)
python scripts\start_work_usage_sample.py %~1 %~2 %~3 --notes "%~4"
exit /b %errorlevel%

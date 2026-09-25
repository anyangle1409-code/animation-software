@echo off
setlocal
cd /d "%~dp0"
if "%~5"=="" (
  echo Usage: LOG_WORK_USAGE.bat task_class model before_percent after_percent minutes [notes]
  echo Example: LOG_WORK_USAGE.bat one_digit_topology Sol 100 86 35 "ring L"
  exit /b 2
)
python scripts\log_work_usage.py %~1 %~2 %~3 %~4 %~5 --notes "%~6"
exit /b %errorlevel%

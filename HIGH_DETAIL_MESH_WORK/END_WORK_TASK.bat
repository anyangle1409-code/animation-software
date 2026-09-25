@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: END_WORK_TASK.bat after_percent [notes]
  exit /b 2
)
python scripts\end_work_usage_sample.py %~1 --notes "%~2"
exit /b %errorlevel%

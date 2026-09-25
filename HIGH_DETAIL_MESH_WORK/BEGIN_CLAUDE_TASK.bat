@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: BEGIN_CLAUDE_TASK.bat task_class [notes]
  exit /b 2
)
python scripts\start_claude_usage_sample.py %~1 --notes "%~2"
exit /b %errorlevel%

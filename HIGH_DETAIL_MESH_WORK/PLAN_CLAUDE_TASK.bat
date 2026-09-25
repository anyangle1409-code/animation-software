@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: PLAN_CLAUDE_TASK.bat mechanical_edit^|report_analysis^|one_file_code^|multi_file_code^|hard_debug^|architecture^|open_ended
  exit /b 2
)
python scripts\plan_claude_task.py %~1
exit /b %errorlevel%

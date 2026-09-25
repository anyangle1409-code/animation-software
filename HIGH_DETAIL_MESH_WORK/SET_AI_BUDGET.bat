@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: SET_AI_BUDGET.bat work_window^|work_week^|claude percent [reset note]
  echo Examples:
  echo   SET_AI_BUDGET.bat work_window 14 "resets in 42 min"
  echo   SET_AI_BUDGET.bat work_week 63 "resets Monday"
  echo   SET_AI_BUDGET.bat claude 35
  exit /b 2
)
python scripts\set_ai_budget.py %~1 %~2 --reset-note "%~3"
exit /b %errorlevel%

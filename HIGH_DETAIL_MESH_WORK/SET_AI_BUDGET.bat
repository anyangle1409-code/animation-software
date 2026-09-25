@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: SET_AI_BUDGET.bat work^|claude percent [reset note]
  exit /b 2
)
python scripts\set_ai_budget.py %~1 %~2 --reset-note "%~3"
exit /b %errorlevel%

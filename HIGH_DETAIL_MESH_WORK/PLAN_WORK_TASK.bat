@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: PLAN_WORK_TASK.bat task_class [context] [failed_attempts]
  exit /b 2
)
set CONTEXT=%~2
if "%CONTEXT%"=="" set CONTEXT=small
set FAILED=%~3
if "%FAILED%"=="" set FAILED=0
python scripts\plan_work_task.py %~1 --context %CONTEXT% --failed-attempts %FAILED%
exit /b %errorlevel%

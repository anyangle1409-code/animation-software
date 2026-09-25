@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: ESTIMATE_WORK_USAGE.bat task_class Astra^|Sol^|Terra^|Luna [context] [reasoning]
  echo Example: ESTIMATE_WORK_USAGE.bat one_digit_topology Sol small medium
  exit /b 2
)
set CONTEXT=%~3
if "%CONTEXT%"=="" set CONTEXT=small
set REASONING=%~4
if "%REASONING%"=="" set REASONING=medium
python scripts\estimate_work_usage.py %~1 %~2 --context %CONTEXT% --reasoning %REASONING%
exit /b %errorlevel%

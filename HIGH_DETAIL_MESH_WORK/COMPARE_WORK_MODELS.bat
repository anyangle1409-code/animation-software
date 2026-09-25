@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: COMPARE_WORK_MODELS.bat task_class [context] [reasoning]
  exit /b 2
)
set CONTEXT=%~2
if "%CONTEXT%"=="" set CONTEXT=small
set REASONING=%~3
if "%REASONING%"=="" set REASONING=medium
python scripts\compare_work_models.py %~1 --context %CONTEXT% --reasoning %REASONING%
exit /b %errorlevel%

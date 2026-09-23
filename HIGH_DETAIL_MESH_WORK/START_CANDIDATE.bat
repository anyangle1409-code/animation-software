@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: START_CANDIDATE.bat v7_knee_retopology
  exit /b 2
)
python scripts\start_candidate.py --version %1
exit /b %errorlevel%

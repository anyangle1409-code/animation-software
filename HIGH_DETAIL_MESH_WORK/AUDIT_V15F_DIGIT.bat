@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: AUDIT_V15F_DIGIT.bat ring_L^|ring_R^|pinky_L^|pinky_R
  exit /b 2
)
python scripts\audit_v15f_digit.py %~1
exit /b %errorlevel%

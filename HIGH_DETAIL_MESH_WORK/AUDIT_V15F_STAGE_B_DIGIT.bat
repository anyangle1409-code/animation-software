@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: AUDIT_V15F_STAGE_B_DIGIT.bat index_L^|index_R^|middle_L^|middle_R
  exit /b 2
)
python scripts\audit_v15f_stage_b_digit.py %~1
if errorlevel 1 exit /b %errorlevel%
python scripts\generate_v15f_stage_b_digit_visual.py %~1
if errorlevel 1 exit /b %errorlevel%
python scripts\write_v15f_handoff.py
exit /b %errorlevel%

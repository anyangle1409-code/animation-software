@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: GENERATE_V15F_STAGE_B_VISUAL.bat index_L^|index_R^|middle_L^|middle_R
  exit /b 2
)
python scripts\generate_v15f_stage_b_digit_visual.py %~1
exit /b %errorlevel%

@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: MARK_V15F_STAGE_B_VISUAL.bat digit pass^|fail [notes]
  exit /b 2
)
python scripts\mark_v15f_stage_b_digit_visual.py %~1 %~2 --notes "%~3"
if errorlevel 1 exit /b %errorlevel%
python scripts\write_v15f_handoff.py
exit /b %errorlevel%

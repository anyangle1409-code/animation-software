@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: MARK_V15F_STAGE_A_VISUAL.bat pass^|fail [notes]
  exit /b 2
)
python scripts\mark_v15f_stage_a_visual.py %~1 --notes "%~2"
if errorlevel 1 exit /b %errorlevel%
python scripts\write_v15f_handoff.py
exit /b %errorlevel%

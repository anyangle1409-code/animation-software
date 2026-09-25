@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_FINAL_SYSTEM_ACCEPTANCE.bat final_character.glb
  exit /b 2
)
python scripts\run_final_system_acceptance.py "%~1"
exit /b %errorlevel%

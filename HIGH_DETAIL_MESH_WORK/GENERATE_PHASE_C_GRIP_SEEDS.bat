@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: GENERATE_PHASE_C_GRIP_SEEDS.bat accepted_hand.glb [label]
  exit /b 2
)
set LABEL=%~2
if "%LABEL%"=="" set LABEL=v15
python scripts\generate_phase_c_grip_seeds.py --character "%~1" --label "%LABEL%"
exit /b %errorlevel%

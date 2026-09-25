@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: EVALUATE_PHASE_C_GRIP.bat accepted_hand.glb candidate.json [label]
  exit /b 2
)
set LABEL=%~3
if "%LABEL%"=="" set LABEL=v15_grip_candidate
python scripts\evaluate_phase_c_grip_candidate.py --character "%~1" --candidate "%~2" --label "%LABEL%"
exit /b %errorlevel%

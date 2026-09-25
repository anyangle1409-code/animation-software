@echo off
setlocal
cd /d "%~dp0"
set FILE=renders_v15f_stage_a\V15F_V13E_STAGE_A_RING_PINKY_PROOF.jpg
if not exist "%FILE%" (
  echo Missing %FILE%
  exit /b 2
)
start "" "%FILE%"
exit /b 0

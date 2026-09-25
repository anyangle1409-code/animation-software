@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: OPEN_V15F_STAGE_B_VISUAL.bat index_L^|index_R^|middle_L^|middle_R
  exit /b 2
)
set FILE=renders_v15f_stage_b\%~1\V15F_V13E_%~1_PROOF.jpg
if not exist "%FILE%" (
  echo Missing %FILE%
  echo Run GENERATE_V15F_STAGE_B_VISUAL.bat %~1 first.
  exit /b 2
)
start "" "%FILE%"
exit /b 0

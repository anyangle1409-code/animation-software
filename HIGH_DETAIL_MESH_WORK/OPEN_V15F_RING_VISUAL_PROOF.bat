@echo off
setlocal
cd /d "%~dp0"
set FILE=renders_v15f_ring_proof\V15F_V13E_RING_L_PROOF.jpg
if not exist "%FILE%" (
  echo Missing %FILE%
  exit /b 2
)
start "" "%FILE%"
exit /b 0

@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
set "REV=%~1"
set "OUT=%~2"
if exist "%OUT%" (
  echo STOP - output folder already exists
  exit /b 2
)
python scripts\original_v1_phase7_equivalence_capture.py "%REV%" --out-dir "%OUT%"
exit /b %ERRORLEVEL%
:usage
echo Usage: RUN_ORIGINAL_V1_PHASE7_EQUIVALENCE.bat ^<rN^> ^<fresh-output-dir^>
exit /b 2

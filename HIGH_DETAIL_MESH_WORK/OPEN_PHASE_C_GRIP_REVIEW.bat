@echo off
setlocal
cd /d "%~dp0"
set LABEL=%~1
if "%LABEL%"=="" set LABEL=v15_grip_candidate
set FILE=reports\phase_c_grip_%LABEL%\phase_c_grip_review.html
if not exist "%FILE%" (
  echo Missing %FILE%
  exit /b 2
)
start "" "%FILE%"
exit /b 0

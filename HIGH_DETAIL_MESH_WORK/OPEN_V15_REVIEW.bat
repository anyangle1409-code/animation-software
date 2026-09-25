@echo off
setlocal
cd /d "%~dp0"
set VERSION=%~1
if "%VERSION%"=="" set VERSION=v15a_deep_hand_rebuild
set FILE=V15_REVIEW_%VERSION%.html
if not exist "%FILE%" (
  echo Missing %FILE%
  exit /b 2
)
start "" "%FILE%"
exit /b 0

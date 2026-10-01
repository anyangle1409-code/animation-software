@echo off
setlocal
cd /d "%~dp0"
if not "%~1"=="" (
  call RUN_ORIGINAL_V1_CANDIDATE_HANDOFF.bat "%~1"
  if errorlevel 2 exit /b 2
)
call RUN_ORIGINAL_V1_PROGRESS.bat
if errorlevel 1 exit /b 2
call RUN_ORIGINAL_V1_BLEND_INVENTORY.bat
if errorlevel 1 exit /b 2
call RUN_ORIGINAL_V1_SESSION_CLOSE.bat
exit /b %ERRORLEVEL%

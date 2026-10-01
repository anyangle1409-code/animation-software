@echo off
setlocal
cd /d "%~dp0"
call RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
if errorlevel 1 exit /b 2
call RUN_ORIGINAL_V1_NEXT.bat
if errorlevel 1 exit /b 2
call RUN_ORIGINAL_V1_EXECUTION_PLAN.bat
if errorlevel 1 exit /b 2
python scripts\original_v1_claude_brief.py
exit /b %ERRORLEVEL%

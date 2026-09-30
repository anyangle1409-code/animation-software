@echo off
setlocal
cd /d "%~dp0"

rem Convenience wrapper for the current highest-priority repair group.
rem Usage:
rem   RUN_ORIGINAL_V1_SHOULDER_CHECK.bat [candidate.blend] [label]

call RUN_ORIGINAL_V1_REPAIR_CHECK.bat shoulder %*
exit /b %ERRORLEVEL%

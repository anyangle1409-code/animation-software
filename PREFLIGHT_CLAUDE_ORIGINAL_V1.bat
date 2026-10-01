@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Compatibility entry point. The old R2 shoulder pickup is historical.
call RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat %*
exit /b %errorlevel%

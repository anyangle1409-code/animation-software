@echo off
setlocal
cd /d "%~dp0"
python scripts\original_v1_session_close.py %*
exit /b %ERRORLEVEL%

@echo off
setlocal
cd /d "%~dp0"
python scripts\original_v1_claude_brief.py %*
exit /b %ERRORLEVEL%

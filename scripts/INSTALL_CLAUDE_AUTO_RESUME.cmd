@echo off
setlocal
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_claude_auto_resume.ps1"
echo.
echo Press any key to close.
pause >nul

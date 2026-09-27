@echo off
setlocal
cd /d "%~dp0"
node scripts\standalone-status.mjs
exit /b %errorlevel%

@echo off
setlocal
cd /d "%~dp0"
node scripts\cleanup-contained-branches.mjs %*
exit /b %errorlevel%

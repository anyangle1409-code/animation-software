@echo off
setlocal
cd /d "%~dp0"
if not exist reports mkdir reports
echo stop>reports\v15f_safe_runner.stop
echo V15f safe runner stop requested.
exit /b 0

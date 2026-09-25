@echo off
setlocal
cd /d "%~dp0"
if not exist reports mkdir reports
echo stop>reports\project_controller.stop
echo Project controller stop requested.
echo It will exit after its current polling cycle.
exit /b 0

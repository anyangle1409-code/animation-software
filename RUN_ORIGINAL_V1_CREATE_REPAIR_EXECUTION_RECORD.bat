@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "DECLARATION=%~1"
set "FINAL_SHA=%~2"
set "OUT=%~3"
if "%DECLARATION%"=="" (echo ERROR: declaration path required.& exit /b 2)
if "%FINAL_SHA%"=="" (echo ERROR: final candidate SHA required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh execution record output path required.& exit /b 2)
if not exist "%DECLARATION%" (echo ERROR: declaration not found: %DECLARATION%& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists; use a fresh path.& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

"%PYTHON%" scripts\create_original_v1_repair_execution_record.py --declaration "%DECLARATION%" --final-sha "%FINAL_SHA%" --out "%OUT%"
if errorlevel 1 exit /b 1

echo.
echo Draft written. Fill executed_operations, edited vertices/bone groups and evidence paths, then run:
echo "%PYTHON%" scripts\validate_original_v1_repair_execution_record.py "%OUT%"
exit /b 0

@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REVIEWED=%~1"
set "OUT=%~2"
if "%REVIEWED%"=="" (echo ERROR: reviewed acceptance record required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh finalized acceptance output path required.& exit /b 2)
if not exist "%REVIEWED%" (echo ERROR: reviewed acceptance record not found: %REVIEWED%& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists: %OUT%& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found. Set PYTHON_EXE.& exit /b 2)

"%PYTHON%" scripts\finalize_original_v1_human_movement_sweep_acceptance.py "%REVIEWED%" "%OUT%"
if errorlevel 1 exit /b 1

"%PYTHON%" scripts\validate_original_v1_human_movement_sweep_acceptance.py "%OUT%" --require-pass
if errorlevel 1 exit /b 1

echo.
echo ENGINEERING PASS:
echo   %OUT%
echo Owner review remains PENDING. No production approval is implied.
exit /b 0

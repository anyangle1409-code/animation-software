@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REVIEWED=%~1"
set "OUT=%~2"
if "%REVIEWED%"=="" (echo ERROR: reviewed IN_REVIEW calibration record required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh calibrated output path required.& exit /b 2)
if not exist "%REVIEWED%" (echo ERROR: reviewed calibration record not found: %REVIEWED%& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists: %OUT%& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found. Set PYTHON_EXE.& exit /b 2)

"%PYTHON%" scripts\finalize_original_v1_human_movement_sweep_runner_calibration.py "%REVIEWED%" "%OUT%"
if errorlevel 1 exit /b 1

"%PYTHON%" scripts\validate_original_v1_human_movement_sweep_runner_calibration.py "%OUT%" --require-calibrated
if errorlevel 1 exit /b 1

echo.
echo CALIBRATED:
echo   %OUT%
echo Owner review remains PENDING. No model/body acceptance is implied.
exit /b 0

@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "RAW=%~1"
set "REV=%~2"
set "OUT=%~3"
if "%RAW%"=="" (echo ERROR: all-sweep raw report required.& exit /b 2)
if "%REV%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh calibration output path required.& exit /b 2)
if not exist "%RAW%" (echo ERROR: raw report not found: %RAW%& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists: %OUT%& exit /b 2)
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\build_original_v1_human_movement_sweep_runner_calibration.py "%RAW%" "%REV%" "%OUT%"
if errorlevel 1 exit /b 1
"%PYTHON%" scripts\validate_original_v1_human_movement_sweep_runner_calibration.py "%OUT%"
if errorlevel 1 exit /b 1
echo.
echo BUILT: %OUT%
echo NOTE: state is IN_REVIEW. Do not change to CALIBRATED until every adapter's human/engineering review is completed.
exit /b 0

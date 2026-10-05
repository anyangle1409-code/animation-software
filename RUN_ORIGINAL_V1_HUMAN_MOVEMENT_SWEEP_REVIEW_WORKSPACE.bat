@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "RAW=%~1"
set "REV=%~2"
set "CAL=%~3"
set "VISUAL=%~4"
set "CONTACT=%~5"
set "OUT=%~6"
set "SWEEPS=%~7"

if "%RAW%"=="" (echo ERROR: raw sweep report required.& exit /b 2)
if "%REV%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%CAL%"=="" (echo ERROR: runner calibration record required.& exit /b 2)
if "%VISUAL%"=="" (echo ERROR: visual capture directory required.& exit /b 2)
if "%CONTACT%"=="" (set "CONTACT=-")
if "%OUT%"=="" (echo ERROR: fresh review-workspace output directory required.& exit /b 2)

if not exist "%RAW%" (echo ERROR: raw sweep report missing: %RAW%& exit /b 2)
if not exist "%CAL%" (echo ERROR: calibration record missing: %CAL%& exit /b 2)
if not exist "%VISUAL%" (echo ERROR: visual directory missing: %VISUAL%& exit /b 2)
if exist "%OUT%" (echo ERROR: output directory exists. Use a fresh path: %OUT%& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

if "%SWEEPS%"=="" (
  "%PYTHON%" scripts\create_original_v1_human_movement_sweep_review_workspace.py ^
    "%RAW%" "%REV%" "%CAL%" "%VISUAL%" "%CONTACT%" "%OUT%"
) else (
  "%PYTHON%" scripts\create_original_v1_human_movement_sweep_review_workspace.py ^
    "%RAW%" "%REV%" "%CAL%" "%VISUAL%" "%CONTACT%" "%OUT%" --sweeps "%SWEEPS%"
)
if errorlevel 1 exit /b 1

echo.
echo BUILT: %OUT%
echo NOTE: motion/visual/contact/acceptance records remain PENDING until engineering review.
echo No PASS, owner acceptance or production approval is inferred.
exit /b 0

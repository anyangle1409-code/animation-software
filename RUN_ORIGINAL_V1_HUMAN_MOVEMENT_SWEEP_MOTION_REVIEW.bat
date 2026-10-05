@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "RAW=%~1"
set "SWEEP=%~2"
set "REVISION=%~3"
set "OUT=%~4"
if "%RAW%"=="" (echo ERROR: raw sweep report required.& exit /b 2)
if "%SWEEP%"=="" (echo ERROR: sweep id required.& exit /b 2)
if "%REVISION%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh motion-review output path required.& exit /b 2)
if not exist "%RAW%" (echo ERROR: raw sweep report not found: %RAW%& exit /b 2)
if exist "%OUT%" (echo ERROR: output already exists: %OUT%& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

"%PYTHON%" scripts\build_original_v1_human_movement_sweep_motion_review.py "%RAW%" "%SWEEP%" "%REVISION%" "%OUT%"
if errorlevel 1 exit /b 1

"%PYTHON%" scripts\validate_original_v1_human_movement_sweep_motion_review.py "%OUT%"
if errorlevel 1 exit /b 1

echo.
echo BUILT: %OUT%
echo NOTE: deterministic replay has been evaluated, but adjacent transition review remains PENDING.
echo Fill evidence_refs + PASS/FAIL for every adjacent transition, then rerun validator with --require-pass.
exit /b 0

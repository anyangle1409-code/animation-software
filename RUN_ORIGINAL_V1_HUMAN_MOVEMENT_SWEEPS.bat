@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "CANDIDATE=%~1"
set "LABEL=%~2"
set "SWEEPS=%~3"
if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)

set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweeps\%LABEL%"
set "OUT=%OUT_DIR%\human_movement_sweeps.json"
if exist "%OUT%" (echo ERROR: sweep report already exists; use a fresh label.& exit /b 2)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER (echo ERROR: Blender not found. Set BLENDER_EXE.& exit /b 2)

if "%SWEEPS%"=="" (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\audit_original_v1_human_movement_sweeps_blender.py -- "%OUT%"
) else (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\audit_original_v1_human_movement_sweeps_blender.py -- "%OUT%" "%SWEEPS%"
)
if errorlevel 1 exit /b 1

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if defined PYTHON (
  "%PYTHON%" scripts\validate_original_v1_human_movement_sweep_report.py "%OUT%"
  if errorlevel 1 exit /b 1
)

echo PASS: read-only sweep diagnostic written:
echo   %OUT%
echo NOTE: calibration_state remains EXPERIMENTAL_UNCALIBRATED until Blender review/calibration.
exit /b 0

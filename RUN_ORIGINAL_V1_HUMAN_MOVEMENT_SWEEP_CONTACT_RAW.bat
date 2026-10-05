@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "CANDIDATE=%~1"
set "REV=%~2"
set "LABEL=%~3"
set "SWEEPS=%~4"
if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%REV%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)
set "OUT=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweep_contact\%LABEL%"
if exist "%OUT%" (echo ERROR: contact output directory exists. Use fresh label.& exit /b 2)
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER (echo ERROR: Blender not found. Set BLENDER_EXE.& exit /b 2)
if "%SWEEPS%"=="" (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\audit_original_v1_human_movement_sweep_contact_blender.py -- "%OUT%" "%REV%"
) else (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\audit_original_v1_human_movement_sweep_contact_blender.py -- "%OUT%" "%REV%" "%SWEEPS%"
)
if errorlevel 1 exit /b 1
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if defined PYTHON (
  for %%F in ("%OUT%\human_movement_sweep_contact_raw_*.json") do (
    "%PYTHON%" scripts\validate_original_v1_human_movement_sweep_contact_raw.py "%%~fF"
    if errorlevel 1 exit /b 1
  )
)
echo PASS: raw contact/load sweep measurements written:
echo   %OUT%
echo NOTE: classifications remain reviewed evidence; this runner never auto-passes contact.
exit /b 0

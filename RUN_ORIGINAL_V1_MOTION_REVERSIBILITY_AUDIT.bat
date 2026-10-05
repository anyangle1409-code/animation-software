@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "CANDIDATE=%~1"
if "%CANDIDATE%"=="" (
  echo ERROR: candidate Blend is required.
  exit /b 2
)
if not exist "%CANDIDATE%" (
  echo ERROR: candidate not found: %CANDIDATE%
  exit /b 2
)
set "LABEL=%~2"
if "%LABEL%"=="" (
  echo ERROR: fresh label required.
  exit /b 2
)
set "POSES=%~3"
if "%POSES%"=="" set "POSES=press_top,pullup_hang,row,curl_peak,pushup_bottom,squat_bottom,lunge"
set "SAMPLES=%~4"
if "%SAMPLES%"=="" set "SAMPLES=21"

set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\motion_reversibility\%LABEL%"
set "OUT=%OUT_DIR%\motion_reversibility.json"
if exist "%OUT%" (
  echo ERROR: evidence already exists: %OUT%
  exit /b 2
)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER (
  echo ERROR: Blender not found. Set BLENDER_EXE.
  exit /b 2
)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"

"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\audit_original_v1_motion_reversibility_blender.py -- "%OUT%" "%POSES%" "%SAMPLES%"
if errorlevel 1 exit /b 1

if defined PYTHON (
  "%PYTHON%" scripts\validate_original_v1_motion_reversibility.py "%OUT%"
) else (
  "%BLENDER%" --background --factory-startup --python-exit-code 1 --python scripts\validate_original_v1_motion_reversibility.py -- "%OUT%"
)
if errorlevel 1 exit /b 1

echo PASS: %OUT%
exit /b 0

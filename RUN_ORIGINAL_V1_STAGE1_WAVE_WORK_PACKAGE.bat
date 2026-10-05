@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "WAVE=%~1"
set "OUT_DIR=%~2"
if "%WAVE%"=="" set "WAVE=current"
if "%OUT_DIR%"=="" set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\stage1_wave_packages\%WAVE%"

if exist "%OUT_DIR%\wave_work_package.json" (
  echo ERROR: wave work package already exists. Use a fresh output directory:
  echo   %OUT_DIR%
  exit /b 2
)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

"%PYTHON%" scripts\build_original_v1_stage1_wave_work_package.py ^
  --wave "%WAVE%" ^
  --out-json "%OUT_DIR%\wave_work_package.json" ^
  --out-md "%OUT_DIR%\wave_work_package.md"
exit /b %ERRORLEVEL%

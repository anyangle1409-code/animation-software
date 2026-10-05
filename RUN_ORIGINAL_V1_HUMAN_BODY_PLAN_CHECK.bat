@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
if not defined PYTHON (
  for /f "delims=" %%I in ('where python.exe 2^>nul') do (
    if not defined PYTHON set "PYTHON=%%I"
  )
)
if not defined PYTHON (
  echo ERROR: Python not found. Set PYTHON_EXE.
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 HUMAN BODY MASTER PLAN CHECK
echo ============================================================
"%PYTHON%" scripts\validate_original_v1_human_body_master_plan.py
exit /b %ERRORLEVEL%

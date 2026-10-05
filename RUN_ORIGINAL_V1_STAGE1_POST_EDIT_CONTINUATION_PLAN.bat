@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "WORKSPACE=%~1"
set "FINAL_CANDIDATE=%~2"
set "REV=%~3"
set "PRIOR=%~4"
set "LABEL=%~5"
set "CAL=%~6"
set "OUT=%~7"

if "%WORKSPACE%"=="" (echo ERROR: workspace required.& exit /b 2)
if "%FINAL_CANDIDATE%"=="" (echo ERROR: final candidate Blend required.& exit /b 2)
if "%REV%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%PRIOR%"=="" (echo ERROR: prior revision or - required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh output directory required as arg 7.& exit /b 2)
if not exist "%WORKSPACE%\workspace_manifest.json" (echo ERROR: workspace manifest missing.& exit /b 2)
if not exist "%FINAL_CANDIDATE%" (echo ERROR: final candidate missing.& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

if "%CAL%"=="" (
  "%PYTHON%" scripts\build_original_v1_stage1_post_edit_continuation_plan.py ^
    --workspace "%WORKSPACE%" ^
    --final-candidate "%FINAL_CANDIDATE%" ^
    --revision "%REV%" ^
    --prior "%PRIOR%" ^
    --label "%LABEL%" ^
    --out-dir "%OUT%"
) else (
  "%PYTHON%" scripts\build_original_v1_stage1_post_edit_continuation_plan.py ^
    --workspace "%WORKSPACE%" ^
    --final-candidate "%FINAL_CANDIDATE%" ^
    --revision "%REV%" ^
    --prior "%PRIOR%" ^
    --label "%LABEL%" ^
    --calibration-record "%CAL%" ^
    --out-dir "%OUT%"
)
exit /b %ERRORLEVEL%

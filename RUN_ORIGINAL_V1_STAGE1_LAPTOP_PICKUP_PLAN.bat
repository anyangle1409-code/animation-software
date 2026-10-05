@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "CANDIDATE=%~1"
set "CURRENT_REV=%~2"
set "NEW_REV=%~3"
set "SOURCE_BRANCH=%~4"
set "SIDE=%~5"
set "LABEL=%~6"
set "WORKSPACE=%~7"
set "OUT_DIR=%~8"
set "WAVE=%~9"

if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%CURRENT_REV%"=="" (echo ERROR: current revision required.& exit /b 2)
if "%NEW_REV%"=="" (echo ERROR: new revision required.& exit /b 2)
if "%SOURCE_BRANCH%"=="" (echo ERROR: source branch required.& exit /b 2)
if "%SIDE%"=="" (echo ERROR: side l/r/bilateral/midline required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if "%WORKSPACE%"=="" (echo ERROR: future repair workspace path required.& exit /b 2)
if "%OUT_DIR%"=="" (echo ERROR: fresh pickup-plan output directory required.& exit /b 2)
if "%WAVE%"=="" set "WAVE=current"
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)
if exist "%OUT_DIR%laptop_pickup_plan.json" (echo ERROR: pickup plan exists. Use fresh OUT_DIR.& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:UsersMark.cachecodex-runtimescodex-primary-runtimedependenciespythonpython.exe" set "PYTHON=C:UsersMark.cachecodex-runtimescodex-primary-runtimedependenciespythonpython.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

"%PYTHON%" scriptsuild_original_v1_stage1_laptop_pickup_plan.py ^
  --candidate "%CANDIDATE%" ^
  --current-revision "%CURRENT_REV%" ^
  --new-revision "%NEW_REV%" ^
  --source-branch "%SOURCE_BRANCH%" ^
  --side "%SIDE%" ^
  --label "%LABEL%" ^
  --workspace "%WORKSPACE%" ^
  --wave "%WAVE%" ^
  --out-dir "%OUT_DIR%"
exit /b %ERRORLEVEL%

@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PACKAGES=%~1"
set "CANDIDATE=%~2"
set "SHA=%~3"
set "SIDE=%~4"
set "SOURCE_BRANCH=%~5"
set "OUT_DIR=%~6"
if "%PACKAGES%"=="" (echo ERROR: repair packages required.& exit /b 2)
if "%CANDIDATE%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%SHA%"=="" (echo ERROR: candidate sha256 required.& exit /b 2)
if "%SIDE%"=="" (echo ERROR: side l/r/bilateral/midline required.& exit /b 2)
if "%SOURCE_BRANCH%"=="" (echo ERROR: source branch required.& exit /b 2)
if "%OUT_DIR%"=="" (echo ERROR: fresh output directory required.& exit /b 2)
if exist "%OUT_DIR%\workspace_manifest.json" (echo ERROR: workspace already exists.& exit /b 2)
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\create_original_v1_repair_workspace.py ^
 --packages "%PACKAGES%" ^
 --candidate "%CANDIDATE%" ^
 --sha256 "%SHA%" ^
 --side "%SIDE%" ^
 --source-branch "%SOURCE_BRANCH%" ^
 --out-dir "%OUT_DIR%"
exit /b %ERRORLEVEL%

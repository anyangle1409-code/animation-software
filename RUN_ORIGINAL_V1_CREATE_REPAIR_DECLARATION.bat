@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PACKAGE=%~1"
set "CANDIDATE=%~2"
set "SHA=%~3"
set "SIDE=%~4"
set "SOURCE_BRANCH=%~5"
set "OUT=%~6"
if "%PACKAGE%"=="" (echo ERROR: repair package id required.& exit /b 2)
if "%CANDIDATE%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%SHA%"=="" (echo ERROR: candidate sha256 required.& exit /b 2)
if "%SIDE%"=="" (echo ERROR: side l/r/bilateral/midline required.& exit /b 2)
if "%SOURCE_BRANCH%"=="" (echo ERROR: source branch required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh output json path required.& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists; use a fresh path.& exit /b 2)
for %%D in ("%OUT%") do if not exist "%%~dpD" mkdir "%%~dpD"
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\create_original_v1_repair_declaration.py --package "%PACKAGE%" --candidate "%CANDIDATE%" --sha256 "%SHA%" --side "%SIDE%" --source-branch "%SOURCE_BRANCH%" --out "%OUT%"
exit /b %ERRORLEVEL%

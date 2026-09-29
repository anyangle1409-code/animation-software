@echo off
setlocal
cd /d "%~dp0"

set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if not "%CURRENT_BRANCH%"=="work/standalone-first-party-audit-20260927" (
  echo Expected branch work/standalone-first-party-audit-20260927; found "%CURRENT_BRANCH%".
  exit /b 1
)

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
)
if not defined BLENDER (
  for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
)
if not defined BLENDER (
  echo Blender not found. Set BLENDER_EXE to blender.exe.
  exit /b 1
)

set "BLEND=ORIGINAL_V1_WORK\HomeGymPT_Male_ORIGINAL_v1.blend"
if not exist "%BLEND%" (
  echo Missing %BLEND%.
  echo Run PREPARE_ORIGINAL_V1_O2.bat first.
  exit /b 1
)
if exist "ORIGINAL_V1_WORK\AUTHORING_TAINT.json" (
  echo AUTHORING_TAINT.json exists.
  echo Recover and inspect the last clean checkpoint. Do not delete the taint record merely to continue.
  exit /b 1
)

echo Preflighting first-party O2 authoring boundary...
"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v4_blender.py
if errorlevel 1 exit /b 1
"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v1_authoring_boundary_blender.py
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo GUARDED ORIGINAL v1 O2 AUTHORING
echo ============================================================
echo Do not import, append, link, or use external image/reference assets.
echo Use stock Blender tools plus committed project scripts only.
echo The guard remains active until Blender closes.
echo ============================================================
echo.

"%BLENDER%" "%CD%\%BLEND%" --python "%CD%\scripts\guard_original_v1_authoring_blender.py"
exit /b %errorlevel%

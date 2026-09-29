@echo off
setlocal
cd /d "%~dp0"

set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
set "BRANCH_OK="
if "%CURRENT_BRANCH%"=="work/standalone-first-party-audit-20260927" set "BRANCH_OK=1"
rem Separate Blender/model branches keep O2 work off the standalone software branch.
if "%CURRENT_BRANCH:~0,26%"=="claude/original-v1-blender" set "BRANCH_OK=1"
if not defined BRANCH_OK (
  echo Expected branch work/standalone-first-party-audit-20260927 or claude/original-v1-blender-*; found "%CURRENT_BRANCH%".
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
  exit /b 1
)

node scripts\export-original-v4-rig.mjs --check
if errorlevel 1 exit /b 1
python -m unittest discover -s scripts -p test_original_v4_payload.py
if errorlevel 1 exit /b 1

"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v4_blender.py
if errorlevel 1 exit /b 1
rem The add-on check concerns the authoring session (recorded live by the guard);
rem audit in a clean factory process so the auditor's own add-ons are not counted.
"%BLENDER%" --background --factory-startup "%BLEND%" --python-exit-code 1 --python scripts\disable_addons_for_guarded_session.py --python scripts\audit_original_v1_authoring_boundary_blender.py -- --require-guarded
if errorlevel 1 exit /b 1

if /I "%~1"=="strict" (
  "%BLENDER%" --background "%BLEND%" --python scripts\audit_original_o2_mesh_blender.py -- --strict
) else (
  "%BLENDER%" --background "%BLEND%" --python scripts\audit_original_o2_mesh_blender.py
)
if errorlevel 1 exit /b 1

echo.
echo ORIGINAL v1 O2 guarded authoring audit PASS.
exit /b 0

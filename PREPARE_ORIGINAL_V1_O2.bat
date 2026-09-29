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
node --version >nul 2>&1
if errorlevel 1 (
  echo Node.js is required for the committed v4 rig export check.
  exit /b 1
)
if not exist "node_modules\esbuild\package.json" (
  echo Local development tools missing. Run npm ci, then rerun this command.
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
    set "BLENDER=%%I"
  )
)
if not defined BLENDER (
  echo Blender not found. Set BLENDER_EXE to blender.exe.
  exit /b 1
)

set "BLEND=ORIGINAL_V1_WORK\HomeGymPT_Male_ORIGINAL_v1.blend"
if not exist "%BLEND%" (
  echo Missing O1 Blend. Run PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat on the laptop first.
  exit /b 1
)

node scripts\export-original-v4-rig.mjs --check
if errorlevel 1 exit /b 1
"%BLENDER%" --background "%BLEND%" --python scripts\materialize_original_v4_blender.py
if errorlevel 1 exit /b 1
"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v4_blender.py
if errorlevel 1 exit /b 1
"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v1_authoring_boundary_blender.py
if errorlevel 1 exit /b 1

echo O2 v4 rig ready.
echo Do NOT open %BLEND% directly for modelling.
echo Use OPEN_ORIGINAL_V1_O2_GUARDED.bat so the first-party authoring guard is active.
exit /b 0

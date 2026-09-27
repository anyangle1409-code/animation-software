@echo off
setlocal
cd /d "%~dp0"

for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "BRANCH=%%I"
if /I not "%BRANCH%"=="work/standalone-first-party-audit-20260927" (
  echo Wrong branch: %BRANCH%
  echo Expected: work/standalone-first-party-audit-20260927
  echo No files were reset or cleaned.
  exit /b 1
)

echo ============================================================
echo ORIGINAL v1 clean-room preparation
echo ============================================================

echo.
echo [1/3] Generate/refresh clean scaffold
call GENERATE_ORIGINAL_V1_CLEAN_SCAFFOLD.bat
if errorlevel 1 goto :fail

echo.
echo [2/3] Audit clean-room workspace
call AUDIT_ORIGINAL_V1_CLEAN_ROOM.bat
if errorlevel 1 goto :fail

echo.
echo [3/3] Open verified Blend
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
  echo Audit passed, but Blender executable was not found for interactive open.
  echo Set BLENDER_EXE and open ORIGINAL_V1_WORK\HomeGymPT_Male_ORIGINAL_v1.blend.
  exit /b 0
)

start "" "%BLENDER%" "%CD%\ORIGINAL_V1_WORK\HomeGymPT_Male_ORIGINAL_v1.blend"

echo.
echo ============================================================
echo ORIGINAL v1 CLEAN START PASS
echo ============================================================
echo The open file is a verified first-party scaffold, not a finished model.
exit /b 0

:fail
echo.
echo ============================================================
echo ORIGINAL v1 CLEAN START FAILED
echo ============================================================
echo Do not model on this workspace until the reported gate is fixed.
exit /b 1

@echo off
setlocal
cd /d "%~dp0"

rem Headless counterpart of OPEN_ORIGINAL_V1_O2_GUARDED.bat: runs one committed,
rem unmodified project script inside the same live first-party authoring guard.
rem Usage: RUN_ORIGINAL_V1_O2_GUARDED_SCRIPT.bat scripts\name.py [script args]

if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_O2_GUARDED_SCRIPT.bat scripts\name.py [args]
  exit /b 1
)

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

set "SCRIPT=%~1"
if /I not "%SCRIPT:~0,8%"=="scripts\" (
  echo Only project scripts under scripts\ may run in the guarded session.
  exit /b 1
)
git ls-files --error-unmatch "%SCRIPT%" >nul 2>&1
if errorlevel 1 (
  echo %SCRIPT% is not a committed project script.
  exit /b 1
)
git diff --quiet HEAD -- "%SCRIPT%" scripts\original_v1_o2_body.py
if errorlevel 1 (
  echo %SCRIPT% or the body generator has uncommitted changes. Commit first.
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
  echo Missing %BLEND%. Run PREPARE_ORIGINAL_V1_O2.bat first.
  exit /b 1
)
if exist "ORIGINAL_V1_WORK\AUTHORING_TAINT.json" (
  echo AUTHORING_TAINT.json exists. Recover the last clean checkpoint; do not delete the record.
  exit /b 1
)

"%BLENDER%" --background --factory-startup "%BLEND%" --python-exit-code 1 --python scripts\audit_original_v4_blender.py
if errorlevel 1 exit /b 1
"%BLENDER%" --background --factory-startup "%BLEND%" --python-exit-code 1 --python scripts\disable_addons_for_guarded_session.py --python scripts\audit_original_v1_authoring_boundary_blender.py
if errorlevel 1 exit /b 1

shift
"%BLENDER%" --background --factory-startup "%CD%\%BLEND%" --python-exit-code 1 --python "%CD%\scripts\disable_addons_for_guarded_session.py" --python "%CD%\scripts\guard_original_v1_authoring_blender.py" --python "%CD%\%SCRIPT%" -- %1 %2 %3 %4
if errorlevel 1 exit /b 1
if exist "ORIGINAL_V1_WORK\AUTHORING_TAINT.json" (
  echo Guard recorded AUTHORING_TAINT.json during the session.
  exit /b 1
)
echo Guarded script completed: %SCRIPT%
exit /b 0

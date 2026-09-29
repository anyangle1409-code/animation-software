@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage: CHECKPOINT_ORIGINAL_V1_O2.bat region_name [strict]
  echo Example: CHECKPOINT_ORIGINAL_V1_O2.bat torso_chest_back
  echo Final O2: CHECKPOINT_ORIGINAL_V1_O2.bat neck_head strict
  exit /b 1
)

set "STRICT="
if /I "%~2"=="strict" set "STRICT=strict"

if defined STRICT (
  call AUDIT_ORIGINAL_V1_O2_AUTHORING.bat strict
) else (
  call AUDIT_ORIGINAL_V1_O2_AUTHORING.bat
)
if errorlevel 1 exit /b 1

if defined STRICT (
  python scripts\checkpoint_original_v1_o2.py --region "%~1" --strict
) else (
  python scripts\checkpoint_original_v1_o2.py --region "%~1"
)
if errorlevel 1 exit /b 1

echo.
echo O2 checkpoint recorded for "%~1".
exit /b 0

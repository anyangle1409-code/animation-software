@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Collision-free wrapper around the guarded axilla repair pipeline.
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat [source-rN]
rem The selector scans actual local candidate/evidence paths so partial work reserves a label.

set "SOURCE_REV=%~1"
if "%SOURCE_REV%"=="" set "SOURCE_REV=r55"
set "TARGET_REV="

for /f "usebackq delims=" %%I in (`python scripts\select_original_v1_collision_free_revision.py %SOURCE_REV% --plain`) do set "TARGET_REV=%%I"
if not defined TARGET_REV (
  echo ERROR: could not select a collision-free target revision.
  exit /b 2
)

echo Selected collision-free target: %TARGET_REV%
call RUN_ORIGINAL_V1_AXILLA_PIT_PIPELINE.bat %SOURCE_REV% %TARGET_REV%
exit /b %ERRORLEVEL%

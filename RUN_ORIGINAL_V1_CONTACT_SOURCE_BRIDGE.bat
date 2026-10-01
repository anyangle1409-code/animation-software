@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~1"
if "%OUT%"=="" set "OUT=ORIGINAL_V1_WORK\contact_source_bridge\current_source_bridge.json"
rem Source evidence only: verifies project-owned exercise/contact semantics and hashes.
rem It does not run Blender or the animation runtime and cannot approve a phase.
python scripts\original_v1_contact_source_bridge.py --json-out "%OUT%"
exit /b %ERRORLEVEL%

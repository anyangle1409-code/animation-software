@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
if "%~3"=="" goto usage
if "%~4"=="" goto usage
python scripts\original_v1_phase7_scene_capture.py "%~1" --authoring-record "%~2" --raw-pair "%~3" --out-dir "%~4"
exit /b %ERRORLEVEL%
:usage
echo Usage: RUN_ORIGINAL_V1_PHASE7_GARMENT_SCENE.bat ^<rN^> ^<authoring-record.json^> ^<raw-pair.json^> ^<fresh-output-dir^>
echo Read-only scene/provenance evidence only. Requires Phase 6 complete.
exit /b 2

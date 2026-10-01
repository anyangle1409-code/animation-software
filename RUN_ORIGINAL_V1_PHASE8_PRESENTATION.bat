@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
if "%~3"=="" goto usage
python scripts\original_v1_phase8_scene_capture.py "%~1" --material-provenance "%~2" --out-dir "%~3"
exit /b %ERRORLEVEL%
:usage
echo Usage: RUN_ORIGINAL_V1_PHASE8_PRESENTATION.bat ^<rN^> ^<material-provenance.json^> ^<fresh-output-dir^>
echo Read-only numeric material/presentation scene evidence only. Requires Phase 7 complete.
exit /b 2

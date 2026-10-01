@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
if "%~3"=="" goto usage
python scripts\original_v1_phase6_capture.py "%~1" --joint-support "%~2" --out-dir "%~3"
exit /b %ERRORLEVEL%
:usage
echo Usage: RUN_ORIGINAL_V1_PHASE6_SURFACE.bat ^<rN^> ^<authored-joint-support.json^> ^<fresh-output-dir^>
echo Read-only evidence capture only. Requires Phase 5 complete. Never repairs or approves the mesh.
exit /b 2

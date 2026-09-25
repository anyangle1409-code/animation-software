@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: AUDIT_PHASE_F_SOURCE_RIG.bat reference.glb candidate.glb
  exit /b 2
)
python scripts\audit_phase_f_source_rig.py --reference "%~1" --candidate "%~2"
exit /b %errorlevel%

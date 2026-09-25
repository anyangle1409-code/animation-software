@echo off
setlocal
cd /d "%~dp0"
if "%~3"=="" (
  echo Usage: VALIDATE_PHASE_F_RUNTIME.bat reference.glb candidate.glb label
  exit /b 2
)
python scripts\run_phase_f_runtime_validation.py --reference "%~1" --candidate "%~2" --label "%~3"
exit /b %errorlevel%

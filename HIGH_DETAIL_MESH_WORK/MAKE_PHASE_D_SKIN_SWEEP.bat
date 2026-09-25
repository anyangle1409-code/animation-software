@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: MAKE_PHASE_D_SKIN_SWEEP.bat candidate_version
  echo Example: MAKE_PHASE_D_SKIN_SWEEP.bat v15a_deep_hand_rebuild
  exit /b 2
)
python scripts\make_phase_d_skin_sweep.py --version %~1
exit /b %errorlevel%

@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: FINISH_CANDIDATE.bat version task
  echo task = knee ^| hand ^| material
  exit /b 2
)
python scripts\finish_candidate.py --version %1 --task %2
exit /b %errorlevel%

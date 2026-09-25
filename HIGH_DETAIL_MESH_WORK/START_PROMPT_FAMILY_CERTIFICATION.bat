@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: START_PROMPT_FAMILY_CERTIFICATION.bat family_id
  echo Example: START_PROMPT_FAMILY_CERTIFICATION.bat hinge
  exit /b 2
)
python scripts\prepare_prompt_family_certification.py %~1
exit /b %errorlevel%

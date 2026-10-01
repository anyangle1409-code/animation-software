@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_LOCAL_BACKUP.bat ^<fresh-directory-outside-repo^>
  exit /b 2
)
python scripts\original_v1_local_backup.py "%~1"
exit /b %ERRORLEVEL%

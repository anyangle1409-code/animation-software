@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" goto :usage
if "%~2"=="" goto :usage
python scripts\original_v1_export_evidence.py "%~1" --out-dir "%~2" --capture --json-out "%~2\candidate_export_verification.json"
exit /b %errorlevel%
:usage
echo Usage: RUN_ORIGINAL_V1_CANDIDATE_EXPORT.bat ^<rN^> ^<fresh repository output directory^>
echo Candidate evidence only. No model save or production approval.
exit /b 2

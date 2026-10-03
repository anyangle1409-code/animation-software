@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Read-only evidence triage after a completed axilla validation.
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_DISPOSITION.bat <candidate-rN> [parent-rN]

set "REV=%~1"
set "PARENT=%~2"
if "%REV%"=="" goto :usage
if "%PARENT%"=="" set "PARENT=r55"
if /I "%REV%"=="%PARENT%" ( echo ERROR: candidate and parent must differ & exit /b 2 )

set "OUT=ORIGINAL_V1_WORK\candidates\repair_checks\axilla_%REV%\post_validation_disposition.json"
set "MD=ORIGINAL_V1_WORK\candidates\repair_checks\axilla_%REV%\post_validation_disposition.md"
if exist "%OUT%" ( echo ERROR: refusing to overwrite %OUT% & exit /b 2 )
if exist "%MD%" ( echo ERROR: refusing to overwrite %MD% & exit /b 2 )

python scripts\original_v1_axilla_disposition.py %REV% %PARENT% --json-out "%OUT%" --markdown-out "%MD%"
if errorlevel 1 exit /b 2

echo DISPOSITION SUMMARY READY: %OUT%
echo Read-only evidence triage only; no lineage, visual acceptance, freeze or production state was changed.
exit /b 0

:usage
echo Usage: %~nx0 ^<candidate-rN^> [parent-rN]
exit /b 2

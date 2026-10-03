@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem End-to-end EXPERIMENTAL local axilla repair loop.
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_PIPELINE.bat <source-rN> <target-rN>
rem Runs pre-edit declaration -> one-dump numeric sweep -> incremental apply -> full validation -> read-only disposition.
rem Every child runner is fail-closed and refuses collisions. This wrapper never accepts/promotes a candidate.

set "SOURCE_REV=%~1"
set "TARGET_REV=%~2"
if "%SOURCE_REV%"=="" goto :usage
if "%TARGET_REV%"=="" goto :usage
if /I "%SOURCE_REV%"=="%TARGET_REV%" (
  echo ERROR: source and target revisions must differ.
  exit /b 2
)

set "EXPECTED_BRANCH=claude/original-v1-blender-o2-20260929"
set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="%EXPECTED_BRANCH%" (
  echo ERROR: Expected %EXPECTED_BRANCH%; found "%CURRENT_BRANCH%".
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 local axilla repair pipeline
echo Source: %SOURCE_REV%
echo Target: %TARGET_REV%
echo Experimental only. No acceptance or production promotion.
echo ============================================================

echo [1/5] Declare local pit evidence/mask before edit...
call RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat %SOURCE_REV% %TARGET_REV%
if errorlevel 1 goto :fail

echo [2/5] Run one-dump deterministic numeric trial sweep...
call RUN_ORIGINAL_V1_AXILLA_PIT_SWEEP.bat %SOURCE_REV% %TARGET_REV%
if errorlevel 1 goto :fail

echo [3/5] Apply selected local incremental corrective...
call RUN_ORIGINAL_V1_AXILLA_PIT_APPLY.bat %SOURCE_REV% %TARGET_REV%
if errorlevel 1 goto :fail

echo [4/5] Run full evidence, local-face audit and real review capture...
call RUN_ORIGINAL_V1_AXILLA_PIT_VALIDATE.bat %TARGET_REV% %SOURCE_REV%
if errorlevel 1 goto :fail

echo [5/5] Build read-only post-validation disposition summary...
call RUN_ORIGINAL_V1_AXILLA_PIT_DISPOSITION.bat %TARGET_REV% %SOURCE_REV%
if errorlevel 1 goto :fail

echo.
echo PIPELINE COMPLETE: %TARGET_REV%
echo The candidate remains experimental. Read the disposition summary and real renders before any continuation or freeze decision.
exit /b 0

:usage
echo Usage: %~nx0 ^<source-rN^> ^<target-rN^>
exit /b 2

:fail
echo.
echo PIPELINE STOPPED. Preserve all outputs already created; do not overwrite or restart with the same target label.
echo Inspect the failed child stage and continue only with a collision-free evidence path.
exit /b 1

@echo off
setlocal
cd /d "%~dp0"

echo.
echo HOME GYM PT - PRIVATE ORIGINAL CT ANATOMY REVIEW
echo ================================================
echo This uses Python 3 and first-party scripts only.
echo NLM original images and derived scan plates stay OUTSIDE this repository.
echo All annotated points are provisional. No bones are approved.
echo.

where py >nul 2>nul
if not errorlevel 1 goto USE_PY
where python >nul 2>nul
if not errorlevel 1 goto USE_PYTHON

echo ERROR: Python 3 was not found on PATH.
echo This process does not require Claude or any pip packages.
echo Install/enable Python 3, then run this file again.
pause
exit /b 1

:USE_PY
py -3 scripts\anatomy_fit\nlm_ct_laptop_review.py --open
goto FINISH

:USE_PYTHON
python scripts\anatomy_fit\nlm_ct_laptop_review.py --open

:FINISH
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo CT review preparation was NOT completed.
  echo Check the error above. Existing source files will not be overwritten.
) else (
  echo.
  echo Review complete. Your default browser should show START HERE.
  echo Private output: %USERPROFILE%\HomeGymPT_Private_Original_CT_Review\PRIVATE_CT_VIEW
)
echo.
pause
exit /b %RESULT%

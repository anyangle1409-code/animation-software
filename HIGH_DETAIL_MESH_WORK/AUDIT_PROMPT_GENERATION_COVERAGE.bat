@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_prompt_generation_coverage.py
exit /b %errorlevel%

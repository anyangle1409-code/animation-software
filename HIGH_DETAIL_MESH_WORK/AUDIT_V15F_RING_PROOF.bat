@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_v15f_ring_proof.py
exit /b %errorlevel%

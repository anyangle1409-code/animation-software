@echo off
setlocal
cd /d "%~dp0"

set "SYNC_PYTHON="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$root=Join-Path $env:ProgramFiles 'Blender Foundation'; $p=Get-ChildItem -Path $root -Filter python.exe -Recurse -ErrorAction SilentlyContinue ^| Where-Object FullName -Like '*\python\bin\python.exe' ^| Sort-Object FullName -Descending ^| Select-Object -First 1 -ExpandProperty FullName; if ($p) { $p }"`) do set "SYNC_PYTHON=%%P"
if not defined SYNC_PYTHON set "SYNC_PYTHON=python"

"%SYNC_PYTHON%" scripts\remote_state_sync.py --sync
exit /b %errorlevel%

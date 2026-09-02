@echo off
rem Daily refresh for the AWL party board (Windows Task Scheduler entry point).
rem Rebuilds site\index.html live from SAP HANA, read-only. Appends to refresh.log.
rem A failure leaves the previous page on disk, still readable.

set "PY=C:\Program Files\Python312\python.exe"
if not exist "%PY%" set "PY=py"

echo. >> "%~dp0refresh.log"
echo === refresh started %DATE% %TIME% >> "%~dp0refresh.log"
"%PY%" "%~dp0build.py" %* >> "%~dp0refresh.log" 2>&1
if errorlevel 1 (
  echo BUILD FAILED - previous page stays on disk >> "%~dp0refresh.log"
  exit /b 1
)
echo === done %DATE% %TIME% >> "%~dp0refresh.log"
exit /b 0

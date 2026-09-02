@echo off
setlocal
rem gst-sync (Windows) - borrow the fleet's GST portal sessions from the VPS holder.
rem The GST portal allows ONE session per username, so only the VPS (gstd) ever logs in;
rem this PC copies its cookie jars and never logs in itself. Safe to run any time.
set "KEY=%USERPROFILE%\.ssh\jivo-gst-sync"
set "DIR=%APPDATA%\gst-portal"
set "TMPF=%TEMP%\jivo-gst-jars.tar"
if not exist "%DIR%" mkdir "%DIR%"
ssh -i "%KEY%" -o IdentitiesOnly=yes -o ConnectTimeout=15 -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=15 -o ServerAliveCountMax=40 root@187.127.129.132 true > "%TMPF%" 2>nul
if errorlevel 1 (echo gst-sync: could not reach the VPS - local sessions unchanged & exit /b 1)
for %%A in ("%TMPF%") do if %%~zA LSS 100 (echo gst-sync: the VPS sent nothing & exit /b 1)
tar -xf "%TMPF%" -C "%DIR%"
if errorlevel 1 (echo gst-sync: extract failed & exit /b 1)
del "%TMPF%" 2>nul
echo gst-sync: %DATE% %TIME% - GST sessions refreshed in %DIR%
endlocal

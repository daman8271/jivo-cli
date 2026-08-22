@echo off
rem Put letsgo.cmd on this Windows box so it can reach JIVO's summon agent.
rem
rem   install-client.cmd <TOKEN> <SUMMON_URL>
rem
rem Both arguments come from Daman. The token identifies this device; only he can
rem mint one (/opt/jivo-summon/tokens.json on the VPS). There is no
rem self-enrolment: the token IS the authorisation.
rem
rem No python anywhere in here on purpose — several boxes have a Microsoft Store
rem python stub that exits 0 while doing nothing, so a python-based installer
rem would appear to succeed and leave the box unable to summon.
setlocal

set "TOKEN=%~1"
set "URL=%~2"

if "%TOKEN%"=="" goto :usage
if "%URL%"=="" goto :usage

where curl.exe >nul 2>&1
if errorlevel 1 (
  echo FATAL: curl not found. Needs Windows 10 1803 or newer.
  exit /b 1
)

set "CONF=%USERPROFILE%\.jivo-summon.env"
> "%CONF%" echo # JIVO summon agent - this device's credentials. Keep private.
>>"%CONF%" echo SUMMON_URL=%URL%
>>"%CONF%" echo SUMMON_TOKEN=%TOKEN%
echo wrote %CONF%

rem Lock it down: remove inherited ACLs, leave only this user and Administrators.
icacls "%CONF%" /inheritance:r /grant:r "%USERNAME%:F" /grant:r "Administrators:F" >nul 2>&1
if errorlevel 1 echo NOTE: could not tighten permissions on %CONF% - check it by hand.

rem Install next to the kit so it is findable, and into a PATH dir if we can.
set "HERE=%~dp0"
set "DEST=%USERPROFILE%\.local\bin"
if not exist "%DEST%" mkdir "%DEST%" >nul 2>&1
copy /y "%HERE%..\client\letsgo.cmd" "%DEST%\letsgo.cmd" >nul
if errorlevel 1 (
  echo FATAL: could not install letsgo.cmd to %DEST%
  exit /b 1
)
echo installed %DEST%\letsgo.cmd

echo %PATH% | find /i "%DEST%" >nul
if errorlevel 1 (
  echo.
  echo NOTE: %DEST% is not on this box's PATH.
  echo       Either add it, or call "%DEST%\letsgo.cmd" directly.
)

echo.
echo verifying...
call "%DEST%\letsgo.cmd" --status
if errorlevel 1 (
  echo.
  echo The client is installed but the agent did not answer.
  echo Check the network, then run: letsgo --status
  exit /b 1
)
echo.
echo OK - say:  letsgo what you need
exit /b 0

:usage
echo usage: install-client.cmd ^<TOKEN^> ^<SUMMON_URL^>
echo.
echo Both come from Daman. On the VPS, list the device tokens with:
echo   python3 -c "import json;[print(k,v['device']) for k,v in json.load(open('/opt/jivo-summon/tokens.json')).items()]"
echo   cat /opt/jivo-summon/state/path-slug
exit /b 2

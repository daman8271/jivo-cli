@echo off
rem letsgo.cmd - say "Let's go" from a JIVO Windows box and reach the summon agent.
rem
rem   letsgo                      just summon; it will ask what you need
rem   letsgo I need to make A/P invoices
rem   letsgo --status             is the agent up
rem
rem Deliberately curl-only, NO python. Several boxes here have a Microsoft Store
rem python stub that prints "Python was not found" and exits 0, so anything built
rem on python silently does nothing. curl ships in System32 on Win10+ and is real.
rem The server renders the answer for us when we ask for text/plain, so there is
rem no JSON to parse in batch.
setlocal EnableDelayedExpansion

set "CONF=%USERPROFILE%\.jivo-summon.env"
if not exist "%CONF%" (
  echo letsgo: no config at %CONF%
  echo         run install-client.cmd from the kit's summon\deploy folder first.
  exit /b 1
)

rem The config is KEY=VALUE lines. Read only the two keys we need, so a stray
rem line in the file cannot turn into a command.
set "SUMMON_URL="
set "SUMMON_TOKEN="
for /f "usebackq tokens=1,* delims==" %%A in ("%CONF%") do (
  if /i "%%A"=="SUMMON_URL"   set "SUMMON_URL=%%B"
  if /i "%%A"=="SUMMON_TOKEN" set "SUMMON_TOKEN=%%B"
)

rem Strip trailing spaces. cmd's `(echo A & echo B) > file` idiom leaves one
rem before the newline, which curl rejects outright as "Malformed input to a URL
rem function" - and an operator hand-editing this file can easily leave one too.
rem for /f already drops the CR of a CRLF; the space is what survives.
for /l %%i in (1,1,16) do if "!SUMMON_URL:~-1!"==" "   set "SUMMON_URL=!SUMMON_URL:~0,-1!"
for /l %%i in (1,1,16) do if "!SUMMON_TOKEN:~-1!"==" " set "SUMMON_TOKEN=!SUMMON_TOKEN:~0,-1!"

if "!SUMMON_URL!"=="" ( echo letsgo: SUMMON_URL missing from %CONF% & exit /b 1 )
if "!SUMMON_TOKEN!"=="" ( echo letsgo: SUMMON_TOKEN missing from %CONF% & exit /b 1 )

where curl.exe >nul 2>&1
if errorlevel 1 ( echo letsgo: curl not found - needs Windows 10 1803 or newer & exit /b 1 )

rem --status: strip /v1/summon off the URL to get the base.
if /i "%~1"=="--status" (
  set "BASE=!SUMMON_URL:/v1/summon=!"
  curl -sS --max-time 20 -H "Authorization: Bearer !SUMMON_TOKEN!" "!BASE!/v1/status"
  exit /b %errorlevel%
)

set "ASK=%*"
if "%ASK%"=="" (
  set /p "ASK=What do you need? (enter to just say hello): "
)

echo summoning the JIVO agent...

rem Send the question as a RAW TEXT body from a temp file. Do not build JSON
rem here: escaping quotes through cmd, curl (and PowerShell, when this is driven
rem over ssh) means some layer always eats an escape, and the first real Windows
rem summon failed with "bad or oversized JSON body" for exactly that reason.
rem A text body has nothing to escape, so whatever the operator typed arrives
rem intact - and the server treats it strictly as data either way.
set "BODY=%TEMP%\letsgo-%RANDOM%.txt"
> "%BODY%" echo !ASK!

rem Accept: text/plain makes the server render the answer too, so there is
rem nothing to parse on the way back. --max-time is generous: a real session
rem thinks for a while.
curl -sS --max-time 480 ^
  -H "Authorization: Bearer !SUMMON_TOKEN!" ^
  -H "Content-Type: text/plain" ^
  -H "Accept: text/plain" ^
  -X POST ^
  --data-binary "@%BODY%" ^
  "!SUMMON_URL!"
set "CURLRC=%errorlevel%"
del /q "%BODY%" 2>nul

if not "%CURLRC%"=="0" (
  echo.
  echo letsgo: could not reach the summon agent. Check the network, then: letsgo --status
  exit /b 1
)
exit /b 0

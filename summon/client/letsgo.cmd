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

if "%SUMMON_URL%"=="" ( echo letsgo: SUMMON_URL missing from %CONF% & exit /b 1 )
if "%SUMMON_TOKEN%"=="" ( echo letsgo: SUMMON_TOKEN missing from %CONF% & exit /b 1 )

where curl.exe >nul 2>&1
if errorlevel 1 ( echo letsgo: curl not found - needs Windows 10 1803 or newer & exit /b 1 )

rem --status: strip /v1/summon off the URL to get the base.
if /i "%~1"=="--status" (
  set "BASE=%SUMMON_URL:/v1/summon=%"
  curl -sS --max-time 20 -H "Authorization: Bearer %SUMMON_TOKEN%" "!BASE!/v1/status"
  exit /b %errorlevel%
)

set "ASK=%*"
if "%ASK%"=="" (
  set /p "ASK=What do you need? (enter to just say hello): "
)

rem Escape the two characters that would break the JSON body. Everything else
rem the operator types is passed through as-is and treated as data by the agent.
set "ASK=%ASK:\=\\%"
set "ASK=%ASK:"=%"

echo summoning the JIVO agent...

rem Accept: text/plain makes the server render the answer, so there is nothing
rem to parse here. --max-time is generous: a real session thinks for a while.
curl -sS --max-time 480 ^
  -H "Authorization: Bearer %SUMMON_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -H "Accept: text/plain" ^
  -X POST ^
  --data "{\"say\":\"lets go\",\"ask\":\"%ASK%\",\"os\":\"windows\",\"cwd\":\"%CD%\"}" ^
  "%SUMMON_URL%"

if errorlevel 1 (
  echo.
  echo letsgo: could not reach the summon agent. Check the network, then: letsgo --status
  exit /b 1
)
exit /b 0

@echo off
REM ARY (Microsoft SQL Server, 138.252.101.118) — run the read-only dsr client
REM against it from Windows.
REM
REM Why this file exists: connections\ary.env is written for bash
REM (`set -a; . connections/ary.env; set +a`), so its values are SINGLE-QUOTED.
REM cmd's `for /f` does NOT strip those quotes, so a naive loop sets
REM DSR_HOST='138.252.101.118' and the client fails with "no such host".
REM This wrapper strips them.
REM
REM Usage (from anywhere):
REM   connections\ary-connect.cmd doctor
REM   connections\ary-connect.cmd query --db FR8HODBNEW "SELECT TOP 5 * FROM SaleHeader"
REM   echo SELECT 1; | connections\ary-connect.cmd query --db FR8HODBNEW
REM
REM Read-only: dsr is SELECT-only and always rolls its transaction back.
cd /d "%~dp0.."
if not exist "connections\ary.env" (
  echo ary-connect: connections\ary.env is missing - ask IT for the ARY credentials.
  exit /b 2
)
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("connections\ary.env") do call :setvar "%%a" "%%b"
dsr-cli\dsr.exe %*
exit /b %errorlevel%

:setvar
set "_n=%~1"
set "_v=%~2"
set "_v=%_v:'=%"
set "%_n%=%_v%"
goto :eof

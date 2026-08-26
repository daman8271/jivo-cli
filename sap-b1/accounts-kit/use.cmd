@echo off
REM ===================================================================
REM  use.cmd  -  pick the SAP company for THIS cmd window
REM  DESKTOP-EQ55Q8H (Satnam), jivo-cli, 2026-08-25
REM
REM    use              show which login/company this window is on
REM    use oil          USER39 on JIVO_OIL_HANADB        (the default)
REM    use mart         USER39 on JIVO_MART_HANADB
REM    use bev          USER39 on JIVO_BEVERAGES_HANADB
REM
REM  One login only: USER39. SAP passwords DIFFER PER COMPANY
REM  (correction C-0031), so each company has its own .env file here and
REM  switching company means loading that file - never just changing
REM  SAPB1_COMPANYDB, which would send the wrong password.
REM
REM  Run this from cmd (not PowerShell) - it sets vars in this window.
REM  A real environment variable beats .env, so `use` always wins.
REM ===================================================================

if "%~1"=="" goto :show

set "_envfile="
if /i "%~1"=="oil"    set "_envfile=%~dp0satnam-user39.env"
if /i "%~1"=="mart"   set "_envfile=%~dp0satnam-user39-mart.env"
if /i "%~1"=="bev"    set "_envfile=%~dp0satnam-user39-bev.env"
if /i "%~1"=="satnam" set "_envfile=%~dp0satnam-user39.env"
if /i "%~1"=="user39" set "_envfile=%~dp0satnam-user39.env"

if "%_envfile%"=="" (
  echo(
  echo   No such company: %~1
  echo   Use one of:  oil ^| mart ^| bev
  echo(
  exit /b 1
)
if not exist "%_envfile%" (
  echo(
  echo   Missing env file: %_envfile%
  echo(
  set "_envfile="
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "SAPB1_" "%_envfile%"`) do set "%%a=%%b"
set "_envfile="

REM One write log per SAP user, same convention as queries\USER36 and
REM queries\manager already on main. (A `delete draft` always ALSO records in
REM queries\<operator-slug> - the CLI ignores this variable for deletes on
REM purpose, so a destroyed draft cannot be diverted.)
if not "%SAPB1_USER%"=="" set "SAPB1_WRITE_LOG=%~dp0..\..\queries\%SAPB1_USER%\sap-writes.jsonl"

:show
echo(
if "%SAPB1_USER%"=="" (
  echo   login    ^(none set in this window - sapb1 will use .env: USER39, Oil^)
) else (
  echo   login    %SAPB1_USER%
)
echo   company  %SAPB1_COMPANYDB%
echo   host     %SAPB1_HOST%:%SAPB1_PORT%
if not "%SAPB1_WRITE_LOG%"=="" echo   log      %SAPB1_WRITE_LOG%
echo(
if /i "%SAPB1_USER%"=="USER39" echo   Drafts and writes from this window are logged as USER39.
echo(

@echo off
REM run.cmd - RM sheet vs live SAP stock, straight to Excel.
REM
REM   run.cmd                       the newest sheet dropped in in\
REM   run.cmd in\01-09-2026.xlsx    a named sheet
REM   run.cmd in\sheet.xlsx --all-warehouses
REM
REM Output lands in out\ and opens by itself.
setlocal
cd /d "%~dp0"

set "PY=python"
where py >nul 2>&1 && set "PY=py -3"

REM a leading "-something" is a flag, not the sheet - so `run.cmd --itr` works
set "SHEET=%~1"
if not "%SHEET%"=="" if not "%SHEET:~0,1%"=="-" (shift) else set "SHEET="

if "%SHEET%"=="" (
  for /f "delims=" %%F in ('dir /b /o-d "in\*.xlsx" "in\*.csv" "in\*.txt" "in\*.tsv" 2^>nul') do (
    set "SHEET=in\%%F"
    goto :got
  )
)
:got
if "%SHEET%"=="" (
  echo No sheet given and nothing in in\ - drop the RM sheet into %~dp0in\ first.
  exit /b 1
)

echo Sheet: %SHEET%
%PY% check.py "%SHEET%" %1 %2 %3 %4 %5
if errorlevel 1 exit /b 1

for /f "delims=" %%F in ('dir /b /o-d "out\*.xlsx" 2^>nul') do (
  start "" "out\%%F"
  goto :done
)
:done
endlocal

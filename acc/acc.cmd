@echo off
rem acc.cmd - the Accounts workbench on Windows.
rem
rem   acc\acc.cmd batch scan --company Oil --limit 50
rem   acc\acc.cmd batch send  acc\_batches\<id>\review-<id>.xlsx
rem
rem `scan` never writes to SAP. `send` creates DRAFTS only, and only with --yes;
rem a person still has to press Add in SAP B1.
rem
rem Finding python is the fiddly part on these boxes. Several of them have the
rem Microsoft Store stub, which prints "Python was not found" and exits 0 - so a
rem naive `python acc.py` would silently do nothing at all. The launcher (`py`)
rem is checked first because it never resolves to the stub, and every candidate
rem has to actually print a version before it is used.
setlocal EnableDelayedExpansion

set "PY="
for %%C in ("py -3" "python" "python3") do (
  if not defined PY (
    for /f "usebackq delims=" %%V in (`%%~C -c "import sys;print(sys.version_info[0])" 2^>nul`) do (
      if "%%V"=="3" set "PY=%%~C"
    )
  )
)

if not defined PY (
  echo acc: no working Python 3 found on this machine.
  echo      The Microsoft Store stub does not count - install real Python from
  echo      python.org and tick "Add python.exe to PATH", then re-open this window.
  exit /b 3
)

%PY% "%~dp0acc.py" %*
exit /b %ERRORLEVEL%

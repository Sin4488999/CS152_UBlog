:: scripts\purge_unverified.bat
@echo off
setlocal enabledelayedexpansion

REM Locate .env (project root assumed one level up from scripts\)
set "SCRIPT_DIR=%~dp0"
set "ENV_FILE=%SCRIPT_DIR%\..\ .env"
set "ENV_FILE=%ENV_FILE:~0,-1%"  REM trim trailing space if any

if not exist "%ENV_FILE%" (
  echo [ERROR] .env not found at "%ENV_FILE%"
  exit /b 1
)

REM Read UBLOG_PROJECT_DIR and UBLOG_VENV_PY from .env (ignore comments/blank lines)
for /f "usebackq tokens=1,* delims==" %%A in (`type "%ENV_FILE%" ^| findstr /R /B /C:"UBLOG_PROJECT_DIR=" /C:"UBLOG_VENV_PY="`) do (
  set "key=%%A"
  set "val=%%B"
  REM strip surrounding quotes if present
  if "!val:~0,1!"=="\"" set "val=!val:~1!"
  if "!val:~-1!"=="\"" set "val=!val:~0,-1!"
  if /I "!key!"=="UBLOG_PROJECT_DIR" set "UBLOG_PROJECT_DIR=!val!"
  if /I "!key!"=="UBLOG_VENV_PY" set "UBLOG_VENV_PY=!val!"
)

if not defined UBLOG_PROJECT_DIR (
  echo [ERROR] UBLOG_PROJECT_DIR is not set in .env
  exit /b 2
)

if not defined UBLOG_VENV_PY (
  set "UBLOG_VENV_PY=%UBLOG_PROJECT_DIR%\.venv\Scripts\python.exe"
)

if not exist "%UBLOG_VENV_PY%" (
  echo [ERROR] Python not found at "%UBLOG_VENV_PY%"
  exit /b 3
)

pushd "%UBLOG_PROJECT_DIR%"
"%UBLOG_VENV_PY%" manage.py purge_unverified --days 7 >> "%UBLOG_PROJECT_DIR%\purge_unverified.log" 2>&1
set "ERR=%ERRORLEVEL%"
popd

if "%ERR%"=="0" (
  echo [OK] Purge finished.
) else (
  echo [ERROR] Purge failed with code %ERR%
)
exit /b %ERR%

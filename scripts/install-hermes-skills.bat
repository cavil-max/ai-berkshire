@echo off
setlocal enabledelayedexpansion

set "MODE=link"
set "DEST=%USERPROFILE%\.hermes\skills"

:parse
if "%~1"=="" goto run
if /i "%~1"=="--copy" set "MODE=copy" & shift & goto parse
if /i "%~1"=="--global" shift & goto parse
if /i "%~1"=="-h" goto usage
if /i "%~1"=="--help" goto usage
echo Unknown option: %~1 >&2
goto usage

:run
for %%I in ("%~dp0..") do set "ROOT=%%~fI"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

%PY% "%ROOT%\scripts\sync-hermes-skills.py"
if errorlevel 1 exit /b %ERRORLEVEL%

if not exist "%DEST%" mkdir "%DEST%"
if errorlevel 1 exit /b %ERRORLEVEL%

for /d %%D in ("%ROOT%\hermes-skills\*") do (
  if exist "%DEST%\%%~nxD" rmdir /s /q "%DEST%\%%~nxD"
  if errorlevel 1 exit /b 1
  if "!MODE!"=="copy" (
    xcopy "%%~fD" "%DEST%\%%~nxD\" /E /I /Y >nul
  ) else (
    mklink /D "%DEST%\%%~nxD" "%%~fD"
  )
  if errorlevel 1 exit /b 1
)

echo Installed Hermes skills to %DEST%
echo Restart Hermes or start a new session to pick up the new skills.
exit /b 0

:usage
echo Usage: install-hermes-skills.bat [--copy] [--global]
echo.
echo Options:
echo   --copy     Copy skill directories instead of symlinking (default: symlink).
echo   --global   Placeholder for consistency; Hermes uses a single skills directory.
echo   -h, --help Show this help.
echo.
echo Default target: %USERPROFILE%\.hermes\skills
exit /b 0

@echo off
setlocal enabledelayedexpansion

set "MODE=link"
set "DEST=%USERPROFILE%\.config\opencode\commands"
set "INSTALL_SKILLS=false"

:parse
if "%~1"=="" goto run
if /i "%~1"=="--copy" set "MODE=copy" & shift & goto parse
if /i "%~1"=="--global" shift & goto parse
if /i "%~1"=="--skills" set "INSTALL_SKILLS=true" & shift & goto parse
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

%PY% "%ROOT%\scripts\sync-opencode.py"
if errorlevel 1 exit /b %ERRORLEVEL%

if not exist "%DEST%" mkdir "%DEST%"
if errorlevel 1 exit /b %ERRORLEVEL%

for %%F in ("%ROOT%\.opencode\command\*.md") do (
  if exist "%DEST%\%%~nxF" del "%DEST%\%%~nxF"
  if errorlevel 1 exit /b 1
  if "!MODE!"=="copy" (
    copy "%%~fF" "%DEST%\%%~nxF" >nul
  ) else (
    mklink "%DEST%\%%~nxF" "%%~fF"
  )
  if errorlevel 1 exit /b 1
)

if "!INSTALL_SKILLS!"=="true" (
  set "SKILLS_DEST=%USERPROFILE%\.config\opencode\skills"
  if not exist "!SKILLS_DEST!" mkdir "!SKILLS_DEST!"
  if errorlevel 1 exit /b %ERRORLEVEL%
  for /d %%D in ("%ROOT%\.opencode\skills\*") do (
    if exist "!SKILLS_DEST!\%%~nxD" rmdir /s /q "!SKILLS_DEST!\%%~nxD"
    if errorlevel 1 exit /b 1
    if "!MODE!"=="copy" (
      xcopy "%%~fD" "!SKILLS_DEST!\%%~nxD\" /E /I /Y >nul
    ) else (
      mklink /D "!SKILLS_DEST!\%%~nxD" "%%~fD"
    )
    if errorlevel 1 exit /b 1
  )
)

echo Installed opencode commands to %DEST%
if "!INSTALL_SKILLS!"=="true" echo Installed opencode skills to !SKILLS_DEST!
echo Restart opencode (or start a new session) to pick up the new commands.
exit /b 0

:usage
echo Usage: install-opencode.bat [--copy] [--global] [--skills]
echo.
echo Options:
echo   --copy     Copy files instead of symlinking (default: symlink).
echo   --global   Placeholder for consistency with sibling install scripts.
echo   --skills   Also install skills to %%USERPROFILE%%\.config\opencode\skills.
echo   -h, --help Show this help.
echo.
echo Default target: %%USERPROFILE%%\.config\opencode\commands
exit /b 0

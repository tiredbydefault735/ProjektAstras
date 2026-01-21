@echo off
SETLOCAL
set PY=C:/Users/Sarah/AppData/Local/Programs/Python/Python312/python.exe
pushd %~dp0\..

echo Using Python: %PY%

%PY% -m PyInstaller --version >NUL 2>&1
if errorlevel 1 (
  echo PyInstaller not available. Install with: %PY% -m pip install pyinstaller
  popd
  exit /b 1
)

set DIST=%CD%\main.onefile-build\dist
set WORK=%CD%\main.onefile-build\build
set SPEC=%CD%\main.onefile-build\spec

mkdir "%DIST%" 2>NUL
mkdir "%WORK%" 2>NUL
mkdir "%SPEC%" 2>NUL

%PY% -m PyInstaller --noconfirm --clean --onefile --name ProjektAstras --distpath "%DIST%" --workpath "%WORK%" --specpath "%SPEC%" --add-data "%CD%\static;static" --add-data "%CD%\i18n;i18n" "frontend\main.py"
if errorlevel 1 (
  echo PyInstaller failed with exit code %ERRORLEVEL%
  popd
  exit /b %ERRORLEVEL%
)

echo Built executable at %DIST%\ProjektAstras.exe

:: Cleanup intermediate PyInstaller files
rd /s /q "%WORK%" 2>NUL
rd /s /q "%SPEC%" 2>NUL
for /r %%f in (*.spec) do del /f "%%f" 2>NUL

popd
ENDLOCAL

@echo off
rem Builds the converter window into one .exe: dist\pxo_to_aseprite.exe here.
rem Double-click it. The .exe runs without Python; it still needs Aseprite.
setlocal
cd /d "%~dp0"

set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
    echo Python is not installed. Get it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" in the installer, then try again.
    pause
    exit /b 2
)

%PY% -c "import PIL, numpy, tkinterdnd2, PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo First run: installing Pillow, NumPy, tkinterdnd2 and PyInstaller...
    %PY% -m pip install --user pillow numpy tkinterdnd2 pyinstaller
    if errorlevel 1 (
        echo Could not install them. Run "%PY% -m pip install pillow numpy tkinterdnd2 pyinstaller" yourself.
        pause
        exit /b 2
    )
)

set WORK=%TEMP%\pxo_to_aseprite_build
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name pxo_to_aseprite ^
    --distpath "%~dp0dist" --workpath "%WORK%" --specpath "%WORK%" ^
    --add-data "%~dp0aseprite_build.lua;." --collect-all tkinterdnd2 ^
    "%~dp0pxo_to_aseprite_gui.pyw"
set RESULT=%errorlevel%
echo.
if %RESULT%==0 (echo Built %~dp0dist\pxo_to_aseprite.exe) else (echo The build failed; see above.)
pause
exit /b %RESULT%

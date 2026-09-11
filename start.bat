@echo off
setlocal

REM Always run from the directory that contains this script.
pushd "%~dp0"
if errorlevel 1 (
    echo ERROR: Failed to open the application folder.
    pause
    exit /b 1
)

set "APP_PYTHON=venv\Scripts\python.exe"

if not exist "%APP_PYTHON%" (
    echo ERROR: The virtual environment was not found.
    echo Run setup.bat first.
    pause
    popd
    exit /b 1
)

"%APP_PYTHON%" -c "import flask, flask_login, flask_sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required packages are not installed in the virtual environment.
    echo Run setup.bat again.
    pause
    popd
    exit /b 1
)

set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

echo ==========================================
echo Starting Learning Support App...
echo ==========================================
echo.

start "" cmd /c "timeout /t 2 >nul && start http://127.0.0.1:5000"

"%APP_PYTHON%" -m flask --app learning_app.app run

pause
popd
endlocal

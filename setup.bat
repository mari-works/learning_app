@echo off
setlocal

REM Always run from the directory that contains this script.
REM When launched from a shortcut or another process, the current directory
REM may otherwise be C:\Windows, causing Python to try to create C:\Windows\venv.
pushd "%~dp0"
if errorlevel 1 (
    echo ERROR: Failed to open the application folder.
    pause
    exit /b 1
)

echo ==========================================
echo Learning Support App - Initial Setup
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Please install Python 3.11 or later.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check Python version (3.11 or later)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"

if errorlevel 1 (
    echo ERROR: Python 3.11 or later is required.
    echo Please update Python and run setup.bat again.
    pause
    exit /b 1
)

REM Create virtual environment
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv

    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Existing virtual environment found.
)

echo.
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

if errorlevel 1 (
    echo ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

echo.
echo Installing required packages...
venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install required packages.
    echo Your Python version may not be compatible.
    pause
    exit /b 1
)

echo.
echo Installing the application...
venv\Scripts\python.exe -m pip install -e .

if errorlevel 1 (
    echo ERROR: Failed to install the application.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Setup completed successfully.
echo Run start.bat next.
echo ==========================================
echo.

pause
popd
endlocal

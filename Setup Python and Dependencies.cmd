@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo Steam Archive Manager - Python setup
echo.

if not exist "%~dp0requirements.txt" (
    echo ERROR: requirements.txt was not found next to this setup file.
    echo.
    pause
    exit /b 1
)

call :find_python
if not defined PYTHON_CMD (
    echo Python 3.10 or newer was not found.
    echo.
    call :install_python_with_winget
    if errorlevel 1 (
        echo.
        echo Install Python 3.10 or newer manually, then run this file again:
        echo https://www.python.org/downloads/windows/
        echo.
        pause
        exit /b 1
    )

    call :find_python
)

if not defined PYTHON_CMD (
    echo ERROR: Python was installed, but it could not be found in this command window.
    echo Close this window, open a new one, then run this file again.
    echo.
    pause
    exit /b 1
)

echo Using %PYTHON_LABEL%
%PYTHON_CMD% --version
echo.

%PYTHON_CMD% -c "from PIL import Image, ImageTk" >nul 2>nul
if not errorlevel 1 (
    echo Pillow is already installed.
    echo Setup complete.
    echo.
    pause
    exit /b 0
)

echo Installing Python dependencies...
%PYTHON_CMD% -m ensurepip --upgrade >nul 2>nul
%PYTHON_CMD% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    echo.
    pause
    exit /b 1
)

%PYTHON_CMD% -c "from PIL import Image, ImageTk; print('Pillow OK')"
if errorlevel 1 (
    echo.
    echo ERROR: Pillow is still unavailable after installation.
    echo.
    pause
    exit /b 1
)

echo.
echo Setup complete. You can now launch Steam Archive Manager.
echo.
pause
exit /b 0

:find_python
set "PYTHON_CMD="
set "PYTHON_LABEL="

if exist "%~dp0portable-python\python.exe" (
    "%~dp0portable-python\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="%~dp0portable-python\python.exe""
        set "PYTHON_LABEL=portable-python"
        exit /b 0
    )
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python314\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist "%%~P" (
        "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_CMD="%%~P""
            set "PYTHON_LABEL=%%~P"
            exit /b 0
        )
    )
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
        set "PYTHON_LABEL=Python Launcher"
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
        set "PYTHON_LABEL=python"
        exit /b 0
    )
)

exit /b 0

:install_python_with_winget
where winget >nul 2>nul
if errorlevel 1 (
    echo winget was not found, so Python cannot be installed automatically.
    exit /b 1
)

echo Installing Python 3.12 with winget...
winget install --exact --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
exit /b %ERRORLEVEL%

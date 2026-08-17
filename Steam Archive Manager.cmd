@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0portable-python\pythonw.exe" (
    "%~dp0portable-python\pythonw.exe" "%~dp0main.py" %*
    exit /b %ERRORLEVEL%
)

if exist "%~dp0portable-python\python.exe" (
    "%~dp0portable-python\python.exe" "%~dp0main.py" %*
    exit /b %ERRORLEVEL%
)

python "%~dp0main.py" %*

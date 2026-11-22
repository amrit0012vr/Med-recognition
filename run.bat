@echo off
echo ========================================================
echo       AI Medicine Recognition System - Startup
echo ========================================================
echo.

set PYTHON_CMD=python
where %PYTHON_CMD% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%USERPROFILE%\anaconda3\python.exe" (
        set PYTHON_CMD=%USERPROFILE%\anaconda3\python.exe
    )
)

echo Using Python: %PYTHON_CMD%
"%PYTHON_CMD%" app.py
pause

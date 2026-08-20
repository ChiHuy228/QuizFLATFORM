@echo off
setlocal

title AzulQuiz Server

echo.
echo ==========================================
echo              AZULQUIZ SERVER
echo ==========================================
echo.

REM -------------------------------------------------
REM Default port
REM -------------------------------------------------
if "%PORT%"=="" (
    set PORT=8000
)

echo [INFO] Starting AzulQuiz...
echo [INFO] Host: 0.0.0.0
echo [INFO] Port: %PORT%
echo.

REM -------------------------------------------------
REM Start Django WSGI using Waitress
REM -------------------------------------------------
python -m waitress ^
    --listen=0.0.0.0:%PORT% ^
    quizplatform.wsgi:application

REM -------------------------------------------------
REM Detect server failure
REM -------------------------------------------------
if errorlevel 1 (
    echo.
    echo [ERROR] AzulQuiz failed to start.
    echo.
    exit /b 1
)

endlocal
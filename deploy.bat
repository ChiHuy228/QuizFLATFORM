@echo off
setlocal

title AzulQuiz Deployment

echo.
echo ==========================================
echo           AZULQUIZ DEPLOYMENT
echo ==========================================
echo.

REM -------------------------------------------------
REM Step 1 - Django system check
REM -------------------------------------------------

echo [1/4] Checking Django configuration...
echo.

python manage.py check

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Django system check failed.
    echo Deployment stopped.
    echo ==========================================
    exit /b 1
)

echo.
echo [OK] Django configuration is valid.
echo.


REM -------------------------------------------------
REM Step 2 - Check migrations
REM -------------------------------------------------

echo [2/4] Checking model migrations...
echo.

python manage.py makemigrations --check --dry-run

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Model changes exist without migrations.
    echo.
    echo Run:
    echo python manage.py makemigrations
    echo.
    echo Then commit the migration files before deploying.
    echo ==========================================
    exit /b 1
)

echo.
echo [OK] Models and migrations are synchronized.
echo.


REM -------------------------------------------------
REM Step 3 - Apply migrations
REM -------------------------------------------------

echo [3/4] Applying database migrations...
echo.

python manage.py migrate --noinput

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Database migration failed.
    echo Deployment stopped.
    echo ==========================================
    exit /b 1
)

echo.
echo [OK] Database migrations completed.
echo.


REM -------------------------------------------------
REM Step 4 - Collect static files
REM -------------------------------------------------

echo [4/4] Collecting static files...
echo.

python manage.py collectstatic --noinput

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Static file collection failed.
    echo Deployment stopped.
    echo ==========================================
    exit /b 1
)

echo.
echo [OK] Static files collected.
echo.


REM -------------------------------------------------
REM Finish
REM -------------------------------------------------

echo.
echo ==========================================
echo     AZULQUIZ DEPLOYMENT PREPARED
echo ==========================================
echo.
echo Django check:        OK
echo Migration check:     OK
echo Database migration:  OK
echo Static files:        OK
echo.
echo Next command:
echo start.bat
echo.

endlocal
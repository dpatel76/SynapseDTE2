@echo off
REM Start Celery Worker service
echo Starting Celery Worker container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d celery-worker

REM Check if started
timeout /t 3 /nobreak >nul
docker-compose -f docker-compose.container.yml ps celery-worker | findstr "Up" >nul
if %errorlevel%==0 (
    echo Celery Worker started successfully
) else (
    echo Failed to start Celery Worker
    exit /b 1
)
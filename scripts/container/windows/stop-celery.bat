@echo off
REM Stop Celery Worker service
echo Stopping Celery Worker container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop celery-worker

if %errorlevel%==0 (
    echo Celery Worker stopped successfully
) else (
    echo Failed to stop Celery Worker
    exit /b 1
)
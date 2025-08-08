@echo off
REM Restart Celery Worker service
echo Restarting Celery Worker container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart celery-worker

if %errorlevel%==0 (
    echo Celery Worker restarted successfully
) else (
    echo Failed to restart Celery Worker
    exit /b 1
)
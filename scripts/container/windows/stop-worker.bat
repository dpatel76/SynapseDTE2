@echo off
REM Stop Worker service
echo Stopping Worker container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop worker

if %errorlevel%==0 (
    echo Worker stopped successfully
) else (
    echo Failed to stop Worker
    exit /b 1
)
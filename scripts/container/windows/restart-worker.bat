@echo off
REM Restart Worker service
echo Restarting Worker container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart worker

if %errorlevel%==0 (
    echo Worker restarted successfully
) else (
    echo Failed to restart Worker
    exit /b 1
)
@echo off
REM Restart Redis service
echo Restarting Redis container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart redis

if %errorlevel%==0 (
    echo Redis restarted successfully
) else (
    echo Failed to restart Redis
    exit /b 1
)
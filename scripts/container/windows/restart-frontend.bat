@echo off
REM Restart Frontend service
echo Restarting Frontend container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart frontend

if %errorlevel%==0 (
    echo Frontend restarted successfully
) else (
    echo Failed to restart Frontend
    exit /b 1
)
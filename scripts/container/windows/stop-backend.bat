@echo off
REM Stop Backend service
echo Stopping Backend container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop backend

if %errorlevel%==0 (
    echo Backend stopped successfully
) else (
    echo Failed to stop Backend
    exit /b 1
)
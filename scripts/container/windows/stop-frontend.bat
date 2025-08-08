@echo off
REM Stop Frontend service
echo Stopping Frontend container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop frontend

if %errorlevel%==0 (
    echo Frontend stopped successfully
) else (
    echo Failed to stop Frontend
    exit /b 1
)
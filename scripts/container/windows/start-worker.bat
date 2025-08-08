@echo off
REM Start Worker service
echo Starting Worker container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d worker

REM Check if started
timeout /t 3 /nobreak >nul
docker-compose -f docker-compose.container.yml ps worker | findstr "Up" >nul
if %errorlevel%==0 (
    echo Worker started successfully
) else (
    echo Failed to start Worker
    exit /b 1
)
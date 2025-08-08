@echo off
REM Restart Backend service
echo Restarting Backend container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart backend

if %errorlevel%==0 (
    echo Backend restarted successfully
    echo Waiting for Backend to be ready...
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:8001/api/v1/health >nul 2>&1
    if %errorlevel%==0 (
        echo Backend is responding
    ) else (
        echo Backend restarted but may not be fully ready yet
    )
) else (
    echo Failed to restart Backend
    exit /b 1
)
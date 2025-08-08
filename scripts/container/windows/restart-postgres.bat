@echo off
REM Restart PostgreSQL service
echo Restarting PostgreSQL container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart postgres

if %errorlevel%==0 (
    echo PostgreSQL restarted successfully
) else (
    echo Failed to restart PostgreSQL
    exit /b 1
)
@echo off
REM Stop PostgreSQL service
echo Stopping PostgreSQL container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop postgres

if %errorlevel%==0 (
    echo PostgreSQL stopped successfully
) else (
    echo Failed to stop PostgreSQL
    exit /b 1
)
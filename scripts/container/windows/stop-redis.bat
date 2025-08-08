@echo off
REM Stop Redis service
echo Stopping Redis container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop redis

if %errorlevel%==0 (
    echo Redis stopped successfully
) else (
    echo Failed to stop Redis
    exit /b 1
)
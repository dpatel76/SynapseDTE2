@echo off
REM Stop Nginx service
echo Stopping Nginx container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml stop nginx

if %errorlevel%==0 (
    echo Nginx stopped successfully
) else (
    echo Failed to stop Nginx
    exit /b 1
)
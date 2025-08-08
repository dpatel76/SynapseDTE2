@echo off
REM Restart Nginx service
echo Restarting Nginx container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml restart nginx

if %errorlevel%==0 (
    echo Nginx restarted successfully
    echo Nginx available at: http://localhost:81
) else (
    echo Failed to restart Nginx
    exit /b 1
)
@echo off
REM Start Nginx service
echo Starting Nginx container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d nginx

REM Check if started
timeout /t 2 /nobreak >nul
curl -s http://localhost:81 >nul 2>&1
if %errorlevel%==0 (
    echo Nginx started successfully
    echo Nginx available at: http://localhost:81
) else (
    echo Nginx started but may not be fully ready yet
)
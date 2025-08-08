@echo off
REM Start Frontend service
echo Starting Frontend container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d frontend

REM Wait for service to be ready
echo Waiting for Frontend to be ready...
set timeout=30
:wait_loop
curl -s http://localhost:3001 >nul 2>&1
if %errorlevel%==0 (
    echo Frontend is ready!
    exit /b 0
)
timeout /t 2 /nobreak >nul
set /a timeout=%timeout%-2
if %timeout% gtr 0 goto wait_loop

echo Frontend failed to start within 30 seconds
exit /b 1
@echo off
REM Start Backend service
echo Starting Backend container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d backend

REM Wait for service to be ready
echo Waiting for Backend to be ready...
set timeout=60
:wait_loop
curl -s http://localhost:8001/api/v1/health >nul 2>&1
if %errorlevel%==0 (
    echo Backend is ready!
    exit /b 0
)
timeout /t 2 /nobreak >nul
set /a timeout=%timeout%-2
if %timeout% gtr 0 goto wait_loop

echo Backend failed to start within 60 seconds
exit /b 1
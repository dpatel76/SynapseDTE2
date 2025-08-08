@echo off
REM Start Redis service
echo Starting Redis container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d redis

REM Wait for service to be healthy
echo Waiting for Redis to be healthy...
set timeout=30
:wait_loop
docker-compose -f docker-compose.container.yml exec redis redis-cli --no-auth-warning -a synapse_redis_password ping >nul 2>&1
if %errorlevel%==0 (
    echo Redis is ready!
    exit /b 0
)
timeout /t 1 /nobreak >nul
set /a timeout=%timeout%-1
if %timeout% gtr 0 goto wait_loop

echo Redis failed to start within 30 seconds
exit /b 1
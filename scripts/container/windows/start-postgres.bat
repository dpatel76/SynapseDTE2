@echo off
REM Start PostgreSQL service
echo Starting PostgreSQL container...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2
docker-compose -f docker-compose.container.yml up -d postgres

REM Wait for service to be healthy
echo Waiting for PostgreSQL to be healthy...
set timeout=30
:wait_loop
docker-compose -f docker-compose.container.yml exec postgres pg_isready -U synapse_user >nul 2>&1
if %errorlevel%==0 (
    echo PostgreSQL is ready!
    exit /b 0
)
timeout /t 1 /nobreak >nul
set /a timeout=%timeout%-1
if %timeout% gtr 0 goto wait_loop

echo PostgreSQL failed to start within 30 seconds
exit /b 1
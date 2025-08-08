@echo off
REM Start Temporal services (postgres, server, ui)
echo Starting Temporal services...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2

REM Start Temporal PostgreSQL first
echo Starting Temporal PostgreSQL...
docker-compose -f docker-compose.container.yml up -d temporal-postgres

REM Wait for Temporal PostgreSQL to be ready
echo Waiting for Temporal PostgreSQL to be healthy...
timeout /t 5 /nobreak >nul

REM Start Temporal Server
echo Starting Temporal Server...
docker-compose -f docker-compose.container.yml up -d temporal

REM Wait for Temporal Server to be ready
echo Waiting for Temporal Server to be ready...
timeout /t 10 /nobreak >nul

REM Start Temporal UI
echo Starting Temporal UI...
docker-compose -f docker-compose.container.yml up -d temporal-ui

REM Check if all services are running
timeout /t 5 /nobreak >nul
docker-compose -f docker-compose.container.yml ps | findstr "temporal.*Up" >nul
if %errorlevel%==0 (
    echo All Temporal services started successfully
    echo Temporal UI available at: http://localhost:8089
) else (
    echo Some Temporal services may not have started properly
    docker-compose -f docker-compose.container.yml ps | findstr temporal
)
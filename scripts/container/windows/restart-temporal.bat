@echo off
REM Restart Temporal services
echo Restarting Temporal services...
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2

echo Restarting Temporal PostgreSQL...
docker-compose -f docker-compose.container.yml restart temporal-postgres
timeout /t 5 /nobreak >nul

echo Restarting Temporal Server...
docker-compose -f docker-compose.container.yml restart temporal
timeout /t 10 /nobreak >nul

echo Restarting Temporal UI...
docker-compose -f docker-compose.container.yml restart temporal-ui

echo All Temporal services restarted
echo Temporal UI available at: http://localhost:8089
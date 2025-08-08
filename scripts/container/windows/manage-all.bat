@echo off
setlocal enabledelayedexpansion

REM Master script to manage all SynapseDTE2 container services
REM Usage: manage-all.bat [start|stop|restart|status]

REM Change to project directory
cd /d C:\Users\%USERNAME%\code\projects\SynapseDTE2

REM Docker compose file
set COMPOSE_FILE=docker-compose.container.yml

REM Check command argument
if "%1"=="" goto :usage
if /i "%1"=="start" goto :start_all
if /i "%1"=="stop" goto :stop_all
if /i "%1"=="restart" goto :restart_all
if /i "%1"=="status" goto :status_all
if /i "%1"=="logs" goto :logs_all
if /i "%1"=="clean" goto :clean_all
goto :usage

:start_all
echo ========================================
echo Starting all SynapseDTE2 services...
echo ========================================
echo.

echo Starting core infrastructure...
docker-compose -f %COMPOSE_FILE% up -d postgres redis
if %errorlevel% neq 0 (
    echo Failed to start core infrastructure
    exit /b 1
)

REM Wait for databases to be ready
echo Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul
:wait_postgres
docker-compose -f %COMPOSE_FILE% exec postgres pg_isready -U synapse_user >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto :wait_postgres
)
echo PostgreSQL is ready!

echo Waiting for Redis to be ready...
:wait_redis
docker-compose -f %COMPOSE_FILE% exec redis redis-cli --no-auth-warning -a synapse_redis_password ping >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto :wait_redis
)
echo Redis is ready!

REM Start Temporal services
echo Starting Temporal services...
docker-compose -f %COMPOSE_FILE% up -d temporal-postgres
timeout /t 5 /nobreak >nul
docker-compose -f %COMPOSE_FILE% up -d temporal
timeout /t 10 /nobreak >nul
docker-compose -f %COMPOSE_FILE% up -d temporal-ui

REM Start application services
echo Starting application services...
docker-compose -f %COMPOSE_FILE% up -d backend celery-worker worker

REM Wait for backend to be ready
echo Waiting for Backend to be ready...
timeout /t 10 /nobreak >nul
:wait_backend
curl -s http://localhost:8001/api/v1/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto :wait_backend
)
echo Backend is ready!

REM Start frontend and nginx
echo Starting web services...
docker-compose -f %COMPOSE_FILE% up -d frontend nginx

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo All services started successfully!
echo ========================================
echo.
echo Access points:
echo   - Frontend: http://localhost:3001
echo   - Backend API: http://localhost:8001
echo   - Temporal UI: http://localhost:8089
echo   - Nginx Proxy: http://localhost:81
goto :end

:stop_all
echo ========================================
echo Stopping all SynapseDTE2 services...
echo ========================================
echo.

REM Stop in reverse order
echo Stopping web services...
docker-compose -f %COMPOSE_FILE% stop nginx frontend

echo Stopping application services...
docker-compose -f %COMPOSE_FILE% stop worker celery-worker backend

echo Stopping Temporal services...
docker-compose -f %COMPOSE_FILE% stop temporal-ui temporal temporal-postgres

echo Stopping core infrastructure...
docker-compose -f %COMPOSE_FILE% stop redis postgres

echo.
echo ========================================
echo All services stopped successfully!
echo ========================================
goto :end

:restart_all
echo ========================================
echo Restarting all SynapseDTE2 services...
echo ========================================
echo.

call :stop_all
echo.
timeout /t 3 /nobreak >nul
call :start_all
goto :end

:status_all
echo ========================================
echo SynapseDTE2 Services Status
echo ========================================
echo.

REM Check each service
set services=postgres redis temporal-postgres temporal temporal-ui backend frontend celery-worker worker nginx
set descriptions=PostgreSQL Redis "Temporal DB" "Temporal Server" "Temporal UI" "Backend API" "Frontend Web" "Celery Worker" "Temporal Worker" "Nginx Proxy"

set i=0
for %%s in (%services%) do (
    set /a i+=1
    set service=%%s
    
    docker-compose -f %COMPOSE_FILE% ps !service! 2>nul | findstr "Up" >nul
    if !errorlevel!==0 (
        echo [OK] !service! is running
    ) else (
        echo [X] !service! is stopped
    )
)

echo.
echo Container Details:
docker-compose -f %COMPOSE_FILE% ps
goto :end

:logs_all
echo ========================================
echo Showing logs for all services (Ctrl+C to exit)...
echo ========================================
docker-compose -f %COMPOSE_FILE% logs -f
goto :end

:clean_all
echo ========================================
echo WARNING: This will stop and remove all containers.
echo Data volumes will be preserved.
echo ========================================
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    echo Cleaning up all containers...
    docker-compose -f %COMPOSE_FILE% down
    echo Cleanup complete!
) else (
    echo Cleanup cancelled.
)
goto :end

:usage
echo ========================================
echo SynapseDTE2 Container Management
echo ========================================
echo.
echo Usage: %~nx0 [start^|stop^|restart^|status^|logs^|clean]
echo.
echo Commands:
echo   start   - Start all services
echo   stop    - Stop all services
echo   restart - Restart all services
echo   status  - Show status of all services
echo   logs    - Show logs from all services
echo   clean   - Stop and remove all containers (preserves data)
echo.
echo Individual service scripts are also available:
echo   - start-^<service^>.bat, stop-^<service^>.bat, restart-^<service^>.bat
echo   - Services: postgres, redis, backend, frontend, celery, temporal, worker, nginx
exit /b 1

:end
endlocal
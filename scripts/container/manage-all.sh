#!/bin/bash

# Master script to manage all SynapseDTE2 container services
# Usage: ./manage-all.sh [start|stop|restart|status]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project directory
cd /Users/dineshpatel/code/projects/SynapseDTE2

# Docker compose file
COMPOSE_FILE="docker-compose.container.yml"

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a service is running
check_service() {
    service=$1
    if docker-compose -f $COMPOSE_FILE ps $service 2>/dev/null | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be healthy
wait_for_service() {
    service=$1
    timeout=$2
    check_cmd=$3
    
    echo "Waiting for $service to be ready..."
    while [ $timeout -gt 0 ]; do
        if eval $check_cmd >/dev/null 2>&1; then
            print_color "$GREEN" "✅ $service is ready!"
            return 0
        fi
        sleep 2
        ((timeout-=2))
    done
    
    print_color "$YELLOW" "⚠️  $service may not be fully ready"
    return 1
}

# Start all services
start_all() {
    print_color "$BLUE" "🚀 Starting all SynapseDTE2 services..."
    echo ""
    
    # Start core infrastructure first
    print_color "$YELLOW" "Starting core infrastructure..."
    docker-compose -f $COMPOSE_FILE up -d postgres redis
    
    # Wait for databases to be ready
    wait_for_service "PostgreSQL" 30 "docker-compose -f $COMPOSE_FILE exec postgres pg_isready -U synapse_user"
    wait_for_service "Redis" 30 "docker-compose -f $COMPOSE_FILE exec redis redis-cli --no-auth-warning -a synapse_redis_password ping"
    
    # Start Temporal services
    print_color "$YELLOW" "Starting Temporal services..."
    docker-compose -f $COMPOSE_FILE up -d temporal-postgres
    sleep 5
    docker-compose -f $COMPOSE_FILE up -d temporal
    sleep 10
    docker-compose -f $COMPOSE_FILE up -d temporal-ui
    
    # Start application services
    print_color "$YELLOW" "Starting application services..."
    docker-compose -f $COMPOSE_FILE up -d backend celery-worker worker
    
    # Wait for backend to be ready
    wait_for_service "Backend" 60 "curl -s http://localhost:8001/api/v1/health"
    
    # Start frontend and nginx
    print_color "$YELLOW" "Starting web services..."
    docker-compose -f $COMPOSE_FILE up -d frontend nginx
    
    wait_for_service "Frontend" 30 "curl -s http://localhost:3001"
    
    echo ""
    print_color "$GREEN" "✅ All services started successfully!"
    echo ""
    print_color "$BLUE" "Access points:"
    echo "  - Frontend: http://localhost:3001"
    echo "  - Backend API: http://localhost:8001"
    echo "  - Temporal UI: http://localhost:8089"
    echo "  - Nginx Proxy: http://localhost:81"
}

# Stop all services
stop_all() {
    print_color "$BLUE" "🛑 Stopping all SynapseDTE2 services..."
    echo ""
    
    # Stop in reverse order
    print_color "$YELLOW" "Stopping web services..."
    docker-compose -f $COMPOSE_FILE stop nginx frontend
    
    print_color "$YELLOW" "Stopping application services..."
    docker-compose -f $COMPOSE_FILE stop worker celery-worker backend
    
    print_color "$YELLOW" "Stopping Temporal services..."
    docker-compose -f $COMPOSE_FILE stop temporal-ui temporal temporal-postgres
    
    print_color "$YELLOW" "Stopping core infrastructure..."
    docker-compose -f $COMPOSE_FILE stop redis postgres
    
    echo ""
    print_color "$GREEN" "✅ All services stopped successfully!"
}

# Restart all services
restart_all() {
    print_color "$BLUE" "🔄 Restarting all SynapseDTE2 services..."
    echo ""
    
    stop_all
    echo ""
    sleep 3
    start_all
}

# Show status of all services
status_all() {
    print_color "$BLUE" "📊 SynapseDTE2 Services Status"
    echo ""
    
    services=(
        "postgres:PostgreSQL Database"
        "redis:Redis Cache"
        "temporal-postgres:Temporal Database"
        "temporal:Temporal Server"
        "temporal-ui:Temporal UI"
        "backend:Backend API"
        "frontend:Frontend Web"
        "celery-worker:Celery Worker"
        "worker:Temporal Worker"
        "nginx:Nginx Proxy"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name service_desc <<< "$service_info"
        
        if check_service $service_name; then
            print_color "$GREEN" "✅ $service_desc is running"
        else
            print_color "$RED" "❌ $service_desc is stopped"
        fi
    done
    
    echo ""
    print_color "$BLUE" "Container Details:"
    docker-compose -f $COMPOSE_FILE ps
}

# Show logs for all services
logs_all() {
    print_color "$BLUE" "📝 Showing logs for all services (Ctrl+C to exit)..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Clean up (stop and remove containers)
clean_all() {
    print_color "$YELLOW" "⚠️  This will stop and remove all containers. Data volumes will be preserved."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_color "$BLUE" "🧹 Cleaning up all containers..."
        docker-compose -f $COMPOSE_FILE down
        print_color "$GREEN" "✅ Cleanup complete!"
    else
        print_color "$YELLOW" "Cleanup cancelled."
    fi
}

# Main script logic
case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status_all
        ;;
    logs)
        logs_all
        ;;
    clean)
        clean_all
        ;;
    *)
        print_color "$BLUE" "SynapseDTE2 Container Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show status of all services"
        echo "  logs    - Show logs from all services"
        echo "  clean   - Stop and remove all containers (preserves data)"
        echo ""
        echo "Individual service scripts are also available in this directory:"
        echo "  - start-<service>.sh, stop-<service>.sh, restart-<service>.sh"
        echo "  - Services: postgres, redis, backend, frontend, celery, temporal, worker, nginx"
        exit 1
        ;;
esac
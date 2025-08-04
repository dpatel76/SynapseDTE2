#!/bin/bash
#
# Run Docker tests in complete isolation from production services
#

set -e

# Configuration
ISOLATED_PROJECT="synapse-isolated-test"
ISOLATED_NETWORK="synapse-test-network"
TEST_COMPOSE_FILE="docker-compose.test.yml"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${2}${1}${NC}"
}

# Check for existing services
check_existing_services() {
    print_status "🔍 Checking for existing services..." "$YELLOW"
    
    # Check if production services are running
    PROD_RUNNING=$(docker-compose ps -q | wc -l)
    
    if [ "$PROD_RUNNING" -gt 0 ]; then
        print_status "⚠️  Production services detected. Tests will run in isolation." "$YELLOW"
        echo "   Using project: $ISOLATED_PROJECT"
        echo "   Using compose file: $TEST_COMPOSE_FILE"
        echo ""
    fi
}

# Create isolated network
create_isolated_network() {
    print_status "🌐 Creating isolated network..." "$YELLOW"
    docker network create $ISOLATED_NETWORK 2>/dev/null || true
}

# Run tests in isolation
run_isolated_tests() {
    print_status "🚀 Starting isolated test environment..." "$GREEN"
    
    # Export environment variables
    export COMPOSE_PROJECT_NAME=$ISOLATED_PROJECT
    export DOCKER_NETWORK=$ISOLATED_NETWORK
    
    # Use test-specific compose file
    export COMPOSE_FILE=$TEST_COMPOSE_FILE
    
    # Run tests with isolated configuration
    python tests/docker/run_all_tests.py \
        --project-name "$ISOLATED_PROJECT" \
        --compose-file "$TEST_COMPOSE_FILE" \
        "$@"
}

# Cleanup isolated environment
cleanup_isolated() {
    print_status "🧹 Cleaning up isolated environment..." "$YELLOW"
    
    # Stop and remove isolated containers
    docker-compose -p $ISOLATED_PROJECT -f $TEST_COMPOSE_FILE down -v --remove-orphans
    
    # Remove isolated network
    docker network rm $ISOLATED_NETWORK 2>/dev/null || true
    
    print_status "✅ Cleanup completed" "$GREEN"
}

# Main execution
main() {
    print_status "=====================================" "$GREEN"
    print_status "🔒 Isolated Docker Test Runner" "$GREEN"
    print_status "=====================================" "$GREEN"
    echo ""
    
    # Check existing services
    check_existing_services
    
    # Create isolated environment
    create_isolated_network
    
    # Set trap for cleanup
    trap cleanup_isolated EXIT
    
    # Run tests
    run_isolated_tests "$@"
}

# Run main function
main "$@"
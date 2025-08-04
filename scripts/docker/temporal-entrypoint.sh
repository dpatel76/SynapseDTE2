#!/bin/bash
set -e

echo "Starting Temporal setup..."

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    until pg_isready -h ${POSTGRES_HOST:-temporal-postgres-container} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-temporal}; do
        echo "PostgreSQL not ready yet, waiting..."
        sleep 2
    done
    echo "PostgreSQL is ready!"
}

# Function to check if schema exists
check_schema_exists() {
    local db=$1
    local result=$(PGPASSWORD=${POSTGRES_PWD:-temporal_password} psql -h ${POSTGRES_HOST:-temporal-postgres-container} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-temporal} -d $db -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_version');")
    echo $result
}

# Wait for PostgreSQL
wait_for_postgres

# Setup environment
export POSTGRES_HOST=${POSTGRES_HOST:-temporal-postgres-container}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export POSTGRES_USER=${POSTGRES_USER:-temporal}
export POSTGRES_PWD=${POSTGRES_PWD:-temporal_password}

# Check if temporal schema is already set up
if [ "$(check_schema_exists temporal)" = "f" ]; then
    echo "Setting up Temporal schema..."
    temporal-sql-tool setup-schema -v 0.0
    temporal-sql-tool update-schema -d /etc/temporal/schema/postgresql/v12/temporal/versioned
else
    echo "Temporal schema already exists"
fi

# Check if temporal_visibility schema is already set up
if [ "$(check_schema_exists temporal_visibility)" = "f" ]; then
    echo "Setting up Temporal visibility schema..."
    temporal-sql-tool --db temporal_visibility setup-schema -v 0.0
    temporal-sql-tool --db temporal_visibility update-schema -d /etc/temporal/schema/postgresql/v12/visibility/versioned
else
    echo "Temporal visibility schema already exists"
fi

echo "Temporal setup complete, starting server..."

# Start the Temporal server
exec /entrypoint.sh autosetup
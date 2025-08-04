#!/bin/bash
set -e

echo "Initializing Temporal database schema..."

# Wait for Temporal PostgreSQL to be ready
echo "Waiting for Temporal PostgreSQL..."
until docker exec temporal-postgres-container pg_isready -U temporal; do
  echo "Temporal PostgreSQL not ready yet, waiting..."
  sleep 2
done

echo "Temporal PostgreSQL is ready!"

# Run temporal-sql-tool to set up schema
echo "Setting up Temporal schema..."

# Create initial schema version
docker run --rm \
  --network synapse-container-network \
  temporalio/admin-tools:1.22.4 \
  -ep temporal-postgres-container:5432 \
  -u temporal \
  -pw temporal_password \
  --pl postgres12 \
  --db temporal \
  setup-schema -v 0.0

# Update schema to latest version
docker run --rm \
  --network synapse-container-network \
  temporalio/admin-tools:1.22.4 \
  -ep temporal-postgres-container:5432 \
  -u temporal \
  -pw temporal_password \
  --pl postgres12 \
  --db temporal \
  update-schema -d /etc/temporal/schema/postgresql/v12/temporal/versioned

# Setup visibility schema
docker run --rm \
  --network synapse-container-network \
  temporalio/admin-tools:1.22.4 \
  -ep temporal-postgres-container:5432 \
  -u temporal \
  -pw temporal_password \
  --pl postgres12 \
  --db temporal_visibility \
  setup-schema -v 0.0

docker run --rm \
  --network synapse-container-network \
  temporalio/admin-tools:1.22.4 \
  -ep temporal-postgres-container:5432 \
  -u temporal \
  -pw temporal_password \
  --pl postgres12 \
  --db temporal_visibility \
  update-schema -d /etc/temporal/schema/postgresql/v12/visibility/versioned

echo "Temporal schema setup complete!"

# Verify schema
echo "Verifying Temporal schema..."
docker exec temporal-postgres-container psql -U temporal -d temporal -c "SELECT * FROM schema_version LIMIT 1;"
docker exec temporal-postgres-container psql -U temporal -d temporal_visibility -c "SELECT * FROM schema_update_history LIMIT 1;"
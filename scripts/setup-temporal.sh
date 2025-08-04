#!/bin/bash
set -e

echo "Setting up Temporal database schema..."

# Setup schema version
docker run --rm --network temporal-container-network \
  temporalio/admin-tools:1.22.4 \
  -ep temporal-postgres:5432 \
  -u temporal \
  -pw temporal_password \
  --pl postgres12 \
  --db temporal \
  setup-schema -v 0.0

# Update schema to latest version
docker run --rm --network temporal-container-network \
  temporalio/admin-tools:1.22.4 \
  -ep temporal-postgres:5432 \
  -u temporal \
  -pw temporal_password \
  --pl postgres12 \
  --db temporal \
  update-schema -d /etc/temporal/schema

echo "Temporal database schema setup complete!"
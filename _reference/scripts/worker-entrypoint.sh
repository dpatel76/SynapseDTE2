#!/bin/bash
set -e

echo "Starting SynapseDTE Temporal Worker..."

# Wait for database
echo "Waiting for database..."
while ! pg_isready -h ${DATABASE_HOST:-localhost} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres}; do
  sleep 1
done
echo "Database is ready!"

# Extract host and port from TEMPORAL_HOST
TEMPORAL_HOST_ONLY="${TEMPORAL_HOST%:*}"
TEMPORAL_PORT="${TEMPORAL_HOST#*:}"

# Use default port if not specified
if [ "$TEMPORAL_HOST_ONLY" = "$TEMPORAL_HOST" ]; then
  TEMPORAL_HOST_ONLY="$TEMPORAL_HOST"
  TEMPORAL_PORT="7233"
fi

# Wait for Temporal server
echo "Waiting for Temporal server at $TEMPORAL_HOST_ONLY:$TEMPORAL_PORT..."
while ! nc -z $TEMPORAL_HOST_ONLY $TEMPORAL_PORT; do
  sleep 1
done
echo "Temporal server is ready!"

# Configure worker
export TEMPORAL_WORKER_ENABLED=true
export PYTHONPATH=/app

# Start worker with signal handling
echo "Starting Temporal worker..."
exec python -m app.temporal.worker
#!/bin/bash
set -e

echo "Starting SynapseDTE Backend..."

# Wait for database
echo "Waiting for database..."
while ! pg_isready -h ${DATABASE_HOST:-localhost} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres}; do
  echo "Database not ready yet, waiting..."
  sleep 2
done
echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
export DOCKER_CONTAINER=1

# Use Python migration script for better control
if [ -f /app/scripts/docker/run_migrations.py ]; then
  python /app/scripts/docker/run_migrations.py
else
  # Fallback to direct alembic command
  echo "Migration script not found, using alembic directly..."
  alembic upgrade head || echo "Migration failed, but continuing..."
fi

# Load seed data if needed
echo "Checking seed data..."
if [ -f /app/scripts/docker/load_seed_data.py ]; then
  python /app/scripts/docker/load_seed_data.py || echo "Seed data loading failed, but continuing..."
else
  echo "Seed data script not found, skipping..."
fi

# Start application
echo "Starting FastAPI application..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers ${WORKERS:-2} \
  --access-log \
  --log-config /app/logging.json
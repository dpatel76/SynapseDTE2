#!/bin/bash
set -e

echo "Starting SynapseDTE Backend (Container Mode)..."

# Wait for postgres
echo "Waiting for PostgreSQL..."
while ! nc -z ${DATABASE_HOST:-postgres} ${DATABASE_PORT:-5432}; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Skip Alembic migrations since they're broken
echo "Skipping database migrations (handled by SQL scripts)..."

# Start the application with fewer workers to avoid resource issues
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --reload
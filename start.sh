#!/bin/bash
set -e

echo "Starting SynapseDTE Backend..."

# Wait for postgres
echo "Waiting for PostgreSQL..."
while ! nc -z ${DATABASE_HOST:-postgres} ${DATABASE_PORT:-5432}; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Create test user if needed
echo "Ensuring test user exists..."
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def create_test_user():
    engine = create_async_engine('${DATABASE_URL}')
    async with engine.begin() as conn:
        # Check if user exists
        result = await conn.execute(text(\"SELECT 1 FROM users WHERE email = 'tester@example.com'\"))
        if not result.first():
            # Insert test user with bcrypt hash for password123
            await conn.execute(text(\"\"\"
                INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) 
                VALUES ('tester@example.com', '\$2b\$12\$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true)
            \"\"\"))
            print('Test user created')
        else:
            print('Test user already exists')
    await engine.dispose()

asyncio.run(create_test_user())
"

# Start the application
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}
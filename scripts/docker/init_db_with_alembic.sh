#!/bin/bash
# Initialize database using Alembic migrations

echo "Waiting for database to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Run Alembic migrations to create all tables
echo "Running Alembic migrations..."
cd /app
alembic upgrade head

# Insert test user with bcrypt password
echo "Creating test user..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME <<EOF
-- Insert test user if not exists
INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) 
VALUES ('tester@example.com', '\$2b\$12\$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = '\$2b\$12\$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie';
EOF

echo "Database initialization complete!"
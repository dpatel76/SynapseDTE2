#!/bin/bash
#
# Database setup for Docker testing
# This script initializes the database without relying on broken migrations
#

set -e

# Configuration
DB_HOST="${DATABASE_HOST:-postgres}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-synapse_dt}"
DB_USER="${DATABASE_USER:-synapse_user}"
DB_PASSWORD="${DATABASE_PASSWORD:-synapse_password}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${2}${1}${NC}"
}

# Wait for database
print_status "⏳ Waiting for database to be ready..." "$YELLOW"
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    sleep 1
done
print_status "✅ Database is ready!" "$GREEN"

# Check if database is already initialized
print_status "🔍 Checking database initialization status..." "$YELLOW"

TABLES_EXIST=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('users', 'test_cycles', 'workflow_phases');
" 2>/dev/null || echo "0")

if [ "$TABLES_EXIST" -ge "3" ]; then
    print_status "✅ Database already initialized with $TABLES_EXIST core tables" "$GREEN"
    
    # Update alembic version to prevent migration attempts
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        INSERT INTO alembic_version (version_num) 
        VALUES ('manual_schema_v1') 
        ON CONFLICT (version_num) DO NOTHING;
    " 2>/dev/null || true
    
    exit 0
fi

# Initialize database
print_status "📦 Initializing database schema..." "$YELLOW"

# Apply initialization SQL if available
if [ -f "/app/scripts/db/init/01-init-schema.sql" ]; then
    print_status "   Applying schema from init script..." "$YELLOW"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "/app/scripts/db/init/01-init-schema.sql" || {
        print_status "❌ Failed to apply schema" "$RED"
        exit 1
    }
elif [ -f "/docker-entrypoint-initdb.d/01-init-schema.sql" ]; then
    print_status "   Applying schema from docker-entrypoint-initdb.d..." "$YELLOW"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "/docker-entrypoint-initdb.d/01-init-schema.sql" || {
        print_status "❌ Failed to apply schema" "$RED"
        exit 1
    }
else
    print_status "⚠️  No initialization script found, trying migrations..." "$YELLOW"
    
    # Try to run migrations
    cd /app
    alembic upgrade head || {
        print_status "❌ Migrations failed" "$RED"
        
        # As a last resort, create minimal schema
        print_status "🔧 Creating minimal schema..." "$YELLOW"
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Minimal schema for testing
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('manual_minimal_v1');

-- Test user
INSERT INTO users (email, password_hash, first_name, last_name, role)
VALUES ('admin@test.local', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Test', 'Admin', 'admin')
ON CONFLICT DO NOTHING;
EOF
    }
fi

print_status "✅ Database initialization completed!" "$GREEN"

# Verify initialization
FINAL_TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
    SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
")

print_status "📊 Database has $FINAL_TABLE_COUNT tables" "$GREEN"
#!/bin/bash
#
# Export current database schema and sample data for Docker testing
#

set -e

# Configuration - adjust these for your environment
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="synapse_dt"
DB_USER="synapse_user"
EXPORT_DIR="./docker/postgres"
EXPORT_FILE="init-db.sql"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${2}${1}${NC}"
}

# Create export directory
mkdir -p "$EXPORT_DIR"

print_status "📦 Exporting database schema and data..." "$YELLOW"

# Export schema only (no data)
print_status "   Exporting schema..." "$YELLOW"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --schema-only \
    --no-owner \
    --no-privileges \
    --if-exists \
    --clean \
    > "$EXPORT_DIR/01-schema.sql"

# Export essential data (lookups, configurations, etc.)
print_status "   Exporting essential data..." "$YELLOW"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --data-only \
    --no-owner \
    --no-privileges \
    --table=alembic_version \
    --table=users \
    --table=roles \
    --table=permissions \
    --table=configurations \
    > "$EXPORT_DIR/02-essential-data.sql" 2>/dev/null || true

# Export sample test data (optional)
if [ "$1" == "--with-test-data" ]; then
    print_status "   Exporting test data..." "$YELLOW"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --data-only \
        --no-owner \
        --no-privileges \
        --table=test_cycles \
        --table=test_scenarios \
        --table=test_cases \
        > "$EXPORT_DIR/03-test-data.sql" 2>/dev/null || true
fi

# Combine all SQL files
print_status "   Creating combined init script..." "$YELLOW"
cat > "$EXPORT_DIR/$EXPORT_FILE" << 'EOF'
-- SynapseDTE Database Initialization Script
-- Generated on: $(date)

-- Ensure we're using the correct database
\c synapse_dt;

-- Set client encoding
SET client_encoding = 'UTF8';

EOF

# Append schema
cat "$EXPORT_DIR/01-schema.sql" >> "$EXPORT_DIR/$EXPORT_FILE"

# Append data files if they exist
for file in "$EXPORT_DIR"/02-*.sql "$EXPORT_DIR"/03-*.sql; do
    if [ -f "$file" ]; then
        echo -e "\n-- Data from $(basename $file)" >> "$EXPORT_DIR/$EXPORT_FILE"
        cat "$file" >> "$EXPORT_DIR/$EXPORT_FILE"
    fi
done

# Add test user creation for containerized testing
cat >> "$EXPORT_DIR/$EXPORT_FILE" << 'EOF'

-- Create test users for containerized testing
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
VALUES 
    ('admin@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Test', 'Admin', 'admin', true, NOW(), NOW()),
    ('user@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Test', 'User', 'user', true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Update sequences to avoid conflicts
SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 0) + 1, false);
EOF

# Clean up temporary files
rm -f "$EXPORT_DIR"/01-*.sql "$EXPORT_DIR"/02-*.sql "$EXPORT_DIR"/03-*.sql

print_status "✅ Database export completed!" "$GREEN"
print_status "   Schema exported to: $EXPORT_DIR/$EXPORT_FILE" "$GREEN"
print_status "   File size: $(du -h "$EXPORT_DIR/$EXPORT_FILE" | cut -f1)" "$GREEN"

# Create Docker entrypoint script
cat > "$EXPORT_DIR/docker-entrypoint-initdb.d/01-init.sh" << 'EOF'
#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Apply the initialization script
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init-db.sql

echo "Database initialization completed!"
EOF

chmod +x "$EXPORT_DIR/docker-entrypoint-initdb.d/01-init.sh"

print_status "\n📝 Next steps:" "$YELLOW"
print_status "1. Review the exported schema: $EXPORT_DIR/$EXPORT_FILE" "$YELLOW"
print_status "2. Update docker-compose.yml to mount this directory" "$YELLOW"
print_status "3. The database will be initialized automatically on container start" "$YELLOW"
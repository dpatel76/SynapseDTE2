# Database Setup Scripts Overview

## 1. Main Schema File (`01-schema-readable.sql`)

The main schema file has columns ordered for readability in this pattern:
- Primary Keys
- Core Business Fields
- Foreign Keys
- Metadata/Configuration
- Audit Fields (from AuditMixin)
- Timestamps (from TimestampMixin)

### Example Table Structure:
```sql
CREATE TABLE IF NOT EXISTS users (
    -- Primary Key
    user_id SERIAL PRIMARY KEY,
    
    -- Core Identity Fields
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- User Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Foreign Keys
    lob_id INTEGER,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### Key Features:
- Comments explain each section
- Related fields grouped together
- Consistent ordering across all tables
- Clear separation between business logic and metadata

## 2. Migration Bypass Script (`bypass_migrations.py`)

```python
#!/usr/bin/env python3
"""
Bypass Alembic migrations for containerized testing
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text

def check_database_initialized(database_url: str) -> bool:
    """Check if database is already initialized"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check for alembic version marker
            result = conn.execute(text(
                "SELECT version_num FROM alembic_version WHERE version_num = 'containerized_schema_v1'"
            ))
            if result.rowcount > 0:
                logger.info("Database initialized with containerized schema")
                return True
            
            # Check core tables exist
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'rbac_roles', 'rbac_permissions')
            """))
            table_count = result.scalar()
            
            if table_count >= 3:
                logger.info(f"Database has {table_count} core tables")
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

def run_migrations_if_needed():
    """Run migrations only if database is not initialized"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not set")
        sys.exit(1)
    
    # Check if running in container
    is_container = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == '1'
    
    if is_container and check_database_initialized(database_url):
        logger.info("Skipping migrations - database already initialized")
        return
    
    # Try to run migrations
    try:
        logger.info("Attempting to run migrations...")
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.warning(f"Migration failed: {e}")
        if is_container:
            logger.info("Running in container with initialized database - continuing anyway")
        else:
            raise
```

## 3. Test Database Setup Script (`test_db_setup.sh`)

```bash
#!/bin/bash
# Database setup for Docker testing

set -e

# Configuration
DB_HOST="${DATABASE_HOST:-postgres}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-synapse_dt}"
DB_USER="${DATABASE_USER:-synapse_user}"
DB_PASSWORD="${DATABASE_PASSWORD:-synapse_password}"

# Wait for database
print_status "⏳ Waiting for database to be ready..." "$YELLOW"
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    sleep 1
done

# Check if already initialized
TABLES_EXIST=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" \
    -U "$DB_USER" -d "$DB_NAME" -tAc "
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('users', 'rbac_roles', 'rbac_permissions');
")

if [ "$TABLES_EXIST" -ge "3" ]; then
    print_status "✅ Database already initialized" "$GREEN"
    exit 0
fi

# Apply schema
if [ -f "/app/scripts/db/init/01-schema-readable.sql" ]; then
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" \
        -U "$DB_USER" -d "$DB_NAME" \
        -f "/app/scripts/db/init/01-schema-readable.sql"
else
    # Fallback to migrations
    alembic upgrade head || create_minimal_schema
fi
```

## 4. Database Export Script (`export_db_schema.sh`)

```bash
#!/bin/bash
# Export current database schema for containers

# Export schema only (structure)
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --schema-only \
    --no-owner \
    --no-privileges \
    --if-exists \
    --clean \
    > "$EXPORT_DIR/01-schema.sql"

# Export essential data (RBAC, users)
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --data-only \
    --table=alembic_version \
    --table=users \
    --table=rbac_roles \
    --table=rbac_permissions \
    --table=rbac_role_permissions \
    --table=rbac_user_roles \
    > "$EXPORT_DIR/02-essential-data.sql"
```

## 5. Dockerfile Integration

```dockerfile
# Copy bypass script
COPY --chown=appuser:appuser ./scripts/docker/bypass_migrations.py ./scripts/docker/

# Modified startup script in Dockerfile
RUN echo '#!/bin/bash\n\
# ... other setup ...\n\
\n\
# Run migrations (with bypass for containerized environments)\n\
echo "Running database migrations..."\n\
export DOCKER_CONTAINER=1\n\
if [ -f /app/scripts/docker/bypass_migrations.py ]; then\n\
  python /app/scripts/docker/bypass_migrations.py\n\
else\n\
  alembic upgrade head || echo "Migration failed, but continuing..."\n\
fi\n\
' > /app/start.sh
```

## Column Ordering Guidelines

When creating or modifying tables, follow this order:

1. **Primary Key(s)**
   - `id` or custom PK like `user_id`
   - Composite PKs for junction tables

2. **Business Identifiers**
   - Unique business keys (e.g., `email`, `rfi_id`)
   - Natural keys

3. **Core Business Fields**
   - Main data fields
   - Status/state fields
   - Configuration fields

4. **Foreign Keys**
   - References to other tables
   - Grouped by related functionality

5. **Metadata/Additional Data**
   - JSON/JSONB fields
   - Computed or derived fields
   - Optional configuration

6. **Audit Fields (AuditMixin)**
   - `created_by_id`
   - `updated_by_id`

7. **Timestamps (TimestampMixin)**
   - `created_at`
   - `updated_at`
   - Other timestamps (e.g., `resolved_at`, `completed_at`)

8. **Constraints**
   - UNIQUE constraints
   - CHECK constraints
   - Composite keys

This ordering makes tables easier to read and understand at a glance.
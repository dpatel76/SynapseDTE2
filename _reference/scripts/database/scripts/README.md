# Migration Scripts

This directory contains Alembic database migrations and related documentation.

## Deployment Scripts Moved

The manual database migration and deployment scripts have been moved to `/scripts/deployment/` for better organization.

## Available Deployment Scripts

The following scripts are now located in `/scripts/deployment/`:

### 1. create_test_database.py

Creates a complete test database with full schema and seed data (requires source database access).

**Usage**:
```bash
python scripts/deployment/create_test_database.py
```

### 2. export_schema.py

Exports database schema and seed data to SQL files for deployment without source database.

**Usage**:
```bash
python scripts/deployment/export_schema.py
```

### 3. create_database_from_schema.py

Creates database from exported SQL schema files (no source database required).

**Usage**:
```bash
python scripts/deployment/create_database_from_schema.py
```

### 4. Deployment Documentation

- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment instructions
- `QUICK_START.md` - Quick start guide for rapid deployment
- `requirements.txt` - Python dependencies

See `/scripts/deployment/` directory for all deployment-related resources.

## Creating New Migration Scripts

When creating new migration scripts, follow these guidelines:

1. **Naming Convention**: Use descriptive names with dates
   ```
   YYYY_MM_DD_description.py
   Example: 2024_01_15_add_audit_fields.py
   ```

2. **Script Structure**:
   ```python
   #!/usr/bin/env python3
   """
   Brief description of what this migration does
   """
   
   import asyncio
   import asyncpg
   import logging
   
   async def run_migration():
       """Main migration logic"""
       pass
   
   if __name__ == "__main__":
       asyncio.run(run_migration())
   ```

3. **Safety Checks**:
   - Always check if changes already exist
   - Use transactions where possible
   - Provide rollback capability
   - Log all operations

4. **Documentation**:
   - Include docstrings
   - Document any manual steps required
   - List prerequisites
   - Provide rollback instructions

## Script Templates

### Basic Migration Template

```python
#!/usr/bin/env python3
"""
Migration: <description>
Date: <date>
Author: <author>

Purpose:
- What this migration does
- Why it's needed

Prerequisites:
- List any requirements

Rollback:
- How to undo this migration
"""

import asyncio
import os
import asyncpg
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Execute the migration"""
    db_url = os.getenv('DATABASE_URL')
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Start transaction
        async with conn.transaction():
            # Your migration logic here
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()


async def rollback():
    """Rollback the migration"""
    # Rollback logic here
    pass


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        asyncio.run(rollback())
    else:
        asyncio.run(run_migration())
```

### Data Migration Template

```python
#!/usr/bin/env python3
"""
Data Migration: <description>
"""

import asyncio
import asyncpg
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


async def migrate_data(source_conn, target_conn):
    """Migrate data from source to target"""
    
    # Example: Copy data with transformation
    source_data = await source_conn.fetch(
        "SELECT * FROM source_table"
    )
    
    for row in source_data:
        # Transform data as needed
        transformed = transform_row(row)
        
        await target_conn.execute("""
            INSERT INTO target_table (col1, col2) 
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, transformed['col1'], transformed['col2'])
    
    logger.info(f"Migrated {len(source_data)} rows")


def transform_row(row: Dict) -> Dict:
    """Transform a single row of data"""
    return {
        'col1': row['old_col1'],
        'col2': row['old_col2'].upper()
    }
```

## Best Practices

1. **Idempotency**: Scripts should be safe to run multiple times
2. **Logging**: Use detailed logging for debugging
3. **Error Handling**: Implement proper error handling and rollback
4. **Testing**: Test on a copy of the database first
5. **Documentation**: Document all changes and requirements
6. **Version Control**: Commit scripts with descriptive messages

## Common Tasks

### Adding a New Column
```python
await conn.execute("""
    ALTER TABLE table_name 
    ADD COLUMN IF NOT EXISTS column_name VARCHAR(255)
""")
```

### Creating an Index
```python
await conn.execute("""
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_name 
    ON table_name(column_name)
""")
```

### Adding a Constraint
```python
await conn.execute("""
    ALTER TABLE table_name 
    ADD CONSTRAINT constraint_name 
    CHECK (column_name IS NOT NULL)
""")
```

### Batch Updates
```python
# Update in batches to avoid locking
batch_size = 1000
offset = 0

while True:
    result = await conn.execute("""
        UPDATE table_name 
        SET column = new_value 
        WHERE id IN (
            SELECT id FROM table_name 
            WHERE condition 
            LIMIT $1 OFFSET $2
        )
    """, batch_size, offset)
    
    if result.split()[-1] == '0':
        break
        
    offset += batch_size
```
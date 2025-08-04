#!/usr/bin/env python3
"""
Export Database Schema and Seed Data
Exports schema and essential data to SQL files for deployment

Purpose:
- Export complete database schema to SQL file
- Export essential seed data to SQL file
- Create portable database setup files

Usage:
    python scripts/deployment/export_schema.py

Output:
    - migrations/schema/complete_schema.sql
    - migrations/schema/seed_data.sql
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaExporter:
    """Export database schema and seed data"""
    
    def __init__(self):
        # Get database URL
        db_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
        
        # Parse connection info
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        self.host = parsed.hostname
        self.port = parsed.port or 5432
        self.user = parsed.username
        self.password = parsed.password
        self.database = parsed.path.lstrip('/')
        
        # Output directory
        self.output_dir = Path(__file__).parent.parent.parent / 'migrations' / 'schema'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def export_schema(self):
        """Export complete schema to SQL file"""
        logger.info("Exporting database schema...")
        
        schema_file = self.output_dir / 'complete_schema.sql'
        
        # pg_dump command for schema only
        cmd = [
            'pg_dump',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            '--schema-only',
            '--no-owner',
            '--no-privileges',
            '--no-tablespaces',
            '--no-unlogged-table-data',
            '--if-exists',
            '--clean',
            f'--file={schema_file}',
            self.database
        ]
        
        # Set password
        env = os.environ.copy()
        env['PGPASSWORD'] = self.password
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Add header to schema file
            with open(schema_file, 'r') as f:
                content = f.read()
            
            header = f"""--
-- SynapseDTE Database Schema
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Version: 2.0.0
--
-- This file contains the complete database schema for SynapseDTE
-- Use with: psql -f complete_schema.sql
--

"""
            
            with open(schema_file, 'w') as f:
                f.write(header + content)
            
            logger.info(f"✓ Schema exported to: {schema_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to export schema: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("pg_dump not found. Please install PostgreSQL client tools.")
            return False
    
    def export_seed_data(self):
        """Export essential seed data to SQL file"""
        logger.info("Exporting seed data...")
        
        seed_file = self.output_dir / 'seed_data.sql'
        
        # Tables to export data from
        seed_tables = [
            'rbac_roles',
            'rbac_permissions', 
            'rbac_role_permissions',
            'lobs',
            'workflow_activity_templates',
            'workflow_activity_dependencies',
            'regulatory_data_dictionary',
            'alembic_version'
        ]
        
        # Export each table's data
        all_data = []
        
        for table in seed_tables:
            cmd = [
                'pg_dump',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--username={self.user}',
                '--no-password',
                '--data-only',
                '--inserts',
                '--column-inserts',
                f'--table={table}',
                self.database
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.password
            
            try:
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if result.stdout.strip():
                    all_data.append(f"\n-- Data for table: {table}\n")
                    all_data.append(result.stdout)
                    logger.info(f"  ✓ Exported data from {table}")
                
            except subprocess.CalledProcessError as e:
                logger.warning(f"  ⚠ Could not export {table}: {e.stderr}")
        
        # Write seed data file
        header = f"""--
-- SynapseDTE Seed Data
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Version: 2.0.0
--
-- This file contains essential seed data for SynapseDTE
-- Use with: psql -f seed_data.sql
--

-- Disable foreign key checks during import
SET session_replication_role = 'replica';

"""
        
        footer = """

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Add test users (password: password123)
INSERT INTO users (email, first_name, last_name, hashed_password, role, lob_id, is_active)
SELECT 
    vals.email,
    vals.first_name,
    vals.last_name,
    '$2b$12$iWH6wK2JpZl0X.HmoYzVn.LrWb8oXP3R5x7JLzLJYUkZ1kTvKHC8m',
    vals.role::user_role_enum,
    (SELECT lob_id FROM lobs ORDER BY lob_id LIMIT 1),
    true
FROM (VALUES
    ('admin@example.com', 'System', 'Administrator', 'Admin'),
    ('tester1@example.com', 'John', 'Tester', 'Tester'),
    ('tester2@example.com', 'Jane', 'Tester', 'Tester'),
    ('test.manager@example.com', 'Test', 'Manager', 'Test Executive'),
    ('report.owner@example.com', 'Report', 'Owner', 'Report Owner'),
    ('data.owner@example.com', 'Data', 'Owner', 'Data Owner')
) AS vals(email, first_name, last_name, role)
ON CONFLICT (email) DO NOTHING;

-- Create user-role assignments
INSERT INTO rbac_user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u
JOIN rbac_roles r ON r.role_name = u.role::text
ON CONFLICT DO NOTHING;
"""
        
        with open(seed_file, 'w') as f:
            f.write(header)
            f.write('\n'.join(all_data))
            f.write(footer)
        
        logger.info(f"✓ Seed data exported to: {seed_file}")
        return True
    
    def create_deployment_package(self):
        """Create a deployment package with instructions"""
        readme_file = self.output_dir / 'README.md'
        
        readme_content = f"""# SynapseDTE Database Deployment Package

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents

- `complete_schema.sql` - Complete database schema (all tables, constraints, indexes)
- `seed_data.sql` - Essential seed data (roles, permissions, test users)
- `README.md` - This file

## Deployment Instructions

### Prerequisites

1. PostgreSQL 12+ installed
2. PostgreSQL client tools (psql)
3. Database user with CREATEDB privilege

### Quick Start

1. **Create database**:
   ```bash
   createdb -U postgres synapse_dt
   ```

2. **Load schema**:
   ```bash
   psql -U postgres -d synapse_dt -f complete_schema.sql
   ```

3. **Load seed data**:
   ```bash
   psql -U postgres -d synapse_dt -f seed_data.sql
   ```

### Using the Automated Script

If Python is available, use the automated script:

```bash
python create_database_from_schema.py
```

### Test Users

After deployment, these test users are available:

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | password123 | Admin |
| tester1@example.com | password123 | Tester |
| tester2@example.com | password123 | Tester |
| test.manager@example.com | password123 | Test Executive |
| report.owner@example.com | password123 | Report Owner |
| data.owner@example.com | password123 | Data Owner |

### Verification

After deployment, verify:

```sql
-- Check tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
-- Should return 126

-- Check users
SELECT email, role FROM users;

-- Check roles
SELECT role_name FROM rbac_roles;
```

### Troubleshooting

1. **Permission errors**: Ensure database user has necessary privileges
2. **Foreign key errors**: The seed_data.sql disables checks during import
3. **Duplicate key errors**: Data already exists, can be ignored

### Support

For issues, check:
- PostgreSQL logs
- Ensure correct PostgreSQL version (12+)
- Verify all files are present
"""
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        logger.info(f"✓ Created deployment README: {readme_file}")
    
    def run(self):
        """Run the complete export process"""
        logger.info("="*80)
        logger.info("DATABASE SCHEMA EXPORT")
        logger.info("="*80)
        logger.info(f"Source database: {self.database}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("")
        
        # Export schema
        if not self.export_schema():
            logger.error("Schema export failed")
            return False
        
        # Export seed data
        if not self.export_seed_data():
            logger.error("Seed data export failed")
            return False
        
        # Create deployment package
        self.create_deployment_package()
        
        logger.info("\n" + "="*80)
        logger.info("✅ Export completed successfully!")
        logger.info(f"Files created in: {self.output_dir}")
        logger.info("\nTo deploy on a new machine:")
        logger.info("1. Copy the migrations/schema directory")
        logger.info("2. Run: python create_database_from_schema.py")
        logger.info("   OR manually: psql -f complete_schema.sql && psql -f seed_data.sql")
        
        return True


def main():
    """Main entry point"""
    exporter = SchemaExporter()
    exporter.run()


if __name__ == "__main__":
    main()
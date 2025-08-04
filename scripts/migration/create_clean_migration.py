#!/usr/bin/env python3
"""
Create a clean database migration for SynapseDTE.
This script generates a fresh migration from the current models,
avoiding the issues with the existing migration files.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.schema import CreateSchema
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext

# Import all models to ensure they're registered
from app.models import *
from app.core.database import Base


def create_test_database():
    """Create a test database for migration testing."""
    # Connect to postgres to create database
    engine = create_engine("postgresql://localhost/postgres")
    
    test_db_name = f"synapse_dt_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with engine.connect() as conn:
        # Terminate existing connections
        conn.execute(text("COMMIT"))
        
        # Check if database exists
        exists = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{test_db_name}'")
        ).fetchone()
        
        if not exists:
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            print(f"Created test database: {test_db_name}")
        
    return test_db_name


def generate_clean_migration(db_url: str):
    """Generate a clean migration file from current models."""
    
    # Create alembic directory structure
    alembic_dir = Path("alembic_clean")
    versions_dir = alembic_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create alembic.ini for clean migrations
    alembic_ini_content = f"""
[alembic]
script_location = alembic_clean
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = {db_url}

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
    
    with open("alembic_clean.ini", "w") as f:
        f.write(alembic_ini_content)
    
    # Create env.py
    env_py_content = '''"""Alembic environment script for clean migrations."""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import Base
from app.models import *  # Import all models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    
    env_py_path = alembic_dir / "env.py"
    with open(env_py_path, "w") as f:
        f.write(env_py_content)
    
    # Create script.py.mako
    mako_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
    
    mako_path = alembic_dir / "script.py.mako"
    with open(mako_path, "w") as f:
        f.write(mako_content)
    
    # Initialize alembic
    alembic_cfg = Config("alembic_clean.ini")
    
    # Create initial migration
    command.revision(
        alembic_cfg,
        autogenerate=True,
        message="Initial schema from models"
    )
    
    print("Clean migration generated in alembic_clean/versions/")


def create_seed_data_migration():
    """Create a migration for seed data."""
    
    seed_migration = '''"""Add seed data for RBAC, test users, and reference data

Revision ID: seed_data_001
Revises: <previous_revision>
Create Date: {timestamp}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
import bcrypt

# revision identifiers, used by Alembic.
revision = 'seed_data_001'
down_revision = '<previous_revision>'  # Update this
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add seed data."""
    
    # Helper to hash passwords
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Define tables for inserts
    users_table = table('users',
        column('id'),
        column('username'),
        column('email'),
        column('full_name'),
        column('hashed_password'),
        column('role'),
        column('is_active'),
        column('created_at'),
        column('updated_at')
    )
    
    lobs_table = table('lobs',
        column('id'),
        column('name'),
        column('code'),
        column('description'),
        column('created_at'),
        column('updated_at')
    )
    
    permissions_table = table('permissions',
        column('id'),
        column('name'),
        column('resource'),
        column('action'),
        column('description'),
        column('created_at')
    )
    
    roles_table = table('roles',
        column('id'),
        column('name'),
        column('description'),
        column('is_active'),
        column('created_at')
    )
    
    # Insert LOBs
    op.bulk_insert(lobs_table, [
        {
            'name': 'Consumer Banking',
            'code': 'CB',
            'description': 'Consumer banking line of business',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'name': 'Corporate Banking',
            'code': 'CORP',
            'description': 'Corporate banking line of business',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'name': 'Investment Banking',
            'code': 'IB',
            'description': 'Investment banking line of business',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'name': 'Wealth Management',
            'code': 'WM',
            'description': 'Wealth management line of business',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ])
    
    # Insert test users
    test_users = [
        {
            'username': 'tester1',
            'email': 'tester1@synapse.com',
            'full_name': 'Test Tester',
            'hashed_password': hash_password('Test123!'),
            'role': 'Tester',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'manager1',
            'email': 'manager1@synapse.com',
            'full_name': 'Test Manager',
            'hashed_password': hash_password('Test123!'),
            'role': 'Test Manager',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'owner1',
            'email': 'owner1@synapse.com',
            'full_name': 'Report Owner',
            'hashed_password': hash_password('Test123!'),
            'role': 'Report Owner',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'executive1',
            'email': 'executive1@synapse.com',
            'full_name': 'Report Executive',
            'hashed_password': hash_password('Test123!'),
            'role': 'Report Owner Executive',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'provider1',
            'email': 'provider1@synapse.com',
            'full_name': 'Data Provider',
            'hashed_password': hash_password('Test123!'),
            'role': 'Data Provider',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'cdo1',
            'email': 'cdo1@synapse.com',
            'full_name': 'Chief Data Officer',
            'hashed_password': hash_password('Test123!'),
            'role': 'CDO',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    op.bulk_insert(users_table, test_users)
    
    # Insert base permissions (sample - add all 92 as needed)
    base_permissions = [
        # Workflow permissions
        {'name': 'workflow.view', 'resource': 'workflow', 'action': 'view', 'description': 'View workflow status'},
        {'name': 'workflow.advance', 'resource': 'workflow', 'action': 'advance', 'description': 'Advance workflow phases'},
        {'name': 'workflow.override', 'resource': 'workflow', 'action': 'override', 'description': 'Override workflow progression'},
        
        # Test execution permissions
        {'name': 'test.execute', 'resource': 'test', 'action': 'execute', 'description': 'Execute tests'},
        {'name': 'test.view', 'resource': 'test', 'action': 'view', 'description': 'View test results'},
        {'name': 'test.review', 'resource': 'test', 'action': 'review', 'description': 'Review test results'},
        
        # Sample permissions
        {'name': 'sample.create', 'resource': 'sample', 'action': 'create', 'description': 'Create samples'},
        {'name': 'sample.view', 'resource': 'sample', 'action': 'view', 'description': 'View samples'},
        {'name': 'sample.approve', 'resource': 'sample', 'action': 'approve', 'description': 'Approve samples'},
        
        # Add more permissions as needed...
    ]
    
    for perm in base_permissions:
        perm['created_at'] = datetime.utcnow()
    
    op.bulk_insert(permissions_table, base_permissions)
    
    # Insert roles
    roles = [
        {'name': 'Tester', 'description': 'Test execution role', 'is_active': True},
        {'name': 'Test Manager', 'description': 'Test management role', 'is_active': True},
        {'name': 'Report Owner', 'description': 'Report ownership role', 'is_active': True},
        {'name': 'Report Owner Executive', 'description': 'Executive report role', 'is_active': True},
        {'name': 'Data Provider', 'description': 'Data provider role', 'is_active': True},
        {'name': 'CDO', 'description': 'Chief Data Officer role', 'is_active': True},
    ]
    
    for role in roles:
        role['created_at'] = datetime.utcnow()
    
    op.bulk_insert(roles_table, roles)
    
    # Note: Role-permission mappings would need to be added based on your permission matrix


def downgrade() -> None:
    """Remove seed data."""
    # Delete in reverse order of dependencies
    op.execute("DELETE FROM role_permissions")
    op.execute("DELETE FROM user_roles")
    op.execute("DELETE FROM roles")
    op.execute("DELETE FROM permissions")
    op.execute("DELETE FROM users WHERE username IN ('tester1', 'manager1', 'owner1', 'executive1', 'provider1', 'cdo1')")
    op.execute("DELETE FROM lobs WHERE code IN ('CB', 'CORP', 'IB', 'WM')")
'''.format(timestamp=datetime.utcnow().isoformat())
    
    # Save seed migration template
    with open("alembic_clean/versions/seed_data_template.py", "w") as f:
        f.write(seed_migration)
    
    print("Seed data migration template created")


def main():
    """Main function to orchestrate clean migration creation."""
    
    print("SynapseDTE Clean Migration Generator")
    print("=" * 50)
    
    # Step 1: Create test database
    print("\n1. Creating test database...")
    test_db_name = create_test_database()
    test_db_url = f"postgresql://localhost/{test_db_name}"
    
    # Step 2: Generate clean migration
    print("\n2. Generating clean migration from models...")
    generate_clean_migration(test_db_url)
    
    # Step 3: Create seed data migration
    print("\n3. Creating seed data migration template...")
    create_seed_data_migration()
    
    # Step 4: Provide instructions
    print("\n" + "=" * 50)
    print("Clean migration generation complete!")
    print("\nNext steps:")
    print("1. Review the generated migration in alembic_clean/versions/")
    print("2. Update the seed data migration with the correct down_revision")
    print("3. Test the migration:")
    print(f"   DATABASE_URL={test_db_url} alembic -c alembic_clean.ini upgrade head")
    print("4. Verify the schema matches production")
    print("5. Run validation tests")
    print("\nTest database created:", test_db_name)
    print("Remember to drop it when done: dropdb", test_db_name)


if __name__ == "__main__":
    main()
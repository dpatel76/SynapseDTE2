#!/usr/bin/env python3
"""
Manually rebuild database by applying SQL files in correct order
This bypasses Alembic migrations
"""
import os
import subprocess
import sys
from pathlib import Path
import re
from datetime import datetime

# Configuration
DB_NAME = os.getenv("DB_NAME", "synapse_dt")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def run_sql_file(file_path, description=None):
    """Execute a SQL file"""
    if description:
        print(f"\n{description}")
    else:
        print(f"\nExecuting: {file_path}")
    
    cmd = f"psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} -f {file_path}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"✓ Completed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    print("Checking database...")
    
    # Check if database exists
    check_cmd = f"psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -lqt | cut -d \\| -f 1 | grep -qw {DB_NAME}"
    exists = subprocess.run(check_cmd, shell=True).returncode == 0
    
    if exists:
        print(f"Database '{DB_NAME}' already exists!")
        response = input("Drop and recreate? (y/N): ").lower()
        if response == 'y':
            print("Dropping existing database...")
            subprocess.run(f"dropdb -U {DB_USER} -h {DB_HOST} -p {DB_PORT} {DB_NAME}", shell=True)
        else:
            print("Using existing database...")
            return True
    
    print(f"Creating database '{DB_NAME}'...")
    cmd = f"createdb -U {DB_USER} -h {DB_HOST} -p {DB_PORT} {DB_NAME}"
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def find_sql_files():
    """Find all SQL files that need to be executed"""
    sql_files = []
    
    # Priority 1: Use existing complete schema if available
    complete_schema = Path("scripts/database/schema/complete_schema.sql")
    if complete_schema.exists():
        print(f"Found complete schema: {complete_schema}")
        return [
            (complete_schema, "Loading complete schema"),
            (Path("scripts/database/schema/seed_data.sql"), "Loading seed data")
        ]
    
    # Priority 2: Build from individual SQL files
    print("Complete schema not found. Collecting individual SQL files...")
    
    # Patterns to find SQL files
    patterns = [
        ("**/create_*_tables.sql", "table creation"),
        ("**/create_*_enum*.sql", "enum types"),
        ("**/add_*_indexes.sql", "indexes"),
        ("**/add_*_constraints.sql", "constraints"),
        ("scripts/database_redesign/*.sql", "redesign scripts"),
        ("scripts/add_*.sql", "additional scripts"),
        ("alembic/versions/*.sql", "migration scripts")
    ]
    
    for pattern, description in patterns:
        files = list(Path(".").glob(pattern))
        for f in files:
            sql_files.append((f, f"{description}: {f.name}"))
    
    # Sort by filename to ensure proper order
    sql_files.sort(key=lambda x: str(x[0]))
    
    return sql_files

def apply_alembic_migrations_as_sql():
    """Extract and apply SQL from Alembic migration files"""
    print("\nProcessing Alembic migrations...")
    
    migrations_dir = Path("alembic/versions")
    if not migrations_dir.exists():
        print("No Alembic migrations directory found")
        return
    
    # Get all Python migration files
    migration_files = sorted(migrations_dir.glob("*.py"))
    
    for migration_file in migration_files:
        if migration_file.name == "__init__.py":
            continue
            
        print(f"\nProcessing migration: {migration_file.name}")
        
        # Read the migration file
        content = migration_file.read_text()
        
        # Extract raw SQL from the migration
        sql_matches = re.findall(r'op\.execute\("""(.*?)"""\)', content, re.DOTALL)
        sql_matches += re.findall(r"op\.execute\('(.*?)'\)", content, re.DOTALL)
        sql_matches += re.findall(r'op\.execute\("(.*?)"\)', content, re.DOTALL)
        
        if sql_matches:
            # Create temporary SQL file
            temp_sql = Path(f"/tmp/migration_{migration_file.stem}.sql")
            with open(temp_sql, 'w') as f:
                f.write(f"-- Migration: {migration_file.name}\n")
                f.write("-- Auto-extracted SQL\n\n")
                for sql in sql_matches:
                    f.write(sql.strip() + ";\n\n")
            
            # Execute the SQL
            run_sql_file(temp_sql, f"Applying migration: {migration_file.stem}")
            
            # Clean up
            temp_sql.unlink()

def verify_database():
    """Verify the database was created successfully"""
    print("\n" + "="*50)
    print("Verifying database setup...")
    print("="*50)
    
    queries = [
        ("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'", "Tables"),
        ("SELECT COUNT(*) as enum_count FROM pg_type WHERE typtype = 'e'", "Enum types"),
        ("SELECT COUNT(*) as role_count FROM roles", "Roles"),
        ("SELECT COUNT(*) as permission_count FROM permissions", "Permissions"),
        ("SELECT COUNT(*) as user_count FROM users", "Users"),
    ]
    
    for query, label in queries:
        cmd = f'psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} -t -c "{query}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            count = result.stdout.strip()
            print(f"{label}: {count}")
        else:
            print(f"{label}: Error - {result.stderr}")
    
    # Show test users
    print("\nTest users:")
    cmd = f"""psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} -c "SELECT u.email, r.role_name FROM users u JOIN user_roles ur ON u.user_id = ur.user_id JOIN roles r ON ur.role_id = r.role_id ORDER BY u.email;" """
    subprocess.run(cmd, shell=True)

def main():
    print("SynapseDTE Manual Database Rebuild")
    print("=================================")
    print(f"Target Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    
    # Create database
    if not create_database():
        print("Failed to create database!")
        sys.exit(1)
    
    # Find SQL files to execute
    sql_files = find_sql_files()
    
    if not sql_files:
        print("No SQL files found!")
        sys.exit(1)
    
    print(f"\nFound {len(sql_files)} SQL files to process")
    
    # Execute SQL files
    failed_files = []
    for file_path, description in sql_files:
        if not run_sql_file(file_path, description):
            failed_files.append(file_path)
    
    # If no complete schema was found, also process Alembic migrations
    if not Path("scripts/database/schema/complete_schema.sql").exists():
        apply_alembic_migrations_as_sql()
    
    # Report results
    if failed_files:
        print(f"\n⚠️  {len(failed_files)} files failed to execute:")
        for f in failed_files:
            print(f"  - {f}")
    
    # Verify database
    verify_database()
    
    print("\n" + "="*50)
    print("Database rebuild complete!")
    print("="*50)
    print("\nNext steps:")
    print("1. Update your .env file with the database connection")
    print("2. Run: uvicorn app.main:app --reload")
    print("3. Login with one of the test users shown above")

if __name__ == "__main__":
    main()
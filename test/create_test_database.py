#!/usr/bin/env python3
"""
Safe test database creation script for migration testing

This script creates an isolated test database that does NOT interfere
with the production database in any way.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


def create_test_database():
    """Create a separate test database for migration testing"""
    
    print("🔒 SAFE TEST DATABASE CREATION")
    print("=" * 50)
    print("This script creates an ISOLATED test database.")
    print("It will NOT affect your production database.")
    print("=" * 50)
    
    # Create a unique test database name
    test_db_name = f"synapse_dt_migration_test_{os.getpid()}"
    test_user = f"synapse_test_user_{os.getpid()}"
    test_password = "test_password_123"
    
    print(f"Test Database: {test_db_name}")
    print(f"Test User: {test_user}")
    print(f"Host: {settings.database_host}")
    print(f"Port: {settings.database_port}")
    print()
    
    try:
        # Check if PostgreSQL is available
        result = subprocess.run(
            ["pg_isready", "-h", settings.database_host, "-p", str(settings.database_port)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ PostgreSQL is not available")
            print("Please ensure PostgreSQL is running")
            return None
        
        print("✅ PostgreSQL is available")
        
        # Create test user
        print("🔄 Creating test user...")
        create_user_cmd = [
            "psql", 
            "-h", settings.database_host, 
            "-p", str(settings.database_port),
            "-U", "postgres",
            "-c", f"CREATE USER {test_user} WITH PASSWORD '{test_password}';"
        ]
        
        result = subprocess.run(create_user_cmd, capture_output=True, text=True)
        if result.returncode == 0 or "already exists" in result.stderr:
            print("✅ Test user created/exists")
        else:
            print(f"⚠️ User creation warning: {result.stderr}")
        
        # Create test database
        print("🔄 Creating test database...")
        create_db_cmd = [
            "psql",
            "-h", settings.database_host,
            "-p", str(settings.database_port), 
            "-U", "postgres",
            "-c", f"CREATE DATABASE {test_db_name} OWNER {test_user};"
        ]
        
        result = subprocess.run(create_db_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Test database created")
        elif "already exists" in result.stderr:
            print("✅ Test database already exists")
        else:
            print(f"❌ Database creation failed: {result.stderr}")
            return None
        
        # Grant privileges
        print("🔄 Granting privileges...")
        grant_cmd = [
            "psql",
            "-h", settings.database_host,
            "-p", str(settings.database_port),
            "-U", "postgres", 
            "-c", f"GRANT ALL PRIVILEGES ON DATABASE {test_db_name} TO {test_user};"
        ]
        
        subprocess.run(grant_cmd, capture_output=True, text=True)
        
        # Test connection
        print("🔄 Testing connection...")
        test_cmd = [
            "psql",
            "-h", settings.database_host,
            "-p", str(settings.database_port),
            "-U", test_user,
            "-d", test_db_name,
            "-c", "SELECT version();"
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = test_password
        
        result = subprocess.run(test_cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            print("✅ Test database connection successful")
            
            # Return connection details
            test_db_url = f"postgresql://{test_user}:{test_password}@{settings.database_host}:{settings.database_port}/{test_db_name}"
            
            return {
                "database_name": test_db_name,
                "user": test_user,
                "password": test_password,
                "url": test_db_url,
                "cleanup_commands": [
                    f"DROP DATABASE IF EXISTS {test_db_name};",
                    f"DROP USER IF EXISTS {test_user};"
                ]
            }
        else:
            print(f"❌ Test connection failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test database: {e}")
        return None


def cleanup_test_database(test_info):
    """Clean up the test database"""
    if not test_info:
        return
        
    print("🧹 Cleaning up test database...")
    
    for cmd in test_info["cleanup_commands"]:
        cleanup_cmd = [
            "psql",
            "-h", settings.database_host,
            "-p", str(settings.database_port),
            "-U", "postgres",
            "-c", cmd
        ]
        
        result = subprocess.run(cleanup_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Executed: {cmd}")
        else:
            print(f"⚠️ Cleanup warning for '{cmd}': {result.stderr}")


if __name__ == "__main__":
    test_info = create_test_database()
    if test_info:
        print("\n✅ Test database ready!")
        print(f"Database URL: {test_info['url']}")
        print("\nTo clean up later, run:")
        for cmd in test_info["cleanup_commands"]:
            print(f"  psql -U postgres -c \"{cmd}\"")
    else:
        print("❌ Failed to create test database")
        sys.exit(1)
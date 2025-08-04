#!/usr/bin/env python3
"""
Database setup script for SynapseDT
Creates the PostgreSQL database and user for the application.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def setup_database():
    """Set up PostgreSQL database and user"""
    print("🚀 Setting up SynapseDT Database")
    print("=" * 50)
    
    # Extract database info from settings
    db_name = settings.database_name
    db_user = settings.database_user
    db_password = settings.database_password
    db_host = settings.database_host
    db_port = settings.database_port
    
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    print()
    
    # Check if PostgreSQL is running
    print("🔍 Checking PostgreSQL status...")
    pg_status = run_command("pg_isready", "PostgreSQL connection check")
    if pg_status is None:
        print("❌ PostgreSQL is not running or not installed")
        print("Please install and start PostgreSQL first:")
        print("  macOS: brew install postgresql && brew services start postgresql")
        print("  Ubuntu: sudo apt install postgresql && sudo systemctl start postgresql")
        return False
    
    # Create database user
    create_user_cmd = f"""
    psql -h {db_host} -p {db_port} -U postgres -c "
    DO \\$\\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{db_user}') THEN
            CREATE USER {db_user} WITH PASSWORD '{db_password}';
        END IF;
    END
    \\$\\$;
    "
    """
    
    if run_command(create_user_cmd, f"Creating user '{db_user}'") is None:
        print("⚠️  Failed to create user. You may need to run this as postgres user:")
        print(f"  sudo -u postgres psql -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\"")
    
    # Create database
    create_db_cmd = f"""
    psql -h {db_host} -p {db_port} -U postgres -c "
    SELECT 'CREATE DATABASE {db_name} OWNER {db_user};'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{db_name}')\\gexec
    "
    """
    
    if run_command(create_db_cmd, f"Creating database '{db_name}'") is None:
        print("⚠️  Failed to create database. You may need to run this as postgres user:")
        print(f"  sudo -u postgres createdb -O {db_user} {db_name}")
    
    # Grant privileges
    grant_cmd = f"""
    psql -h {db_host} -p {db_port} -U postgres -c "
    GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};
    ALTER USER {db_user} CREATEDB;
    "
    """
    
    run_command(grant_cmd, f"Granting privileges to '{db_user}'")
    
    # Test connection
    test_cmd = f"psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -c 'SELECT version();'"
    
    print("\n🧪 Testing database connection...")
    if run_command(test_cmd, "Database connection test"):
        print("\n✅ Database setup completed successfully!")
        print(f"✅ You can now run migrations: alembic upgrade head")
        return True
    else:
        print("\n❌ Database connection test failed")
        print("Please check your PostgreSQL installation and configuration")
        return False


def run_migrations():
    """Run Alembic migrations"""
    print("\n🔄 Running database migrations...")
    
    # Run migrations
    if run_command("alembic upgrade head", "Running migrations"):
        print("✅ Database migrations completed successfully!")
        return True
    else:
        print("❌ Database migrations failed")
        return False


def main():
    """Main setup function"""
    print("SynapseDT Database Setup")
    print("=" * 30)
    print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Please copy env.example to .env and configure it first.")
        print("  cp env.example .env")
        return
    
    # Setup database
    if setup_database():
        # Ask if user wants to run migrations
        response = input("\n🤔 Would you like to run database migrations now? (y/N): ")
        if response.lower() in ['y', 'yes']:
            run_migrations()
        else:
            print("ℹ️  You can run migrations later with: alembic upgrade head")
    
    print("\n🎉 Setup complete! You can now start the application:")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main() 
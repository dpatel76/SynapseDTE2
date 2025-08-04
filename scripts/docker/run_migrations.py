#!/usr/bin/env python3
"""
Run Alembic migrations for containerized environment.
Handles both fresh installs and updates.
"""

import os
import sys
import logging
import subprocess
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_database(database_url: str, max_retries: int = 30):
    """Wait for database to be available."""
    logger.info("Waiting for database to be ready...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            return True
        except OperationalError:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready yet, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                logger.error("Database connection failed after maximum retries")
                return False
        finally:
            if 'engine' in locals():
                engine.dispose()
    
    return False

def check_alembic_version(database_url: str):
    """Check if alembic_version table exists and has a version."""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("alembic_version table does not exist")
                return None
            
            # Get current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            if row:
                version = row[0]
                logger.info(f"Current Alembic version: {version}")
                return version
            else:
                logger.info("alembic_version table exists but is empty")
                return ""
                
    except Exception as e:
        logger.error(f"Error checking Alembic version: {e}")
        return None
    finally:
        if 'engine' in locals():
            engine.dispose()

def run_migrations():
    """Run Alembic migrations with proper handling for containerized environment."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Construct from individual components
        host = os.environ.get('DATABASE_HOST', 'localhost')
        port = os.environ.get('DATABASE_PORT', '5432')
        name = os.environ.get('DATABASE_NAME', 'synapse_dt')
        user = os.environ.get('DATABASE_USER', 'synapse_user')
        password = os.environ.get('DATABASE_PASSWORD', 'synapse_password')
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    # Ensure we use regular postgresql URL for Alembic (not asyncpg)
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Wait for database
    if not wait_for_database(database_url):
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    # Check current Alembic version
    current_version = check_alembic_version(database_url)
    
    if current_version is None:
        # Fresh database or no Alembic setup
        logger.info("Fresh database detected, running migrations to create all tables")
        # Run migrations to create all tables from models
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                env={**os.environ, "DATABASE_URL": database_url}
            )
            if result.returncode != 0:
                logger.error(f"Failed to run migrations: {result.stderr}")
                sys.exit(1)
            logger.info("Initial migrations completed successfully")
            if result.stdout:
                logger.info(f"Migration output: {result.stdout}")
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            sys.exit(1)
    else:
        # Alembic is already set up, run normal upgrade
        logger.info("Running Alembic migrations...")
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                env={**os.environ, "DATABASE_URL": database_url}
            )
            if result.returncode != 0:
                logger.error(f"Migration failed: {result.stderr}")
                # Don't exit on migration failure - app might still work
                logger.warning("Continuing despite migration failure...")
            else:
                logger.info("Migrations completed successfully")
                if result.stdout:
                    logger.info(f"Migration output: {result.stdout}")
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            logger.warning("Continuing despite migration error...")
    
    logger.info("Migration process completed")

if __name__ == "__main__":
    run_migrations()
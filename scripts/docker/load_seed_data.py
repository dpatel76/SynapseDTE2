#!/usr/bin/env python3
"""
Load seed data into database after migrations have run.
This script loads SQL seed files in proper order to respect foreign key constraints.
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Construct from individual components
        host = os.environ.get('DATABASE_HOST', 'localhost')
        port = os.environ.get('DATABASE_PORT', '5432')
        name = os.environ.get('DATABASE_NAME', 'synapse_dt')
        user = os.environ.get('DATABASE_USER', 'synapse_user')
        password = os.environ.get('DATABASE_PASSWORD', 'synapse_password')
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    # Ensure we use regular postgresql URL (not asyncpg)
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    return database_url

def check_seed_data_exists(engine):
    """Check if seed data has already been loaded."""
    try:
        with engine.connect() as conn:
            # Check if we have any roles
            result = conn.execute(text("SELECT COUNT(*) FROM rbac_roles"))
            role_count = result.scalar()
            
            # Check if we have any LOBs
            result = conn.execute(text("SELECT COUNT(*) FROM lobs"))
            lob_count = result.scalar()
            
            # Check if we have any users
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if role_count > 0:
                logger.info(f"Seed data already exists ({role_count} roles, {lob_count} lobs, {user_count} users found)")
                return True
            
            logger.info(f"Database has {role_count} roles, {lob_count} lobs, {user_count} users")
            return False
    except Exception as e:
        logger.error(f"Error checking seed data: {e}")
        return False

def load_sql_file(engine, file_path):
    """Load a single SQL file into the database."""
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        # Skip empty files
        if not sql_content.strip():
            logger.warning(f"Skipping empty file: {file_path}")
            return True
        
        # Execute SQL
        with engine.connect() as conn:
            conn.execute(text(sql_content))
            conn.commit()
        
        logger.info(f"Successfully loaded: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return False

def load_seed_data():
    """Load all seed data files in proper order."""
    database_url = get_database_url()
    
    # Create engine
    engine = create_engine(database_url)
    
    # Check if seed data already exists
    if check_seed_data_exists(engine):
        logger.info("Seed data already loaded, skipping...")
        return True
    
    logger.info("Loading seed data...")
    
    # Try to load the simple seed data file first
    seed_file = Path("/app/scripts/docker/create_seed_data.sql")
    if not seed_file.exists():
        # Try local path for development
        seed_file = Path("scripts/docker/create_seed_data.sql")
    
    if seed_file.exists():
        logger.info("Loading simplified seed data...")
        if load_sql_file(engine, seed_file):
            logger.info("Successfully loaded seed data")
            success_count = 1
            error_count = 0
        else:
            logger.error("Failed to load seed data")
            success_count = 0
            error_count = 1
    else:
        logger.error(f"Seed file not found: {seed_file}")
        success_count = 0
        error_count = 1
    
    # Verify key tables
    logger.info("\nVerifying key tables:")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            logger.info(f"Users: {result.scalar()}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM rbac_roles"))
            logger.info(f"Roles: {result.scalar()}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM reports"))
            logger.info(f"Reports: {result.scalar()}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM test_cycles"))
            logger.info(f"Test Cycles: {result.scalar()}")
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
    
    logger.info(f"\nSeed data loading complete! Success: {success_count}, Errors: {error_count}")
    
    # Clean up
    engine.dispose()
    
    return error_count == 0

if __name__ == "__main__":
    success = load_seed_data()
    sys.exit(0 if success else 1)
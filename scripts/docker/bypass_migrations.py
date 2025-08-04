#!/usr/bin/env python3
"""
Skip Alembic migrations for containerized environment.
Database is already initialized via SQL scripts in docker-entrypoint-initdb.d.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def skip_migrations():
    """Skip migrations - database is initialized via SQL scripts."""
    logger.info("Skipping Alembic migrations - database initialized via SQL scripts")
    logger.info("If you need to run migrations manually, use: alembic upgrade head")
    # Exit successfully
    sys.exit(0)

if __name__ == "__main__":
    skip_migrations()
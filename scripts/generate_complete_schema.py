#!/usr/bin/env python3
"""
Generate complete database schema from SQLAlchemy models
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, MetaData
from app.core.database import Base
from app.models import *  # Import all models

def generate_schema():
    """Generate complete schema SQL from models"""
    
    # Create in-memory SQLite engine for schema generation
    engine = create_engine("sqlite:///:memory:")
    
    # Create all tables in memory
    Base.metadata.create_all(engine)
    
    # Get PostgreSQL-compatible DDL
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import postgresql
    
    output_file = "scripts/database/08032025/01_complete_schema_from_models.sql"
    
    with open(output_file, 'w') as f:
        f.write("-- Complete Database Schema Generated from SQLAlchemy Models\n")
        f.write("-- This includes all tables defined in the application\n\n")
        
        # Write extensions
        f.write("-- Enable required extensions\n")
        f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
        f.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
        
        # Get all tables in dependency order
        sorted_tables = []
        metadata = Base.metadata
        
        # First pass - tables without foreign keys
        for table in metadata.sorted_tables:
            if not table.foreign_keys:
                sorted_tables.append(table)
        
        # Second pass - remaining tables
        for table in metadata.sorted_tables:
            if table not in sorted_tables:
                sorted_tables.append(table)
        
        # Generate CREATE TABLE statements
        for table in sorted_tables:
            # Skip alembic_version table
            if table.name == 'alembic_version':
                continue
                
            # Generate PostgreSQL-specific DDL
            create_stmt = CreateTable(table).compile(dialect=postgresql.dialect())
            f.write(f"\n-- Table: {table.name}\n")
            f.write(str(create_stmt) + ";\n")
    
    print(f"Schema generated: {output_file}")
    print(f"Total tables: {len([t for t in sorted_tables if t.name != 'alembic_version'])}")

if __name__ == "__main__":
    generate_schema()
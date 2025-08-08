#!/usr/bin/env python3
"""
Create all tables from individual SQL files
"""

import os
from pathlib import Path

def create_complete_schema():
    """Merge all table creation SQLs into one file"""
    
    sql_seeds_dir = Path(__file__).parent / "sql_seeds"
    output_file = Path(__file__).parent / "01_complete_schema.sql"
    
    # Files to skip
    skip_files = {'alembic_version.sql'}
    
    with open(output_file, 'w') as out:
        out.write("-- Complete SynapseDTE Database Schema\n")
        out.write("-- Generated from individual table SQL files\n")
        out.write("-- Date: 2025-08-03\n\n")
        
        # Extensions
        out.write("-- Enable required extensions\n")
        out.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
        out.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
        
        # First, extract CREATE TYPE statements from all files
        out.write("-- Custom Types\n")
        types_found = set()
        for sql_file in sorted(sql_seeds_dir.glob("*.sql")):
            if sql_file.name in skip_files:
                continue
            
            with open(sql_file, 'r') as f:
                content = f.read()
                # Look for CREATE TYPE statements
                for line in content.split('\n'):
                    if 'CREATE TYPE' in line and 'AS ENUM' in line:
                        # Extract type name
                        type_name = line.split('CREATE TYPE')[1].split('AS ENUM')[0].strip()
                        if type_name not in types_found:
                            types_found.add(type_name)
                            out.write(f"DROP TYPE IF EXISTS {type_name} CASCADE;\n")
                            # Find the full type definition
                            start = content.find(line)
                            end = content.find(');', start) + 2
                            type_def = content[start:end]
                            out.write(type_def + '\n\n')
        
        # Now extract CREATE TABLE statements
        out.write("\n-- Tables\n")
        table_count = 0
        
        # First pass - tables without foreign keys (read from table_creation_order.txt)
        order_file = Path(__file__).parent / "table_creation_order.txt"
        if order_file.exists():
            with open(order_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if '. ' in line and '(' in line:
                    # Extract table name
                    table_name = line.split('. ')[1].split(' ')[0]
                    sql_file = sql_seeds_dir / f"{table_name}.sql"
                    
                    if sql_file.exists() and sql_file.name not in skip_files:
                        with open(sql_file, 'r') as f:
                            content = f.read()
                            
                        # Extract CREATE TABLE statement
                        if 'CREATE TABLE' in content:
                            start = content.find('CREATE TABLE')
                            # Find the end of the CREATE TABLE statement
                            end = content.rfind(');')
                            if end > start:
                                create_stmt = content[start:end+2]
                                out.write(f"\n-- Table: {table_name}\n")
                                out.write(create_stmt + '\n')
                                table_count += 1
        
        out.write(f"\n-- Total tables: {table_count}\n")
    
    print(f"Created complete schema file: {output_file}")
    print(f"Total tables: {table_count}")
    
    # Also create a simple test user insert
    test_user_file = Path(__file__).parent / "99_test_user.sql"
    with open(test_user_file, 'w') as f:
        f.write("-- Test user with bcrypt hash for password123\n")
        f.write("INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES\n")
        f.write("('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true)\n")
        f.write("ON CONFLICT (email) DO UPDATE SET hashed_password = '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie';\n")

if __name__ == "__main__":
    create_complete_schema()
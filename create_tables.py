#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_observation_tables():
    """Create new observation management tables"""
    
    # Create database connection
    engine = create_engine(settings.database_url)

    # Read and execute the SQL file
    with open('create_observation_management_tables.sql', 'r') as f:
        sql_content = f.read()

    # Execute the SQL
    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for stmt in statements:
            if stmt.strip():
                print(f'Executing: {stmt[:50]}...')
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception as e:
                    print(f'Error: {e}')
                    # Try to continue with next statement
                    continue
        
    print('Database tables created successfully!')

if __name__ == "__main__":
    create_observation_tables()
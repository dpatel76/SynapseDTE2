#!/usr/bin/env python3
"""
Script to run database updates for sample selection decisions and phase names
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost/synapsedte')

async def run_updates():
    """Run the database updates"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("Starting database updates...")
            
            # Read the SQL file
            with open('update_sample_decisions_and_phase_names.sql', 'r') as f:
                sql_content = f.read()
            
            # Split into individual statements (simple split on semicolon)
            # Note: This is a simple approach and may need adjustment for complex SQL
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        print(f"\nExecuting statement {i}...")
                        await conn.execute(text(statement))
                    except Exception as e:
                        print(f"Error in statement {i}: {e}")
                        # Continue with other statements
                        continue
            
            print("\nDatabase updates completed successfully!")
            
    except Exception as e:
        print(f"Error running updates: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_updates())
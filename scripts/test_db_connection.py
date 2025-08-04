#!/usr/bin/env python3
"""Test database connection"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    # Use the asyncpg URL directly
    database_url = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
    
    print(f"Testing connection to: {database_url}")
    
    try:
        engine = create_async_engine(database_url, echo=True)
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Connection successful!")
            
            # List current tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"\nFound {len(tables)} tables:")
            for table in tables[:20]:  # Show first 20
                print(f"  - {table}")
            if len(tables) > 20:
                print(f"  ... and {len(tables) - 20} more")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_connection())
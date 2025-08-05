#!/usr/bin/env python3
"""
Script to load fry14m_scheduled1_data from reference database to container database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys

# Database connections
SOURCE_DB = {
    'host': 'localhost',
    'port': 5432,
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password'
}

TARGET_DB = {
    'host': 'localhost',
    'port': 5433,
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password'
}

def get_connection(db_config):
    """Create a database connection"""
    return psycopg2.connect(**db_config)

def copy_fry14m_data():
    """Copy fry14m_scheduled1_data from source to target database"""
    source_conn = None
    target_conn = None
    
    try:
        # Connect to source database
        print("Connecting to source database...")
        source_conn = get_connection(SOURCE_DB)
        source_cursor = source_conn.cursor(cursor_factory=RealDictCursor)
        
        # Connect to target database
        print("Connecting to target database...")
        target_conn = get_connection(TARGET_DB)
        target_cursor = target_conn.cursor()
        
        # Check if table exists in target
        target_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'fry14m_scheduled1_data'
            )
        """)
        
        if not target_cursor.fetchone()[0]:
            print("Error: Table fry14m_scheduled1_data does not exist in target database")
            return False
        
        # Clear existing data in target
        print("Clearing existing data in target...")
        target_cursor.execute("TRUNCATE TABLE fry14m_scheduled1_data RESTART IDENTITY")
        
        # Fetch data from source
        print("Fetching data from source...")
        source_cursor.execute("SELECT * FROM fry14m_scheduled1_data ORDER BY id")
        rows = source_cursor.fetchall()
        print(f"Found {len(rows)} rows to copy")
        
        # Get column names (excluding 'id' as it will be auto-generated)
        if rows:
            columns = [col for col in rows[0].keys() if col != 'id']
            
            # Prepare insert query
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            insert_query = f"""
                INSERT INTO fry14m_scheduled1_data ({column_names})
                VALUES ({placeholders})
            """
            
            # Insert data in batches
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                batch_data = []
                
                for row in batch:
                    values = [row[col] for col in columns]
                    batch_data.append(values)
                
                target_cursor.executemany(insert_query, batch_data)
                total_inserted += len(batch_data)
                print(f"Inserted {total_inserted}/{len(rows)} rows...")
            
            # Commit the transaction
            target_conn.commit()
            print(f"Successfully copied {total_inserted} rows")
            
            # Verify the copy
            target_cursor.execute("SELECT COUNT(*) FROM fry14m_scheduled1_data")
            count = target_cursor.fetchone()[0]
            print(f"Verification: Target table now has {count} rows")
            
            return True
        else:
            print("No data found in source table")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        if target_conn:
            target_conn.rollback()
        return False
        
    finally:
        # Close connections
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()

if __name__ == "__main__":
    print("Starting fry14m_scheduled1_data data copy...")
    success = copy_fry14m_data()
    
    if success:
        print("Data copy completed successfully!")
        sys.exit(0)
    else:
        print("Data copy failed!")
        sys.exit(1)
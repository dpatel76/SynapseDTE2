#!/usr/bin/env python3
"""
Break circular dependencies and clean up test cycle data.
This script identifies circular foreign key dependencies and breaks them.
"""

import os
from dotenv import load_dotenv
import psycopg2
import sys

load_dotenv()

def break_circular_dependencies_and_cleanup():
    """Break circular dependencies then clean up test cycles"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)
    
    # Convert async URL to sync URL if needed
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Connect to database with autocommit
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        print("\n=== Breaking Circular Dependencies and Cleaning Test Cycles ===\n")
        
        # Step 1: Identify problematic circular dependencies
        print("Step 1: Breaking circular dependencies...")
        
        # Tables with known circular dependencies
        circular_tables = [
            ('document_submissions', 'test_case_id'),
            ('sample_records', 'set_id'),
            ('test_cases', 'phase_id'),
        ]
        
        for table, column in circular_tables:
            try:
                cur.execute(f"UPDATE {table} SET {column} = NULL")
                if cur.rowcount > 0:
                    print(f"  ✓ Nullified {cur.rowcount} {column} references in {table}")
            except psycopg2.errors.UndefinedTable:
                pass
            except psycopg2.errors.UndefinedColumn:
                pass
            except Exception as e:
                print(f"  ⚠️  Error with {table}.{column}: {str(e)}")
        
        print("\nStep 2: Deleting orphaned records...")
        
        # Delete records that no longer have valid references
        orphan_tables = [
            'document_submissions',
            'sample_records',
            'test_cases',
            'sample_sets',
            'request_info_phases',
            'report_attributes',
            'attribute_scoping_recommendations',
        ]
        
        for table in orphan_tables:
            try:
                cur.execute(f"DELETE FROM {table}")
                if cur.rowcount > 0:
                    print(f"  ✓ Deleted {cur.rowcount} records from {table}")
            except psycopg2.errors.UndefinedTable:
                pass
            except Exception as e:
                print(f"  ⚠️  Error deleting from {table}: {str(e)}")
        
        print("\nStep 3: Now cleaning up all test cycle data...")
        
        # Now run the comprehensive cleanup
        # Get all tables that depend on test_cycles
        cur.execute("""
            SELECT DISTINCT tc.table_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND ccu.table_name = 'test_cycles'
              AND tc.table_schema = 'public'
            ORDER BY tc.table_name;
        """)
        
        dependent_tables = [row[0] for row in cur.fetchall()]
        
        # Delete from all dependent tables
        for table in dependent_tables:
            try:
                cur.execute(f"DELETE FROM {table}")
                if cur.rowcount > 0:
                    print(f"  ✓ Deleted {cur.rowcount} records from {table}")
            except psycopg2.errors.UndefinedTable:
                pass
            except Exception as e:
                # Only print if it's not about missing columns
                if 'column "cycle_id" does not exist' not in str(e):
                    print(f"  ⚠️  Error with {table}: {str(e)}")
        
        # Finally, delete test_cycles
        print("\nStep 4: Deleting test_cycles...")
        cur.execute("DELETE FROM test_cycles")
        print(f"  ✓ Deleted {cur.rowcount} test cycles")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM test_cycles")
        remaining = cur.fetchone()[0]
        
        if remaining == 0:
            print("\n" + "="*60)
            print("🎉 SUCCESS! All test cycle data has been removed!")
            print("="*60)
            print("\nThe database is now clean and ready for fresh data.")
            print("\nNext steps:")
            print("1. Log in as test.manager@example.com")
            print("2. Navigate to 'Test Cycles' in the menu")
            print("3. Create a new test cycle")
            print("4. Add reports and assign testers")
            print("\nThe dashboard will now show:")
            print("- 0 test cycles (until you create one)")
            print("- 0 at-risk reports")
            print("- Real-time workflow progress as testers work")
            print("- Accurate metrics based on actual data")
        else:
            print(f"\n❌ ERROR: {remaining} test cycles still remain!")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    break_circular_dependencies_and_cleanup()
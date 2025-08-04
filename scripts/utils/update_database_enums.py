#!/usr/bin/env python3
"""
Update database enums for clean architecture migration
"""

import psycopg2

def update_enums():
    """Update enum types in the database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='synapse_dt',
            user='synapse_user',
            password='synapse_password'
        )
        
        cur = conn.cursor()
        
        # Add new values to workflow_phase_enum
        print("Adding new workflow phase enum values...")
        try:
            cur.execute("ALTER TYPE workflow_phase_enum ADD VALUE IF NOT EXISTS 'Data Owner ID';")
            cur.execute("ALTER TYPE workflow_phase_enum ADD VALUE IF NOT EXISTS 'Test Execution';")
            conn.commit()
            print("✅ Added new workflow phase enum values")
        except Exception as e:
            print(f"  Note: {e}")
            conn.rollback()
        
        # Check if notification table exists and what columns it has
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'notifications'
        """)
        notification_columns = cur.fetchall()
        
        if notification_columns:
            print(f"\nNotification table columns: {notification_columns}")
            
            # Update notifications if the table exists
            cur.execute("""
                UPDATE notifications 
                SET message = REPLACE(
                    REPLACE(
                        REPLACE(message, 'Data Provider', 'Data Owner'),
                        'Test Manager', 'Test Executive'
                    ),
                    'CDO', 'Data Executive'
                )
                WHERE message LIKE '%Data Provider%' 
                   OR message LIKE '%Test Manager%'
                   OR message LIKE '%CDO%'
            """)
            print(f"✅ Updated {cur.rowcount} notification messages")
        
        # Update audit logs
        print("\nUpdating audit log entries...")
        try:
            cur.execute("""
                UPDATE audit_log 
                SET user_role = CASE 
                    WHEN user_role = 'CDO' THEN 'Data Executive'
                    WHEN user_role = 'Test Manager' THEN 'Test Executive'
                    WHEN user_role = 'Data Provider' THEN 'Data Owner'
                    ELSE user_role
                END
                WHERE user_role IN ('CDO', 'Test Manager', 'Data Provider')
            """)
            print(f"✅ Updated {cur.rowcount} audit log entries")
        except Exception as e:
            print(f"  Note: Could not update audit_log: {e}")
            conn.rollback()
        
        # Update SLA configurations
        print("\nUpdating SLA configurations...")
        cur.execute("""
            UPDATE universal_sla_configurations 
            SET phase_name = CASE 
                WHEN phase_name = 'Data Provider ID' THEN 'Data Owner ID'
                WHEN phase_name = 'Testing' THEN 'Test Execution'
                ELSE phase_name
            END
            WHERE phase_name IN ('Data Provider ID', 'Testing')
        """)
        print(f"✅ Updated {cur.rowcount} SLA configurations")
        
        # Update table names if needed
        print("\nChecking for tables to rename...")
        tables_to_rename = [
            ('data_provider_assignments', 'data_owner_assignments'),
            ('data_provider_phase', 'data_owner_phase'),
            ('data_provider_notifications', 'data_owner_notifications'),
            ('testing_execution_phase', 'test_execution_phase'),
            ('testing_test_executions', 'test_executions'),
        ]
        
        for old_name, new_name in tables_to_rename:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{old_name}'
                )
            """)
            if cur.fetchone()[0]:
                print(f"  - Renaming {old_name} to {new_name}")
                try:
                    cur.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
                    print(f"    ✅ Renamed successfully")
                except Exception as e:
                    print(f"    ⚠️  {e}")
                    conn.rollback()
        
        # Update column names
        print("\nUpdating column names...")
        column_updates = [
            ('reports', 'data_provider_id', 'data_owner_id'),
            ('workflow_phases', 'assigned_data_provider', 'assigned_data_owner'),
        ]
        
        for table, old_col, new_col in column_updates:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{old_col}'
                )
            """)
            if cur.fetchone()[0]:
                print(f"  - Renaming {table}.{old_col} to {new_col}")
                try:
                    cur.execute(f"ALTER TABLE {table} RENAME COLUMN {old_col} TO {new_col}")
                    print(f"    ✅ Renamed successfully")
                except Exception as e:
                    print(f"    ⚠️  {e}")
                    conn.rollback()
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n✅ Database enum updates completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    update_enums()
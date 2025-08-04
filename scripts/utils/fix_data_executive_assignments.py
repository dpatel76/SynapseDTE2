#!/usr/bin/env python3
"""Fix Data Executive assignments to show in dashboard"""

import asyncio
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
# Convert to sync URL if needed
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def fix_assignments():
    """Fix Data Executive assignments"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("=== Fixing Data Executive Assignments ===")
            
            # Get Data Executive user (David Brown)
            result = conn.execute(text("""
                SELECT user_id, first_name, last_name, email, lob_id
                FROM users
                WHERE email = 'cdo@example.com'
                AND is_active = true
            """))
            de = result.fetchone()
            
            if not de:
                print("❌ Data Executive user not found!")
                return
            
            de_id = de[0]
            de_lob_id = de[4]
            print(f"✅ Found Data Executive: {de[1]} {de[2]} (ID: {de_id})")
            
            # Update existing assignments to have cdo_id set correctly
            result = conn.execute(text("""
                UPDATE data_provider_assignments
                SET cdo_id = :cdo_id
                WHERE lob_id = :lob_id
                AND cdo_id IS NULL
                AND cycle_id = 9
                AND report_id = 156
                RETURNING assignment_id, attribute_id
            """), {"cdo_id": de_id, "lob_id": de_lob_id})
            
            updated = result.fetchall()
            print(f"\n✅ Updated {len(updated)} assignments with cdo_id = {de_id}")
            
            # Also create some new assignments for testing
            # Find non-PK attributes that need data provider assignment
            result = conn.execute(text("""
                SELECT DISTINCT
                    ra.attribute_id,
                    ra.attribute_name
                FROM report_attributes ra
                JOIN cycle_report_scoping_tester_decisions tsd ON (
                    ra.attribute_id = tsd.attribute_id
                    AND ra.cycle_id = tsd.cycle_id
                    AND ra.report_id = tsd.report_id
                )
                JOIN attribute_lob_assignments ala ON (
                    ra.attribute_id = ala.attribute_id
                    AND ra.cycle_id = ala.cycle_id
                    AND ra.report_id = ala.report_id
                )
                WHERE ra.cycle_id = 9
                AND ra.report_id = 156
                AND ra.is_primary_key = false
                AND tsd.final_scoping = true
                AND ala.lob_id = :lob_id
                AND NOT EXISTS (
                    SELECT 1 FROM data_provider_assignments dpa
                    WHERE dpa.cycle_id = 9
                    AND dpa.report_id = 156
                    AND dpa.attribute_id = ra.attribute_id
                )
                LIMIT 2
            """), {"lob_id": de_lob_id})
            
            attrs_to_assign = result.fetchall()
            
            print(f"\nFound {len(attrs_to_assign)} attributes needing assignment")
            
            # Create assignments
            for attr_id, attr_name in attrs_to_assign:
                conn.execute(text("""
                    INSERT INTO data_provider_assignments 
                    (cycle_id, report_id, attribute_id, lob_id, cdo_id, assigned_by, assigned_at, status)
                    VALUES (9, 156, :attr_id, :lob_id, :cdo_id, :assigned_by, :now, 'Assigned')
                """), {
                    "attr_id": attr_id,
                    "lob_id": de_lob_id,
                    "cdo_id": de_id,
                    "assigned_by": de_id,
                    "now": datetime.utcnow()
                })
                print(f"  ✅ Created assignment for {attr_name}")
            
            # Get data owners in this LOB for assignment
            result = conn.execute(text("""
                SELECT user_id, first_name, last_name
                FROM users
                WHERE lob_id = :lob_id
                AND role = 'Data Owner'
                AND is_active = true
                LIMIT 1
            """), {"lob_id": de_lob_id})
            
            data_owner = result.fetchone()
            
            if data_owner:
                # Assign a data provider to one of the existing assignments
                result = conn.execute(text("""
                    UPDATE data_provider_assignments
                    SET data_provider_id = :data_provider_id,
                        status = 'Completed'
                    WHERE cycle_id = 9
                    AND report_id = 156
                    AND cdo_id = :cdo_id
                    AND data_provider_id IS NULL
                    AND assignment_id = (
                        SELECT assignment_id 
                        FROM data_provider_assignments
                        WHERE cycle_id = 9
                        AND report_id = 156
                        AND cdo_id = :cdo_id
                        AND data_provider_id IS NULL
                        LIMIT 1
                    )
                    RETURNING assignment_id, attribute_id
                """), {
                    "data_provider_id": data_owner[0],
                    "cdo_id": de_id
                })
                
                if result.rowcount > 0:
                    print(f"\n✅ Assigned {data_owner[1]} {data_owner[2]} to one attribute")
            
            trans.commit()
            print("\n✅ All assignments fixed!")
            
            # Show current state
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN data_provider_id IS NOT NULL THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN data_provider_id IS NULL THEN 1 ELSE 0 END) as pending
                FROM data_provider_assignments
                WHERE cdo_id = :cdo_id
            """), {"cdo_id": de_id})
            
            stats = result.fetchone()
            print(f"\nCurrent assignment statistics for Data Executive:")
            print(f"  Total: {stats[0]}")
            print(f"  Completed: {stats[1]}")
            print(f"  Pending: {stats[2]}")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    print("Fixing Data Executive assignments...")
    fix_assignments()
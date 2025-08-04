#!/usr/bin/env python3
"""Create pending assignments for Data Executive dashboard"""

import asyncio
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
# Convert to sync URL if needed
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def create_assignments():
    """Create pending assignments"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("=== Creating Pending Assignments ===")
            
            # Get Data Executive user
            result = conn.execute(text("""
                SELECT user_id, first_name, last_name, lob_id
                FROM users
                WHERE email = 'cdo@example.com'
            """))
            de = result.fetchone()
            de_id = de[0]
            de_lob_id = de[3]
            
            print(f"Data Executive: {de[1]} {de[2]} (ID: {de_id})")
            
            # Find attributes that need assignment in different cycles/reports
            result = conn.execute(text("""
                SELECT DISTINCT
                    ra.cycle_id,
                    tc.cycle_name,
                    ra.report_id,
                    r.report_name,
                    ra.attribute_id,
                    ra.attribute_name
                FROM report_attributes ra
                JOIN test_cycles tc ON ra.cycle_id = tc.cycle_id
                JOIN reports r ON ra.report_id = r.report_id
                JOIN cycle_report_scoping_tester_decisions tsd ON (
                    ra.attribute_id = tsd.attribute_id
                    AND ra.cycle_id = tsd.cycle_id
                    AND ra.report_id = tsd.report_id
                )
                WHERE ra.is_primary_key = false
                AND tsd.final_scoping = true
                AND NOT EXISTS (
                    SELECT 1 FROM data_provider_assignments dpa
                    WHERE dpa.cycle_id = ra.cycle_id
                    AND dpa.report_id = ra.report_id
                    AND dpa.attribute_id = ra.attribute_id
                )
                AND EXISTS (
                    SELECT 1 FROM attribute_lob_assignments ala
                    WHERE ala.cycle_id = ra.cycle_id
                    AND ala.report_id = ra.report_id
                    AND ala.attribute_id = ra.attribute_id
                    AND ala.lob_id = :lob_id
                )
                ORDER BY ra.cycle_id DESC, ra.report_id DESC
                LIMIT 8
            """), {"lob_id": de_lob_id})
            
            attrs = result.fetchall()
            
            if not attrs:
                print("No attributes found that need assignment. Creating some test data...")
                
                # Create attribute LOB assignments for testing
                result = conn.execute(text("""
                    SELECT ra.cycle_id, ra.report_id, ra.attribute_id, ra.attribute_name
                    FROM report_attributes ra
                    JOIN cycle_report_scoping_tester_decisions tsd ON (
                        ra.attribute_id = tsd.attribute_id
                        AND ra.cycle_id = tsd.cycle_id
                        AND ra.report_id = tsd.report_id
                    )
                    WHERE ra.is_primary_key = false
                    AND tsd.final_scoping = true
                    AND ra.cycle_id IN (8, 9)
                    AND NOT EXISTS (
                        SELECT 1 FROM attribute_lob_assignments ala
                        WHERE ala.cycle_id = ra.cycle_id
                        AND ala.report_id = ra.report_id
                        AND ala.attribute_id = ra.attribute_id
                        AND ala.lob_id = :lob_id
                    )
                    LIMIT 5
                """), {"lob_id": de_lob_id})
                
                for row in result.fetchall():
                    conn.execute(text("""
                        INSERT INTO attribute_lob_assignments
                        (cycle_id, report_id, attribute_id, lob_id, assigned_by, assigned_at)
                        VALUES (:cycle_id, :report_id, :attr_id, :lob_id, 1, :now)
                    """), {
                        "cycle_id": row[0],
                        "report_id": row[1],
                        "attr_id": row[2],
                        "lob_id": de_lob_id,
                        "now": datetime.utcnow()
                    })
                    print(f"  Created LOB assignment for {row[3]}")
            
            print(f"\nCreating assignments for {len(attrs)} attributes...")
            
            # Get data owner for some assignments
            result = conn.execute(text("""
                SELECT user_id, first_name, last_name
                FROM users
                WHERE lob_id = :lob_id
                AND role = 'Data Owner'
                AND is_active = true
                LIMIT 1
            """), {"lob_id": de_lob_id})
            data_owner = result.fetchone()
            
            # Create varied assignments
            for i, (cycle_id, cycle_name, report_id, report_name, attr_id, attr_name) in enumerate(attrs):
                
                # Vary the assignment states
                if i < 2:  # First 2 - pending (no data provider)
                    data_provider_id = None
                    status = 'Assigned'
                    assigned_at = datetime.utcnow() - timedelta(hours=i*2)
                elif i < 4:  # Next 2 - in progress
                    data_provider_id = data_owner[0] if data_owner else None
                    status = 'In Progress'
                    assigned_at = datetime.utcnow() - timedelta(days=i)
                else:  # Rest - completed
                    data_provider_id = data_owner[0] if data_owner else None
                    status = 'Completed'
                    assigned_at = datetime.utcnow() - timedelta(days=i*2)
                
                conn.execute(text("""
                    INSERT INTO data_provider_assignments
                    (cycle_id, report_id, attribute_id, lob_id, cdo_id, data_provider_id, 
                     assigned_by, assigned_at, status)
                    VALUES (:cycle_id, :report_id, :attr_id, :lob_id, :cdo_id, :dp_id,
                            :assigned_by, :assigned_at, :status)
                    ON CONFLICT (cycle_id, report_id, attribute_id) DO UPDATE
                    SET cdo_id = :cdo_id,
                        data_provider_id = :dp_id,
                        status = :status,
                        assigned_at = :assigned_at
                """), {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "attr_id": attr_id,
                    "lob_id": de_lob_id,
                    "cdo_id": de_id,
                    "dp_id": data_provider_id,
                    "assigned_by": de_id,
                    "assigned_at": assigned_at,
                    "status": status
                })
                
                dp_name = f"{data_owner[1]} {data_owner[2]}" if data_provider_id else "Not assigned"
                print(f"  ✅ {cycle_name} - {report_name}: {attr_name} -> {dp_name} ({status})")
            
            trans.commit()
            print("\n✅ Assignments created successfully!")
            
            # Show summary
            result = conn.execute(text("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM data_provider_assignments
                WHERE cdo_id = :cdo_id
                GROUP BY status
                ORDER BY status
            """), {"cdo_id": de_id})
            
            print("\nAssignment Summary:")
            for row in result.fetchall():
                print(f"  {row[0]}: {row[1]}")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    create_assignments()
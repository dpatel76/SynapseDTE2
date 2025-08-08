#!/usr/bin/env python3
"""Setup test data for Data Executive dashboard"""

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

def setup_test_data():
    """Setup test data for Data Executive"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("=== Setting up test data for Data Executive ===")
            
            # Get Data Executive user
            result = conn.execute(text("""
                SELECT u.user_id, u.first_name, u.last_name, u.email, u.lob_id, l.lob_name
                FROM users u
                JOIN lobs l ON u.lob_id = l.lob_id
                WHERE u.email = 'cdo@example.com'
                AND u.is_active = true
            """))
            de = result.fetchone()
            
            if not de:
                print("❌ Data Executive user cdo@example.com not found!")
                return
            
            de_id = de[0]
            de_lob_id = de[4]
            print(f"✅ Found Data Executive: {de[1]} {de[2]} (ID: {de_id}, LOB: {de[5]})")
            
            # Find non-PK attributes in cycle 9, report 156 that need assignment
            result = conn.execute(text("""
                SELECT DISTINCT
                    ra.attribute_id,
                    ra.attribute_name,
                    ra.is_primary_key,
                    tsd.final_scoping,
                    ala.lob_id
                FROM report_attributes ra
                LEFT JOIN cycle_report_scoping_tester_decisions tsd ON (
                    ra.attribute_id = tsd.attribute_id
                    AND ra.cycle_id = tsd.cycle_id
                    AND ra.report_id = tsd.report_id
                )
                LEFT JOIN attribute_lob_assignments ala ON (
                    ra.attribute_id = ala.attribute_id
                    AND ra.cycle_id = ala.cycle_id
                    AND ra.report_id = ala.report_id
                    AND ala.lob_id = :lob_id
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
                    AND dpa.lob_id = :lob_id
                )
                LIMIT 5
            """), {"lob_id": de_lob_id})
            
            attributes_to_assign = result.fetchall()
            
            print(f"\nFound {len(attributes_to_assign)} non-PK attributes needing assignment for LOB {de[5]}:")
            for attr in attributes_to_assign:
                print(f"  - {attr[1]} (ID: {attr[0]})")
            
            if not attributes_to_assign:
                print("\n⚠️  No unassigned non-PK attributes found for this LOB.")
                print("Creating some attribute LOB assignments...")
                
                # Create LOB assignments for non-PK attributes
                result = conn.execute(text("""
                    SELECT ra.attribute_id, ra.attribute_name
                    FROM report_attributes ra
                    JOIN cycle_report_scoping_tester_decisions tsd ON (
                        ra.attribute_id = tsd.attribute_id
                        AND ra.cycle_id = tsd.cycle_id
                        AND ra.report_id = tsd.report_id
                    )
                    WHERE ra.cycle_id = 9
                    AND ra.report_id = 156
                    AND ra.is_primary_key = false
                    AND tsd.final_scoping = true
                    AND NOT EXISTS (
                        SELECT 1 FROM attribute_lob_assignments ala
                        WHERE ala.cycle_id = 9
                        AND ala.report_id = 156
                        AND ala.attribute_id = ra.attribute_id
                        AND ala.lob_id = :lob_id
                    )
                    LIMIT 3
                """), {"lob_id": de_lob_id})
                
                attrs_to_assign_lob = result.fetchall()
                
                for attr_id, attr_name in attrs_to_assign_lob:
                    conn.execute(text("""
                        INSERT INTO attribute_lob_assignments 
                        (cycle_id, report_id, attribute_id, lob_id, assigned_by, assigned_at)
                        VALUES (9, 156, :attr_id, :lob_id, :de_id, :now)
                    """), {
                        "attr_id": attr_id,
                        "lob_id": de_lob_id,
                        "de_id": de_id,
                        "now": datetime.utcnow()
                    })
                    print(f"  ✅ Created LOB assignment for {attr_name}")
            
            # Create data provider assignments for testing
            # These will show up as assignments that need data providers
            for i, attr in enumerate(attributes_to_assign[:2]):  # Create 2 assignments
                attr_id = attr[0]
                attr_name = attr[1]
                
                # Create assignment record without data provider (CDO needs to assign)
                conn.execute(text("""
                    INSERT INTO data_provider_assignments 
                    (cycle_id, report_id, attribute_id, lob_id, cdo_id, assigned_by, assigned_at, status)
                    VALUES (9, 156, :attr_id, :lob_id, :cdo_id, :assigned_by, :now, 'Assigned')
                    ON CONFLICT (cycle_id, report_id, attribute_id) DO UPDATE
                    SET cdo_id = :cdo_id,
                        lob_id = :lob_id,
                        assigned_at = :now
                """), {
                    "attr_id": attr_id,
                    "lob_id": de_lob_id,
                    "cdo_id": de_id,
                    "assigned_by": 1,  # Admin user
                    "now": datetime.utcnow()
                })
                print(f"\n✅ Created assignment for {attr_name} - needs data provider")
            
            trans.commit()
            print("\n✅ Test data setup complete!")
            print("\nThe Data Executive dashboard should now show:")
            print("- Pending assignments that need data providers")
            print("- Recent activity for assigned attributes")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    print("Setting up test data for Data Executive dashboard...")
    setup_test_data()
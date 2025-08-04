#!/usr/bin/env python3
"""Check Data Executive assignments and dashboard data"""

import asyncio
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
# Convert to sync URL if needed
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def check_data_executive_assignments():
    """Check Data Executive assignments"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            print("=== Checking Data Executive Users ===")
            # Get all Data Executive users
            result = conn.execute(text("""
                SELECT u.user_id, u.first_name, u.last_name, u.email, u.lob_id, l.lob_name
                FROM users u
                JOIN lobs l ON u.lob_id = l.lob_id
                WHERE u.role = 'Data Executive'
                AND u.is_active = true
            """))
            data_execs = result.fetchall()
            
            print(f"\nFound {len(data_execs)} Data Executive users:")
            for de in data_execs:
                print(f"  - {de[1]} {de[2]} ({de[3]}) - LOB: {de[5]} (ID: {de[4]})")
            
            if not data_execs:
                print("\nNo Data Executive users found!")
                return
            
            # For each Data Executive, check their assignments
            for de in data_execs:
                de_id = de[0]
                de_name = f"{de[1]} {de[2]}"
                print(f"\n=== Checking assignments for {de_name} (ID: {de_id}) ===")
                
                # Check attribute LOB assignments for this Data Executive's LOB
                print("\n1. Checking AttributeLOBAssignments for Data Executive's LOB:")
                result = conn.execute(text("""
                    SELECT 
                        ala.assignment_id,
                        ala.cycle_id,
                        ala.report_id,
                        ala.attribute_id,
                        ra.attribute_name,
                        ala.lob_id,
                        l.lob_name,
                        ala.assigned_at
                    FROM attribute_lob_assignments ala
                    JOIN report_attributes ra ON ala.attribute_id = ra.attribute_id
                    JOIN lobs l ON ala.lob_id = l.lob_id
                    WHERE ala.lob_id = :lob_id
                    ORDER BY ala.assigned_at DESC
                    LIMIT 10
                """), {"lob_id": de[4]})
                
                ala_rows = result.fetchall()
                print(f"  Found {len(ala_rows)} AttributeLOBAssignments")
                for row in ala_rows:
                    print(f"    - Cycle {row[1]}, Report {row[2]}: {row[4]} -> LOB {row[6]}")
                
                # Check data provider assignments where this CDO assigned
                print("\n2. Checking DataProviderAssignments (assigned_by):")
                result = conn.execute(text("""
                    SELECT 
                        dpa.assignment_id,
                        dpa.cycle_id,
                        dpa.report_id,
                        dpa.attribute_id,
                        ra.attribute_name,
                        dpa.data_provider_id,
                        u.first_name || ' ' || u.last_name as data_provider_name,
                        dpa.assigned_at,
                        dpa.status
                    FROM data_provider_assignments dpa
                    LEFT JOIN report_attributes ra ON dpa.attribute_id = ra.attribute_id
                    LEFT JOIN users u ON dpa.data_provider_id = u.user_id
                    WHERE dpa.assigned_by = :cdo_id
                    ORDER BY dpa.assigned_at DESC
                    LIMIT 10
                """), {"cdo_id": de_id})
                
                dpa_rows = result.fetchall()
                print(f"  Found {len(dpa_rows)} DataProviderAssignments (assigned_by)")
                for row in dpa_rows:
                    print(f"    - Cycle {row[1]}, Report {row[2]}: {row[4]} -> {row[6]} (Status: {row[8]})")
                
                # Check data provider assignments where this CDO is listed as cdo_id
                print("\n3. Checking DataProviderAssignments (cdo_id):")
                result = conn.execute(text("""
                    SELECT 
                        dpa.assignment_id,
                        dpa.cycle_id,
                        dpa.report_id,
                        dpa.attribute_id,
                        ra.attribute_name,
                        dpa.data_provider_id,
                        u.first_name || ' ' || u.last_name as data_provider_name,
                        dpa.assigned_at,
                        dpa.status
                    FROM data_provider_assignments dpa
                    LEFT JOIN report_attributes ra ON dpa.attribute_id = ra.attribute_id
                    LEFT JOIN users u ON dpa.data_provider_id = u.user_id
                    WHERE dpa.cdo_id = :cdo_id
                    ORDER BY dpa.assigned_at DESC
                    LIMIT 10
                """), {"cdo_id": de_id})
                
                dpa_cdo_rows = result.fetchall()
                print(f"  Found {len(dpa_cdo_rows)} DataProviderAssignments (cdo_id)")
                for row in dpa_cdo_rows:
                    print(f"    - Cycle {row[1]}, Report {row[2]}: {row[4]} -> {row[6]} (Status: {row[8]})")
                
                # Check non-PK attributes that need assignment
                print("\n4. Checking non-PK attributes needing assignment:")
                result = conn.execute(text("""
                    SELECT DISTINCT
                        ra.cycle_id,
                        ra.report_id,
                        ra.attribute_id,
                        ra.attribute_name,
                        ra.is_primary_key,
                        tsd.final_scoping
                    FROM report_attributes ra
                    LEFT JOIN cycle_report_scoping_tester_decisions tsd ON (
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
                        AND dpa.data_provider_id IS NOT NULL
                    )
                    ORDER BY ra.cycle_id DESC, ra.report_id DESC
                    LIMIT 10
                """))
                
                pending_attrs = result.fetchall()
                print(f"  Found {len(pending_attrs)} non-PK attributes needing data provider assignment")
                for row in pending_attrs:
                    print(f"    - Cycle {row[0]}, Report {row[1]}: {row[3]} (Scoped: {row[5]})")
            
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    print("Checking Data Executive assignments...")
    check_data_executive_assignments()
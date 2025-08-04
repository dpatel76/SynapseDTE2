#!/usr/bin/env python3
"""Final Data Owner phase analysis with fact-based evaluation"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json
from collections import defaultdict

async def final_analysis():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        cycle_id = 55
        report_id = 156
        
        print("=== FACT-BASED DATA OWNER PHASE EVALUATION ===")
        print(f"Cycle ID: {cycle_id}, Report ID: {report_id}\n")
        
        # (1) When are Data Executive assignments created?
        print("(1) WHEN PHASE STARTS, DATA EXECUTIVE ASSIGNMENTS WILL BE CREATED:")
        print("    - Created by: StartDataProviderPhaseUseCase._create_universal_assignments()")
        print("    - Timing: Immediately when phase is started")
        print("    - Type: UniversalAssignment records")
        print("    - assignment_type = 'DATA_OWNER_IDENTIFICATION'")
        print("    - context_type = 'attribute_assignment'")
        
        # (2) Count scoped non-PK attributes
        print("\n(2) SCOPED NON-PK ATTRIBUTES AND VERSION:")
        
        # Get scoping phase
        scoping_result = await db.execute(text("""
            SELECT phase_id, status 
            FROM workflow_phases
            WHERE cycle_id = :cycle_id AND report_id = :report_id 
            AND phase_name = 'Scoping' AND status = 'Complete'
            ORDER BY created_at DESC LIMIT 1
        """), {"cycle_id": cycle_id, "report_id": report_id})
        
        scoping_phase = scoping_result.first()
        scoping_phase_id = scoping_phase.phase_id
        
        # Count attributes
        attr_result = await db.execute(text("""
            SELECT 
                COUNT(CASE WHEN report_owner_decision = 'approved' AND is_primary_key = false THEN 1 END) as approved_non_pk
            FROM cycle_report_scoping_attributes
            WHERE phase_id = :phase_id
        """), {"phase_id": scoping_phase_id})
        
        counts = attr_result.first()
        approved_non_pk_count = counts.approved_non_pk
        
        print(f"    - Approved Non-PK Attributes: {approved_non_pk_count}")
        print(f"    - Version: phase_id = {scoping_phase_id}")
        
        # List the attributes
        attr_list_result = await db.execute(text("""
            SELECT attribute_id, 
                   JSON_EXTRACT(attribute_json, '$.attribute_name') as attribute_name
            FROM cycle_report_scoping_attributes
            WHERE phase_id = :phase_id
            AND is_primary_key = false
            AND report_owner_decision = 'approved'
            ORDER BY JSON_EXTRACT(attribute_json, '$.attribute_name')
        """), {"phase_id": scoping_phase_id})
        
        approved_attrs = []
        for row in attr_list_result:
            approved_attrs.append({'id': row.attribute_id, 'name': row.attribute_name})
        
        print("    - Attributes:")
        for i, attr in enumerate(approved_attrs, 1):
            print(f"      {i}. {attr['name']} (ID: {attr['id']})")
        
        # (3) Count approved samples  
        print("\n(3) APPROVED SAMPLES AND VERSION:")
        
        # Get sample selection phase
        sample_result = await db.execute(text("""
            SELECT phase_id, status
            FROM workflow_phases
            WHERE cycle_id = :cycle_id AND report_id = :report_id 
            AND phase_name = 'Sample Selection' AND status = 'Complete'
            ORDER BY created_at DESC LIMIT 1
        """), {"cycle_id": cycle_id, "report_id": report_id})
        
        sample_phase = sample_result.first()
        sample_phase_id = sample_phase.phase_id
        
        # Count approved samples
        sample_count_result = await db.execute(text("""
            SELECT COUNT(*) as approved_count
            FROM cycle_report_sample_selection_samples
            WHERE phase_id = :phase_id
            AND report_owner_decision = 'approved'
        """), {"phase_id": sample_phase_id})
        
        approved_sample_count = sample_count_result.scalar()
        print(f"    - Approved Samples: {approved_sample_count}")
        print(f"    - Version: phase_id = {sample_phase_id}")
        
        # Get unique LOBs from approved samples
        lob_result = await db.execute(text("""
            SELECT DISTINCT 
                JSON_EXTRACT(sample_data, '$.lob_name') as lob_name,
                lob_id
            FROM cycle_report_sample_selection_samples
            WHERE phase_id = :phase_id
            AND report_owner_decision = 'approved'
            AND JSON_EXTRACT(sample_data, '$.lob_name') IS NOT NULL
        """), {"phase_id": sample_phase_id})
        
        unique_lobs = []
        lob_ids = {}
        for row in lob_result:
            if row.lob_name:
                lob_name = row.lob_name.strip('"')  # Remove JSON quotes
                unique_lobs.append(lob_name)
                lob_ids[lob_name] = row.lob_id
        
        unique_lobs = sorted(set(unique_lobs))
        print(f"    - Unique LOBs from approved samples: {len(unique_lobs)}")
        for i, lob in enumerate(unique_lobs, 1):
            print(f"      {i}. {lob}")
        
        # (4) Calculate Data Executive assignments
        print("\n(4) DATA EXECUTIVE ASSIGNMENTS TO BE CREATED:")
        
        # Get Data Executives for LOBs
        if unique_lobs:
            # Get from LOB table
            cdo_result = await db.execute(text("""
                SELECT l.lob_name, l.lob_id, 
                       u.user_id, u.first_name, u.last_name, u.email
                FROM lobs l
                LEFT JOIN users u ON l.chief_data_officer_id = u.user_id
                WHERE l.lob_name = ANY(:lobs)
                AND l.is_active = true
                ORDER BY l.lob_name
            """), {"lobs": unique_lobs})
            
            data_executives = {}
            exec_assignments = defaultdict(list)
            
            print("\n    Data Executives by LOB:")
            for row in cdo_result:
                if row.user_id:
                    exec_info = {
                        'user_id': row.user_id,
                        'name': f"{row.first_name} {row.last_name}",
                        'email': row.email
                    }
                    data_executives[row.lob_name] = exec_info
                    print(f"    - {row.lob_name}: {exec_info['name']} ({exec_info['email']})")
                    
                    # Calculate assignments for this executive
                    for attr in approved_attrs:
                        exec_assignments[exec_info['email']].append({
                            'attribute': attr['name'],
                            'lob': row.lob_name
                        })
                else:
                    print(f"    - {row.lob_name}: NO DATA EXECUTIVE ASSIGNED")
        
        # Summary
        total_assignments = approved_non_pk_count * len(unique_lobs)
        print(f"\n    TOTAL ASSIGNMENTS: {approved_non_pk_count} attributes × {len(unique_lobs)} LOBs = {total_assignments}")
        
        print("\n    Assignments by Data Executive:")
        total_listed = 0
        for exec_email, assignments in sorted(exec_assignments.items()):
            print(f"\n    {exec_email}: {len(assignments)} assignments")
            # List all assignments
            for i, assignment in enumerate(assignments, 1):
                print(f"      {i}. {assignment['attribute']} - {assignment['lob']}")
            total_listed += len(assignments)
        
        print(f"\n    Total assignments to be created: {total_listed}")
        
        # Check existing assignments
        existing_result = await db.execute(text("""
            SELECT COUNT(*) as count
            FROM universal_assignments
            WHERE assignment_type = 'DATA_OWNER_IDENTIFICATION'
            AND context_type = 'attribute_assignment'
            AND JSON_EXTRACT(context_data, '$.cycle_id') = :cycle_id
            AND JSON_EXTRACT(context_data, '$.report_id') = :report_id
        """), {"cycle_id": cycle_id, "report_id": report_id})
        
        existing_count = existing_result.scalar()
        if existing_count > 0:
            print(f"\n    NOTE: {existing_count} assignments already exist in database!")
    
    await engine.dispose()

asyncio.run(final_analysis())
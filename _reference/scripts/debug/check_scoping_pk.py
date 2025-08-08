#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.scoping import TesterScopingDecision
from app.models.testing import DataProviderAssignment
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import asyncio

async def check_scoping_primary_keys():
    async with AsyncSessionLocal() as db:
        # Check scoping decisions for cycle 9, report 156
        cycle_id = 9
        report_id = 156
        
        print(f"Checking scoping decisions for cycle {cycle_id}, report {report_id}")
        
        # Get scoping decisions with attributes
        scoping_query = select(TesterScopingDecision).options(
            selectinload(TesterScopingDecision.attribute)
        ).where(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id,
            TesterScopingDecision.final_scoping == True
        )
        
        result = await db.execute(scoping_query)
        scoping_decisions = result.scalars().all()
        
        print(f"Found {len(scoping_decisions)} scoped attributes")
        
        # Check for primary key attributes in scoping
        pk_scoped = [s for s in scoping_decisions if s.attribute and s.attribute.is_primary_key]
        non_pk_scoped = [s for s in scoping_decisions if s.attribute and not s.attribute.is_primary_key]
        
        print(f"Primary key scoped attributes: {len(pk_scoped)}")
        print(f"Non-primary key scoped attributes: {len(non_pk_scoped)}")
        
        if pk_scoped:
            print("\nPrimary Key Attributes (from scoping):")
            for pk_scoped_attr in pk_scoped:
                print(f"  - {pk_scoped_attr.attribute.attribute_name} (ID: {pk_scoped_attr.attribute_id}, is_primary_key: {pk_scoped_attr.attribute.is_primary_key})")
        
        print("\nAll Scoped Attributes:")
        for scoped in scoping_decisions:
            if scoped.attribute:
                print(f"  - {scoped.attribute.attribute_name} (ID: {scoped.attribute_id}, is_primary_key: {scoped.attribute.is_primary_key})")
        
        # Now check data provider assignments
        print(f"\n--- Data Provider Assignments ---")
        assignment_query = select(DataProviderAssignment).options(
            selectinload(DataProviderAssignment.attribute)
        ).where(
            DataProviderAssignment.cycle_id == cycle_id,
            DataProviderAssignment.report_id == report_id
        )
        
        assignment_result = await db.execute(assignment_query)
        assignments = assignment_result.scalars().all()
        
        print(f"Found {len(assignments)} data provider assignments")
        
        pk_assignments = [a for a in assignments if a.attribute and a.attribute.is_primary_key]
        non_pk_assignments = [a for a in assignments if a.attribute and not a.attribute.is_primary_key]
        
        print(f"Primary key assignments: {len(pk_assignments)}")
        print(f"Non-primary key assignments: {len(non_pk_assignments)}")
        
        if pk_assignments:
            print("\nPrimary Key Attributes (from assignments):")
            for pk_assignment in pk_assignments:
                print(f"  - {pk_assignment.attribute.attribute_name} (ID: {pk_assignment.attribute_id})")

asyncio.run(check_scoping_primary_keys()) 
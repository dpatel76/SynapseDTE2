#!/usr/bin/env python3
"""
Test Data Provider Core Logic Without Authentication
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from app.core.config import settings
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
# AttributeLOBAssignment removed - table doesn't exist
# from app.models.data_owner import DataProviderAssignment, DataProviderSLAViolation

# Fix database URL for async operations
database_url = settings.database_url
if "postgresql://" in database_url and "asyncpg" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async database engine
engine = create_async_engine(database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_core_logic():
    """Test the core data provider status logic"""
    async with AsyncSessionLocal() as db:
        try:
            print("=== TESTING CORE DATA PROVIDER LOGIC ===")
            
            # Test both cycles
            test_cases = [
                (8, 160, "Recent cycle (might be what user is viewing)"),
                (4, 156, "Cycle with scoped attributes")
            ]
            
            for cycle_id, report_id, description in test_cases:
                print(f"\n--- Testing {description}: cycle_id={cycle_id}, report_id={report_id} ---")
                
                # Step 1: Get scoped non-primary key attributes
                scoped_attributes = await db.execute(
                    select(ReportAttribute)
                    .where(and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True,
                        ReportAttribute.is_primary_key == False
                    ))
                )
                scoped_attrs = scoped_attributes.scalars().all()
                total_attributes = len(scoped_attrs)
                print(f"1. Scoped non-PK attributes: {total_attributes}")
                
                if total_attributes == 0:
                    print("   -> Would return empty status (should work now)")
                    continue
                
                # Step 2: Get LOB assignments
                lob_assignments = await db.execute(
                    select(AttributeLOBAssignment)
                    .where(and_(
                        AttributeLOBAssignment.cycle_id == cycle_id,
                        AttributeLOBAssignment.report_id == report_id
                    ))
                )
                lob_assignments = lob_assignments.scalars().all()
                attributes_with_lob_assignments = len(set(assignment.attribute_id for assignment in lob_assignments))
                print(f"2. Attributes with LOB assignments: {attributes_with_lob_assignments}")
                
                # Step 3: Get data provider assignments
                data_owner_assignments = await db.execute(
                    select(DataProviderAssignment)
                    .where(and_(
                        DataProviderAssignment.cycle_id == cycle_id,
                        DataProviderAssignment.report_id == report_id
                    ))
                )
                data_owner_assignments = data_owner_assignments.scalars().all()
                attributes_with_data_owners = len(set(assignment.attribute_id for assignment in data_owner_assignments if assignment.data_owner_id))
                pending_cdo_assignments = len([a for a in data_owner_assignments if not a.data_owner_id])
                print(f"3. Attributes with data providers: {attributes_with_data_owners}")
                print(f"4. Pending CDO assignments: {pending_cdo_assignments}")
                
                # Step 4: Get overdue assignments
                overdue_assignments = await db.execute(
                    select(DataProviderSLAViolation)
                    .where(and_(
                        DataProviderSLAViolation.cycle_id == cycle_id,
                        DataProviderSLAViolation.report_id == report_id,
                        DataProviderSLAViolation.is_resolved == False
                    ))
                )
                overdue_assignments = overdue_assignments.scalars().all()
                overdue_count = len(overdue_assignments)
                print(f"5. Overdue assignments: {overdue_count}")
                
                # Step 5: Get phase status
                phase = await db.execute(
                    select(WorkflowPhase)
                    .where(and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == 'Data Provider ID'
                    ))
                )
                phase = phase.scalar_one_or_none()
                phase_status = phase.status if phase else "Not Started"
                print(f"6. Phase status: {phase_status}")
                
                # Calculate completion requirements
                can_submit_lob_assignments = attributes_with_lob_assignments == total_attributes
                can_complete_phase = attributes_with_data_owners == total_attributes and overdue_count == 0
                print(f"7. Can submit LOB assignments: {can_submit_lob_assignments}")
                print(f"8. Can complete phase: {can_complete_phase}")
                
                print("   ✅ Core logic completed successfully!")
                
        except Exception as e:
            print(f"ERROR in core logic: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_core_logic()) 
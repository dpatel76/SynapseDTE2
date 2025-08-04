#!/usr/bin/env python3
"""Initialize scoping phase directly without permission checks"""

import asyncio
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase
from app.models.scoping import ScopingVersion, ScopingAttribute
from app.models.report_attribute import ReportAttribute
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import uuid

async def init_scoping():
    """Initialize scoping phase with initial version"""
    async with AsyncSessionLocal() as db:
        # Get the scoping phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == 55,
                WorkflowPhase.report_id == 156,
                WorkflowPhase.phase_name == "Scoping"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            print("❌ Scoping phase not found!")
            return
            
        print(f"Found scoping phase: {phase.phase_id}")
        
        # Check if initial version already exists
        version_query = select(ScopingVersion).where(
            ScopingVersion.phase_id == phase.phase_id
        )
        existing_version = await db.execute(version_query)
        if existing_version.scalar_one_or_none():
            print("✅ Initial version already exists")
            return
        
        # Get planning phase and attributes
        planning_phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == phase.cycle_id,
                WorkflowPhase.report_id == phase.report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        planning_phase_result = await db.execute(planning_phase_query)
        planning_phase = planning_phase_result.scalar_one_or_none()
        
        if not planning_phase:
            print("❌ Planning phase not found!")
            return
            
        # Get planning attributes
        planning_attrs_query = select(ReportAttribute).where(
            ReportAttribute.phase_id == planning_phase.phase_id
        )
        planning_attrs_result = await db.execute(planning_attrs_query)
        planning_attributes = planning_attrs_result.scalars().all()
        
        print(f"Found {len(planning_attributes)} planning attributes")
        
        # Create initial scoping version
        initial_version = ScopingVersion(
            phase_id=phase.phase_id,
            version_number=1,
            version_status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by_id=3,  # Using user_id 3
            updated_by_id=3
        )
        db.add(initial_version)
        await db.flush()  # Get the version_id
        
        print(f"Created initial version: {initial_version.version_id}")
        
        # Create scoping attributes from planning attributes
        scoping_attributes = []
        for planning_attr in planning_attributes:
            scoping_attr = ScopingAttribute(
                version_id=initial_version.version_id,
                phase_id=phase.phase_id,
                planning_attribute_id=planning_attr.id,
                llm_recommendation={},  # Empty initial recommendation
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by_id=3,
                updated_by_id=3
            )
            scoping_attributes.append(scoping_attr)
        
        db.add_all(scoping_attributes)
        
        # Update phase state
        phase.state = "In Progress"
        phase.actual_start_date = datetime.utcnow()
        phase.started_by = 3
        phase.updated_at = datetime.utcnow()
        
        # Update version statistics
        initial_version.total_attributes = len(scoping_attributes)
        initial_version.updated_at = datetime.utcnow()
        
        await db.commit()
        
        print(f"✅ Successfully initialized scoping phase:")
        print(f"   - Created version {initial_version.version_number}")
        print(f"   - Imported {len(scoping_attributes)} attributes")
        print(f"   - Phase state: {phase.state}")

if __name__ == "__main__":
    asyncio.run(init_scoping())
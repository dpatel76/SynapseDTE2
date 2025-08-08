#!/usr/bin/env python3
"""
Properly approve a data profiling version and all its rules.
This ensures both the version and rules are in the correct state for execution.
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule
from app.models.workflow import WorkflowPhase

async def approve_version_and_rules(cycle_id: int, report_id: int):
    # Create async engine and session
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt")
    
    engine = create_async_engine(database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get phase_id for Data Profiling
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
            phase_result = await db.execute(phase_query)
            phase = phase_result.scalar_one_or_none()
            
            if not phase:
                print(f"❌ Data Profiling phase not found for cycle {cycle_id}, report {report_id}")
                return
            
            print(f"✅ Found Data Profiling phase: {phase.phase_id}")
            
            # Get latest version
            version_query = select(DataProfilingRuleVersion).where(
                DataProfilingRuleVersion.phase_id == phase.phase_id
            ).order_by(DataProfilingRuleVersion.version_number.desc()).limit(1)
            
            version_result = await db.execute(version_query)
            version = version_result.scalar_one_or_none()
            
            if not version:
                print(f"❌ No data profiling version found for phase {phase.phase_id}")
                return
            
            print(f"📋 Found version {version.version_number} (ID: {version.version_id})")
            print(f"   Current status: {version.version_status}")
            
            # Update version status to approved
            if version.version_status != 'approved':
                version.version_status = 'approved'
                version.approved_at = datetime.utcnow()
                version.approved_by_id = 1  # System user
                version.updated_at = datetime.utcnow()
                print(f"✅ Version marked as APPROVED")
            
            # Update all rules to approved status
            rules_result = await db.execute(
                update(ProfilingRule)
                .where(ProfilingRule.version_id == version.version_id)
                .values(
                    status='approved',
                    approved_by_id=1,  # System user
                    approved_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            rules_updated = rules_result.rowcount
            print(f"✅ Updated {rules_updated} rules to 'approved' status")
            
            # Update version rule counts
            version.total_rules = rules_updated
            version.approved_rules = rules_updated
            version.rejected_rules = 0
            version.updated_at = datetime.utcnow()
            
            await db.commit()
            print(f"\n✅ Version {version.version_number} and all its rules are now APPROVED!")
            print(f"   You can now execute the profiling rules.")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            await db.rollback()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python approve_version_with_rules.py <cycle_id> <report_id>")
        print("Example: python approve_version_with_rules.py 55 156")
        sys.exit(1)
    
    cycle_id = int(sys.argv[1])
    report_id = int(sys.argv[2])
    
    print(f"🚀 Approving version and rules for Cycle {cycle_id}, Report {report_id}")
    asyncio.run(approve_version_and_rules(cycle_id, report_id))
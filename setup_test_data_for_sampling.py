#!/usr/bin/env python3
"""
Setup test data for sample generation
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.cycle_report_data_source import CycleReportDataSource

CYCLE_ID = 55
REPORT_ID = 156

async def setup_test_data():
    """Setup minimal test data for sample generation"""
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://testuser:testpass@localhost:5432/test_platform_db")
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print(f"=== Setting up test data for Cycle {CYCLE_ID}, Report {REPORT_ID} ===\n")
        
        # Get planning phase
        planning_phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == CYCLE_ID,
                    WorkflowPhase.report_id == REPORT_ID,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
        )
        planning_phase = planning_phase_query.scalar_one_or_none()
        
        if not planning_phase:
            print("❌ No planning phase found!")
            return
        
        print(f"Planning Phase ID: {planning_phase.phase_id}")
        
        # 1. Add some test attributes to planning phase
        existing_attrs_query = await db.execute(
            select(ReportAttribute).where(
                ReportAttribute.phase_id == planning_phase.phase_id
            )
        )
        existing_attrs = existing_attrs_query.scalars().all()
        
        if len(existing_attrs) == 0:
            print("\n1. Creating test attributes in planning phase...")
            
            test_attributes = [
                {
                    "attribute_name": "customer_id",
                    "data_type": "integer",
                    "is_primary_key": True,
                    "mandatory_flag": True,
                    "business_rules": "Unique identifier for customer"
                },
                {
                    "attribute_name": "credit_limit",
                    "data_type": "numeric",
                    "is_primary_key": False,
                    "mandatory_flag": True,
                    "business_rules": "Customer credit limit in USD"
                },
                {
                    "attribute_name": "account_status",
                    "data_type": "text",
                    "is_primary_key": False,
                    "mandatory_flag": True,
                    "business_rules": "Active, Inactive, or Suspended"
                },
                {
                    "attribute_name": "balance",
                    "data_type": "decimal",
                    "is_primary_key": False,
                    "mandatory_flag": False,
                    "business_rules": "Current account balance"
                }
            ]
            
            for attr_data in test_attributes:
                attr = ReportAttribute(
                    phase_id=planning_phase.phase_id,
                    attribute_name=attr_data["attribute_name"],
                    data_type=attr_data["data_type"],
                    is_primary_key=attr_data["is_primary_key"],
                    mandatory_flag=attr_data["mandatory_flag"],
                    business_rules=attr_data["business_rules"],
                    is_scoped=True,  # Mark as scoped for sample generation
                    created_by=1,
                    updated_by=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(attr)
            
            await db.commit()
            print(f"   ✅ Created {len(test_attributes)} test attributes")
        else:
            print(f"\n1. Found {len(existing_attrs)} existing attributes")
            
            # Update them to be scoped
            for attr in existing_attrs:
                if not attr.is_scoped:
                    attr.is_scoped = True
                    attr.updated_at = datetime.utcnow()
            
            await db.commit()
            print("   ✅ Updated attributes to be scoped")
        
        # 2. Add a mock data source to planning phase
        data_sources_query = await db.execute(
            select(CycleReportDataSource).where(
                CycleReportDataSource.phase_id == planning_phase.phase_id
            )
        )
        existing_sources = data_sources_query.scalars().all()
        
        if len(existing_sources) == 0:
            print("\n2. Creating mock data source...")
            
            # Update phase_data to include a mock data source
            phase_data = planning_phase.phase_data or {}
            phase_data["data_sources"] = [{
                "id": 1,
                "name": "Test Database",
                "type": "database",
                "criteria": {
                    "database_name": "test_db",
                    "schema_name": "public",
                    "table_name": "customer_data"
                }
            }]
            
            planning_phase.phase_data = phase_data
            planning_phase.updated_at = datetime.utcnow()
            
            # Flag as modified
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(planning_phase, 'phase_data')
            
            await db.commit()
            print("   ✅ Created mock data source")
        else:
            print(f"\n2. Found {len(existing_sources)} existing data sources")
        
        # 3. Check scoping phase
        scoping_phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == CYCLE_ID,
                    WorkflowPhase.report_id == REPORT_ID,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
        )
        scoping_phase = scoping_phase_query.scalar_one_or_none()
        
        if scoping_phase:
            print(f"\n3. Scoping Phase ID: {scoping_phase.phase_id}")
            print("   Note: Scoping phase exists but may not have approved attributes")
            print("   Sample generation will fall back to planning attributes")
        else:
            print("\n3. No scoping phase found - sample generation will use planning attributes")
        
        print("\n=== Setup Complete ===")
        print("You should now be able to generate samples.")
        print("\nNote: Since we're using mock data, the actual sample generation")
        print("will create mock samples rather than querying a real database.")
        
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_test_data())
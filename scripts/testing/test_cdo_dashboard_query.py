#!/usr/bin/env python3
"""Test CDO dashboard query directly"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
# Convert to async URL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def test_queries():
    """Test CDO dashboard queries"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("=== Testing CDO Dashboard Queries ===\n")
            
            # 1. Simple count query
            result = await session.execute(
                text("SELECT COUNT(*) FROM data_provider_assignments WHERE cdo_id = 5")
            )
            count = result.scalar()
            print(f"1. Simple count of assignments for CDO 5: {count}")
            
            # 2. Get assignment details
            result = await session.execute(
                text("""
                    SELECT 
                        dpa.assignment_id,
                        dpa.cycle_id,
                        dpa.report_id,
                        dpa.attribute_id,
                        dpa.cdo_id,
                        dpa.data_provider_id,
                        dpa.status,
                        ra.attribute_name
                    FROM data_provider_assignments dpa
                    LEFT JOIN report_attributes ra ON dpa.attribute_id = ra.attribute_id
                    WHERE dpa.cdo_id = 5
                """)
            )
            assignments = result.fetchall()
            print(f"\n2. Assignments with attribute names:")
            for a in assignments:
                print(f"   - Assignment {a[0]}: Cycle {a[1]}, Report {a[2]}, Attr {a[7]} (ID: {a[3]}), Status: {a[6]}")
            
            # 3. Test the full join query
            from app.models.testing import DataProviderAssignment
            from app.models.report_attribute import ReportAttribute
            from app.models.report import Report
            from app.models.test_cycle import TestCycle
            from app.models.user import User
            
            result = await session.execute(
                select(DataProviderAssignment)
                .where(DataProviderAssignment.cdo_id == 5)
            )
            orm_assignments = result.scalars().all()
            print(f"\n3. ORM query for DataProviderAssignment: Found {len(orm_assignments)} assignments")
            
            # 4. Test with joins
            result = await session.execute(
                select(DataProviderAssignment, ReportAttribute)
                .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
                .where(DataProviderAssignment.cdo_id == 5)
            )
            joined_assignments = result.all()
            print(f"\n4. ORM query with ReportAttribute join: Found {len(joined_assignments)} assignments")
            
            # 5. Check if the issue is with missing report attributes
            result = await session.execute(
                text("""
                    SELECT 
                        dpa.assignment_id,
                        dpa.attribute_id,
                        ra.attribute_id as ra_attr_id,
                        ra.attribute_name
                    FROM data_provider_assignments dpa
                    LEFT JOIN report_attributes ra 
                        ON dpa.attribute_id = ra.attribute_id
                        AND dpa.cycle_id = ra.cycle_id
                        AND dpa.report_id = ra.report_id
                    WHERE dpa.cdo_id = 5
                """)
            )
            attr_check = result.fetchall()
            print(f"\n5. Checking attribute join with cycle/report match:")
            for a in attr_check:
                print(f"   - Assignment {a[0]}: DPA attr_id={a[1]}, RA attr_id={a[2]}, Name={a[3]}")
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_queries())
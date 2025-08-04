#!/usr/bin/env python3
"""Fix both llm_generated flag and historical issues for cycle 13"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, and_, or_, select
from app.models.report_attribute import ReportAttribute
from app.core.config import get_settings

settings = get_settings()

# The only 2 attributes that should have historical issues based on user selection
VALID_HISTORICAL_ATTRIBUTES = [
    "Cycle Ending Balances Mix - Penalty",  
    "APR at Cycle End"
]

async def fix_cycle_13_issues():
    # Create async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Starting fixes for cycle 13...")
        
        # 1. Fix llm_generated flag where LLM data exists
        result1 = await session.execute(
            update(ReportAttribute)
            .where(
                and_(
                    ReportAttribute.cycle_id == 13,
                    ReportAttribute.report_id == 156,
                    or_(
                        ReportAttribute.llm_rationale != None,
                        ReportAttribute.risk_score != None
                    )
                )
            )
            .values(llm_generated=True)
        )
        print(f"✅ Updated {result1.rowcount} attributes with llm_generated=True")
        
        # 2. Reset all historical_issues_flag to False
        result2 = await session.execute(
            update(ReportAttribute)
            .where(
                and_(
                    ReportAttribute.cycle_id == 13,
                    ReportAttribute.report_id == 156
                )
            )
            .values(historical_issues_flag=False)
        )
        print(f"✅ Reset {result2.rowcount} attributes to historical_issues_flag=False")
        
        # 3. Set only the intended attributes to True
        result3 = await session.execute(
            update(ReportAttribute)
            .where(
                and_(
                    ReportAttribute.cycle_id == 13,
                    ReportAttribute.report_id == 156,
                    ReportAttribute.attribute_name.in_(VALID_HISTORICAL_ATTRIBUTES)
                )
            )
            .values(historical_issues_flag=True)
        )
        print(f"✅ Set {result3.rowcount} attributes to historical_issues_flag=True")
        
        # Verify the historical issues
        verify_query = select(ReportAttribute.attribute_name).where(
            and_(
                ReportAttribute.cycle_id == 13,
                ReportAttribute.report_id == 156,
                ReportAttribute.historical_issues_flag == True
            )
        )
        result = await session.execute(verify_query)
        hist_attrs = result.scalars().all()
        
        print(f"\nAttributes with historical_issues_flag=True:")
        for attr in hist_attrs:
            print(f"   - {attr}")
        
        await session.commit()
        print("\n✅ All fixes completed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_cycle_13_issues())
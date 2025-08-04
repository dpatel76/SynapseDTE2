#!/usr/bin/env python3
"""Fix historical issues to only Current Credit Limit and check LLM descriptions"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, and_, select
from app.models.report_attribute import ReportAttribute
from app.core.config import get_settings

settings = get_settings()

# Only Current Credit Limit should have historical issues
VALID_HISTORICAL_ATTRIBUTE = "Current Credit Limit"

async def fix_cycle_13_correct():
    # Create async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Fixing cycle 13 data...")
        
        # 1. Reset ALL historical_issues_flag to False
        result1 = await session.execute(
            update(ReportAttribute)
            .where(
                and_(
                    ReportAttribute.cycle_id == 13,
                    ReportAttribute.report_id == 156
                )
            )
            .values(historical_issues_flag=False)
        )
        print(f"✅ Reset {result1.rowcount} attributes to historical_issues_flag=False")
        
        # 2. Set only Current Credit Limit to True
        result2 = await session.execute(
            update(ReportAttribute)
            .where(
                and_(
                    ReportAttribute.cycle_id == 13,
                    ReportAttribute.report_id == 156,
                    ReportAttribute.attribute_name == VALID_HISTORICAL_ATTRIBUTE
                )
            )
            .values(historical_issues_flag=True)
        )
        print(f"✅ Set {result2.rowcount} attribute(s) to historical_issues_flag=True")
        
        # 3. Check what's in the description field for a few attributes
        check_query = select(
            ReportAttribute.attribute_name,
            ReportAttribute.description,
            ReportAttribute.llm_generated,
            ReportAttribute.historical_issues_flag
        ).where(
            and_(
                ReportAttribute.cycle_id == 13,
                ReportAttribute.report_id == 156
            )
        ).limit(10)
        
        result = await session.execute(check_query)
        attrs = result.all()
        
        print(f"\nSample attributes from cycle 13:")
        for attr in attrs[:5]:
            print(f"\n- {attr.attribute_name}")
            print(f"  description: {attr.description[:50]}...")
            print(f"  llm_generated: {attr.llm_generated}")
            print(f"  historical_issues: {attr.historical_issues_flag}")
        
        # Verify Current Credit Limit
        verify_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == 13,
                ReportAttribute.report_id == 156,
                ReportAttribute.attribute_name == VALID_HISTORICAL_ATTRIBUTE
            )
        )
        result = await session.execute(verify_query)
        credit_limit = result.scalar_one_or_none()
        
        if credit_limit:
            print(f"\n✅ Current Credit Limit verified:")
            print(f"   - historical_issues_flag: {credit_limit.historical_issues_flag}")
            print(f"   - description: {credit_limit.description[:50]}...")
        else:
            print(f"\n❌ Warning: Current Credit Limit attribute not found!")
        
        await session.commit()
        print("\n✅ Fixes completed!")

if __name__ == "__main__":
    asyncio.run(fix_cycle_13_correct())
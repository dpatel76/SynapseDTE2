#!/usr/bin/env python3
"""Fix historical issues flags for cycle 13 - only keep the intended 2 attributes"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, and_
from app.models.report_attribute import ReportAttribute
from app.core.config import get_settings

settings = get_settings()

# The only 2 attributes that should have historical issues based on user selection
VALID_HISTORICAL_ATTRIBUTES = [
    "Cycle Ending Balances Mix - Penalty",  # One of the originally selected
    "APR at Cycle End"  # Another originally selected
]

async def fix_historical_flags():
    # Create async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # First, set all historical_issues_flag to False for cycle 13
        await session.execute(
            update(ReportAttribute)
            .where(
                and_(
                    ReportAttribute.cycle_id == 13,
                    ReportAttribute.report_id == 156
                )
            )
            .values(historical_issues_flag=False)
        )
        
        # Then set only the intended attributes to True
        await session.execute(
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
        
        await session.commit()
        print(f"✅ Reset historical issues flags for cycle 13")
        print(f"✅ Only {len(VALID_HISTORICAL_ATTRIBUTES)} attributes now have historical_issues_flag=True")
        print(f"   - {VALID_HISTORICAL_ATTRIBUTES[0]}")
        print(f"   - {VALID_HISTORICAL_ATTRIBUTES[1]}")

if __name__ == "__main__":
    asyncio.run(fix_historical_flags())
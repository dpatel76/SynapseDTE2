#!/usr/bin/env python3
"""Fix llm_generated flag for cycle 13 where LLM data exists"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, and_, or_
from app.models.report_attribute import ReportAttribute
from app.core.config import get_settings

settings = get_settings()

async def fix_llm_flags():
    # Create async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Update llm_generated to True where we have LLM data
        result = await session.execute(
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
        
        await session.commit()
        print(f"✅ Updated {result.rowcount} attributes with llm_generated=True for cycle 13")

if __name__ == "__main__":
    asyncio.run(fix_llm_flags())
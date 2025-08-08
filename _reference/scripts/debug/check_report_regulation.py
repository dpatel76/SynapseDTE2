import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def check_report():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/synapse_dt")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT r.report_id, r.report_name, r.regulatory_framework
                FROM reports r
                WHERE r.report_id = 156
            """)
        )
        report = result.mappings().first()
        print(f"Report 156:")
        print(f"  Name: {report['report_name']}")
        print(f"  Regulatory Framework: {report['regulatory_framework']}")
    
    await engine.dispose()

asyncio.run(check_report())

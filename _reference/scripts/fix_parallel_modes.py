"""Fix parallel execution modes"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_parallel_modes():
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    async with engine.connect() as conn:
        # Fix parallel execution modes
        await conn.execute(text("""
            UPDATE workflow_activity_templates
            SET execution_mode = 'parallel'
            WHERE phase_name IN ('Request for Information', 'Test Execution', 'Observation Management')
            AND activity_type != 'START'
        """))
        await conn.commit()
        
        # Verify
        result = await conn.execute(text("""
            SELECT phase_name, COUNT(*) as total, 
                   COUNT(CASE WHEN execution_mode = 'parallel' THEN 1 END) as parallel
            FROM workflow_activity_templates
            WHERE phase_name IN ('Request for Information', 'Test Execution', 'Observation Management')
            GROUP BY phase_name
            ORDER BY phase_name
        """))
        
        print('Parallel phase statistics:')
        for row in result:
            print(f'  - {row[0]}: {row[1]} total, {row[2]} parallel')
        
        # Overall stats
        result = await conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(handler_name) as with_handler,
                   COUNT(retry_policy) as with_retry,
                   COUNT(CASE WHEN execution_mode = 'parallel' THEN 1 END) as parallel
            FROM workflow_activity_templates
        """))
        stats = result.fetchone()
        print(f'\nOverall statistics:')
        print(f'  Total templates: {stats[0]}')
        print(f'  With handler: {stats[1]}')
        print(f'  With retry policy: {stats[2]}')
        print(f'  Parallel activities: {stats[3]}')
        
        # Show some parallel activities
        result = await conn.execute(text("""
            SELECT phase_name, activity_name, activity_type, execution_mode
            FROM workflow_activity_templates
            WHERE execution_mode = 'parallel'
            ORDER BY phase_name, activity_order
            LIMIT 10
        """))
        print(f'\nSample parallel activities:')
        for row in result:
            print(f'  - {row[0]}: {row[1]} ({row[2]}) - {row[3]}')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_parallel_modes())
import asyncio
from sqlalchemy import create_engine, text
from app.core.config import get_settings

async def fix_stuck_execution():
    # Create database connection
    settings = get_settings()
    db_url = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Update stuck execution to failed
        conn.execute(text("""
            UPDATE cycle_report_test_execution_results 
            SET execution_status = 'failed',
                error_message = 'Execution failed - stuck in running state',
                completed_at = NOW()
            WHERE id = 21 AND execution_status = 'running'
        """))
        conn.commit()
        print("Updated execution 21 to failed status")

if __name__ == "__main__":
    asyncio.run(fix_stuck_execution())
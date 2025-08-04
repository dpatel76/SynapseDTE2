"""Check Dynamic Workflow Configuration"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_configuration():
    """Check all dynamic workflow configuration settings"""
    
    print("\n🔧 DYNAMIC WORKFLOW CONFIGURATION CHECK")
    print("=" * 60)
    
    # Core Settings
    print("\n📌 Core Workflow Settings:")
    print(f"  use_dynamic_workflows: {settings.use_dynamic_workflows}")
    print(f"  workflow_version: {settings.workflow_version}")
    print(f"  temporal_worker_enabled: {settings.temporal_worker_enabled}")
    
    # Dynamic Activity Settings
    print("\n⚡ Dynamic Activity Settings:")
    print(f"  dynamic_activity_retry_enabled: {settings.dynamic_activity_retry_enabled}")
    print(f"  dynamic_activity_timeout_enabled: {settings.dynamic_activity_timeout_enabled}")
    print(f"  parallel_activity_max_concurrent: {settings.parallel_activity_max_concurrent}")
    print(f"  workflow_activity_signal_timeout: {settings.workflow_activity_signal_timeout}s")
    
    # Handler Configuration
    print("\n🔌 Handler Configuration:")
    print(f"  activity_handler_package: {settings.activity_handler_package}")
    print(f"  fallback_handler: {settings.fallback_handler}")
    print(f"  manual_activity_handler: {settings.manual_activity_handler}")
    
    # Feature Flags
    print("\n🚀 Feature Flags:")
    print(f"  enable_activity_dependencies: {settings.enable_activity_dependencies}")
    print(f"  enable_conditional_activities: {settings.enable_conditional_activities}")
    print(f"  enable_activity_compensation: {settings.enable_activity_compensation}")
    print(f"  track_activity_metrics: {settings.track_activity_metrics}")
    
    # Database Check
    print("\n💾 Database Configuration:")
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    async with engine.connect() as conn:
        # Check if dynamic workflow tables exist
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('workflow_activity_templates', 'workflow_activities', 'workflow_activity_dependencies')
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        print(f"  Required tables found: {len(tables)}/3")
        for table in tables:
            print(f"    ✓ {table}")
        
        # Check activity templates
        result = await conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(handler_name) as with_handler,
                   COUNT(CASE WHEN execution_mode = 'parallel' THEN 1 END) as parallel
            FROM workflow_activity_templates
        """))
        
        stats = result.fetchone()
        if stats and stats[0] > 0:
            print(f"\n  Activity Templates:")
            print(f"    Total: {stats[0]}")
            print(f"    With handlers: {stats[1]}")
            print(f"    Parallel: {stats[2]}")
        
        # Check if retry policies are configured
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM workflow_activity_templates 
            WHERE retry_policy IS NOT NULL
        """))
        retry_count = result.scalar()
        print(f"    With retry policies: {retry_count}")
    
    await engine.dispose()
    
    # Configuration Status
    print("\n✅ Configuration Status:")
    if settings.use_dynamic_workflows and settings.workflow_version == "v2":
        print("  🟢 Dynamic workflows are ENABLED")
        print("  🟢 V2 workflow will be used by default")
    else:
        print("  🔴 Dynamic workflows are DISABLED")
        print("  🔴 Legacy workflow will be used")
    
    if not settings.temporal_worker_enabled:
        print("  ⚠️  WARNING: Temporal worker is DISABLED")
        print("     Set temporal_worker_enabled=true to process workflows")
    
    print("\n" + "=" * 60)
    
    # Recommendations
    print("\n📋 Recommendations:")
    if not settings.use_dynamic_workflows:
        print("  1. Set use_dynamic_workflows=true to enable the new system")
    if settings.workflow_version != "v2":
        print("  2. Set workflow_version='v2' to use dynamic workflows")
    if not settings.temporal_worker_enabled:
        print("  3. Set temporal_worker_enabled=true to process workflows")
    
    if stats and stats[0] > 0 and stats[1] < stats[0]:
        print("  4. Some activity templates are missing handlers")
        print("     Run: python -m scripts.apply_full_workflow_updates")


if __name__ == "__main__":
    asyncio.run(check_configuration())
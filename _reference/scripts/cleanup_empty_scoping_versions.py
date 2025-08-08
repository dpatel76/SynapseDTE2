#!/usr/bin/env python3
"""
Cleanup script to remove empty scoping versions (versions with 0 attributes).
This helps keep the version history clean and meaningful.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.scoping import ScopingVersion
from app.models.workflow import WorkflowPhase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"


async def cleanup_empty_versions(dry_run: bool = True):
    """
    Remove scoping versions with 0 attributes.
    
    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Find all empty versions
            empty_versions_query = select(ScopingVersion).where(
                ScopingVersion.total_attributes == 0
            )
            result = await db.execute(empty_versions_query)
            empty_versions = result.scalars().all()
            
            if not empty_versions:
                logger.info("No empty versions found. Nothing to clean up.")
                return
            
            logger.info(f"Found {len(empty_versions)} empty versions")
            
            # Group by phase for better reporting
            phases_affected = {}
            for version in empty_versions:
                if version.phase_id not in phases_affected:
                    # Get phase details
                    phase_query = select(WorkflowPhase).where(
                        WorkflowPhase.phase_id == version.phase_id
                    )
                    phase_result = await db.execute(phase_query)
                    phase = phase_result.scalar_one_or_none()
                    
                    phases_affected[version.phase_id] = {
                        'phase': phase,
                        'versions': []
                    }
                
                phases_affected[version.phase_id]['versions'].append(version)
            
            # Report what will be deleted
            logger.info("\nEmpty versions to be deleted:")
            logger.info("-" * 80)
            
            for phase_id, data in phases_affected.items():
                phase = data['phase']
                versions = data['versions']
                
                if phase:
                    logger.info(f"\nPhase: {phase.phase_name} (Cycle: {phase.cycle_id}, Report: {phase.report_id})")
                else:
                    logger.info(f"\nPhase ID: {phase_id}")
                
                logger.info(f"  Empty versions: {len(versions)}")
                for v in sorted(versions, key=lambda x: x.version_number):
                    logger.info(f"    - Version {v.version_number}: {v.version_id} (created: {v.created_at})")
            
            if dry_run:
                logger.info("\n[DRY RUN] No changes made. Run with --execute to actually delete.")
            else:
                # Actually delete the empty versions
                delete_count = 0
                for version in empty_versions:
                    await db.delete(version)
                    delete_count += 1
                
                await db.commit()
                logger.info(f"\nSuccessfully deleted {delete_count} empty versions.")
                
                # Verify remaining versions
                remaining_query = select(ScopingVersion).where(
                    ScopingVersion.total_attributes > 0
                )
                remaining_result = await db.execute(remaining_query)
                remaining_versions = remaining_result.scalars().all()
                
                logger.info(f"Remaining versions with attributes: {len(remaining_versions)}")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()


async def main():
    """Main entry point for the cleanup script."""
    import sys
    
    # Check for command line arguments
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        logger.info("Running in EXECUTE mode - changes will be made!")
    else:
        logger.info("Running in DRY RUN mode - no changes will be made.")
        logger.info("Use --execute flag to actually delete empty versions.")
    
    await cleanup_empty_versions(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
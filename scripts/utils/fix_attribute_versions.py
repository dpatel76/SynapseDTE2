#!/usr/bin/env python3
"""
Fix attribute versioning flags in the database
"""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine
from app.models.report_attribute import ReportAttribute
from app.core.logging import get_logger

logger = get_logger(__name__)


async def fix_attribute_versions():
    """Fix is_latest_version flags for all attributes"""
    async with AsyncSessionLocal() as db:
        try:
            # Get all attributes
            result = await db.execute(
                select(ReportAttribute).order_by(
                    ReportAttribute.cycle_id,
                    ReportAttribute.report_id,
                    ReportAttribute.attribute_name,
                    ReportAttribute.version_number
                )
            )
            attributes = result.scalars().all()
            
            logger.info(f"Found {len(attributes)} total attributes")
            
            # Group by cycle, report, and attribute name
            grouped = {}
            for attr in attributes:
                key = (attr.cycle_id, attr.report_id, attr.attribute_name)
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(attr)
            
            logger.info(f"Found {len(grouped)} unique attribute groups")
            
            # Fix is_latest_version flags
            fixes_needed = 0
            for key, versions in grouped.items():
                # Sort by version number
                versions.sort(key=lambda x: x.version_number, reverse=True)
                
                # The first one (highest version) should be marked as latest
                for i, attr in enumerate(versions):
                    should_be_latest = (i == 0)
                    if attr.is_latest_version != should_be_latest:
                        fixes_needed += 1
                        attr.is_latest_version = should_be_latest
                        logger.info(f"Fixed attribute {attr.attribute_id} ({attr.attribute_name}) - is_latest_version={should_be_latest}")
            
            # Also ensure all attributes have proper flags
            for attr in attributes:
                # Ensure is_active is set (default True for non-archived)
                if attr.is_active is None:
                    attr.is_active = True
                    fixes_needed += 1
                    logger.info(f"Fixed attribute {attr.attribute_id} - is_active=True")
                
                # Ensure approval_status is set
                if not attr.approval_status:
                    attr.approval_status = 'pending'
                    fixes_needed += 1
                    logger.info(f"Fixed attribute {attr.attribute_id} - approval_status='pending'")
            
            if fixes_needed > 0:
                await db.commit()
                logger.info(f"✅ Fixed {fixes_needed} attribute version flags")
            else:
                logger.info("✅ All attribute version flags are already correct")
            
            # Report statistics
            latest_count = sum(1 for attr in attributes if attr.is_latest_version)
            active_count = sum(1 for attr in attributes if attr.is_active)
            approved_count = sum(1 for attr in attributes if attr.approval_status == 'approved')
            
            logger.info(f"\nAttribute Statistics:")
            logger.info(f"  Total attributes: {len(attributes)}")
            logger.info(f"  Latest versions: {latest_count}")
            logger.info(f"  Active attributes: {active_count}")
            logger.info(f"  Approved attributes: {approved_count}")
            
        except Exception as e:
            logger.error(f"Error fixing attribute versions: {str(e)}")
            await db.rollback()
            raise


async def main():
    logger.info("Starting attribute version fix...")
    await fix_attribute_versions()
    logger.info("Attribute version fix completed!")


if __name__ == "__main__":
    asyncio.run(main())
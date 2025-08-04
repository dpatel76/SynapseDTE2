"""
Service to mark versions as approved by tester when submitted
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from app.models.sample_selection import SampleSelectionVersion
from app.models.scoping import ScopingVersion
from app.models.data_profiling import DataProfilingVersion
from app.core.logging import get_logger

logger = get_logger(__name__)


class VersionTesterApprovalService:
    """Service to mark versions as approved by tester when submitted"""
    
    @staticmethod
    async def mark_sample_selection_approved_by_tester(
        db: AsyncSession,
        version_id: str,
        tester_id: int
    ) -> None:
        """Mark Sample Selection version as approved by tester"""
        
        # Get the version
        version_query = await db.execute(
            select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Sample Selection version {version_id} not found")
            return
            
        # Update metadata to mark as approved by tester
        version.metadata = version.metadata or {}
        version.metadata['approved_by_tester'] = True
        version.metadata['tester_id'] = tester_id
        version.metadata['tester_approval_date'] = datetime.utcnow().isoformat()
        
        # Flag metadata as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(version, 'metadata')
        
        version.updated_at = datetime.utcnow()
        version.updated_by_id = tester_id
        
        await db.commit()
        
        logger.info(
            f"Marked Sample Selection version {version_id} as approved by tester {tester_id}"
        )
    
    @staticmethod
    async def mark_scoping_approved_by_tester(
        db: AsyncSession,
        version_id: str,
        tester_id: int
    ) -> None:
        """Mark Scoping version as approved by tester"""
        
        # Get the version
        version_query = await db.execute(
            select(ScopingVersion).where(
                ScopingVersion.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Scoping version {version_id} not found")
            return
            
        # Update metadata to mark as approved by tester
        version.metadata = version.metadata or {}
        version.metadata['approved_by_tester'] = True
        version.metadata['tester_id'] = tester_id
        version.metadata['tester_approval_date'] = datetime.utcnow().isoformat()
        
        # Flag metadata as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(version, 'metadata')
        
        version.updated_at = datetime.utcnow()
        version.updated_by_id = tester_id
        
        await db.commit()
        
        logger.info(
            f"Marked Scoping version {version_id} as approved by tester {tester_id}"
        )
    
    @staticmethod
    async def mark_data_profiling_approved_by_tester(
        db: AsyncSession,
        version_id: str,
        tester_id: int
    ) -> None:
        """Mark Data Profiling version as approved by tester"""
        
        # Get the version
        version_query = await db.execute(
            select(DataProfilingVersion).where(
                DataProfilingVersion.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Data Profiling version {version_id} not found")
            return
            
        # Update metadata to mark as approved by tester
        version.metadata = version.metadata or {}
        version.metadata['approved_by_tester'] = True
        version.metadata['tester_id'] = tester_id
        version.metadata['tester_approval_date'] = datetime.utcnow().isoformat()
        
        # Flag metadata as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(version, 'metadata')
        
        version.updated_at = datetime.utcnow()
        version.updated_by_id = tester_id
        
        await db.commit()
        
        logger.info(
            f"Marked Data Profiling version {version_id} as approved by tester {tester_id}"
        )
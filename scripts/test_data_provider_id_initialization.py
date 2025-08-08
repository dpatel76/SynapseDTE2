#!/usr/bin/env python
"""
Test script to verify Data Provider ID phase initialization
"""

import asyncio
import logging
from sqlalchemy import select, and_
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_data_provider_id_initialization():
    """Test that Data Provider ID phase creates LOB attribute mappings when started"""
    
    from app.core.database import AsyncSessionLocal
    from app.models.workflow import WorkflowPhase
    from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping, DataOwnerLOBAttributeVersion
    
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Testing Data Provider ID phase initialization...")
            
            # Check if Data Provider ID phase exists
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == 2,
                    WorkflowPhase.report_id == 3,
                    WorkflowPhase.phase_name == "Data Provider ID"
                )
            )
            phase_result = await db.execute(phase_query)
            phase = phase_result.scalar_one_or_none()
            
            if not phase:
                logger.error("Data Provider ID phase not found for cycle 2, report 3")
                return False
            
            logger.info(f"Found Data Provider ID phase: {phase.phase_id}")
            logger.info(f"Phase status: {phase.status}, state: {phase.state}")
            
            # Check if any versions exist
            version_query = select(DataOwnerLOBAttributeVersion).where(
                DataOwnerLOBAttributeVersion.phase_id == phase.phase_id
            )
            version_result = await db.execute(version_query)
            versions = version_result.scalars().all()
            
            logger.info(f"Found {len(versions)} version(s) for phase {phase.phase_id}")
            
            if versions:
                for version in versions:
                    logger.info(f"  Version {version.version_id}: status={version.version_status}, created={version.created_at}")
                    
                    # Check mappings for this version
                    mappings_query = select(DataOwnerLOBAttributeMapping).where(
                        DataOwnerLOBAttributeMapping.version_id == version.version_id
                    )
                    mappings_result = await db.execute(mappings_query)
                    mappings = mappings_result.scalars().all()
                    
                    logger.info(f"    Mappings in version: {len(mappings)}")
                    
                    if mappings:
                        # Show sample mappings
                        for i, mapping in enumerate(mappings[:5]):
                            logger.info(f"      Mapping {i+1}: attribute_id={mapping.attribute_id}, lob_id={mapping.lob_id}, status={mapping.assignment_status}")
                        
                        if len(mappings) > 5:
                            logger.info(f"      ... and {len(mappings) - 5} more mappings")
                    
                    # Summary stats
                    assigned_count = sum(1 for m in mappings if m.data_owner_id is not None)
                    unassigned_count = len(mappings) - assigned_count
                    logger.info(f"    Total: {len(mappings)}, Assigned: {assigned_count}, Unassigned: {unassigned_count}")
            else:
                logger.warning("No versions found - phase may not have been properly initialized")
                
                # Check for orphaned mappings without version
                orphaned_query = select(DataOwnerLOBAttributeMapping).where(
                    DataOwnerLOBAttributeMapping.phase_id == phase.phase_id
                )
                orphaned_result = await db.execute(orphaned_query)
                orphaned = orphaned_result.scalars().all()
                
                if orphaned:
                    logger.warning(f"Found {len(orphaned)} orphaned mappings without version")
                else:
                    logger.info("No orphaned mappings found")
                
                return False
            
            # Overall success check
            if versions and len(mappings) > 0:
                logger.info("✅ Data Provider ID phase initialization appears to be working!")
                return True
            else:
                logger.warning("⚠️ Data Provider ID phase exists but no mappings were created")
                return False
            
        except Exception as e:
            logger.error(f"Test failed with error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False


async def check_prerequisites():
    """Check if prerequisites for Data Provider ID phase are met"""
    
    from app.core.database import AsyncSessionLocal
    from app.models.workflow import WorkflowPhase
    from app.models.scoping import ScopingVersion
    from app.models.sample_selection import SampleSelectionVersion
    
    async with AsyncSessionLocal() as db:
        logger.info("\n=== CHECKING PREREQUISITES ===")
        
        # Check Scoping phase
        scoping_phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == 2,
                WorkflowPhase.report_id == 3,
                WorkflowPhase.phase_name == "Scoping"
            )
        )
        scoping_phase_result = await db.execute(scoping_phase_query)
        scoping_phase = scoping_phase_result.scalar_one_or_none()
        
        if scoping_phase:
            logger.info(f"✅ Scoping phase found: status={scoping_phase.status}")
            
            # Check for approved scoping version - check version_status only
            scoping_version_query = select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == scoping_phase.phase_id,
                    ScopingVersion.version_status == "approved"
                )
            )
            scoping_version_result = await db.execute(scoping_version_query)
            scoping_version = scoping_version_result.scalar_one_or_none()
            
            if scoping_version:
                logger.info(f"✅ Approved scoping version found: {scoping_version.version_id}")
            else:
                logger.warning("❌ No approved scoping version found")
        else:
            logger.warning("❌ Scoping phase not found")
        
        # Check Sample Selection phase
        sample_phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == 2,
                WorkflowPhase.report_id == 3,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
        sample_phase_result = await db.execute(sample_phase_query)
        sample_phase = sample_phase_result.scalar_one_or_none()
        
        if sample_phase:
            logger.info(f"✅ Sample Selection phase found: status={sample_phase.status}")
            
            # Check for approved sample version - check version_status only
            sample_version_query = select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == sample_phase.phase_id,
                    SampleSelectionVersion.version_status == "approved"
                )
            )
            sample_version_result = await db.execute(sample_version_query)
            sample_version = sample_version_result.scalar_one_or_none()
            
            if sample_version:
                logger.info(f"✅ Approved sample selection version found: {sample_version.version_id}")
            else:
                logger.warning("❌ No approved sample selection version found")
        else:
            logger.warning("❌ Sample Selection phase not found")


async def main():
    """Main test function"""
    logger.info("="*60)
    logger.info("DATA PROVIDER ID PHASE INITIALIZATION TEST")
    logger.info("="*60)
    
    # Check prerequisites
    await check_prerequisites()
    
    # Run the test
    logger.info("\n=== TESTING INITIALIZATION ===")
    test_passed = await test_data_provider_id_initialization()
    
    logger.info("\n" + "="*60)
    if test_passed:
        logger.info("✅ TEST PASSED: Data Provider ID phase initialization is working")
    else:
        logger.info("❌ TEST FAILED: Issues found with Data Provider ID initialization")
    logger.info("="*60)
    
    return test_passed


if __name__ == "__main__":
    asyncio.run(main())
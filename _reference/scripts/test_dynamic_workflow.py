"""
Test Dynamic Workflow Implementation
Tests the new dynamic activity execution system
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.services.workflow_service import WorkflowService
from app.models import TestCycle, Report, CycleReport, User
from app.models.workflow_activity import WorkflowActivity, WorkflowActivityTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_data(db: AsyncSession):
    """Create test data for workflow execution"""
    
    # Check if test cycle exists
    result = await db.execute(
        select(TestCycle).where(TestCycle.cycle_name == "Dynamic Test Cycle")
    )
    cycle = result.scalar_one_or_none()
    
    if not cycle:
        # Create test cycle
        cycle = TestCycle(
            cycle_name="Dynamic Test Cycle",
            cycle_type="Q4 2024",
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 12, 31),
            status="In Progress",
            created_by=1
        )
        db.add(cycle)
        await db.commit()
        await db.refresh(cycle)
        logger.info(f"Created test cycle: {cycle.cycle_id}")
    
    # Check if report exists
    result = await db.execute(
        select(Report).where(Report.report_name == "Dynamic Test Report")
    )
    report = result.scalar_one_or_none()
    
    if not report:
        # Create test report
        report = Report(
            report_name="Dynamic Test Report",
            report_type="Regulatory",
            description="Test report for dynamic workflow",
            frequency="Quarterly",
            created_by=1
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        logger.info(f"Created test report: {report.report_id}")
    
    # Check if cycle report exists
    result = await db.execute(
        select(CycleReport).where(
            CycleReport.cycle_id == cycle.cycle_id,
            CycleReport.report_id == report.report_id
        )
    )
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        # Create cycle report
        cycle_report = CycleReport(
            cycle_id=cycle.cycle_id,
            report_id=report.report_id,
            status="Not Started",
            created_by=1
        )
        db.add(cycle_report)
        await db.commit()
        logger.info("Created cycle report")
    
    return cycle.cycle_id, report.report_id


async def check_activity_templates(db: AsyncSession):
    """Check if activity templates are populated"""
    result = await db.execute(
        select(WorkflowActivityTemplate)
        .order_by(WorkflowActivityTemplate.phase_name, WorkflowActivityTemplate.activity_order)
        .limit(10)
    )
    templates = result.scalars().all()
    
    if not templates:
        logger.error("No activity templates found! Run populate_dynamic_activity_templates.py first")
        return False
    
    logger.info(f"Found {len(templates)} activity templates")
    for template in templates[:5]:
        logger.info(f"  - {template.phase_name}: {template.activity_name} ({template.activity_type.value})")
    
    return True


async def start_workflow(db: AsyncSession, cycle_id: int, report_id: int):
    """Start the dynamic workflow"""
    
    # Get workflow service
    workflow_service = WorkflowService(db)
    
    # Start workflow with V2 enabled
    result = await workflow_service.start_test_cycle_workflow(
        cycle_id=cycle_id,
        user_id=1,  # System user
        report_ids=[report_id],
        skip_phases=[],  # Run all phases
        metadata={
            "use_v2_workflow": True,
            "include_optional": False,
            "test_mode": True
        }
    )
    
    logger.info(f"Started workflow: {result['workflow_id']}")
    return result['workflow_id']


async def monitor_workflow(db: AsyncSession, workflow_id: str):
    """Monitor workflow progress"""
    
    workflow_service = WorkflowService(db)
    
    # Check status every 5 seconds
    for i in range(12):  # Monitor for 1 minute
        try:
            status = await workflow_service.get_workflow_status(workflow_id)
            logger.info(f"Workflow status: {status['status']}")
            
            if 'current_phase' in status:
                logger.info(f"  Current phase: {status['current_phase']}")
            
            if 'completed_phases' in status:
                logger.info(f"  Completed phases: {status['completed_phases']}")
            
            # Check activities
            result = await db.execute(
                select(WorkflowActivity)
                .where(WorkflowActivity.status.in_(["IN_PROGRESS", "COMPLETED"]))
                .order_by(WorkflowActivity.activity_id.desc())
                .limit(5)
            )
            activities = result.scalars().all()
            
            if activities:
                logger.info("  Recent activities:")
                for activity in activities:
                    logger.info(f"    - {activity.phase_name}/{activity.activity_name}: {activity.status.value}")
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error checking status: {str(e)}")
            break


async def complete_manual_activity(db: AsyncSession):
    """Simulate completing a manual activity"""
    
    # Find a pending manual activity
    result = await db.execute(
        select(WorkflowActivity)
        .where(
            WorkflowActivity.status == "IN_PROGRESS",
            WorkflowActivity.is_manual == True
        )
        .limit(1)
    )
    activity = result.scalar_one_or_none()
    
    if activity:
        logger.info(f"Completing manual activity: {activity.activity_name}")
        
        # Mark as completed
        activity.status = "COMPLETED"
        activity.completed_at = datetime.utcnow()
        activity.completed_by = 1
        
        await db.commit()
        logger.info("Manual activity marked as completed")
        return True
    
    return False


async def main():
    """Main test function"""
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check prerequisites
        logger.info("Checking activity templates...")
        if not await check_activity_templates(session):
            logger.error("Please run populate_dynamic_activity_templates.py first")
            return
        
        # Create test data
        logger.info("Creating test data...")
        cycle_id, report_id = await create_test_data(session)
        
        # Start workflow
        logger.info("Starting dynamic workflow...")
        workflow_id = await start_workflow(session, cycle_id, report_id)
        
        # Monitor progress
        logger.info("Monitoring workflow progress...")
        
        # Give workflow time to start
        await asyncio.sleep(2)
        
        # Simulate completing manual activities
        for i in range(3):
            await asyncio.sleep(5)
            if await complete_manual_activity(session):
                logger.info(f"Completed manual activity {i+1}")
        
        # Continue monitoring
        await monitor_workflow(session, workflow_id)
        
        # Final status check
        workflow_service = WorkflowService(session)
        final_status = await workflow_service.get_workflow_status(workflow_id)
        
        logger.info("\n=== Final Workflow Status ===")
        logger.info(f"Status: {final_status.get('status')}")
        logger.info(f"Completed phases: {final_status.get('completed_phases', [])}")
        
        # Check activity records
        result = await session.execute(
            select(WorkflowActivity)
            .where(WorkflowActivity.cycle_id == cycle_id)
            .order_by(WorkflowActivity.phase_name, WorkflowActivity.activity_order)
        )
        all_activities = result.scalars().all()
        
        logger.info(f"\n=== Activity Summary ===")
        logger.info(f"Total activities created: {len(all_activities)}")
        
        by_status = {}
        for activity in all_activities:
            status = activity.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        for status, count in by_status.items():
            logger.info(f"  {status}: {count}")
    
    await engine.dispose()
    logger.info("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())
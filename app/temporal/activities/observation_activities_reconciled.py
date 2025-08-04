"""Observation Management Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Observation Phase
2. Create Observations
3. Auto-Group Similar Observations
4. Review & Approve Observations
5. Generate Impact Assessment
6. Complete Observation Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
# Observation service removed - will use direct logic
from app.services.llm_service import get_llm_service
from app.models import ObservationRecord, TestExecution
# Note: Observation and ObservationRecord models removed - use ObservationRecord
from sqlalchemy import select, and_, update, func, distinct

logger = logging.getLogger(__name__)


@activity.defn
async def start_observation_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start observation management phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Start observation phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observations",
                new_state="In Progress",
                notes="Started via Temporal workflow",
                user_id=user_id
            )
            
            # Get failed test count
            result = await db.execute(
                select(func.count(TestExecution.execution_id))
                .where(
                    and_(
                        TestExecution.cycle_id == cycle_id,
                        TestExecution.report_id == report_id,
                        TestExecution.test_result == 'fail'
                    )
                )
            )
            failed_tests = result.scalar()
            
            logger.info(f"Started observation phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status,
                    "started_at": datetime.utcnow().isoformat(),
                    "failed_tests": failed_tests
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start observation phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def create_observations_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    observation_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 2: Create observations from failed tests
    
    Human-in-the-loop activity for creating observations.
    """
    try:
        async for db in get_db():
            if observation_data and observation_data.get('observations'):
                # Process created observations
                observations = observation_data['observations']
                created_observations = []
                
                for obs_data in observations:
                    # Create observation
                    observation = Observation(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        test_execution_id=obs_data.get('test_execution_id'),
                        sample_id=obs_data.get('sample_id'),
                        attribute_id=obs_data.get('attribute_id'),
                        observation_type=obs_data.get('type', 'data_quality'),
                        severity=obs_data.get('severity', 'medium'),
                        title=obs_data['title'],
                        description=obs_data['description'],
                        impact=obs_data.get('impact', ''),
                        recommendation=obs_data.get('recommendation', ''),
                        status='draft',
                        created_by=user_id
                    )
                    db.add(observation)
                    created_observations.append(observation)
                
                await db.commit()
                
                # Auto-generate observations from failed tests if requested
                if observation_data.get('auto_generate_from_failures'):
                    # Auto-generate observations from failed tests
                    failed_tests = await db.execute(
                        select(TestExecution).where(
                            and_(
                                TestExecution.cycle_id == cycle_id,
                                TestExecution.report_id == report_id,
                                TestExecution.test_result == 'fail'
                            )
                        )
                    )
                    for test in failed_tests.scalars():
                        auto_obs = Observation(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            test_execution_id=test.execution_id,
                            sample_id=test.sample_id,
                            attribute_id=test.attribute_id,
                            observation_type='test_failure',
                            severity='high',
                            title=f"Test failure for {test.test_case_id}",
                            description=f"Test failed with result: {test.actual_result}",
                            status='draft',
                            created_by=user_id
                        )
                        db.add(auto_obs)
                        created_observations.append(auto_obs)
                
                logger.info(f"Created {len(created_observations)} observations for cycle {cycle_id}, report {report_id}")
                
                return {
                    "success": True,
                    "data": {
                        "observations_created": len(created_observations),
                        "manual_observations": len(observations),
                        "auto_generated": observation_data.get('auto_generate_from_failures', False),
                        "ready_for_grouping": len(created_observations) > 0
                    }
                }
            else:
                # Get current observation count
                result = await db.execute(
                    select(func.count(Observation.observation_id))
                    .where(
                        and_(
                            Observation.cycle_id == cycle_id,
                            Observation.report_id == report_id
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_observation_creation",
                        "message": "Waiting for observations to be created",
                        "current_observations": count
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed to create observations: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def auto_group_observations_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 3: Auto-group similar observations using LLM"""
    try:
        async for db in get_db():
            llm_service = get_llm_service()
            # Get all ungrouped observations
            result = await db.execute(
                select(Observation).where(
                    and_(
                        Observation.cycle_id == cycle_id,
                        Observation.report_id == report_id,
                        Observation.group_id.is_(None)
                    )
                )
            )
            observations = result.scalars().all()
            
            if not observations:
                return {
                    "success": True,
                    "data": {
                        "message": "No ungrouped observations found",
                        "groups_created": 0
                    }
                }
            
            # Use LLM to analyze and group observations
            grouping_result = await llm_service.group_similar_observations(
                observations=observations,
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            # Create observation groups
            groups_created = 0
            
            for group_data in grouping_result.get('groups', []):
                # Create group
                group = ObservationRecord(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    group_name=group_data['name'],
                    group_type=group_data.get('type', 'similar_issues'),
                    description=group_data['description'],
                    common_theme=group_data.get('theme', ''),
                    impact_level=group_data.get('impact_level', 'medium'),
                    created_by=user_id
                )
                db.add(group)
                await db.flush()
                
                # Assign observations to group
                for obs_id in group_data['observation_ids']:
                    await db.execute(
                        update(Observation)
                        .where(Observation.observation_id == obs_id)
                        .values(
                            group_id=group.group_id,
                            grouped_at=datetime.utcnow()
                        )
                    )
                
                groups_created += 1
            
            await db.commit()
            
            logger.info(f"Created {groups_created} observation groups for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "observations_analyzed": len(observations),
                    "groups_created": groups_created,
                    "grouping_method": "llm_analysis",
                    "ready_for_review": groups_created > 0
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to group observations: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def review_approve_observations_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    review_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 4: Review and approve observations
    
    Human-in-the-loop activity for observation review.
    """
    try:
        async for db in get_db():
            if review_data and review_data.get('reviews'):
                # Process observation reviews
                reviews = review_data['reviews']
                approved_count = 0
                rejected_count = 0
                revised_count = 0
                
                for review in reviews:
                    observation_id = review['observation_id']
                    action = review['action']  # 'approve', 'reject', 'revise'
                    
                    observation = await db.get(Observation, observation_id)
                    if not observation:
                        continue
                    
                    if action == 'approve':
                        observation.status = 'approved'
                        observation.approved_by = user_id
                        observation.approved_at = datetime.utcnow()
                        observation.review_notes = review.get('notes', '')
                        approved_count += 1
                        
                    elif action == 'reject':
                        observation.status = 'rejected'
                        observation.rejected_by = user_id
                        observation.rejected_at = datetime.utcnow()
                        observation.rejection_reason = review.get('reason', '')
                        rejected_count += 1
                        
                    elif action == 'revise':
                        # Update observation with revisions
                        if 'title' in review:
                            observation.title = review['title']
                        if 'description' in review:
                            observation.description = review['description']
                        if 'severity' in review:
                            observation.severity = review['severity']
                        if 'impact' in review:
                            observation.impact = review['impact']
                        if 'recommendation' in review:
                            observation.recommendation = review['recommendation']
                        
                        observation.status = 'revised'
                        observation.revised_by = user_id
                        observation.revised_at = datetime.utcnow()
                        observation.revision_notes = review.get('notes', '')
                        revised_count += 1
                
                # Process group reviews if provided
                if review_data.get('group_reviews'):
                    for group_review in review_data['group_reviews']:
                        group_id = group_review['group_id']
                        
                        # Update group approval status
                        group = await db.get(ObservationRecord, group_id)
                        if group:
                            group.approved = group_review.get('approved', False)
                            group.approved_by = user_id if group_review.get('approved') else None
                            group.approved_at = datetime.utcnow() if group_review.get('approved') else None
                            group.review_notes = group_review.get('notes', '')
                
                await db.commit()
                
                # Check if all observations are reviewed
                pending_result = await db.execute(
                    select(func.count(Observation.observation_id))
                    .where(
                        and_(
                            Observation.cycle_id == cycle_id,
                            Observation.report_id == report_id,
                            Observation.status == 'draft'
                        )
                    )
                )
                pending_count = pending_result.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "observations_approved": approved_count,
                        "observations_rejected": rejected_count,
                        "observations_revised": revised_count,
                        "pending_review": pending_count,
                        "all_reviewed": pending_count == 0
                    }
                }
            else:
                # Get review status
                result = await db.execute(
                    select(
                        func.count(Observation.observation_id).label('total'),
                        func.count(Observation.observation_id).filter(
                            Observation.status == 'approved'
                        ).label('approved')
                    ).where(
                        and_(
                            Observation.cycle_id == cycle_id,
                            Observation.report_id == report_id
                        )
                    )
                )
                stats = result.first()
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_review",
                        "message": "Waiting for observation review and approval",
                        "total_observations": stats.total,
                        "approved_observations": stats.approved
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in observation review: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def generate_impact_assessment_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 5: Generate impact assessment for observations"""
    try:
        async for db in get_db():
            # Generate impact assessment
            # Get observation counts by severity
            severity_result = await db.execute(
                select(
                    Observation.severity,
                    func.count(Observation.observation_id).label('count')
                ).where(
                    and_(
                        Observation.cycle_id == cycle_id,
                        Observation.report_id == report_id,
                        Observation.status == 'approved'
                    )
                ).group_by(Observation.severity)
            )
            severity_counts = {row.severity: row.count for row in severity_result}
            
            # Generate assessment summary
            total_observations = sum(severity_counts.values())
            high_severity = severity_counts.get('high', 0)
            
            assessment = {
                'total_observations': total_observations,
                'high_severity_count': high_severity,
                'risk_level': 'High' if high_severity > 5 else 'Medium' if high_severity > 0 else 'Low',
                'summary': f"Found {total_observations} observations with {high_severity} high severity issues"
            }
            
            # Get observation statistics by severity
            severity_stats = await db.execute(
                select(
                    Observation.severity,
                    func.count(Observation.observation_id).label('count')
                ).where(
                    and_(
                        Observation.cycle_id == cycle_id,
                        Observation.report_id == report_id,
                        Observation.status == 'approved'
                    )
                ).group_by(Observation.severity)
            )
            
            severity_breakdown = {row.severity: row.count for row in severity_stats}
            
            # Get group impact summary
            group_stats = await db.execute(
                select(
                    ObservationRecord.impact_level,
                    func.count(ObservationRecord.group_id).label('count')
                ).where(
                    and_(
                        ObservationRecord.cycle_id == cycle_id,
                        ObservationRecord.report_id == report_id,
                        ObservationRecord.approved == True
                    )
                ).group_by(ObservationRecord.impact_level)
            )
            
            impact_breakdown = {row.impact_level: row.count for row in group_stats}
            
            logger.info(f"Generated impact assessment for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "impact_assessment": assessment,
                    "severity_breakdown": severity_breakdown,
                    "impact_breakdown": impact_breakdown,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to generate impact assessment: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_observation_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 6: Complete observation management phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Get final observation statistics
            result = await db.execute(
                select(
                    func.count(Observation.observation_id).label('total'),
                    func.count(Observation.observation_id).filter(
                        Observation.status == 'approved'
                    ).label('approved'),
                    func.count(distinct(Observation.group_id)).label('groups')
                ).where(
                    and_(
                        Observation.cycle_id == cycle_id,
                        Observation.report_id == report_id
                    )
                )
            )
            stats = result.first()
            
            # Complete observation phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observations",
                new_state="Complete",
                notes=f"Completed with {stats.approved} approved observations in {stats.groups} groups",
                user_id=user_id
            )
            
            # Advance to Preparing Test Report phase
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Observations",
                to_phase="Preparing Test Report",
                user_id=user_id
            )
            
            logger.info(f"Completed observation phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": "Observations",
                    "total_observations": stats.total,
                    "approved_observations": stats.approved,
                    "observation_groups": stats.groups,
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_phase": "Preparing Test Report"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete observation phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
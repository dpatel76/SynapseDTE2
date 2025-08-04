"""Scoping Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Scoping Phase
2. Generate LLM Recommendations  
3. Tester Review & Decisions
4. Report Owner Approval
5. Complete Scoping Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from sqlalchemy import select, and_
from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.services.llm_service import get_llm_service
from app.models import Report, CycleReport, ReportAttribute, User
from app.schemas.planning import ReportAttributeUpdate

logger = logging.getLogger(__name__)


@activity.defn
async def start_scoping_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start scoping phase using existing workflow orchestrator"""
    try:
        async for db in get_db():
            from sqlalchemy import select, and_
            from app.models.workflow import WorkflowPhase
            
            # Start scoping phase by updating workflow phase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            result = await db.execute(phase_query)
            phase = result.scalar_one_or_none()
            
            if not phase:
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Scoping",
                    state="In Progress",
                    status="In Progress",
                    actual_start_date=datetime.utcnow(),
                    started_by=user_id
                )
                db.add(phase)
            else:
                phase.state = "In Progress"
                phase.status = "In Progress"
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
            
            await db.commit()
            
            logger.info(f"Started scoping phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status,
                    "started_at": phase.actual_start_date.isoformat() if phase.actual_start_date else datetime.utcnow().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start scoping phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def generate_llm_recommendations_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 2: Generate LLM recommendations for test attributes"""
    try:
        async for db in get_db():
            # Get report details
            report = await db.get(Report, report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Get LLM service (existing implementation)
            llm_service = get_llm_service()
            
            # Call existing LLM service to generate attributes
            result = await llm_service.generate_test_attributes(
                regulatory_context=report.regulation or "",
                report_type=report.regulation,
                business_rules=report.description or "",
                sample_size=25,  # Default
                cycle_id=cycle_id,
                report_id=report_id,
                preferred_provider="claude"  # Use Claude for quality
            )
            
            if result['success']:
                attributes = result.get('attributes', [])
                logger.info(f"Generated {len(attributes)} test attributes for report {report_id}")
                
                # Store attributes directly without orchestrator
                from app.models.report_attribute import ReportAttribute
                stored_attributes = []
                
                for attr in attributes:
                    # Create attribute in pending approval state
                    new_attr = ReportAttribute(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_name=attr.get('attribute_name'),
                        data_type=attr.get('data_type', 'String'),
                        description=attr.get('description'),
                        cde_flag=attr.get('cde_flag', False),
                        historical_issues_flag=attr.get('historical_issues_flag', False),
                        approval_status='pending',
                        llm_generated=True,
                        llm_rationale=attr.get('rationale', ''),
                        version_created_by=user_id
                    )
                    db.add(new_attr)
                    stored_attributes.append(new_attr)
                
                await db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "attributes_generated": len(attributes),
                        "llm_provider": result.get('metadata', {}).get('provider'),
                        "model_used": result.get('metadata', {}).get('model'),
                        "attributes": stored_attributes,
                        "requires_review": True
                    }
                }
            else:
                raise Exception(f"LLM generation failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Failed to generate LLM recommendations: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def tester_review_attributes_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    review_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 3: Tester reviews and makes decisions on attributes
    
    This is a human-in-the-loop activity that waits for tester input.
    The workflow should signal this activity when tester completes review.
    """
    try:
        async for db in get_db():
            if review_data and review_data.get('attribute_decisions'):
                # Process tester decisions
                orchestrator = await get_workflow_orchestrator(db)
                
                decisions = review_data['attribute_decisions']
                approved_count = 0
                rejected_count = 0
                modified_count = 0
                
                for decision in decisions:
                    attribute_id = decision['attribute_id']
                    action = decision['action']  # 'approve', 'reject', 'modify'
                    
                    if action == 'approve':
                        # Update attribute to approved by tester
                        await orchestrator.update_report_attribute(
                            attribute_id=attribute_id,
                            update_data=ReportAttributeUpdate(
                                approval_status='tester_approved',
                                tester_notes=decision.get('notes', '')
                            ),
                            updated_by=user_id
                        )
                        approved_count += 1
                        
                    elif action == 'reject':
                        # Mark attribute as rejected
                        await orchestrator.update_report_attribute(
                            attribute_id=attribute_id,
                            update_data=ReportAttributeUpdate(
                                approval_status='rejected',
                                is_scoped=False,
                                tester_notes=decision.get('notes', '')
                            ),
                            updated_by=user_id
                        )
                        rejected_count += 1
                        
                    elif action == 'modify':
                        # Update attribute with modifications
                        modifications = decision.get('modifications', {})
                        await orchestrator.update_report_attribute(
                            attribute_id=attribute_id,
                            update_data=ReportAttributeUpdate(
                                **modifications,
                                approval_status='tester_approved',
                                tester_notes=decision.get('notes', '')
                            ),
                            updated_by=user_id
                        )
                        modified_count += 1
                
                return {
                    "success": True,
                    "data": {
                        "reviewed_by": user_id,
                        "approved_count": approved_count,
                        "rejected_count": rejected_count,
                        "modified_count": modified_count,
                        "review_completed_at": datetime.utcnow().isoformat(),
                        "requires_report_owner_approval": approved_count > 0 or modified_count > 0
                    }
                }
            else:
                # Return pending status if no review data provided
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_tester_review",
                        "message": "Waiting for tester to review attributes"
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in tester review: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def report_owner_approval_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    approval_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 4: Report Owner reviews and approves tester-approved attributes
    
    This is a human-in-the-loop activity that waits for report owner input.
    """
    try:
        async for db in get_db():
            if approval_data and approval_data.get('approval_decision'):
                # Process report owner decision
                orchestrator = await get_workflow_orchestrator(db)
                
                decision = approval_data['approval_decision']
                
                if decision == 'approve_all':
                    # Approve all tester-approved attributes
                    result = await db.execute(
                        select(ReportAttribute).where(
                            and_(
                                ReportAttribute.cycle_id == cycle_id,
                                ReportAttribute.report_id == report_id,
                                ReportAttribute.approval_status == 'tester_approved'
                            )
                        )
                    )
                    attributes = result.scalars().all()
                    
                    for attr in attributes:
                        await orchestrator.update_report_attribute(
                            attribute_id=attr.attribute_id,
                            update_data=ReportAttributeUpdate(
                                approval_status='approved',
                                is_scoped=True
                            ),
                            updated_by=user_id
                        )
                    
                    return {
                        "success": True,
                        "data": {
                            "approved_by": user_id,
                            "attributes_approved": len(attributes),
                            "approval_type": "bulk_approval",
                            "approved_at": datetime.utcnow().isoformat(),
                            "ready_to_complete": True
                        }
                    }
                    
                elif decision == 'selective_approval':
                    # Process individual attribute approvals
                    attribute_decisions = approval_data.get('attribute_decisions', [])
                    approved_count = 0
                    sent_back_count = 0
                    
                    for attr_decision in attribute_decisions:
                        attribute_id = attr_decision['attribute_id']
                        approved = attr_decision['approved']
                        
                        if approved:
                            await orchestrator.update_report_attribute(
                                attribute_id=attribute_id,
                                update_data=ReportAttributeUpdate(
                                    approval_status='approved',
                                    is_scoped=True
                                ),
                                updated_by=user_id
                            )
                            approved_count += 1
                        else:
                            # Send back for tester review
                            await orchestrator.update_report_attribute(
                                attribute_id=attribute_id,
                                update_data=ReportAttributeUpdate(
                                    approval_status='pending',
                                    tester_notes=f"Report owner feedback: {attr_decision.get('feedback', '')}"
                                ),
                                updated_by=user_id
                            )
                            sent_back_count += 1
                    
                    return {
                        "success": True,
                        "data": {
                            "approved_by": user_id,
                            "attributes_approved": approved_count,
                            "attributes_sent_back": sent_back_count,
                            "approval_type": "selective_approval",
                            "approved_at": datetime.utcnow().isoformat(),
                            "ready_to_complete": sent_back_count == 0
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Invalid approval decision"
                    }
            else:
                # Return pending status if no approval data provided
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_report_owner_approval",
                        "message": "Waiting for report owner to approve attributes"
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in report owner approval: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_scoping_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 5: Complete scoping phase and advance workflow"""
    try:
        async for db in get_db():
            orchestrator = await get_workflow_orchestrator(db)
            
            # Verify all attributes are properly reviewed and approved
            result = await db.execute(
                select(ReportAttribute).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True,
                        ReportAttribute.approval_status == 'approved'
                    )
                )
            )
            approved_attributes = result.scalars().all()
            
            if not approved_attributes:
                raise ValueError("No approved attributes found. Cannot complete scoping phase.")
            
            # Complete scoping phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Scoping",
                new_state="Complete",
                notes=f"Completed with {len(approved_attributes)} approved attributes",
                user_id=user_id
            )
            
            # Advance to next phases (Sample Selection and Data Provider ID in parallel)
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Scoping",
                to_phase="Sample Selection",
                user_id=user_id
            )
            
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Scoping",
                to_phase="Data Provider ID",
                user_id=user_id
            )
            
            logger.info(f"Completed scoping phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": phase.phase_name,
                    "approved_attributes_count": len(approved_attributes),
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_phases": ["Sample Selection", "Data Provider ID"]
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete scoping phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
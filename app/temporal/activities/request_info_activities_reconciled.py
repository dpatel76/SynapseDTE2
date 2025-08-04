"""Request for Information Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Request Info Phase
2. Generate Test Cases
3. Create Information Requests
4. Send RFI Emails
5. Track Responses
6. Complete Request Info Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.services.email_service import get_email_service
from app.models import TestCase, DataProviderNotification, DataOwnerAssignment, ReportAttribute, SampleSet, SampleRecord
from sqlalchemy import select, and_, update, func

logger = logging.getLogger(__name__)


@activity.defn
async def start_request_info_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start request for information phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Start request info phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request Info",
                new_state="In Progress",
                notes="Started via Temporal workflow",
                user_id=user_id
            )
            
            # Get approved samples and data provider assignments
            sample_result = await db.execute(
                select(func.count(SampleSelection.sample_id))
                .join(SampleSet)
                .where(
                    and_(
                        SampleSelection.cycle_id == cycle_id,
                        SampleSelection.report_id == report_id,
                        SampleSet.status == 'approved'
                    )
                )
            )
            sample_count = sample_result.scalar()
            
            dp_result = await db.execute(
                select(func.count(distinct(DataProviderAssignment.data_provider_id)))
                .where(
                    and_(
                        DataProviderAssignment.cycle_id == cycle_id,
                        DataProviderAssignment.report_id == report_id,
                        DataProviderAssignment.status == 'approved'
                    )
                )
            )
            provider_count = dp_result.scalar()
            
            logger.info(f"Started request info phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status,
                    "started_at": datetime.utcnow().isoformat(),
                    "approved_samples": sample_count,
                    "data_providers": provider_count
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start request info phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def generate_test_cases_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 2: Generate test cases from approved attributes and samples"""
    try:
        async for db in get_db():
            # Get approved sample sets
            sample_result = await db.execute(
                select(SampleSet)
                .where(
                    and_(
                        SampleSet.cycle_id == cycle_id,
                        SampleSet.report_id == report_id,
                        SampleSet.status == 'Approved'
                    )
                )
            )
            sample_sets = sample_result.scalars().all()
            
            # Get scoped attributes with data provider assignments
            attr_result = await db.execute(
                select(ReportAttribute, DataOwnerAssignment)
                .join(
                    DataOwnerAssignment,
                    and_(
                        DataOwnerAssignment.attribute_id == ReportAttribute.attribute_id,
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id
                    )
                ).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True
                    )
                )
            )
            attribute_assignments = attr_result.all()
            
            # Generate test cases (one per sample-attribute combination)
            test_cases_created = 0
            
            # Get sample records from sample sets
            samples = []
            for sample_set in sample_sets:
                sample_records = await db.execute(
                    select(SampleRecord).where(
                        SampleRecord.sample_set_id == sample_set.sample_set_id
                    )
                )
                samples.extend(sample_records.scalars().all())
            
            for sample in samples:
                for attribute, assignment in attribute_assignments:
                    # Create test case
                    test_case = TestCase(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        sample_id=sample.sample_id,
                        attribute_id=attribute.attribute_id,
                        data_provider_id=assignment.data_owner_id,
                        test_case_name=f"{attribute.attribute_name} - Sample {sample.record_id}",
                        test_description=f"Test {attribute.attribute_name} for sample record {sample.record_id}",
                        expected_result=attribute.validation_rules or "Value should be present and valid",
                        test_type='data_validation',
                        priority='high' if attribute.mandatory_flag == 'Mandatory' else 'medium',
                        status='pending',
                        created_by=user_id
                    )
                    db.add(test_case)
                    test_cases_created += 1
            
            await db.commit()
            
            logger.info(f"Generated {test_cases_created} test cases for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "test_cases_created": test_cases_created,
                    "samples_count": len(samples),
                    "attributes_count": len(attribute_assignments),
                    "ready_for_requests": test_cases_created > 0
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to generate test cases: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def create_information_requests_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 3: Create information request packages for data providers"""
    try:
        async for db in get_db():
            # Get test cases grouped by data provider
            result = await db.execute(
                select(TestCase)
                .where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                ).order_by(TestCase.data_provider_id)
            )
            test_cases = result.scalars().all()
            
            # Group by data provider
            provider_test_cases = {}
            for tc in test_cases:
                if tc.data_provider_id not in provider_test_cases:
                    provider_test_cases[tc.data_provider_id] = []
                provider_test_cases[tc.data_provider_id].append(tc)
            
            # Create information requests
            requests_created = 0
            deadline = datetime.utcnow() + timedelta(days=14)  # 2 week deadline
            
            for provider_id, test_cases in provider_test_cases.items():
                # Create information request
                info_request = InformationRequest(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    data_provider_id=provider_id,
                    request_type='data_submission',
                    status='pending',
                    due_date=deadline,
                    instructions="Please provide the requested data for the following test cases",
                    test_case_count=len(test_cases),
                    created_by=user_id
                )
                db.add(info_request)
                await db.flush()
                
                # Link test cases to request
                for tc in test_cases:
                    tc.information_request_id = info_request.request_id
                    tc.status = 'awaiting_data'
                
                requests_created += 1
            
            await db.commit()
            
            logger.info(f"Created {requests_created} information requests for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "requests_created": requests_created,
                    "total_test_cases": len(test_cases),
                    "deadline": deadline.isoformat(),
                    "ready_for_emails": requests_created > 0
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to create information requests: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def send_rfi_emails_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 4: Send RFI emails to data providers"""
    try:
        async for db in get_db():
            email_service = get_email_service(db)
            
            # Get information requests with provider details
            result = await db.execute(
                select(InformationRequest, User)
                .join(User, InformationRequest.data_provider_id == User.user_id)
                .where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id,
                        InformationRequest.status == 'pending'
                    )
                )
            )
            requests = result.all()
            
            emails_sent = 0
            email_errors = []
            
            for request, provider in requests:
                try:
                    # Get test cases for this request
                    tc_result = await db.execute(
                        select(TestCase)
                        .where(TestCase.information_request_id == request.request_id)
                    )
                    test_cases = tc_result.scalars().all()
                    
                    # Send RFI email
                    result = await email_service.send_rfi_email(
                        provider=provider,
                        request=request,
                        test_cases=test_cases,
                        cycle_id=cycle_id,
                        report_id=report_id
                    )
                    
                    if result['success']:
                        emails_sent += 1
                        
                        # Update request status
                        request.email_sent = True
                        request.email_sent_at = datetime.utcnow()
                        request.status = 'sent'
                    else:
                        email_errors.append({
                            'request_id': request.request_id,
                            'provider_email': provider.email,
                            'error': result.get('error')
                        })
                        
                except Exception as e:
                    email_errors.append({
                        'request_id': request.request_id,
                        'provider_email': provider.email,
                        'error': str(e)
                    })
            
            await db.commit()
            
            logger.info(f"Sent {emails_sent} RFI emails for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "emails_sent": emails_sent,
                    "email_errors": len(email_errors),
                    "errors": email_errors,
                    "all_sent": emails_sent == len(requests)
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to send RFI emails: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def track_rfi_responses_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    response_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 5: Track RFI responses from data providers
    
    Human-in-the-loop activity that monitors response status.
    """
    try:
        async for db in get_db():
            if response_data and response_data.get('check_responses'):
                # Check current response status
                result = await db.execute(
                    select(
                        func.count(InformationRequest.request_id).label('total'),
                        func.count(InformationRequest.request_id).filter(
                            InformationRequest.status == 'completed'
                        ).label('completed'),
                        func.count(InformationRequest.request_id).filter(
                            InformationRequest.status == 'overdue'
                        ).label('overdue')
                    ).where(
                        and_(
                            InformationRequest.cycle_id == cycle_id,
                            InformationRequest.report_id == report_id
                        )
                    )
                )
                stats = result.first()
                
                # Check for overdue requests
                await db.execute(
                    update(InformationRequest)
                    .where(
                        and_(
                            InformationRequest.cycle_id == cycle_id,
                            InformationRequest.report_id == report_id,
                            InformationRequest.status == 'sent',
                            InformationRequest.due_date < datetime.utcnow()
                        )
                    ).values(status='overdue')
                )
                
                # Send reminders if needed
                if response_data.get('send_reminders'):
                    email_service = get_email_service(db)
                    
                    overdue_result = await db.execute(
                        select(InformationRequest, User)
                        .join(User, InformationRequest.data_provider_id == User.user_id)
                        .where(
                            and_(
                                InformationRequest.cycle_id == cycle_id,
                                InformationRequest.report_id == report_id,
                                InformationRequest.status == 'overdue'
                            )
                        )
                    )
                    overdue_requests = overdue_result.all()
                    
                    reminders_sent = 0
                    for request, provider in overdue_requests:
                        result = await email_service.send_rfi_reminder(
                            provider=provider,
                            request=request
                        )
                        if result['success']:
                            reminders_sent += 1
                            request.last_reminder_sent = datetime.utcnow()
                    
                    await db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "total_requests": stats.total,
                        "completed_requests": stats.completed,
                        "overdue_requests": stats.overdue,
                        "pending_requests": stats.total - stats.completed - stats.overdue,
                        "completion_percentage": (stats.completed / stats.total * 100) if stats.total > 0 else 0,
                        "all_completed": stats.completed == stats.total,
                        "reminders_sent": reminders_sent if response_data.get('send_reminders') else 0
                    }
                }
            else:
                # Return current status
                result = await db.execute(
                    select(func.count(InformationRequest.request_id))
                    .where(
                        and_(
                            InformationRequest.cycle_id == cycle_id,
                            InformationRequest.report_id == report_id
                        )
                    )
                )
                total = result.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "status": "monitoring_responses",
                        "message": "Monitoring RFI responses from data providers",
                        "total_requests": total
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in response tracking: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_request_info_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 6: Complete request for information phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Get final statistics
            result = await db.execute(
                select(
                    func.count(InformationRequest.request_id).label('total'),
                    func.count(InformationRequest.request_id).filter(
                        InformationRequest.status == 'completed'
                    ).label('completed')
                ).where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id
                    )
                )
            )
            stats = result.first()
            
            # Complete request info phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request Info",
                new_state="Complete",
                notes=f"Completed with {stats.completed}/{stats.total} requests fulfilled",
                user_id=user_id
            )
            
            # Advance to Testing phase
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Request Info",
                to_phase="Testing",
                user_id=user_id
            )
            
            logger.info(f"Completed request info phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": "Request Info",
                    "total_requests": stats.total,
                    "completed_requests": stats.completed,
                    "completion_rate": (stats.completed / stats.total * 100) if stats.total > 0 else 0,
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_phase": "Testing"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete request info phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
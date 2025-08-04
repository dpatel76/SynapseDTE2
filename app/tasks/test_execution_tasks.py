"""
Background tasks for test execution
Implements proper async patterns based on planning phase lessons
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm.attributes import flag_modified

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.background_jobs import job_manager
from app.core.exceptions import BusinessLogicError
from app.models.test_execution import TestExecution, TestExecutionAudit
from app.models.workflow import WorkflowPhase
from app.services.llm_service import get_llm_service
from app.services.database_connection_service import DatabaseConnectionService
from app.services.value_extraction_service import ValueExtractionService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def execute_test_case_celery_task(
    self,
    job_id: str,
    execution_id: int,
    sample_data: Dict[str, Any],
    evidence: Dict[str, Any],
    executed_by_id: int
):
    """
    Celery task wrapper for test case execution
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            execute_test_case_task(
                job_id=job_id,
                execution_id=execution_id,
                sample_data=sample_data,
                evidence=evidence,
                executed_by_id=executed_by_id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Test execution task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def execute_test_case_task(
    job_id: str,
    execution_id: int,
    sample_data: Dict[str, Any],
    evidence: Dict[str, Any],
    executed_by_id: int
) -> Dict[str, Any]:
    """
    Execute test case in background task
    Applies all lessons learned from planning phase issues
    """
    logger.info(f"Starting test execution task {job_id} for execution {execution_id}")
    
    try:
        # Create new session for async task (CRITICAL: Session management lesson)
        async with AsyncSessionLocal() as task_db:
            # Update job status to running (CRITICAL: Job status lesson)
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Loading test execution data",
                progress_percentage=0
            )
            
            # Reload execution in task session (CRITICAL: Session management lesson)
            execution_query = await task_db.execute(
                select(TestExecution).where(TestExecution.id == execution_id)
            )
            execution = execution_query.scalar_one_or_none()
            
            if not execution:
                raise BusinessLogicError(f"Test execution {execution_id} not found")
            
            # Update execution status
            execution.execution_status = "running"
            execution.started_at = datetime.utcnow()
            execution.updated_at = datetime.utcnow()
            execution.updated_by = executed_by_id
            task_db.add(execution)  # Ensure tracking
            await task_db.commit()
            
            job_manager.update_job_progress(
                job_id,
                current_step="Extracting values from evidence",
                progress_percentage=20
            )
            
            # Initialize value extraction service
            extraction_service = ValueExtractionService()
            
            # Prepare evidence data based on analysis method
            if execution.analysis_method == "llm_analysis":
                job_manager.update_job_progress(
                    job_id,
                    current_step="Processing with LLM",
                    progress_percentage=40
                )
                
                # Extract values using the reusable service
                try:
                    extracted_values = await extraction_service.extract_values_from_evidence(
                        evidence=evidence,
                        sample_data=sample_data,
                        evidence_type="document"
                    )
                    
                except Exception as e:
                    logger.error(f"Document extraction failed: {str(e)}")
                    raise BusinessLogicError(f"Document extraction failed: {str(e)}")
                    
            elif execution.analysis_method == "database_query":
                job_manager.update_job_progress(
                    job_id,
                    current_step="Executing SQL query",
                    progress_percentage=40
                )
                
                # Prepare evidence data for query execution
                try:
                    # Get data source details from evidence
                    data_source_id = evidence.get("data_source_id")
                    if not data_source_id:
                        raise BusinessLogicError("No data source ID found in evidence")
                    
                    # Load data source with connection details
                    from app.models.request_info import RFIDataSource
                    ds_result = await task_db.execute(
                        select(RFIDataSource).where(RFIDataSource.data_source_id == data_source_id)
                    )
                    data_source = ds_result.scalar_one_or_none()
                    
                    if not data_source:
                        raise BusinessLogicError(f"Data source {data_source_id} not found")
                    
                    # Use the SAME logic as RFI phase to get connection details
                    connection_details = data_source.connection_details
                    if isinstance(connection_details, str) and connection_details.strip():
                        import json
                        try:
                            connection_details = json.loads(connection_details)
                        except json.JSONDecodeError:
                            # Handle encrypted connection details if needed
                            from app.core.encryption import EncryptionService
                            encryption_service = EncryptionService()
                            connection_details = encryption_service.decrypt_dict(connection_details)
                    
                    # Prepare evidence with connection details
                    query_evidence = {
                        "query_text": evidence.get("query_text", ""),
                        "data_source_id": data_source_id,
                        "connection_details": connection_details,
                        "connection_type": data_source.connection_type
                    }
                    
                    # Extract values using the reusable service
                    extracted_values = await extraction_service.extract_values_from_evidence(
                        evidence=query_evidence,
                        sample_data=sample_data,
                        evidence_type="database_query"
                    )
                    
                except Exception as e:
                    logger.error(f"Query extraction failed: {str(e)}")
                    raise BusinessLogicError(f"Query extraction failed: {str(e)}")
            
            job_manager.update_job_progress(
                job_id,
                current_step="Analyzing results",
                progress_percentage=60
            )
            
            # Analyze results
            if extracted_values:
                # Get expected value from sample data
                expected_value = sample_data.get("expected_value") or sample_data.get("sample_value")
                actual_value = extracted_values.get("extracted_value")
                
                logger.info(f"[DEBUG] Building analysis_results for execution {execution_id}")
                logger.info(f"[DEBUG] Expected value: {expected_value}")
                logger.info(f"[DEBUG] Actual value: {actual_value}")
                logger.info(f"[DEBUG] Extracted values: {extracted_values}")
                
                # Don't auto-decide pass/fail - just present the data
                analysis_results = {
                    "expected_value": expected_value,
                    "actual_value": actual_value,
                    "primary_key_values": extracted_values.get("primary_key_values", {}),
                    "attribute_name": sample_data.get("attribute_name"),
                    "sample_identifier": sample_data.get("sample_identifier"),
                    "confidence_score": extracted_values.get("confidence_score", 1.0),
                    "extraction_details": extracted_values,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "requires_review": True,  # Always require human review
                    "execution_source": "celery_task"  # Track execution source
                }
                
                logger.info(f"[DEBUG] Analysis results structure: {json.dumps(analysis_results, indent=2)}")
                
                # Update execution with results
                execution.analysis_results = analysis_results
                execution.extracted_value = str(actual_value) if actual_value is not None else None
                execution.expected_value = str(expected_value) if expected_value is not None else None
                execution.sample_value = str(expected_value) if expected_value is not None else None  # Also set sample_value
                execution.llm_confidence_score = extracted_values.get("confidence_score")
                execution.test_result = "pending_review"  # Don't auto-decide
                execution.execution_status = "completed"
                execution.completed_at = datetime.utcnow()
                execution.database_query_executed = evidence.get("query_text")
                execution.database_result_count = extracted_values.get("row_count", 0)
                
                logger.info(f"[DEBUG] Set test_result to: {execution.test_result}")
                logger.info(f"[DEBUG] Set sample_value to: {execution.sample_value}")
                logger.info(f"[DEBUG] Set extracted_value to: {execution.extracted_value}")
                
            else:
                # No values extracted
                execution.execution_status = "failed"
                execution.error_message = "No values could be extracted"
                execution.completed_at = datetime.utcnow()
            
            # Update timestamps (CRITICAL: Timestamp lesson)
            execution.updated_at = datetime.utcnow()
            execution.updated_by = executed_by_id
            
            # Ensure tracking (CRITICAL: Session management lesson)
            task_db.add(execution)
            flag_modified(execution, 'analysis_results')
            
            logger.info(f"[DEBUG] BEFORE COMMIT - execution.analysis_results: {execution.analysis_results}")
            logger.info(f"[DEBUG] BEFORE COMMIT - execution.test_result: {execution.test_result}")
            logger.info(f"[DEBUG] BEFORE COMMIT - execution.sample_value: {execution.sample_value}")
            logger.info(f"[DEBUG] BEFORE COMMIT - execution.extracted_value: {execution.extracted_value}")
            
            # Create audit log
            audit = TestExecutionAudit(
                execution_id=execution_id,
                action="completed",
                action_details={
                    "status": execution.execution_status,
                    "result": execution.test_result,
                    "confidence_score": execution.llm_confidence_score
                },
                performed_by=executed_by_id,
                performed_at=datetime.utcnow()
            )
            task_db.add(audit)
            
            await task_db.commit()
            
            logger.info(f"[DEBUG] AFTER COMMIT - Successfully committed execution {execution_id}")
            
            # Verify data was saved correctly
            verification_result = await task_db.execute(
                select(TestExecution).where(TestExecution.id == execution_id)
            )
            verified_execution = verification_result.scalar_one_or_none()
            if verified_execution:
                logger.info(f"[DEBUG] VERIFICATION - analysis_results from DB: {verified_execution.analysis_results}")
                logger.info(f"[DEBUG] VERIFICATION - test_result from DB: {verified_execution.test_result}")
                logger.info(f"[DEBUG] VERIFICATION - sample_value from DB: {verified_execution.sample_value}")
                
                # Check if it has is_match (which it shouldn't)
                if verified_execution.analysis_results and 'is_match' in verified_execution.analysis_results:
                    logger.error(f"[DEBUG] ERROR: 'is_match' found in analysis_results! This should NOT happen!")
                    logger.error(f"[DEBUG] Full analysis_results: {verified_execution.analysis_results}")
            
            job_manager.update_job_progress(
                job_id,
                current_step="Test execution completed",
                progress_percentage=100
            )
            
            # Prepare completion result - use verified_execution to ensure we get fresh DB data
            completion_result = {
                "execution_id": execution_id,
                "status": verified_execution.execution_status if verified_execution else execution.execution_status,
                "result": verified_execution.test_result if verified_execution else execution.test_result,
                "confidence_score": verified_execution.llm_confidence_score if verified_execution else execution.llm_confidence_score,
                "analysis_results": verified_execution.analysis_results if verified_execution else execution.analysis_results,
                "completed_at": verified_execution.completed_at.isoformat() if verified_execution and verified_execution.completed_at else None
            }
            
            # Log what we're about to send to job manager
            logger.info(f"[DEBUG] completion_result being sent to job_manager: {json.dumps(completion_result, indent=2)}")
            
            # Complete job successfully
            job_manager.complete_job(job_id, result=completion_result)
            
            logger.info(f"Test execution job {job_id} completed successfully")
            return completion_result
            
    except Exception as e:
        logger.error(f"Test execution job {job_id} failed: {str(e)}", exc_info=True)
        
        # Update execution status in database
        try:
            async with AsyncSessionLocal() as error_db:
                execution = await error_db.get(TestExecution, execution_id)
                if execution:
                    execution.execution_status = "failed"
                    execution.error_message = str(e)
                    execution.completed_at = datetime.utcnow()
                    execution.updated_at = datetime.utcnow()
                    execution.updated_by = executed_by_id
                    await error_db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update execution status: {str(db_error)}")
        
        job_manager.complete_job(job_id, error=str(e))
        raise
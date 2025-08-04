"""
LLM-related background tasks
Handles long-running LLM operations without blocking the UI
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.llm_service import get_llm_service
from app.models.report_attribute import ReportAttribute
from app.models.llm_audit import LLMAuditLog
from app.models.document import Document
from app.models.test_execution import DocumentAnalysis, TestExecution
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_attributes_task(
    self,
    cycle_id: int,
    report_id: int,
    regulatory_context: str,
    report_type: str,
    user_id: int,
    additional_context: Optional[Dict] = None
):
    """
    Generate attributes using LLM in background
    This task handles the long-running LLM operations outside of database transactions
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _generate_attributes_async(
                cycle_id, report_id, regulatory_context, 
                report_type, user_id, additional_context
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Attribute generation failed: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _generate_attributes_async(
    cycle_id: int,
    report_id: int,
    regulatory_context: str,
    report_type: str,
    user_id: int,
    additional_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Async helper for attribute generation"""
    
    # Create new database session for this task
    async with AsyncSessionLocal() as db:
        try:
            # Get LLM service
            llm_service = get_llm_service()
            
            # Generate attributes using LLM
            # This is the long-running operation
            result = await llm_service.generate_test_attributes(
                regulatory_context=regulatory_context,
                report_type=report_type,
                additional_context=additional_context
            )
            
            # Save generated attributes to database
            # Use a new transaction for saving results
            saved_attributes = []
            
            for attr_data in result.get("attributes", []):
                attribute = ReportAttribute(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_name=attr_data.get("name"),
                    description=attr_data.get("description"),
                    data_type=attr_data.get("data_type", "string"),
                    is_required=attr_data.get("is_required", True),
                    llm_generated=True,
                    created_by=user_id,
                    # Enhanced fields from LLM
                    validation_rules=attr_data.get("validation_rules"),
                    expected_source=attr_data.get("expected_source"),
                    keywords=attr_data.get("keywords"),
                    testing_approach=attr_data.get("testing_approach"),
                    risk_rating=attr_data.get("risk_rating")
                )
                
                db.add(attribute)
                saved_attributes.append(attribute)
            
            # Commit the transaction
            await db.commit()
            
            # Log the operation
            audit_log = LLMAuditLog(
                user_id=user_id,
                operation_type="attribute_generation",
                model_used=result.get("model_used", "unknown"),
                prompt_tokens=result.get("prompt_tokens", 0),
                completion_tokens=result.get("completion_tokens", 0),
                total_tokens=result.get("total_tokens", 0),
                response_time_ms=result.get("response_time_ms", 0),
                success=True,
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            db.add(audit_log)
            await db.commit()
            
            return {
                "status": "success",
                "attributes_generated": len(saved_attributes),
                "model_used": result.get("model_used"),
                "total_tokens": result.get("total_tokens"),
                "task_id": self.request.id if hasattr(self, 'request') else None
            }
            
        except Exception as e:
            logger.error(f"Error in attribute generation: {str(e)}")
            
            # Log the failure
            audit_log = LLMAuditLog(
                user_id=user_id,
                operation_type="attribute_generation",
                success=False,
                error_message=str(e),
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            db.add(audit_log)
            await db.commit()
            
            raise


@celery_app.task(bind=True, max_retries=3)
def analyze_document_for_testing(
    self,
    document_id: int,
    attribute_name: str,
    sample_identifier: str,
    execution_id: int,
    user_id: int
):
    """
    Analyze document to extract test values using LLM
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _analyze_document_async(
                document_id, attribute_name, sample_identifier,
                execution_id, user_id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Document analysis failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _analyze_document_async(
    document_id: int,
    attribute_name: str,
    sample_identifier: str,
    execution_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Async helper for document analysis"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get document
            doc_query = select(Document).where(Document.document_id == document_id)
            doc_result = await db.execute(doc_query)
            document = doc_result.scalar_one_or_none()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Extract text from document (this would use document service)
            # For now, we'll assume the document content is available
            document_text = document.extracted_text or ""
            
            if not document_text:
                raise ValueError("Document has no extracted text")
            
            # Use LLM to extract the specific value
            extraction_result = await llm_service.extract_value_from_document(
                document_text=document_text,
                attribute_name=attribute_name,
                sample_identifier=sample_identifier,
                document_name=document.file_name
            )
            
            # Update document analysis record
            analysis_update = update(DocumentAnalysis).where(
                DocumentAnalysis.execution_id == execution_id
            ).values(
                extracted_value=extraction_result.get("value"),
                confidence_score=extraction_result.get("confidence_score", 0.0),
                extraction_context=extraction_result.get("context"),
                analysis_completed_at=datetime.utcnow(),
                analysis_status="completed",
                llm_model_used=extraction_result.get("model_used")
            )
            
            await db.execute(analysis_update)
            
            # Update test execution
            test_update = update(TestExecution).where(
                TestExecution.execution_id == execution_id
            ).values(
                retrieved_value=extraction_result.get("value"),
                confidence_score=extraction_result.get("confidence_score", 0.0),
                test_status="completed",
                test_notes=f"Extracted from {document.file_name}"
            )
            
            await db.execute(test_update)
            
            # Check if test passed (compare with expected value)
            test_query = select(TestExecution).where(
                TestExecution.execution_id == execution_id
            )
            test_result = await db.execute(test_query)
            test_execution = test_result.scalar_one()
            
            if test_execution.expected_value and extraction_result.get("value"):
                test_passed = (
                    str(test_execution.expected_value).strip().lower() == 
                    str(extraction_result.get("value")).strip().lower()
                )
                
                test_update = update(TestExecution).where(
                    TestExecution.execution_id == execution_id
                ).values(test_passed=test_passed)
                
                await db.execute(test_update)
            
            await db.commit()
            
            # Log the operation
            audit_log = LLMAuditLog(
                user_id=user_id,
                operation_type="document_extraction",
                model_used=extraction_result.get("model_used", "unknown"),
                prompt_tokens=extraction_result.get("prompt_tokens", 0),
                completion_tokens=extraction_result.get("completion_tokens", 0),
                total_tokens=extraction_result.get("total_tokens", 0),
                response_time_ms=extraction_result.get("response_time_ms", 0),
                success=True,
                metadata={
                    "document_id": document_id,
                    "attribute_name": attribute_name,
                    "execution_id": execution_id
                }
            )
            
            db.add(audit_log)
            await db.commit()
            
            return {
                "status": "success",
                "extracted_value": extraction_result.get("value"),
                "confidence_score": extraction_result.get("confidence_score"),
                "model_used": extraction_result.get("model_used")
            }
            
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            
            # Update status to failed
            analysis_update = update(DocumentAnalysis).where(
                DocumentAnalysis.execution_id == execution_id
            ).values(
                analysis_status="failed",
                error_message=str(e),
                analysis_completed_at=datetime.utcnow()
            )
            
            await db.execute(analysis_update)
            
            test_update = update(TestExecution).where(
                TestExecution.execution_id == execution_id
            ).values(
                test_status="failed",
                test_notes=f"Analysis failed: {str(e)}"
            )
            
            await db.execute(test_update)
            
            await db.commit()
            
            raise


@celery_app.task(bind=True, max_retries=3)
def generate_scoping_recommendations(
    self,
    cycle_id: int,
    report_id: int,
    attributes: List[Dict[str, Any]],
    user_id: int,
    job_id: Optional[str] = None
):
    """
    Generate scoping recommendations using LLM in background
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _generate_scoping_recommendations_async(
                cycle_id, report_id, attributes, user_id, job_id, self.request.id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Scoping recommendation generation failed: {str(exc)}")
        
        # Update job status to failed if job_id provided
        if job_id:
            from app.core.background_jobs import BackgroundJobManager
            job_manager = BackgroundJobManager()
            job = job_manager.get_job(job_id)
            if job:
                job.status = job_manager.JobStatus.FAILED
                job.error = str(exc)
                job.completed_at = datetime.utcnow()
                job_manager._save_jobs_to_file()
        
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _generate_scoping_recommendations_async(
    cycle_id: int,
    report_id: int,
    attributes: List[Dict[str, Any]],
    user_id: int,
    job_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """Async helper for scoping recommendations"""
    
    # Get job manager if job_id provided
    job_manager = None
    job = None
    if job_id:
        from app.core.background_jobs import BackgroundJobManager, JobStatus
        job_manager = BackgroundJobManager()
        job = job_manager.get_job(job_id)
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job_manager._save_jobs_to_file()
    
    async with AsyncSessionLocal() as db:
        try:
            llm_service = get_llm_service()
            
            # Process attributes in batches to avoid token limits
            batch_size = 20  # Configure based on LLM limits
            all_recommendations = []
            total_batches = (len(attributes) + batch_size - 1) // batch_size
            
            for batch_num, i in enumerate(range(0, len(attributes), batch_size)):
                batch = attributes[i:i + batch_size]
                
                # Update job progress
                if job:
                    job.progress_percentage = int((batch_num / total_batches) * 100)
                    job.current_step = f"Processing batch {batch_num + 1} of {total_batches}"
                    job.message = f"Generating LLM recommendations for {len(batch)} attributes..."
                    job.completed_steps = batch_num
                    job_manager._save_jobs_to_file()
                
                # Generate recommendations for this batch
                result = await llm_service.generate_scoping_recommendations(
                    attributes=batch,
                    report_type=attributes[0].get("report_type") if attributes else None
                )
                
                all_recommendations.extend(result.get("recommendations", []))
            
            # Update job to save recommendations phase
            if job:
                job.current_step = "Saving recommendations to database"
                job.message = f"Saving {len(all_recommendations)} recommendations..."
                job.progress_percentage = 90
                job_manager._save_jobs_to_file()
            
            # Save recommendations to database
            # Get the scoping version and add attributes with recommendations
            from app.models.scoping import ScopingVersion
            from app.models.workflow import WorkflowPhase
            from app.services.scoping_service import ScopingService
            
            # Get the current scoping version
            phase_result = await db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Scoping"
                    )
                )
            )
            phase = phase_result.scalar_one_or_none()
            
            if phase and all_recommendations:
                # Get the latest draft version
                version_result = await db.execute(
                    select(ScopingVersion).where(
                        and_(
                            ScopingVersion.phase_id == phase.phase_id,
                            ScopingVersion.version_status == "draft"
                        )
                    ).order_by(ScopingVersion.version_number.desc())
                )
                version = version_result.scalar_one_or_none()
                
                if version:
                    # Add attributes with recommendations
                    service = ScopingService(db)
                    planning_attr_ids = []
                    llm_recommendations = []
                    
                    for rec in all_recommendations:
                        if rec.get("attribute_id"):
                            planning_attr_ids.append(rec["attribute_id"])
                            llm_recommendations.append({
                                "recommendation": rec.get("recommendation", "include"),
                                "confidence_score": rec.get("confidence_score", 0.8),
                                "rationale": rec.get("rationale", ""),
                                "provider": "llm",
                                "is_cde": rec.get("is_cde", False),
                                "is_primary_key": rec.get("is_primary_key", False),
                                "has_historical_issues": rec.get("has_historical_issues", False),
                                "data_quality_score": rec.get("data_quality_score"),
                                "risk_factors": rec.get("risk_factors", [])
                            })
                    
                    if planning_attr_ids:
                        await service.add_attributes_to_version(
                            version_id=version.version_id,
                            planning_attribute_ids=planning_attr_ids,
                            llm_recommendations=llm_recommendations,
                            user_id=user_id
                        )
            
            # Mark job as completed
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress_percentage = 100
                job.current_step = "Completed"
                job.message = f"Successfully generated recommendations for {len(all_recommendations)} attributes"
                job.result = {
                    "recommendations_count": len(all_recommendations),
                    "attributes_processed": len(attributes)
                }
                job_manager._save_jobs_to_file()
            
            return {
                "status": "success",
                "recommendations_count": len(all_recommendations),
                "task_id": task_id,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in scoping recommendations: {str(e)}")
            
            # Update job status to failed
            if job:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                job_manager._save_jobs_to_file()
            
            raise
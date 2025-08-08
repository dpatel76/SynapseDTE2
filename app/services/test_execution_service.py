"""
Unified Test Execution Service
Handles test execution with evidence integration, LLM analysis, and tester approval workflow
"""

import json
import asyncio
import traceback
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload

from app.models.test_execution import TestExecution, TestExecutionReview, TestExecutionAudit
from app.schemas.test_execution_unified import (
    TestExecutionCreateRequest, TestExecutionUpdateRequest, TestExecutionReviewRequest,
    BulkTestExecutionRequest, BulkReviewRequest, TestExecutionResponse, TestExecutionReviewResponse,
    TestExecutionSummaryResponse, TestExecutionDashboardResponse, BulkTestExecutionResponse,
    BulkReviewResponse, TestExecutionCompletionStatusResponse
)
from app.core.exceptions import ValidationError, ResourceNotFoundError, BusinessLogicError
from app.services.llm_service import HybridLLMService
from app.services.database_connection_service import DatabaseConnectionService
from app.services.value_extraction_service import ValueExtractionService
from app.core.logging import get_logger
from app.utils.phase_helpers import get_cycle_report_from_phase

logger = get_logger(__name__)


class TestExecutionService:
    """
    Unified test execution service with evidence integration and tester approval workflow
    """
    
    def __init__(self, db: AsyncSession, llm_service: HybridLLMService, db_service: DatabaseConnectionService):
        self.db = db
        self.llm_service = llm_service
        self.db_service = db_service
    
    def _convert_decimals_to_str(self, obj):
        """Convert Decimal objects to strings for JSON serialization"""
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_str(v) for v in obj]
        return obj
    
    async def create_test_execution(
        self,
        request: TestExecutionCreateRequest,
        phase_id: int,
        cycle_id: int,
        report_id: int,
        executed_by: int,
        created_by: int
    ) -> TestExecutionResponse:
        """
        Create a new test execution with evidence integration
        """
        try:
            # 1. Verify phase exists
            from app.models.workflow import WorkflowPhase
            phase_result = await self.db.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
            )
            phase = phase_result.scalar_one_or_none()
            if not phase:
                raise ResourceNotFoundError(f"Phase with ID {phase_id} not found")
            
            # 2. Get evidence and verify it's approved
            evidence = await self._get_evidence(request.evidence_id)
            
            # Check if evidence is approved
            evidence_status = evidence.get("validation_status", "").lower()
            if evidence_status not in ["valid", "approved"]:
                # For now, we'll allow pending evidence but log a warning
                logger.warning(f"Evidence {request.evidence_id} has status '{evidence_status}' - allowing test execution anyway")
                # In production, you might want to raise an error:
                # raise ValidationError(f"Evidence must be approved before test execution. Current status: {evidence_status}")
            
            # 3. Get next execution number
            execution_number = await self._get_next_execution_number(request.test_case_id)
            
            # 4. Mark previous execution as not latest (and commit the change)
            await self._mark_previous_execution_not_latest(request.test_case_id)
            await self.db.commit()  # Commit the update before creating new record
            
            # 5. Get sample data (evidence already fetched above)
            sample_data = await self._get_sample_data(request.test_case_id)
            
            # 6. Create initial execution record
            execution = TestExecution(
                phase_id=phase_id,
                # cycle_id and report_id are accessed through phase relationship
                test_case_id=request.test_case_id,
                evidence_id=request.evidence_id,
                execution_number=execution_number,
                is_latest_execution=True,
                execution_reason=request.execution_reason.value if hasattr(request.execution_reason, 'value') else request.execution_reason,
                test_type=request.test_type.value if hasattr(request.test_type, 'value') else request.test_type,
                analysis_method=request.analysis_method.value if hasattr(request.analysis_method, 'value') else request.analysis_method,
                execution_status="pending",
                execution_method=request.execution_method.value if hasattr(request.execution_method, 'value') else request.execution_method,
                executed_by=executed_by,
                created_by=created_by,
                updated_by=created_by,
                # Always use "valid" for the constraint - the actual status is tracked in evidence
                evidence_validation_status="valid",
                evidence_version_number=evidence.get("version_number", 1),
                processing_notes=request.processing_notes,
                analysis_results={}  # Will be populated during execution
            )
            
            self.db.add(execution)
            await self.db.commit()
            await self.db.refresh(execution)
            
            # Get the execution with required data
            result = await self.db.execute(
                select(TestExecution)
                .where(TestExecution.id == execution.id)
            )
            execution = result.scalar_one()
            
            # 6. Create audit log
            await self._create_audit_log(
                execution.id,
                "created",
                {"execution_reason": request.execution_reason},
                executed_by
            )
            
            # 7. Execute test case synchronously (like RFI)
            logger.info(f"Executing test case synchronously for execution {execution.id}")
            
            # Check if we should execute in background (for data source tests)
            if request.configuration and request.configuration.get("execute_in_background", False):
                # Use Celery for background execution
                from app.tasks.test_execution_tasks import execute_test_case_celery_task
                from app.core.background_jobs import job_manager
                from app.core.redis_job_manager import get_redis_job_manager
                import uuid
                
                # Generate job ID
                job_id = str(uuid.uuid4())
                
                # Use Redis job manager for cross-container state
                redis_job_manager = get_redis_job_manager()
                
                # Create job record in Redis
                redis_job_manager.create_job(
                    job_id,
                    job_type="test_execution",
                    metadata={
                        "execution_id": execution.id,
                        "test_case_id": request.test_case_id,
                        "evidence_id": request.evidence_id,
                        "phase_id": phase_id,
                        "cycle_id": cycle_id,
                        "report_id": report_id
                    }
                )
                
                # Submit Celery task
                result = execute_test_case_celery_task.apply_async(
                    args=[
                        job_id,
                        execution.id,
                        sample_data,
                        evidence,
                        executed_by
                    ],
                    task_id=job_id,  # Use the same job_id as task_id
                    queue='testing'
                )
                
                logger.info(f"Started test execution as Celery task {result.id} for execution {execution.id}")
                
                # Update execution with job ID
                execution.background_job_id = job_id
                execution.execution_status = "pending"
                await self.db.commit()
                
            else:
                # Execute the test case immediately (synchronous)
                try:
                    await self._execute_test_case(execution.id, sample_data, evidence)
                except Exception as exec_error:
                    logger.error(f"Error during test execution: {str(exec_error)}")
                    logger.error(f"Error type: {type(exec_error).__name__}")
                    logger.error(f"Error traceback: ", exc_info=True)
                    # Update execution status to failed
                    execution.execution_status = "failed"
                    execution.error_message = str(exec_error)
                    execution.error_details = {
                        "error_type": type(exec_error).__name__,
                        "error_details": str(exec_error),
                        "traceback": traceback.format_exc()
                    }
                    execution.completed_at = datetime.utcnow()
                    await self.db.commit()
                    raise
            
            # Refresh execution to get updated data
            await self.db.refresh(execution)
            
            # Get phase info for cycle_id and report_id
            phase_info = await self._get_phase_info_for_test_case(request.test_case_id)
            
            # Build response data
            response_data = {
                "id": execution.id,
                "phase_id": execution.phase_id,
                "cycle_id": phase_info["cycle_id"],
                "report_id": phase_info["report_id"],
                "test_case_id": execution.test_case_id,
                "evidence_id": execution.evidence_id,
                "execution_number": execution.execution_number,
                "is_latest_execution": execution.is_latest_execution,
                "execution_reason": execution.execution_reason,
                "test_type": execution.test_type,
                "analysis_method": execution.analysis_method,
                "sample_value": execution.sample_value,
                "extracted_value": execution.extracted_value,
                "expected_value": execution.expected_value,
                "test_result": execution.test_result,
                "comparison_result": execution.comparison_result,
                "variance_details": execution.variance_details,
                "llm_confidence_score": execution.llm_confidence_score,
                "llm_analysis_rationale": execution.llm_analysis_rationale,
                "llm_model_used": execution.llm_model_used,
                "llm_tokens_used": execution.llm_tokens_used,
                "llm_processing_time_ms": execution.llm_processing_time_ms,
                "database_query_executed": execution.database_query_executed,
                "database_result_count": execution.database_result_count,
                "execution_status": execution.execution_status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "processing_time_ms": execution.processing_time_ms,
                "error_message": execution.error_message,
                "retry_count": execution.retry_count if execution.retry_count is not None else 0,
                "error_details": execution.error_details or {},
                "database_result_sample": execution.database_result_sample or {},
                "database_execution_time_ms": execution.database_execution_time_ms,
                "analysis_results": execution.analysis_results or {},
                "evidence_validation_status": execution.evidence_validation_status,
                "evidence_version_number": execution.evidence_version_number,
                "execution_summary": execution.execution_summary,
                "processing_notes": execution.processing_notes,
                "executed_by": execution.executed_by,
                "execution_method": execution.execution_method,
                "created_at": execution.created_at,
                "updated_at": execution.updated_at,
                "created_by": execution.created_by,
                "updated_by": execution.updated_by
            }
            
            logger.info(f"Returning test execution response: {response_data}")
            
            # Return response
            return TestExecutionResponse(**response_data)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating test execution: {str(e)}")
            raise BusinessLogicError(f"Failed to create test execution: {str(e)}")
    
    async def execute_test_case(self, execution_id: int) -> TestExecutionResponse:
        """
        Execute a specific test case with evidence analysis
        """
        try:
            execution = await self._get_execution(execution_id)
            
            # Update status to running
            execution.execution_status = "running"
            execution.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Create audit log
            await self._create_audit_log(
                execution_id,
                "started",
                {"started_at": execution.started_at.isoformat()},
                execution.executed_by
            )
            
            # Get evidence and sample data
            evidence = await self._get_evidence(execution.evidence_id)
            sample_data = await self._get_sample_data(execution.test_case_id)
            
            # Execute the test case
            await self._execute_test_case(execution_id, sample_data, evidence)
            
            # Refresh execution data
            await self.db.refresh(execution)
            return TestExecutionResponse.from_orm(execution)
            
        except Exception as e:
            logger.error(f"Error executing test case: {str(e)}")
            await self._handle_execution_error(execution_id, str(e))
            raise BusinessLogicError(f"Failed to execute test case: {str(e)}")
    
    async def _execute_test_case(self, execution_id: int, sample_data: Dict[str, Any], evidence: Dict[str, Any]):
        """
        Internal method to execute test case with evidence analysis
        """
        logger.info(f"[DEBUG] SYNCHRONOUS: _execute_test_case called for execution {execution_id}")
        logger.info(f"[DEBUG] Sample data: {sample_data}")
        logger.info(f"[DEBUG] Evidence keys: {evidence.keys() if evidence else 'None'}")
        
        try:
            
            execution = await self._get_execution(execution_id)
            
            # Set start time if not already set
            if not execution.started_at:
                execution.started_at = datetime.utcnow()
                execution.execution_status = "running"
                await self.db.commit()
            
            # 1. Extract sample value
            sample_value = await self._extract_sample_value(sample_data, execution.test_case_id)
            
            # 2. Use ValueExtractionService (same as RFI)
            extraction_service = ValueExtractionService()
            
            # Determine evidence type
            evidence_type = "document" if evidence.get("evidence_type") == "document" else "database_query"
            
            # Prepare evidence dict for value extraction service
            if evidence_type == "document":
                # For documents, we need to read the file content
                file_path = evidence.get("file_path") or evidence.get("document_path")
                document_content = ""
                
                if file_path:
                    import os
                    logger.info(f"Reading document from path: {file_path}")
                    if os.path.exists(file_path):
                        if file_path.endswith('.pdf'):
                            import PyPDF2
                            with open(file_path, 'rb') as file:
                                pdf_reader = PyPDF2.PdfReader(file)
                                for page in pdf_reader.pages:
                                    document_content += page.extract_text() + "\n"
                            logger.info(f"Extracted PDF content, length: {len(document_content)}")
                        else:
                            with open(file_path, 'r') as file:
                                document_content = file.read()
                            logger.info(f"Read text file content, length: {len(document_content)}")
                    else:
                        logger.warning(f"Document file not found: {file_path}")
                
                # Prepare evidence dict with content for ValueExtractionService
                evidence_for_extraction = {
                    "content": document_content,
                    "document_type": evidence.get("document_type", "pdf"),
                    "file_path": file_path
                }
            else:
                # For database queries, pass the evidence as-is
                evidence_for_extraction = evidence
            
            # Extract values using the same service as RFI
            extracted_values = await extraction_service.extract_values_from_evidence(
                evidence=evidence_for_extraction,
                sample_data=sample_data,
                evidence_type=evidence_type
            )
            
            # Get the extracted value
            extracted_value = extracted_values.get("extracted_value", "")
            
            # Build analysis results without auto-deciding pass/fail
            analysis_results = {
                "expected_value": sample_value,
                "actual_value": extracted_value,
                "primary_key_values": extracted_values.get("primary_key_values", {}),
                # Add sample/expected primary key values
                "sample_primary_key_values": sample_data.get("primary_key_attributes", {}),
                "attribute_name": sample_data.get("attribute_name"),
                "sample_identifier": sample_data.get("sample_identifier"),
                "confidence_score": extracted_values.get("confidence_score", 1.0),
                "extraction_details": extracted_values,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "requires_review": True,  # Always require human review
                "execution_source": "sync_execution",  # Track execution source
                # Include all query data for UI display (like RFI does)
                "all_rows": extracted_values.get("all_rows", []),
                "columns": extracted_values.get("columns", []),
                "row_count": extracted_values.get("row_count", 0),
                "extraction_method": extracted_values.get("extraction_method"),
                # Include the full sample data for reference
                "sample_data": sample_data.get("sample_data", {})
            }
            
            logger.info(f"[DEBUG] Synchronous execution - sample_value: {sample_value}")
            logger.info(f"[DEBUG] Synchronous execution - extracted_value: {extracted_value}")
            logger.info(f"[DEBUG] Synchronous execution - analysis_results: {analysis_results}")
            
            # 3. Don't auto-decide - just present the data
            test_result = "pending_review"  # Always pending review
            comparison_result = None  # No auto-comparison
            variance_details = {}
            
            logger.info(f"[DEBUG] Synchronous execution - test_result: {test_result} (always pending_review)")
            
            # 4. Update execution with results
            execution.sample_value = str(sample_value) if sample_value is not None else None
            execution.extracted_value = str(extracted_value) if extracted_value is not None else None
            execution.expected_value = str(sample_value) if sample_value is not None else None
            execution.test_result = test_result
            execution.comparison_result = comparison_result
            execution.variance_details = variance_details
            # Convert Decimals to strings before saving to JSONB
            execution.analysis_results = self._convert_decimals_to_str(analysis_results)
            execution.execution_status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.processing_time_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
            
            # Update execution method fields based on evidence type
            if evidence_type == "document":
                execution.analysis_method = "llm_analysis"
                execution.llm_confidence_score = extracted_values.get("confidence_score")
                execution.llm_analysis_rationale = extracted_values.get("extraction_metadata", {}).get("rationale")
            else:
                execution.analysis_method = "database_query"
                execution.database_query_executed = extracted_values.get("query_executed")
                execution.database_result_count = extracted_values.get("row_count", 0)
                # Convert database result sample Decimals
                if extracted_values.get("all_rows"):
                    execution.database_result_sample = self._convert_decimals_to_str(extracted_values.get("all_rows", [])[:5])
            
            logger.info(f"[DEBUG] Synchronous execution final analysis_results: {execution.analysis_results}")
            
            # Check if analysis_results is being transformed
            if not isinstance(execution.analysis_results, dict):
                logger.error(f"[DEBUG] ERROR: analysis_results is not a dict! Type: {type(execution.analysis_results)}")
            elif "is_match" in execution.analysis_results:
                logger.error(f"[DEBUG] ERROR: 'is_match' found in analysis_results during sync execution!")
                logger.error(f"[DEBUG] This should NOT happen - investigating...")
            
            # 5. Generate execution summary
            execution.execution_summary = await self._generate_execution_summary(execution)
            
            await self.db.commit()
            
            # 6. Create audit log
            await self._create_audit_log(
                execution_id,
                "completed",
                {
                    "test_result": test_result,
                    "comparison_result": comparison_result,
                    "processing_time_ms": execution.processing_time_ms
                },
                execution.executed_by
            )
            
        except Exception as e:
            logger.error(f"Error in test case execution: {str(e)}")
            await self._handle_execution_error(execution_id, str(e))
            raise
    
    async def _extract_value_from_evidence(self, evidence: Dict[str, Any], execution: TestExecution) -> Tuple[str, Dict[str, Any]]:
        """
        Extract value from evidence using appropriate method
        """
        analysis_results = {}
        
        if evidence.get("evidence_type") == "document":
            # Use LLM to extract value from document
            extracted_value, llm_results = await self._extract_from_document(evidence, execution)
            analysis_results["llm_analysis"] = llm_results
            
            # Update LLM-specific fields
            execution.llm_confidence_score = llm_results.get("confidence_score")
            execution.llm_analysis_rationale = llm_results.get("rationale")
            execution.llm_model_used = llm_results.get("model_used")
            execution.llm_tokens_used = llm_results.get("tokens_used")
            execution.llm_response_raw = llm_results.get("response_raw")
            execution.llm_processing_time_ms = llm_results.get("processing_time_ms")
            
        else:  # data_source
            # Use database query to extract value
            extracted_value, db_results = await self._extract_from_database(evidence, execution)
            analysis_results["database_analysis"] = db_results
            
            # Update database-specific fields
            execution.database_query_executed = db_results.get("query_executed")
            execution.database_result_count = db_results.get("result_count")
            execution.database_execution_time_ms = db_results.get("execution_time_ms")
            execution.database_result_sample = db_results.get("result_sample")
        
        return extracted_value, analysis_results
    
    async def _extract_from_document(self, evidence: Dict[str, Any], execution: TestExecution) -> Tuple[str, Dict[str, Any]]:
        """
        Extract value from document using LLM analysis
        """
        try:
            # Import value extraction service
            from app.services.value_extraction_service import ValueExtractionService
            value_service = ValueExtractionService()
            
            # Get sample data for context
            sample_data = await self._get_sample_data_for_test_case(execution.test_case_id)
            
            # Read document content if file path is provided
            document_content = evidence.get("document_content", "")
            # Check for file_path or document_path (evidence uses document_path)
            file_path = evidence.get("file_path") or evidence.get("document_path")
            
            logger.info(f"Looking for document content - file_path: {file_path}")
            logger.info(f"Evidence keys: {evidence.keys()}")
            
            if not document_content and file_path:
                # Read the file content
                import os
                logger.info(f"Checking if file exists: {file_path}")
                if file_path and os.path.exists(file_path):
                    # For PDFs, we need to extract text first
                    if file_path.endswith('.pdf'):
                        # Import PDF extraction utility
                        import PyPDF2
                        logger.info(f"Reading PDF file: {file_path}")
                        with open(file_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            document_content = ""
                            logger.info(f"PDF has {len(pdf_reader.pages)} pages")
                            for page in pdf_reader.pages:
                                page_text = page.extract_text()
                                document_content += page_text + "\n"
                        logger.info(f"Extracted PDF content length: {len(document_content)}")
                    else:
                        logger.info(f"Reading text file: {file_path}")
                        with open(file_path, 'r') as file:
                            document_content = file.read()
                        logger.info(f"Read text content length: {len(document_content)}")
                else:
                    logger.warning(f"File does not exist: {file_path}")
            
            # Prepare evidence dict for value extraction service
            evidence_dict = {
                "content": document_content,
                "document_type": evidence.get("document_type", "pdf"),
                "file_path": file_path  # Use the resolved file_path
            }
            
            # Extract values using the service
            extraction_result = await value_service.extract_values_from_evidence(
                evidence=evidence_dict,
                sample_data=sample_data,
                evidence_type="document"
            )
            
            # Get extracted value and metadata
            extracted_value = extraction_result.get("extracted_value", "")
            
            return extracted_value, {
                "confidence_score": extraction_result.get("confidence_score", 0.0),
                "rationale": extraction_result.get("extraction_metadata", {}).get("rationale", ""),
                "model_used": extraction_result.get("extraction_metadata", {}).get("model", "unknown"),
                "tokens_used": extraction_result.get("extraction_metadata", {}).get("tokens_used", 0),
                "processing_time_ms": extraction_result.get("extraction_metadata", {}).get("processing_time_ms", 0),
                "response_raw": extraction_result.get("extraction_metadata", {}),
                "extraction_method": "llm_analysis",
                "primary_key_values": extraction_result.get("primary_key_values", {})
            }
            
        except Exception as e:
            logger.error(f"Error extracting from document: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error traceback: ", exc_info=True)
            return "", {
                "confidence_score": 0.0,
                "rationale": f"Error during extraction: {str(e)}",
                "model_used": "error",
                "tokens_used": 0,
                "processing_time_ms": 0,
                "response_raw": {},
                "extraction_method": "error"
            }
    
    async def _extract_from_database(self, evidence: Dict[str, Any], execution: TestExecution) -> Tuple[str, Dict[str, Any]]:
        """
        Extract value from database using query execution
        """
        try:
            # Get data source details to get connection type and connection details
            from app.models.request_info import RFIDataSource
            
            data_source_id = evidence.get("data_source_id")
            if not data_source_id:
                raise BusinessLogicError("No data source ID found in evidence")
            
            # Load data source with connection details
            ds_result = await self.db.execute(
                select(RFIDataSource).where(RFIDataSource.data_source_id == data_source_id)
            )
            data_source = ds_result.scalar_one_or_none()
            
            if not data_source:
                raise BusinessLogicError(f"Data source {data_source_id} not found")
            
            # Get connection details (same logic as in test_execution_tasks.py)
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
            
            # Use database service to execute query with correct parameters
            db_response = await self.db_service.execute_query(
                connection_type=data_source.connection_type,
                connection_details=connection_details,
                query=evidence.get("query_text"),
                parameters=None
            )
            
            extracted_value = ""
            if db_response.get("results") and len(db_response["results"]) > 0:
                # Extract first result value
                first_result = db_response["results"][0]
                if isinstance(first_result, dict) and first_result:
                    extracted_value = str(list(first_result.values())[0])
                else:
                    extracted_value = str(first_result)
            
            return extracted_value, {
                "query_executed": evidence.get("query_text", ""),
                "result_count": len(db_response.get("results", [])),
                "execution_time_ms": db_response.get("execution_time_ms", 0),
                "result_sample": db_response.get("results", [])[:5],  # First 5 results
                "connection_validated": db_response.get("connection_validated", False)
            }
            
        except Exception as e:
            logger.error(f"Error extracting from database: {str(e)}")
            return "", {
                "query_executed": evidence.get("query_text", ""),
                "result_count": 0,
                "execution_time_ms": 0,
                "result_sample": [],
                "connection_validated": False,
                "error": str(e)
            }
    
    async def _compare_values(self, sample_value: str, extracted_value: str, test_case_id: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Compare sample and extracted values to determine test result
        """
        try:
            # Direct comparison
            comparison_result = sample_value == extracted_value
            
            # Calculate variance if numeric
            variance_details = {}
            try:
                sample_numeric = float(sample_value)
                extracted_numeric = float(extracted_value)
                variance = abs(sample_numeric - extracted_numeric)
                variance_percentage = (variance / abs(sample_numeric)) * 100 if sample_numeric != 0 else 0
                variance_details = {
                    "variance": variance,
                    "variance_percentage": variance_percentage,
                    "is_numeric": True
                }
            except (ValueError, TypeError):
                variance_details = {
                    "is_numeric": False,
                    "string_similarity": self._calculate_string_similarity(sample_value, extracted_value)
                }
            
            # Determine test result
            if comparison_result:
                test_result = "pass"
            elif variance_details.get("is_numeric") and variance_details.get("variance_percentage", 100) < 5:
                test_result = "pass"  # Accept small numeric variance
            elif variance_details.get("string_similarity", 0) > 0.9:
                test_result = "pass"  # Accept high string similarity
            else:
                test_result = "fail"
            
            return test_result, comparison_result, variance_details
            
        except Exception as e:
            logger.error(f"Error comparing values: {str(e)}")
            return "inconclusive", False, {"error": str(e)}
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using simple character comparison
        """
        if not str1 or not str2:
            return 0.0
        
        str1_lower = str1.lower().strip()
        str2_lower = str2.lower().strip()
        
        if str1_lower == str2_lower:
            return 1.0
        
        # Simple character overlap calculation
        common_chars = set(str1_lower) & set(str2_lower)
        total_chars = set(str1_lower) | set(str2_lower)
        
        return len(common_chars) / len(total_chars) if total_chars else 0.0
    
    async def create_test_execution_review(
        self,
        execution_id: int,
        request: TestExecutionReviewRequest,
        phase_id: int,
        reviewed_by: int
    ) -> TestExecutionReviewResponse:
        """
        Create a review for test execution results
        """
        try:
            # Verify execution exists
            execution = await self._get_execution(execution_id)
            
            # Check if review already exists for this execution by this user
            from sqlalchemy import select, and_
            existing_review_query = select(TestExecutionReview).where(
                and_(
                    TestExecutionReview.execution_id == execution_id,
                    TestExecutionReview.reviewed_by == reviewed_by
                )
            )
            existing_review_result = await self.db.execute(existing_review_query)
            existing_review = existing_review_result.scalar_one_or_none()
            
            if existing_review:
                # Update existing review instead of creating new one
                existing_review.review_status = request.review_status
                existing_review.review_notes = request.review_notes
                existing_review.reviewer_comments = request.reviewer_comments
                existing_review.recommended_action = request.recommended_action
                existing_review.accuracy_score = request.accuracy_score
                existing_review.completeness_score = request.completeness_score
                existing_review.consistency_score = request.consistency_score
                existing_review.overall_score = await self._calculate_overall_score(request)
                existing_review.requires_retest = request.requires_retest
                existing_review.retest_reason = request.retest_reason
                existing_review.escalation_required = request.escalation_required
                existing_review.escalation_reason = request.escalation_reason
                existing_review.updated_by = reviewed_by
                existing_review.updated_at = datetime.utcnow()
                
                review = existing_review
            else:
                # Calculate overall score
                overall_score = await self._calculate_overall_score(request)
                
                # Create new review record
                review = TestExecutionReview(
                    execution_id=execution_id,
                    phase_id=phase_id,
                    review_status=request.review_status,
                    review_notes=request.review_notes,
                    reviewer_comments=request.reviewer_comments,
                    recommended_action=request.recommended_action,
                    accuracy_score=request.accuracy_score,
                    completeness_score=request.completeness_score,
                    consistency_score=request.consistency_score,
                    overall_score=overall_score,
                    review_criteria_used=await self._get_review_criteria(),
                    requires_retest=request.requires_retest,
                    retest_reason=request.retest_reason,
                    escalation_required=request.escalation_required,
                    escalation_reason=request.escalation_reason,
                    reviewed_by=reviewed_by,
                    created_by=reviewed_by,
                    updated_by=reviewed_by
                )
                
                self.db.add(review)
            
            # Update the test execution's test_result based on review status
            if request.review_status == "approved":
                execution.test_result = "pass"
            elif request.review_status == "rejected":
                execution.test_result = "fail"
            
            await self.db.commit()
            await self.db.refresh(review)
            await self.db.refresh(execution)
            
            # Create audit log
            await self._create_audit_log(
                execution_id,
                "reviewed",
                {
                    "review_status": request.review_status,
                    "overall_score": review.overall_score,
                    "requires_retest": request.requires_retest
                },
                reviewed_by
            )
            
            # Update test case status if approved
            if request.review_status == "approved":
                await self._update_test_case_status(execution.test_case_id, "completed")
            
            return TestExecutionReviewResponse.from_orm(review)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating test execution review: {str(e)}")
            raise BusinessLogicError(f"Failed to create review: {str(e)}")
    
    async def get_test_execution_dashboard(
        self,
        cycle_id: int,
        report_id: int,
        phase_id: int
    ) -> TestExecutionDashboardResponse:
        """
        Get test execution dashboard with summary statistics
        """
        try:
            # Get summary statistics
            summary = await self._get_execution_summary(cycle_id, report_id, phase_id)
            
            # Get recent executions
            recent_executions = await self._get_recent_executions(cycle_id, report_id, phase_id, limit=10)
            
            # Get pending reviews
            pending_reviews = await self._get_pending_reviews(cycle_id, report_id, phase_id, limit=10)
            
            # Get quality metrics
            quality_metrics = await self._get_quality_metrics(cycle_id, report_id, phase_id)
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(cycle_id, report_id, phase_id)
            
            return TestExecutionDashboardResponse(
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                summary=summary,
                recent_executions=recent_executions,
                pending_reviews=pending_reviews,
                quality_metrics=quality_metrics,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Error getting test execution dashboard: {str(e)}")
            raise BusinessLogicError(f"Failed to get dashboard: {str(e)}")
    
    async def check_phase_completion(self, cycle_id: int, report_id: int, phase_id: int) -> TestExecutionCompletionStatusResponse:
        """
        Check if test execution phase can be completed
        """
        try:
            # Get all test cases for this phase
            test_cases = await self._get_test_cases_for_phase(cycle_id, report_id, phase_id)
            
            total_test_cases = len(test_cases)
            completed_test_cases = 0
            approved_test_cases = 0
            blocking_issues = []
            completion_requirements = []
            
            for test_case in test_cases:
                # Check if test case has approved execution
                latest_execution = await self._get_latest_execution(test_case["test_case_id"])
                if not latest_execution:
                    blocking_issues.append(f"Test case {test_case['test_case_id']} not executed")
                    continue
                
                if latest_execution.execution_status == "completed":
                    completed_test_cases += 1
                    
                    # Check if test case has approved review
                    review = await self._get_latest_review(latest_execution.id)
                    if review and review.review_status == "approved":
                        approved_test_cases += 1
                    else:
                        blocking_issues.append(f"Test case {test_case['test_case_id']} not approved")
                else:
                    blocking_issues.append(f"Test case {test_case['test_case_id']} execution not completed")
            
            can_complete = len(blocking_issues) == 0 and approved_test_cases == total_test_cases
            completion_percentage = (approved_test_cases / total_test_cases * 100) if total_test_cases > 0 else 0
            
            if not can_complete:
                if approved_test_cases < total_test_cases:
                    completion_requirements.append("All test cases must be approved")
                if completed_test_cases < total_test_cases:
                    completion_requirements.append("All test cases must be executed")
            
            return TestExecutionCompletionStatusResponse(
                can_complete=can_complete,
                completion_requirements=completion_requirements,
                blocking_issues=blocking_issues,
                total_test_cases=total_test_cases,
                completed_test_cases=completed_test_cases,
                approved_test_cases=approved_test_cases,
                completion_percentage=completion_percentage
            )
            
        except Exception as e:
            logger.error(f"Error checking phase completion: {str(e)}")
            raise BusinessLogicError(f"Failed to check completion: {str(e)}")
    
    # Helper methods
    
    async def _get_next_execution_number(self, test_case_id: str) -> int:
        """Get next execution number for test case"""
        result = await self.db.execute(
            select(func.max(TestExecution.execution_number))
            .where(TestExecution.test_case_id == test_case_id)
        )
        max_number = result.scalar_one_or_none()
        return (max_number or 0) + 1
    
    async def _mark_previous_execution_not_latest(self, test_case_id: str):
        """Mark previous execution as not latest"""
        await self.db.execute(
            update(TestExecution)
            .where(TestExecution.test_case_id == test_case_id)
            .values(is_latest_execution=False)
        )
        # Note: Commit is handled by the calling method
    
    async def _get_evidence(self, evidence_id: int) -> Dict[str, Any]:
        """Get evidence details from Request for Information phase"""
        from app.models.request_info import TestCaseEvidence
        
        try:
            # Get evidence from TestCaseEvidence table - use explicit columns to avoid lazy loading
            result = await self.db.execute(
                select(
                    TestCaseEvidence.id,
                    TestCaseEvidence.evidence_type,
                    TestCaseEvidence.validation_status,
                    TestCaseEvidence.version_number,
                    TestCaseEvidence.file_path,
                    TestCaseEvidence.original_filename,
                    TestCaseEvidence.planning_data_source_id,
                    TestCaseEvidence.rfi_data_source_id,
                    TestCaseEvidence.query_text,
                    TestCaseEvidence.query_parameters,
                    TestCaseEvidence.sample_id,
                    TestCaseEvidence.data_owner_id,
                    TestCaseEvidence.submitted_at
                )
                .where(TestCaseEvidence.id == evidence_id)
            )
            evidence_row = result.mappings().fetchone()
            
            if not evidence_row:
                logger.warning(f"Evidence {evidence_id} not found, using default values")
                return {
                    "evidence_id": evidence_id,
                    "evidence_type": "document",
                    "validation_status": "valid",
                    "version_number": 1,
                    "document_path": "/path/to/document",
                    "context": {}
                }
            
            # Build evidence dict
            evidence_dict = {
                "evidence_id": evidence_row["id"],
                "evidence_type": evidence_row["evidence_type"],
                "validation_status": evidence_row["validation_status"],
                "version_number": evidence_row["version_number"],
                "document_path": evidence_row["file_path"],
                "document_name": evidence_row["original_filename"],
                "data_source_id": evidence_row["planning_data_source_id"] or evidence_row["rfi_data_source_id"],
                "query_text": evidence_row["query_text"],
                "query_parameters": evidence_row["query_parameters"],
                "context": {
                    "sample_id": evidence_row["sample_id"],
                    "submitted_by": evidence_row["data_owner_id"],
                    "submission_date": evidence_row["submitted_at"].isoformat() if evidence_row["submitted_at"] else None
                }
            }
            
            # If it's a data source evidence, load and decrypt connection details
            if evidence_row["evidence_type"] == "data_source" and evidence_dict["data_source_id"]:
                connection_info = await self._get_data_source_connection_details(evidence_dict["data_source_id"])
                if connection_info:
                    evidence_dict["connection_type"] = connection_info["connection_type"]
                    evidence_dict["connection_details"] = connection_info["connection_details"]
            
            return evidence_dict
        except Exception as e:
            logger.error(f"Error getting evidence {evidence_id}: {str(e)}")
            # Return default values on error
            return {
                "evidence_id": evidence_id,
                "evidence_type": "document",
                "validation_status": "valid",
                "version_number": 1,
                "document_path": "/path/to/document",
                "context": {}
            }
    
    async def _get_data_source_connection_details(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """Get and decrypt data source connection details - same as RFI"""
        from app.models.request_info import RFIDataSource
        
        # Get data source from RFI data sources table
        result = await self.db.execute(
            select(RFIDataSource)
            .where(RFIDataSource.data_source_id == data_source_id)
        )
        data_source = result.scalar_one_or_none()
        
        if not data_source:
            return None
        
        # Decrypt connection details for use
        decrypted_details = await self._decrypt_connection_details(data_source.connection_details)
        
        return {
            'data_source_id': str(data_source.data_source_id),
            'connection_type': data_source.connection_type,
            'connection_details': decrypted_details
        }
    
    async def _decrypt_connection_details(self, encrypted_details: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt connection details - same as RFI"""
        from app.core.encryption import decrypt_connection_details
        try:
            return decrypt_connection_details(encrypted_details)
        except Exception:
            # If decryption fails, assume it's already decrypted (backwards compatibility)
            return encrypted_details
    
    async def _get_primary_key_attributes(self, cycle_id: int, report_id: int, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get primary key attributes dynamically from scoping phase"""
        from app.models.report_attribute import ReportAttribute
        
        primary_key_attributes = {}
        
        if not cycle_id or not report_id:
            # Fallback to hardcoded keys if no cycle/report info
            default_keys = ["Bank ID", "Customer ID", "Period ID", "Reference Number"]
            for key in default_keys:
                if key in sample_data:
                    primary_key_attributes[key] = sample_data[key]
            return primary_key_attributes
        
        # Get primary key attributes from report_attribute table
        pk_result = await self.db.execute(
            select(ReportAttribute.attribute_name)
            .where(
                and_(
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_primary_key == True
                )
            )
            .order_by(ReportAttribute.primary_key_order.nulls_last())
        )
        primary_keys = [row.attribute_name for row in pk_result.mappings()]
        
        # If no primary keys found in report_attribute, check phase_data
        if not primary_keys:
            phase_result = await self.db.execute(
                select(WorkflowPhase.phase_data)
                .where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Scoping"
                    )
                )
            )
            phase_data = phase_result.scalar_one_or_none()
            if phase_data and isinstance(phase_data, dict):
                primary_keys = phase_data.get('primary_keys', [])
        
        # Still no primary keys? Use defaults
        if not primary_keys:
            primary_keys = ["Bank ID", "Customer ID", "Period ID", "Reference Number"]
        
        # Extract primary key values from sample data
        for key in primary_keys:
            if key in sample_data:
                primary_key_attributes[key] = sample_data[key]
        
        return primary_key_attributes
    
    async def _get_primary_key_list(self, cycle_id: int, report_id: int) -> List[str]:
        """Get list of primary key attribute names dynamically"""
        from app.models.report_attribute import ReportAttribute
        
        if not cycle_id or not report_id:
            return ["Bank ID", "Customer ID", "Period ID", "Reference Number"]
        
        # Get primary key attributes from report_attribute table
        pk_result = await self.db.execute(
            select(ReportAttribute.attribute_name)
            .where(
                and_(
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_primary_key == True
                )
            )
            .order_by(ReportAttribute.primary_key_order.nulls_last())
        )
        primary_keys = [row.attribute_name for row in pk_result.mappings()]
        
        # If no primary keys found in report_attribute, check phase_data
        if not primary_keys:
            from app.models.workflow import WorkflowPhase
            phase_result = await self.db.execute(
                select(WorkflowPhase.phase_data)
                .where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Scoping"
                    )
                )
            )
            phase_data = phase_result.scalar_one_or_none()
            if phase_data and isinstance(phase_data, dict):
                primary_keys = phase_data.get('primary_keys', [])
        
        # Still no primary keys? Use defaults
        if not primary_keys:
            primary_keys = ["Bank ID", "Customer ID", "Period ID", "Reference Number"]
        
        return primary_keys
    
    async def _get_sample_data(self, test_case_id: str) -> Dict[str, Any]:
        """Get sample data for test case"""
        from app.models.request_info import CycleReportTestCase
        from app.models.sample_selection import SampleSelectionSample
        from app.models.workflow import WorkflowPhase
        
        # Convert test_case_id to integer
        try:
            test_case_id_int = int(test_case_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid test_case_id format: {test_case_id}")
            return {}
        
        # Get test case details with phase information
        result = await self.db.execute(
            select(
                CycleReportTestCase.id,
                CycleReportTestCase.test_case_name,
                CycleReportTestCase.attribute_name,
                CycleReportTestCase.sample_id,
                CycleReportTestCase.data_owner_id,
                CycleReportTestCase.phase_id,
                WorkflowPhase.cycle_id,
                WorkflowPhase.report_id
            )
            .outerjoin(WorkflowPhase, WorkflowPhase.phase_id == CycleReportTestCase.phase_id)
            .where(CycleReportTestCase.id == test_case_id_int)
        )
        test_case_row = result.mappings().fetchone()
        
        if not test_case_row:
            logger.error(f"Test case {test_case_id} not found")
            return {}
        
        # Extract test case data from row
        tc_id = test_case_row["id"]
        tc_test_case_name = test_case_row["test_case_name"]
        tc_attribute_name = test_case_row["attribute_name"]
        tc_sample_id = test_case_row["sample_id"]
        tc_data_owner_id = test_case_row["data_owner_id"]
        tc_phase_id = test_case_row["phase_id"]
        tc_cycle_id = test_case_row["cycle_id"]
        tc_report_id = test_case_row["report_id"]
        
        # Try to get sample data from sample selection table
        sample_result = await self.db.execute(
            select(SampleSelectionSample)
            .where(SampleSelectionSample.sample_id == tc_sample_id)
        )
        sample = sample_result.scalar_one_or_none()
        
        if sample and sample.sample_data:
            # Get the attribute value from sample_data JSON
            attribute_value = sample.sample_data.get(tc_attribute_name, "")
            
            # Get primary key values from sample_data dynamically
            primary_key_attributes = await self._get_primary_key_attributes(
                tc_cycle_id,
                tc_report_id,
                sample.sample_data
            )
            
            # Get primary key list
            primary_key_list = await self._get_primary_key_list(
                tc_cycle_id,
                tc_report_id
            )
            
            return {
                "test_case_id": test_case_id,
                "sample_id": tc_sample_id,
                "sample_value": attribute_value,
                "expected_value": attribute_value,  # Add expected_value key
                "sample_data": sample.sample_data or {},
                "primary_key_attributes": primary_key_attributes,
                "primary_key_list": primary_key_list,  # Add for value extraction service
                "attribute_name": tc_attribute_name,
                "sample_identifier": sample.sample_identifier,
                "context": {
                    "test_case_name": tc_test_case_name,
                    "data_owner_id": tc_data_owner_id
                }
            }
        else:
            # If no sample found, try to extract from evidence query
            # Get the approved evidence to extract primary keys from query
            evidence_result = await self.db.execute(
                select(TestCaseEvidence.query_text, TestCaseEvidence.created_at)
                .where(
                    and_(
                        TestCaseEvidence.test_case_id == test_case_id_int,
                        TestCaseEvidence.is_current.is_(True),
                        TestCaseEvidence.tester_decision == "approved"
                    )
                )
                .order_by(TestCaseEvidence.created_at.desc())
            )
            evidence_row = evidence_result.mappings().fetchone()
            
            primary_key_attributes = {}
            if evidence_row and evidence_row["query_text"]:
                # Parse the WHERE clause to extract primary key values
                import re
                query_text = evidence_row["query_text"]
                query_lower = query_text.lower()
                
                # Get primary keys dynamically
                primary_keys = await self._get_primary_key_list(
                    tc_cycle_id,
                    tc_report_id
                )
                
                # Extract values for each primary key from query
                for pk in primary_keys:
                    # Convert to database column name format (e.g., "Bank ID" -> "bank_id")
                    column_name = pk.lower().replace(" ", "_")
                    pattern = rf"{column_name}\s*=\s*'([^']+)'"
                    match = re.search(pattern, evidence.query_text, re.IGNORECASE)
                    if match:
                        primary_key_attributes[pk] = match.group(1)
            
            logger.warning(f"No sample data found for test case {test_case_id}, using primary keys from evidence query")
            
            return {
                "test_case_id": test_case_id,
                "sample_id": tc_sample_id,
                "sample_value": "",  # We don't have the expected value
                "expected_value": "",
                "sample_data": {},
                "primary_key_attributes": primary_key_attributes,
                "primary_key_list": primary_keys,  # Add for value extraction service
                "attribute_name": tc_attribute_name,
                "sample_identifier": tc_sample_id,
                "context": {
                    "test_case_name": tc_test_case_name,
                    "data_owner_id": tc_data_owner_id
                }
            }
    
    async def _extract_sample_value(self, sample_data: Dict[str, Any], test_case_id: str) -> str:
        """Extract expected value from sample data"""
        return sample_data.get("sample_value", "")
    
    async def _generate_execution_summary(self, execution: TestExecution) -> str:
        """Generate human-readable execution summary"""
        return f"Test execution {execution.execution_number} for {execution.test_case_id}: {execution.test_result}"
    
    async def _handle_execution_error(self, execution_id: int, error_message: str):
        """Handle execution error by updating status and creating audit log"""
        try:
            execution = await self._get_execution(execution_id)
            execution.execution_status = "failed"
            execution.error_message = error_message
            execution.completed_at = datetime.utcnow()
            await self.db.commit()
            
            await self._create_audit_log(
                execution_id,
                "failed",
                {"error_message": error_message},
                execution.executed_by
            )
        except Exception as e:
            logger.error(f"Error handling execution error: {str(e)}")
    
    async def _get_execution(self, execution_id: int) -> TestExecution:
        """Get execution by ID"""
        result = await self.db.execute(
            select(TestExecution).where(TestExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if not execution:
            raise ResourceNotFoundError(f"Test execution {execution_id} not found")
        return execution
    
    async def _create_audit_log(self, execution_id: int, action: str, details: Dict[str, Any], performed_by: int):
        """Create audit log entry"""
        audit = TestExecutionAudit(
            execution_id=execution_id,
            action=action,
            action_details=details,
            performed_by=performed_by
        )
        self.db.add(audit)
        await self.db.commit()
    
    async def _calculate_overall_score(self, request: TestExecutionReviewRequest) -> float:
        """Calculate overall quality score"""
        scores = [
            request.accuracy_score or 0.0,
            request.completeness_score or 0.0,
            request.consistency_score or 0.0
        ]
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    
    async def _get_review_criteria(self) -> Dict[str, Any]:
        """Get review criteria configuration"""
        return {
            "criteria_version": "1.0",
            "accuracy_weight": 0.4,
            "completeness_weight": 0.3,
            "consistency_weight": 0.3,
            "minimum_threshold": 0.8,
            "auto_approve_threshold": 0.95
        }
    
    async def _update_test_case_status(self, test_case_id: str, status: str):
        """Update test case status"""
        # Implementation depends on test case models
        pass
    
    async def _get_execution_summary(self, cycle_id: int, report_id: int, phase_id: int) -> TestExecutionSummaryResponse:
        """Get execution summary statistics"""
        # Implementation for summary statistics
        return TestExecutionSummaryResponse(
            total_executions=0,
            completed_executions=0,
            failed_executions=0,
            pending_executions=0,
            pending_reviews=0,
            approved_reviews=0,
            rejected_reviews=0,
            completion_percentage=0.0,
            average_processing_time_ms=0,
            success_rate=0.0
        )
    
    async def _get_recent_executions(self, cycle_id: int, report_id: int, phase_id: int, limit: int) -> List[TestExecutionResponse]:
        """Get recent executions"""
        return []
    
    async def _get_pending_reviews(self, cycle_id: int, report_id: int, phase_id: int, limit: int) -> List[TestExecutionResponse]:
        """Get executions pending review"""
        return []
    
    async def _get_quality_metrics(self, cycle_id: int, report_id: int, phase_id: int) -> Dict[str, Any]:
        """Get quality metrics"""
        return {}
    
    async def _get_performance_metrics(self, cycle_id: int, report_id: int, phase_id: int) -> Dict[str, Any]:
        """Get performance metrics"""
        return {}
    
    async def _get_test_cases_for_phase(self, cycle_id: int, report_id: int, phase_id: int) -> List[Dict[str, Any]]:
        """Get all test cases for phase"""
        return []
    
    async def _get_latest_execution(self, test_case_id: str) -> Optional[TestExecution]:
        """Get latest execution for test case"""
        result = await self.db.execute(
            select(TestExecution)
            .where(TestExecution.test_case_id == test_case_id)
            .where(TestExecution.is_latest_execution == True)
        )
        return result.scalar_one_or_none()
    
    async def _get_latest_review(self, execution_id: int) -> Optional[TestExecutionReview]:
        """Get latest review for execution"""
        result = await self.db.execute(
            select(TestExecutionReview)
            .where(TestExecutionReview.execution_id == execution_id)
            .order_by(desc(TestExecutionReview.reviewed_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def _get_phase_id_for_cycle_report(self, cycle_id: int, report_id: int, phase_name: str) -> int:
        """Get phase_id for a specific cycle, report, and phase name"""
        from app.models.workflow import WorkflowPhase
        
        result = await self.db.execute(
            select(WorkflowPhase.phase_id)
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        phase_id = result.scalar_one_or_none()
        
        if not phase_id:
            raise ResourceNotFoundError(f"Phase '{phase_name}' not found for cycle {cycle_id}, report {report_id}")
        
        return phase_id
    
    async def _get_phase_info_for_test_case(self, test_case_id: str) -> Dict[str, Any]:
        """Get phase information for a test case"""
        from app.models.request_info import CycleReportTestCase
        from app.models.workflow import WorkflowPhase
        
        # Convert test_case_id to integer
        try:
            test_case_id_int = int(test_case_id)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid test_case_id format: {test_case_id}")
        
        # Get test case with phase information
        tc_result = await self.db.execute(
            select(
                CycleReportTestCase.phase_id,
                WorkflowPhase.cycle_id,
                WorkflowPhase.report_id,
                WorkflowPhase.phase_name
            )
            .outerjoin(WorkflowPhase, WorkflowPhase.phase_id == CycleReportTestCase.phase_id)
            .where(CycleReportTestCase.id == test_case_id_int)
        )
        tc_row = tc_result.mappings().fetchone()
        
        if not tc_row:
            raise ResourceNotFoundError(f"Test case {test_case_id} not found")
        
        return {
            "phase_id": tc_row["phase_id"],
            "cycle_id": tc_row["cycle_id"],
            "report_id": tc_row["report_id"],
            "phase_name": tc_row["phase_name"] or "Testing"
        }
    
    async def _get_phase_id_for_execution(self, execution_id: int) -> int:
        """Get phase_id for an execution"""
        result = await self.db.execute(
            select(TestExecution.phase_id)
            .where(TestExecution.id == execution_id)
        )
        phase_id = result.scalar_one_or_none()
        
        if not phase_id:
            raise ResourceNotFoundError(f"Execution {execution_id} not found")
        
        return phase_id
    
    async def _mark_phase_complete(self, cycle_id: int, report_id: int, phase_id: int, user_id: int):
        """Mark phase as complete"""
        from app.models.workflow import WorkflowPhase
        
        result = await self.db.execute(
            select(WorkflowPhase)
            .where(WorkflowPhase.phase_id == phase_id)
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ResourceNotFoundError(f"Phase {phase_id} not found")
        
        phase.status = "Completed"
        phase.completed_date = datetime.utcnow()
        phase.updated_by_id = user_id
        phase.updated_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def _get_execution(self, execution_id: int) -> TestExecution:
        """Get execution by ID"""
        result = await self.db.execute(
            select(TestExecution)
            .where(TestExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        
        if not execution:
            raise ResourceNotFoundError(f"Execution {execution_id} not found")
        
        return execution
    
    async def _get_approved_evidence_for_test_case(self, test_case_id: str) -> Optional[Dict[str, Any]]:
        """Get approved evidence for test case"""
        from app.models.request_info import TestCaseEvidence
        
        # Convert test_case_id to integer
        try:
            test_case_id_int = int(test_case_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid test_case_id format: {test_case_id}")
            return None
        
        # First check if there's any evidence at all
        # Use explicit columns to avoid lazy loading issues
        all_evidence_result = await self.db.execute(
            select(
                TestCaseEvidence.id,
                TestCaseEvidence.evidence_type,
                TestCaseEvidence.validation_status,
                TestCaseEvidence.tester_decision,
                TestCaseEvidence.version_number,
                TestCaseEvidence.file_path,
                TestCaseEvidence.original_filename,
                TestCaseEvidence.planning_data_source_id,
                TestCaseEvidence.rfi_data_source_id,
                TestCaseEvidence.query_text,
                TestCaseEvidence.test_case_id,
                TestCaseEvidence.query_parameters,
                TestCaseEvidence.sample_id,
                TestCaseEvidence.data_owner_id,
                TestCaseEvidence.submitted_at
            )
            .where(
                and_(
                    TestCaseEvidence.test_case_id == test_case_id_int,
                    TestCaseEvidence.is_current.is_(True)
                )
            )
            .order_by(TestCaseEvidence.version_number.desc())
        )
        all_evidence = all_evidence_result.mappings().fetchall()
        
        if not all_evidence:
            logger.warning(f"No evidence found for test case {test_case_id}")
            return None
        
        # Check for tester-approved evidence first, then validation status
        approved_evidence = None
        for row in all_evidence:
            # Access row data by name
            ev_id = row["id"]
            ev_type = row["evidence_type"]
            ev_validation_status = row["validation_status"]
            ev_tester_decision = row["tester_decision"]
            
            # Check tester decision field
            if ev_tester_decision == 'approved':
                logger.info(f"Found tester-approved evidence {ev_id} for test case {test_case_id}")
                approved_evidence = row
                break
            # Fallback to validation status
            elif ev_validation_status in ['valid', 'approved', 'Valid', 'Approved']:
                approved_evidence = row
                break
        
        if not approved_evidence:
            # Get the status of the most recent evidence
            latest_row = all_evidence[0]
            latest_id = latest_row["id"]
            latest_validation_status = latest_row["validation_status"]
            latest_tester_decision = latest_row["tester_decision"]
            logger.warning(f"No approved evidence found for test case {test_case_id}. Latest evidence has tester_decision: {latest_tester_decision}, validation_status: {latest_validation_status}")
            
            # Allow pending evidence to be used for testing if no approved evidence exists
            # This allows testers to execute tests while evidence is pending approval
            if latest_validation_status in ['pending', 'Pending'] or latest_tester_decision is None:
                logger.info(f"Using evidence {latest_id} (status: {latest_validation_status}, tester_decision: {latest_tester_decision}) for test case {test_case_id}")
                approved_evidence = latest_row
            else:
                return None
        
        evidence_row = approved_evidence
        
        return {
            "id": evidence_row["id"],
            "evidence_type": evidence_row["evidence_type"],
            "validation_status": evidence_row["validation_status"],
            "version_number": evidence_row["version_number"],
            "document_path": evidence_row["file_path"],
            "document_name": evidence_row["original_filename"],
            "data_source_id": evidence_row["planning_data_source_id"] or evidence_row["rfi_data_source_id"],
            "query_text": evidence_row["query_text"],
            "query_parameters": evidence_row["query_parameters"],
            "context": {
                "sample_id": evidence_row["sample_id"],
                "submitted_by": evidence_row["data_owner_id"],
                "submitted_at": evidence_row["submitted_at"].isoformat() if evidence_row["submitted_at"] else None
            }
        }
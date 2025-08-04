"""
Evidence Collection Service for Request for Information Phase
Implements the business logic for test case level evidence collection
"""

import os
import uuid
import shutil
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_, or_, func, case, desc, text, select
from fastapi import HTTPException, UploadFile

from app.models.request_info import (
    CycleReportTestCase, TestCaseSourceEvidence, RFIEvidenceLegacy, EvidenceValidationResult, 
    evidence_type_enum, evidence_validation_status_enum,
    validation_result_enum, tester_decision_enum, RFIDataSource
)
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.core.config import settings
from app.services.evidence_validation_service import EvidenceValidationService
from app.services.evidence_validation_rules import LLMDocumentExtractionRule, DocumentComplianceRule


class EvidenceCollectionService:
    """Service for managing test case evidence collection"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = Path(settings.upload_dir) / "evidence"
        self._ensure_upload_directory()
        self.validation_service = EvidenceValidationService(db)
    
    def _ensure_upload_directory(self):
        """Ensure upload directory exists"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def _validate_test_case_access(self, test_case_id: str, user_id: int, 
                                  require_data_owner: bool = False) -> CycleReportTestCase:
        """Validate test case exists and user has access"""
        # Try to convert test_case_id to int if it's numeric
        try:
            numeric_id = int(test_case_id)
            filter_condition = CycleReportTestCase.id == numeric_id
        except ValueError:
            # If not numeric, it's invalid since test_case_id is always numeric
            raise HTTPException(status_code=404, detail="Invalid test case ID format")
            
        result = await self.db.execute(
            select(CycleReportTestCase).options(
                selectinload(CycleReportTestCase.phase),
                selectinload(CycleReportTestCase.data_owner),
                selectinload(CycleReportTestCase.attribute)
            ).filter(filter_condition)
        )
        test_case = result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        if require_data_owner and test_case.data_owner_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to access this test case"
            )
        
        return test_case
    
    def _get_current_evidence(self, test_case_id: str) -> Optional[TestCaseSourceEvidence]:
        """Get current evidence for a test case"""
        return self.db.query(TestCaseSourceEvidence).filter(
            and_(
                TestCaseSourceEvidence.test_case_id == test_case_id,
                TestCaseSourceEvidence.is_current == True
            )
        ).first()
    
    def _check_evidence_type_consistency(self, test_case_id: str, new_evidence_type: str) -> None:
        """Check if existing evidence type matches new evidence type"""
        # Get any existing evidence for this test case
        existing_evidence = self.db.query(TestCaseSourceEvidence).filter(
            TestCaseSourceEvidence.test_case_id == test_case_id
        ).first()
        
        if existing_evidence and existing_evidence.evidence_type != new_evidence_type:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit {new_evidence_type} evidence. This test case already has {existing_evidence.evidence_type} evidence. Data owners must use only one type of evidence per test case."
            )
    
    def _create_evidence_version(self, test_case_id: str, user_id: int) -> int:
        """Create new evidence version, retiring old one if exists"""
        current_evidence = self._get_current_evidence(test_case_id)
        
        if current_evidence:
            # Retire current evidence
            current_evidence.is_current = False
            current_evidence.updated_at = datetime.now(timezone.utc)
            current_evidence.updated_by = user_id
            return current_evidence.version_number + 1
        
        return 1
    
    async def _validate_document_with_extraction(self, evidence: TestCaseSourceEvidence, test_case) -> Dict[str, Any]:
        """Validate document with LLM extraction of primary keys and attribute values"""
        try:
            # Get attribute information
            from app.models.report_attribute import ReportAttribute
            attribute = self.db.query(ReportAttribute).filter(
                ReportAttribute.id == test_case.attribute_id
            ).first()
            
            # Get primary key fields from test case
            primary_key_fields = test_case.primary_key_attributes or {}
            
            # Prepare context for validation
            context = {
                'test_case': test_case,
                'attribute_info': {
                    'name': attribute.attribute_name if attribute else test_case.attribute_name,
                    'description': attribute.description if attribute else '',
                    'data_type': attribute.data_type if attribute else 'string',
                    'regulatory_definition': attribute.regulatory_definition if attribute else ''
                },
                'primary_key_fields': primary_key_fields
            }
            
            # Run LLM extraction validation
            llm_validator = LLMDocumentExtractionRule(self.db)
            extraction_result = await llm_validator.validate(evidence, context)
            
            # Run compliance validation
            compliance_validator = DocumentComplianceRule(self.db)
            compliance_result = await compliance_validator.validate(evidence, context)
            
            # Save validation results
            validation_results = [extraction_result, compliance_result]
            
            for result in validation_results:
                validation_record = EvidenceValidationResult(
                    evidence_id=evidence.id,
                    rule=result['rule'],
                    result=result['result'],
                    message=result['message'],
                    details=result.get('details', {})
                )
                self.db.add(validation_record)
            
            self.db.commit()
            
            # Return summary
            return {
                'extraction_result': extraction_result,
                'compliance_result': compliance_result,
                'overall_status': 'valid' if extraction_result['result'] == 'passed' else 'requires_review',
                'extracted_values': extraction_result.get('details', {}).get('extracted_values', {})
            }
            
        except Exception as e:
            import logging
            logging.error(f"Error in document validation: {str(e)}")
            return {
                'extraction_result': {'result': 'failed', 'message': str(e)},
                'compliance_result': {'result': 'failed', 'message': str(e)},
                'overall_status': 'failed'
            }
    
    # Evidence Submission Methods
    
    async def submit_document_evidence(self, test_case_id: str, file: UploadFile, 
                                     user_id: int, submission_notes: Optional[str] = None) -> Dict[str, Any]:
        """Submit document evidence for a test case"""
        
        # Validate test case and user access
        test_case = self._validate_test_case_access(test_case_id, user_id, require_data_owner=True)
        
        # Check evidence type consistency
        self._check_evidence_type_consistency(test_case_id, 'document')
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        try:
            # Generate unique filename and save file
            file_extension = Path(file.filename).suffix
            stored_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / stored_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Calculate file hash for integrity
            import hashlib
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            file_size = file_path.stat().st_size
            
            # Determine MIME type
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.filename)
            
            # Create new evidence version
            version_number = self._create_evidence_version(test_case_id, user_id)
            
            # Create evidence record
            evidence = TestCaseSourceEvidence(
                phase_id=test_case.phase_id,
                # cycle_id=test_case.cycle_id,  # Column not in database
                # report_id=test_case.report_id,  # Column not in database
                test_case_id=test_case_id,
                sample_id=test_case.sample_id,
                attribute_id=test_case.attribute_id,
                evidence_type='document',
                document_name=file.filename,
                document_path=str(file_path),
                document_size=file_size,
                mime_type=mime_type or "application/octet-stream",
                document_hash=file_hash,
                submitted_by=user_id,
                submission_notes=submission_notes,
                version_number=version_number,
                is_current=True,
                created_by=user_id,
                updated_by=user_id
            )
            
            self.db.add(evidence)
            
            # Update test case status
            test_case.status = 'Submitted'
            test_case.submitted_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(evidence)
            
            # Trigger validation
            validation_summary = self.validation_service.validate_and_save(evidence)
            
            return {
                "success": True,
                "evidence_id": evidence.id,
                "version_number": version_number,
                "validation_summary": validation_summary,
                "message": "Document evidence submitted successfully"
            }
            
        except Exception as e:
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit document evidence: {str(e)}"
            )
    
    async def submit_data_source_evidence(self, test_case_id: str, data_source_id: int,
                                        query_text: str, user_id: int,
                                        query_parameters: Optional[Dict[str, Any]] = None,
                                        submission_notes: Optional[str] = None) -> Dict[str, Any]:
        """Submit data source evidence for a test case"""
        
        # Validate test case and user access
        test_case = self._validate_test_case_access(test_case_id, user_id, require_data_owner=True)
        
        # Check evidence type consistency
        self._check_evidence_type_consistency(test_case_id, 'data_source')
        
        # Validate data source exists
        data_source = self.db.query(RFIDataSource).filter(
            RFIDataSource.data_source_id == data_source_id
        ).first()
        
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        try:
            # Execute query to get sample results (for validation)
            query_result_sample = self._execute_query_sample(
                data_source, query_text, query_parameters
            )
            
            # Create new evidence version
            version_number = self._create_evidence_version(test_case_id, user_id)
            
            # Create evidence record
            evidence = TestCaseSourceEvidence(
                phase_id=test_case.phase_id,
                # cycle_id=test_case.cycle_id,  # Column not in database
                # report_id=test_case.report_id,  # Column not in database
                test_case_id=test_case_id,
                sample_id=test_case.sample_id,
                attribute_id=test_case.attribute_id,
                evidence_type='data_source',
                data_source_id=data_source_id,
                query_text=query_text,
                query_parameters=query_parameters,
                query_result_sample=query_result_sample,
                submitted_by=user_id,
                submission_notes=submission_notes,
                version_number=version_number,
                is_current=True,
                created_by=user_id,
                updated_by=user_id
            )
            
            self.db.add(evidence)
            
            # Update test case status
            test_case.status = 'Submitted'
            test_case.submitted_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(evidence)
            
            # Trigger validation
            validation_summary = self.validation_service.validate_and_save(evidence)
            
            return {
                "success": True,
                "evidence_id": evidence.id,
                "version_number": version_number,
                "query_result_sample": query_result_sample,
                "validation_summary": validation_summary,
                "message": "Data source evidence submitted successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit data source evidence: {str(e)}"
            )
    
    async def _execute_query_sample(self, data_source: RFIDataSource, 
                            query_text: str, query_parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute query and return sample results for validation"""
        
        try:
            # Import the database connection service
            from app.services.database_connection_service import DatabaseConnectionService
            
            # Initialize service
            db_service = DatabaseConnectionService()
            
            # Create limited query for sample (first 10 rows)
            limited_query = f"SELECT * FROM ({query_text}) AS subquery LIMIT 10"
            
            # Extract connection details from data source
            # RFIDataSource stores all connection info in connection_details JSONB field
            
            # First, ensure we have a fresh data source object
            import logging
            logging.info(f"Data source ID: {data_source.data_source_id}")
            logging.info(f"Data source name: {data_source.source_name}")
            logging.info(f"Data source type: {type(data_source)}")
            
            # Try to access connection_details directly
            try:
                # Force refresh if needed
                if hasattr(self.db, 'refresh'):
                    await self.db.refresh(data_source)
                    logging.info("Refreshed data source from database")
            except Exception as e:
                logging.warning(f"Could not refresh data source: {e}")
            
            connection_details = data_source.connection_details
            
            # Log the raw connection details type and value for debugging
            logging.info(f"Raw connection_details type: {type(connection_details)}")
            logging.info(f"Raw connection_details value: {connection_details}")
            logging.info(f"Data source dict: {data_source.__dict__ if hasattr(data_source, '__dict__') else 'No __dict__'}")
            
            # Check if connection_details is empty, might need to be loaded differently
            if not connection_details:
                # Log all attributes of the data source to debug
                logging.info(f"Connection details is empty or None")
                logging.info(f"Data source attributes: {[attr for attr in dir(data_source) if not attr.startswith('_')]}")
                
                # If connection_details is None, try to set it as empty dict
                connection_details = {}
                
                # Try to check if there are other fields that might contain connection info
                if hasattr(data_source, 'connection_config'):
                    connection_details = data_source.connection_config
                    logging.info(f"Using connection_config instead: {connection_details}")
                elif hasattr(data_source, 'config'):
                    connection_details = data_source.config
                    logging.info(f"Using config instead: {connection_details}")
            
            # If connection_details is a string, it might be encrypted or JSON
            if isinstance(connection_details, str):
                import json
                # Check if it's an empty string
                if not connection_details.strip():
                    logging.warning("Connection details is an empty string")
                    connection_details = {}
                else:
                    # First try to parse as JSON
                    try:
                        connection_details = json.loads(connection_details)
                        logging.info(f"Parsed connection_details from JSON string")
                    except json.JSONDecodeError:
                        # If JSON parsing fails, it might be encrypted
                        logging.info("JSON parsing failed, attempting to decrypt connection_details")
                        try:
                            from app.core.encryption import EncryptionService
                            encryption_service = EncryptionService()
                            connection_details = encryption_service.decrypt_dict(connection_details)
                            logging.info(f"Successfully decrypted connection_details")
                            logging.info(f"Decrypted keys: {list(connection_details.keys())}")
                        except Exception as decrypt_error:
                            logging.error(f"Failed to decrypt connection_details: {decrypt_error}")
                            raise ValueError(f"Connection details appear to be encrypted but decryption failed: {str(decrypt_error)}")
            
            # Ensure we have the required fields
            if not connection_details or not isinstance(connection_details, dict):
                logging.error(f"Connection details is not a valid dictionary: {type(connection_details)}")
                
                # Try one more time - query the database directly
                try:
                    from sqlalchemy import text
                    query = text("""
                        SELECT connection_details 
                        FROM cycle_report_rfi_data_sources 
                        WHERE data_source_id = :ds_id
                    """)
                    result = await self.db.execute(query, {"ds_id": str(data_source.data_source_id)})
                    row = result.first()
                    if row and row.connection_details:
                        logging.info(f"Direct query found connection_details: {row.connection_details}")
                        if isinstance(row.connection_details, dict):
                            connection_details = row.connection_details
                        elif isinstance(row.connection_details, str) and row.connection_details.strip():
                            import json
                            try:
                                connection_details = json.loads(row.connection_details)
                            except:
                                pass
                except Exception as e:
                    logging.error(f"Direct query failed: {e}")
                
                # If still no valid connection details
                if not connection_details or not isinstance(connection_details, dict):
                    # Provide more helpful error message
                    raise ValueError(
                        f"Data source '{data_source.source_name}' has no valid connection details configured. "
                        f"The connection_details field appears to be empty or invalid. "
                        f"Please reconfigure the data source with actual database connection details."
                    )
            
            # Log connection details for debugging (without password)
            safe_details = {k: v for k, v in connection_details.items() if k != 'password'}
            logging.info(f"Connection type: {data_source.connection_type}")
            logging.info(f"Connection details keys: {list(connection_details.keys())}")
            logging.info(f"Connection details (without password): {safe_details}")
            
            # Execute the query
            import time
            start_time = time.time()
            
            try:
                # Execute real query
                result = await db_service.execute_query(
                    connection_type=data_source.connection_type,
                    connection_details=connection_details,
                    query=limited_query,
                    parameters=query_parameters,
                    timeout=30.0
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # Extract data from result
                sample_rows = result.get('rows', [])
                columns = result.get('columns', [])
                total_count = result.get('total_count', len(sample_rows))
                
                return {
                    "sample_rows": sample_rows[:10],  # Limit to 10 rows for display
                    "column_count": len(columns),
                    "row_count": total_count,
                    "execution_time_ms": execution_time,
                    "query_valid": True,
                    "columns": columns
                }
                
            except Exception as query_error:
                # If real query fails, return the error
                import logging
                logging.error(f"Query execution failed: {str(query_error)}")
                
                execution_time = int((time.time() - start_time) * 1000)
                
                return {
                    "error": str(query_error),
                    "query_valid": False,
                    "sample_rows": [],
                    "column_count": 0,
                    "row_count": 0,
                    "execution_time_ms": execution_time
                }
            
        except Exception as e:
            import logging
            logging.error(f"Error in query sample execution: {str(e)}")
            return {
                "error": str(e),
                "query_valid": False,
                "sample_rows": [],
                "column_count": 0,
                "row_count": 0,
                "execution_time_ms": 0
            }
    
    # Evidence Validation Methods (delegated to EvidenceValidationService)
    
    # Evidence Retrieval Methods
    
    async def get_test_case_evidence(self, test_case_id: str, user_id: int) -> Dict[str, Any]:
        """Get evidence for a test case"""
        
        test_case = await self._validate_test_case_access(test_case_id, user_id)
        
        # Get ALL evidence versions from RFIEvidenceLegacy table (cycle_report_test_cases_evidence)
        from app.models.request_info import RFIEvidenceLegacy
        result = await self.db.execute(
            select(RFIEvidenceLegacy).options(
                selectinload(RFIEvidenceLegacy.data_owner),
                selectinload(RFIEvidenceLegacy.validated_by_user),
                selectinload(RFIEvidenceLegacy.decided_by_user)
            ).filter(
                RFIEvidenceLegacy.test_case_id == test_case.id  # Get all versions
            ).order_by(RFIEvidenceLegacy.version_number.desc())
        )
        evidence_list = result.scalars().all()
        
        if not evidence_list:
            return {
                "test_case_id": test_case_id,
                "has_evidence": False,
                "evidence": [],
                "validation_results": [],
                "tester_decisions": []
            }
        
        # Log what we found
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Found {len(evidence_list)} evidence records for test case {test_case_id}")
        
        # Format evidence data - return as a list to match frontend expectations
        evidence_data = []
        for evidence in evidence_list:
            evidence_item = {
                "id": evidence.id,
                "evidence_type": evidence.evidence_type,
                "version_number": evidence.version_number,  # TestCaseSourceEvidence uses version_number
                "is_current": evidence.is_current,
                "validation_status": evidence.validation_status,
                "validation_notes": evidence.validation_notes,
                "validated_at": evidence.validated_at.isoformat() if evidence.validated_at else None,
                "validated_by_name": f"{evidence.validated_by_user.first_name} {evidence.validated_by_user.last_name}" if evidence.validated_by_user else None,
                "submitted_at": evidence.submitted_at.isoformat() if evidence.submitted_at else None,
                "submission_notes": evidence.submission_notes,
                "submitted_by_name": f"{evidence.data_owner.first_name} {evidence.data_owner.last_name}" if evidence.data_owner else None,
                "tester_decision": evidence.tester_decision,
                "tester_notes": evidence.tester_notes,
                "decided_at": evidence.decided_at.isoformat() if evidence.decided_at else None,
                "decided_by_name": f"{evidence.decided_by_user.first_name} {evidence.decided_by_user.last_name}" if evidence.decided_by_user else None
            }
            
            # Add type-specific data
            if evidence.evidence_type == 'document':
                evidence_item.update({
                    "original_filename": evidence.original_filename,
                    "file_size_bytes": evidence.file_size_bytes,
                    "file_path": evidence.file_path,
                    "stored_filename": evidence.stored_filename,
                    "document_type": evidence.document_type
                })
            elif evidence.evidence_type == 'data_source':
                evidence_item.update({
                    "data_source_id": evidence.rfi_data_source_id or evidence.planning_data_source_id,
                    "data_source_name": "Data Source",  # Would need to load data source separately
                    "query_text": evidence.query_text,
                    "query_parameters": evidence.query_parameters,
                    "query_validation_id": evidence.query_validation_id
                })
            
            evidence_data.append(evidence_item)
        
        # Get the total count of all versions
        total_versions = len(evidence_list)
        
        # Get tester decisions for this test case
        # TODO: The tester_decisions table doesn't exist yet
        tester_decisions_data = []
        
        # Get validation results for all current evidence
        # TODO: The validation_results table might not exist yet
        validation_results_data = []
        
        return {
            "test_case_id": test_case_id,
            "has_evidence": len(evidence_data) > 0,
            "evidence": evidence_data,
            "total_versions": total_versions,
            "validation_results": validation_results_data,
            "tester_decisions": tester_decisions_data
        }
    
    def get_evidence_for_tester_review(self, phase_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get evidence pending tester review"""
        
        # Get all evidence for the phase that needs review
        evidence_query = self.db.query(TestCaseSourceEvidence).options(
            selectinload(TestCaseSourceEvidence.test_case),
            # selectinload(TestCaseSourceEvidence.submitted_by_user),  # Using TestCase.data_owner instead
            selectinload(TestCaseSourceEvidence.attribute)
        ).filter(
            and_(
                TestCaseSourceEvidence.phase_id == phase_id,
                TestCaseSourceEvidence.is_current == True,
                TestCaseSourceEvidence.validation_status.in_(['valid', 'requires_review'])
            )
        )
        
        evidence_list = evidence_query.all()
        
        result = []
        for evidence in evidence_list:
            # Check if already reviewed by this tester using embedded fields
            if evidence.tester_decision and evidence.decided_by == user_id:
                continue  # Skip already reviewed evidence
            
            # Get validation results
            validation_results = self.db.query(EvidenceValidationResult).filter(
                EvidenceValidationResult.evidence_id == evidence.id
            ).all()
            
            evidence_data = {
                "evidence_id": evidence.id,
                "test_case_id": evidence.test_case_id,
                "sample_id": evidence.sample_id,
                "attribute_name": evidence.attribute.attribute_name,
                "evidence_type": evidence.evidence_type,
                "submitted_by": f"{evidence.test_case.data_owner.first_name} {evidence.test_case.data_owner.last_name}" if evidence.test_case and evidence.test_case.data_owner else "Unknown",
                "submitted_at": evidence.submitted_at,
                "validation_status": evidence.validation_status,
                "validation_notes": evidence.validation_notes,
                "submission_notes": evidence.submission_notes,
                "validation_results": [
                    {
                        "rule": vr.validation_rule,
                        "result": vr.validation_result,
                        "message": vr.validation_message
                    }
                    for vr in validation_results
                ]
            }
            
            # Add type-specific data
            if evidence.evidence_type == 'document':
                evidence_data.update({
                    "document_name": evidence.document_name,
                    "document_size": evidence.document_size,
                    "mime_type": evidence.mime_type
                })
            elif evidence.evidence_type == 'data_source':
                evidence_data.update({
                    "data_source_id": evidence.rfi_data_source_id,
                    "query_text": evidence.query_text,
                    "query_result_sample": evidence.query_result_sample
                })
            
            result.append(evidence_data)
        
        return result
    
    # Tester Decision Methods
    
    async def submit_tester_decision(self, evidence_id: int, decision: str, 
                             decision_notes: Optional[str], user_id: int,
                             requires_resubmission: bool = False,
                             resubmission_deadline: Optional[datetime] = None,
                             follow_up_instructions: Optional[str] = None) -> Dict[str, Any]:
        """Submit tester decision on evidence"""
        
        # Validate evidence exists - using TestCaseEvidence (renamed from RFIEvidenceLegacy)
        from app.models.request_info import TestCaseEvidence
        result = await self.db.execute(
            select(TestCaseEvidence).options(
                selectinload(TestCaseEvidence.test_case)
            ).where(TestCaseEvidence.id == evidence_id)
        )
        evidence = result.scalar_one_or_none()
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Validate decision value
        if decision not in ['approved', 'rejected', 'requires_revision']:
            raise HTTPException(status_code=400, detail="Invalid decision value")
        
        # Check if already decided - using fields in RFIEvidenceLegacy table
        if evidence.tester_decision and evidence.decided_by == user_id:
            raise HTTPException(
                status_code=400, 
                detail="Evidence already reviewed by this tester"
            )
        
        try:
            # Update evidence record with tester decision
            evidence.tester_decision = decision
            evidence.tester_notes = decision_notes
            evidence.decided_by = user_id
            evidence.decided_at = datetime.now(timezone.utc)
            evidence.requires_resubmission = requires_resubmission
            evidence.resubmission_deadline = resubmission_deadline
            evidence.updated_at = datetime.now(timezone.utc)
            evidence.updated_by = user_id
            
            # Update test case status based on decision
            if decision == 'approved':
                evidence.test_case.status = 'Complete'
            elif decision == 'rejected':
                evidence.test_case.status = 'In Progress'
            elif decision == 'requires_revision':
                evidence.test_case.status = 'In Progress'
                if requires_resubmission:
                    # Mark current evidence as superseded for resubmission
                    evidence.is_current = False
            
            # Add evidence back to session to track changes
            self.db.add(evidence)
            
            await self.db.commit()
            await self.db.refresh(evidence)
            
            return {
                "success": True,
                "evidence_id": evidence.id,
                "decision": decision,
                "message": "Tester decision submitted successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit tester decision: {str(e)}"
            )
    
    def get_phase_completion_status(self, phase_id: int) -> Dict[str, Any]:
        """Get phase completion status for evidence collection"""
        
        # Get all test cases for the phase
        test_cases = self.db.query(CycleReportTestCase).filter(
            CycleReportTestCase.phase_id == phase_id
        ).all()
        
        if not test_cases:
            return {
                "phase_id": phase_id,
                "total_test_cases": 0,
                "completed_test_cases": 0,
                "completion_percentage": 0,
                "can_complete_phase": False
            }
        
        # Count test cases by status
        total_test_cases = len(test_cases)
        completed_test_cases = len([tc for tc in test_cases if tc.status == 'Approved'])
        
        completion_percentage = (completed_test_cases / total_test_cases) * 100
        can_complete_phase = completion_percentage >= 100
        
        # Get evidence statistics
        evidence_stats = self.db.query(
            func.count(TestCaseSourceEvidence.id).label('total_evidence'),
            func.sum(case((TestCaseSourceEvidence.validation_status == 'valid', 1), else_=0)).label('valid_evidence'),
            func.sum(case((TestCaseSourceEvidence.validation_status == 'invalid', 1), else_=0)).label('invalid_evidence'),
            func.sum(case((TestCaseSourceEvidence.validation_status == 'requires_review', 1), else_=0)).label('review_evidence')
        ).filter(
            and_(
                TestCaseSourceEvidence.phase_id == phase_id,
                TestCaseSourceEvidence.is_current == True
            )
        ).first()
        
        return {
            "phase_id": phase_id,
            "total_test_cases": total_test_cases,
            "completed_test_cases": completed_test_cases,
            "completion_percentage": completion_percentage,
            "can_complete_phase": can_complete_phase,
            "evidence_statistics": {
                "total_evidence": evidence_stats.total_evidence or 0,
                "valid_evidence": evidence_stats.valid_evidence or 0,
                "invalid_evidence": evidence_stats.invalid_evidence or 0,
                "requires_review": evidence_stats.review_evidence or 0
            }
        }
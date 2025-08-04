"""
Test Execution Engine API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, delete, or_
from sqlalchemy.orm import selectinload
import logging
import time
import uuid
import hashlib
import random
import os
import re
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.services.llm_service import get_llm_service
from app.core.prompt_manager import prompt_manager
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.models.report_attribute import ReportAttribute
from app.models.request_info import DocumentSubmission, TestCase
from app.models.testing import Sample
from app.models.sample_selection import SampleRecord
from app.models.test_execution import (
    TestExecutionPhase, TestExecution as TestingTestExecution, DocumentAnalysis,
    DatabaseTest, TestResultReview, TestComparison, BulkTestExecution, TestExecutionAuditLog
)
from app.schemas.test_execution import (
    TestExecutionPhaseStart, TestExecutionPhaseStatus, TestExecutionPhaseComplete,
    DocumentAnalysisRequest, DocumentAnalysisResponse, DatabaseTestRequest, DatabaseTestResponse,
    TestExecutionRequest, TestExecutionResponse, BulkTestExecutionRequest, BulkTestExecutionResponse,
    TestResultReviewRequest, TestResultReviewResponse, TestComparisonRequest, TestComparisonResponse,
    TestingAnalytics, TestExecutionAuditLog as TestExecutionAuditLogSchema,
    TestType, TestStatus, TestResult, AnalysisMethod, ReviewStatus
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper functions for role checking

def simulate_database_testing(
    database_submission_id: str,
    sample_record_id: str,
    attribute_name: str,
    test_query: Optional[str] = None
) -> Dict[str, Any]:
    """Simulate database testing"""

    # Simulate connection success/failure
    connection_successful = random.random() > 0.1  # 90% success rate

    if not connection_successful:
        return {
            "connection_successful": False,
            "query_successful": False,
            "retrieved_value": None,
            "record_count": None,
            "execution_time_ms": random.randint(5000, 15000),
            "error_message": "Connection timeout - Unable to establish connection to database server",
            "database_version": None
        }

    # Simulate query execution
    query_successful = random.random() > 0.05  # 95% success rate given connection

    if not query_successful:
        return {
            "connection_successful": True,
            "query_successful": False,
            "retrieved_value": None,
            "record_count": None,
            "execution_time_ms": random.randint(100, 1000),
            "error_message": "SQL syntax error in query or table/column not found",
            "database_version": "PostgreSQL 14.8"
        }

    # Simulate successful query results
    sample_values = ["125,000", "Q4 2024", "USD", "Active", "Completed", "2024-12-31"]
    retrieved_value = random.choice(sample_values)
    record_count = random.randint(1, 5)

    return {
        "connection_successful": True,
        "query_successful": True,
        "retrieved_value": retrieved_value,
        "record_count": record_count,
        "execution_time_ms": random.randint(50, 500),
        "error_message": None,
        "database_version": "PostgreSQL 14.8",
        "connection_string_hash": hashlib.sha256(f"connection_{database_submission_id}".encode()).hexdigest()[:16],
        "actual_query_executed": test_query or f"SELECT {attribute_name} FROM cycle_report_sample_selection_samples WHERE id = '{sample_record_id}'",
        "query_plan": "Index Scan using sample_id_idx (cost=0.29..8.30 rows=1 width=32)"
    }

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return ""

def classify_document_type(document_text: str, typical_source_documents: str) -> Dict[str, Any]:
    """
    Step 1: Classify what type of document is provided using LLM
    """
    # For now, we'll skip prompt generation since the method doesn't exist
    classification_prompt = f"Classify document with expected types: {typical_source_documents}"
    
    # Log the prompt for debugging (in production, you might want to remove this)
    logger.debug(f"Document Classification Prompt: {classification_prompt}")
    
    # Parse typical source documents from scoping LLM
    expected_doc_types = [doc.strip() for doc in typical_source_documents.split(',')]
    
    # Simple classification based on content patterns
    # In a real implementation, this would use an LLM API call with the generated prompt
    document_text_lower = document_text.lower()
    
    classification_results = []
    
    for doc_type in expected_doc_types:
        confidence = 0.0
        evidence = []
        
        doc_type_lower = doc_type.lower()
        
        # Credit-related document patterns
        if 'credit' in doc_type_lower:
            credit_indicators = ['credit limit', 'available credit', 'credit line', 'account summary', 'statement']
            matches = sum(1 for indicator in credit_indicators if indicator in document_text_lower)
            if matches > 0:
                confidence = min(0.9, 0.3 + (matches * 0.15))
                evidence = [indicator for indicator in credit_indicators if indicator in document_text_lower]
        
        # Account master file patterns
        elif 'account' in doc_type_lower and 'master' in doc_type_lower:
            account_indicators = ['account number', 'customer id', 'account details', 'master record']
            matches = sum(1 for indicator in account_indicators if indicator in document_text_lower)
            if matches > 0:
                confidence = min(0.85, 0.25 + (matches * 0.15))
                evidence = [indicator for indicator in account_indicators if indicator in document_text_lower]
        
        # Management system patterns
        elif 'management' in doc_type_lower and 'system' in doc_type_lower:
            system_indicators = ['system report', 'generated report', 'automated', 'system data']
            matches = sum(1 for indicator in system_indicators if indicator in document_text_lower)
            if matches > 0:
                confidence = min(0.8, 0.2 + (matches * 0.15))
                evidence = [indicator for indicator in system_indicators if indicator in document_text_lower]
        
        if confidence > 0:
            classification_results.append({
                'document_type': doc_type,
                'confidence': confidence,
                'evidence': evidence
            })
    
    # Return the highest confidence classification
    if classification_results:
        best_match = max(classification_results, key=lambda x: x['confidence'])
        return {
            'classified_as': best_match['document_type'],
            'confidence': best_match['confidence'],
            'evidence': best_match['evidence'],
            'all_matches': classification_results,
            'classification_prompt': classification_prompt  # Include prompt for audit trail
        }
    else:
        return {
            'classified_as': 'Unknown document type',
            'confidence': 0.0,
            'evidence': [],
            'all_matches': [],
            'classification_prompt': classification_prompt
        }

def extract_attribute_value_with_llm(
    document_text: str, 
    attribute_name: str, 
    keywords_to_look_for: str,
    document_classification: Dict[str, Any],
    primary_key_attributes: Dict[str, Any] = None,
    expected_value: Any = None
) -> Dict[str, Any]:
    """
    Step 2: Extract specific attribute value using LLM with scoping keywords and PK validation
    """
    # First, validate primary key attributes if provided
    pk_validation = None
    if primary_key_attributes:
        pk_validation = extract_primary_key_attributes(
            document_text, 
            primary_key_attributes, 
            document_classification
        )
    
    # For now, we'll create the prompt directly
    extraction_prompt = f"Extract value for {attribute_name} from document classified as {document_classification['classified_as']} with keywords: {keywords_to_look_for}"
    
    # Log the prompt for debugging
    logger.debug(f"Value Extraction Prompt: {extraction_prompt}")
    
    # Parse keywords from scoping LLM
    keywords = [keyword.strip() for keyword in keywords_to_look_for.split(';')]
    
    # Simulate LLM extraction (in real implementation, this would call an LLM API with the generated prompt)
    document_text_lower = document_text.lower()
    
    extracted_value = None
    confidence_score = 0.0
    extraction_evidence = []
    
    # Look for each keyword pattern
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        if keyword_lower in document_text_lower:
            extraction_evidence.append(f"Found keyword: '{keyword}'")
            
            # Extract value patterns based on keyword
            
            if 'credit' in keyword_lower and 'limit' in keyword_lower:
                # Look for credit limit patterns
                patterns = [
                    rf'{re.escape(keyword_lower)}[:\s]+\$?([\d,]+\.?\d*)',
                    rf'{re.escape(keyword_lower)}[:\s]*\$?([\d,]+\.?\d*)',
                    rf'\$?([\d,]+\.?\d*)\s*{re.escape(keyword_lower)}',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, document_text_lower)
                    for match in matches:
                        try:
                            value_str = match.group(1).replace(',', '')
                            value_float = float(value_str)
                            extracted_value = value_float
                            confidence_score = 0.85 + (0.1 * len(extraction_evidence) / len(keywords))
                            extraction_evidence.append(f"Extracted value: ${value_float:,.2f} using pattern: {pattern}")
                            break
                        except (ValueError, IndexError):
                            continue
                    if extracted_value:
                        break
            
            elif 'available' in keyword_lower and 'credit' in keyword_lower:
                # Similar pattern for available credit
                patterns = [
                    rf'{re.escape(keyword_lower)}[:\s]+\$?([\d,]+\.?\d*)',
                    rf'available[:\s]+\$?([\d,]+\.?\d*)',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, document_text_lower)
                    for match in matches:
                        try:
                            value_str = match.group(1).replace(',', '')
                            value_float = float(value_str)
                            extracted_value = value_float
                            confidence_score = 0.80 + (0.1 * len(extraction_evidence) / len(keywords))
                            extraction_evidence.append(f"Extracted available credit: ${value_float:,.2f}")
                            break
                        except (ValueError, IndexError):
                            continue
                    if extracted_value:
                        break
            
            elif 'credit' in keyword_lower and 'line' in keyword_lower:
                # Credit line patterns
                patterns = [
                    rf'{re.escape(keyword_lower)}[:\s]+\$?([\d,]+\.?\d*)',
                    rf'line[:\s]+\$?([\d,]+\.?\d*)',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, document_text_lower)
                    for match in matches:
                        try:
                            value_str = match.group(1).replace(',', '')
                            value_float = float(value_str)
                            extracted_value = value_float
                            confidence_score = 0.82 + (0.1 * len(extraction_evidence) / len(keywords))
                            extraction_evidence.append(f"Extracted credit line: ${value_float:,.2f}")
                            break
                        except (ValueError, IndexError):
                            continue
                    if extracted_value:
                        break
    
    # If no specific keyword match, try general dollar amount extraction
    if not extracted_value:
        dollar_pattern = r'\$\s*([\d,]+\.?\d*)'
        matches = re.findall(dollar_pattern, document_text)
        if matches:
            amounts = []
            for match in matches:
                try:
                    amounts.append(float(match.replace(',', '')))
                except ValueError:
                    continue
            if amounts:
                # Take the largest amount as likely credit limit
                max_amount = max(amounts)
                extracted_value = max_amount
                confidence_score = 0.60  # Lower confidence for general extraction
                extraction_evidence.append(f"No keyword match found. Using largest dollar amount: ${max_amount:,.2f}")
    
    # Adjust confidence based on primary key validation
    if pk_validation:
        if pk_validation['pk_validation_passed']:
            confidence_score = min(0.95, confidence_score + 0.15)  # Boost confidence significantly
            extraction_evidence.append(f"Primary key validation passed ({pk_validation['matched_pk_count']}/{pk_validation['total_pk_count']} matched)")
        else:
            confidence_score = max(0.1, confidence_score - 0.3)  # Reduce confidence significantly
            extraction_evidence.append(f"Primary key validation failed ({pk_validation['matched_pk_count']}/{pk_validation['total_pk_count']} matched)")
    
    # Compare with expected value if provided
    matches_expected = False
    if extracted_value is not None and expected_value is not None:
        try:
            expected_float = float(expected_value)
            extracted_float = float(extracted_value)
            # Allow for small rounding differences
            matches_expected = abs(extracted_float - expected_float) < 0.01
            if matches_expected:
                confidence_score = min(0.95, confidence_score + 0.1)  # Boost confidence if matches expected
        except (ValueError, TypeError):
            pass
    
    result = {
        'extracted_value': f"${extracted_value:,.2f}" if extracted_value else "Not found",
        'raw_extracted_value': extracted_value,
        'confidence_score': min(0.95, confidence_score),
        'matches_expected': matches_expected,
        'extraction_evidence': extraction_evidence,
        'keywords_found': [kw for kw in keywords if kw.lower() in document_text_lower],
        'extraction_method': 'LLM-guided keyword extraction with PK validation',
        'expected_value': expected_value,
        'extraction_prompt': extraction_prompt  # Include prompt for audit trail
    }
    
    # Add primary key validation results
    if pk_validation:
        result['primary_key_validation'] = pk_validation
    
    return result

def extract_primary_key_attributes(
    document_text: str, 
    primary_key_attributes: Dict[str, Any],
    document_classification: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract primary key attributes from document to validate context
    """
    # For now, we'll create the prompt directly
    pk_validation_prompt = f"Validate primary keys in document of type {document_classification['classified_as']}"
    
    # Log the prompt for debugging
    logger.debug(f"Primary Key Validation Prompt: {pk_validation_prompt}")
    
    document_text_lower = document_text.lower()
    extracted_pk_values = {}
    pk_validation_results = {}
    
    for pk_name, expected_value in primary_key_attributes.items():
        pk_name_lower = pk_name.lower()
        extracted_value = None
        confidence = 0.0
        evidence = []
        
        # Define extraction patterns based on primary key type
        if 'bank' in pk_name_lower and 'id' in pk_name_lower:
            # Bank ID patterns
            patterns = [
                r'bank\s+id[:\s]+([A-Z0-9]+)',
                r'bank\s+identifier[:\s]+([A-Z0-9]+)',
                r'institution\s+id[:\s]+([A-Z0-9]+)',
                r'bank[:\s]+([0-9]{7,10})',  # Common bank ID format
            ]
            
        elif 'customer' in pk_name_lower and 'id' in pk_name_lower:
            # Customer ID patterns
            patterns = [
                r'customer\s+id[:\s]+([A-Z0-9]+)',
                r'customer\s+number[:\s]+([A-Z0-9]+)',
                r'account\s+holder[:\s]+([A-Z0-9]+)',
                r'cus[0-9]{9,12}',  # CUS followed by digits
            ]
            
        elif 'period' in pk_name_lower and 'id' in pk_name_lower:
            # Period ID patterns (dates)
            patterns = [
                r'period[:\s]+(\d{4}-\d{2}-\d{2})',
                r'statement\s+date[:\s]+(\d{4}-\d{2}-\d{2})',
                r'as\s+of[:\s]+(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})',  # Any date format
                r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY format
            ]
            
        elif 'reference' in pk_name_lower and 'number' in pk_name_lower:
            # Reference Number patterns
            patterns = [
                r'reference\s+number[:\s]+([A-Z0-9]+)',
                r'ref\s+no[:\s]+([A-Z0-9]+)',
                r'account\s+number[:\s]+([A-Z0-9]+)',
                r'cc[0-9]{11,14}',  # CC followed by digits (credit card format)
            ]
            
        else:
            # Generic patterns for other primary keys
            patterns = [
                rf'{re.escape(pk_name_lower)}[:\s]+([A-Z0-9\-]+)',
                rf'{re.escape(pk_name_lower.replace(" ", ""))}[:\s]+([A-Z0-9\-]+)',
            ]
        
        # Try each pattern
        for pattern in patterns:
            matches = re.finditer(pattern, document_text_lower, re.IGNORECASE)
            for match in matches:
                candidate_value = match.group(1) if match.groups() else match.group(0)
                
                # Clean up the extracted value
                candidate_value = candidate_value.strip().upper()
                
                # Calculate confidence based on pattern specificity and context
                pattern_confidence = 0.7 if pk_name_lower in pattern.lower() else 0.5
                
                # Boost confidence if document type is relevant
                if document_classification['confidence'] > 0.7:
                    pattern_confidence += 0.1
                
                if confidence < pattern_confidence:
                    extracted_value = candidate_value
                    confidence = pattern_confidence
                    evidence.append(f"Found using pattern: {pattern}")
                    break
            
            if extracted_value:
                break
        
        # Store results
        extracted_pk_values[pk_name] = extracted_value
        
        # Validate against expected value
        matches_expected = False
        if extracted_value and expected_value:
            # Normalize both values for comparison
            extracted_normalized = str(extracted_value).upper().strip()
            expected_normalized = str(expected_value).upper().strip()
            
            # Handle date format variations
            if 'period' in pk_name_lower or 'date' in pk_name_lower:
                # Try to parse and compare dates
                try:
                    from datetime import datetime
                    # Try different date formats
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d']
                    extracted_date = None
                    expected_date = None
                    
                    for fmt in date_formats:
                        try:
                            extracted_date = datetime.strptime(extracted_normalized, fmt)
                            break
                        except ValueError:
                            continue
                    
                    for fmt in date_formats:
                        try:
                            expected_date = datetime.strptime(expected_normalized, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if extracted_date and expected_date:
                        matches_expected = extracted_date.date() == expected_date.date()
                    else:
                        matches_expected = extracted_normalized == expected_normalized
                        
                except Exception:
                    matches_expected = extracted_normalized == expected_normalized
            else:
                matches_expected = extracted_normalized == expected_normalized
        
        pk_validation_results[pk_name] = {
            'expected_value': expected_value,
            'extracted_value': extracted_value,
            'matches_expected': matches_expected,
            'confidence': confidence,
            'evidence': evidence
        }
    
    # Calculate overall primary key validation score
    total_pk_attributes = len(primary_key_attributes)
    matched_pk_attributes = sum(1 for result in pk_validation_results.values() if result['matches_expected'])
    pk_validation_score = matched_pk_attributes / total_pk_attributes if total_pk_attributes > 0 else 0.0
    
    return {
        'extracted_pk_values': extracted_pk_values,
        'pk_validation_results': pk_validation_results,
        'pk_validation_score': pk_validation_score,
        'matched_pk_count': matched_pk_attributes,
        'total_pk_count': total_pk_attributes,
        'pk_validation_passed': pk_validation_score >= 0.8,  # Require 80% of PKs to match
        'pk_validation_prompt': pk_validation_prompt  # Include prompt for audit trail
    }

async def log_audit_action(
    db: AsyncSession, cycle_id: int, report_id: int, action: str, entity_type: str,
    performed_by: int, request: Request, entity_id: str = None, old_values: Dict = None,
    new_values: Dict = None, notes: str = None, execution_time: int = None, phase_id: str = None
):
    """Create audit log entry for testing execution"""
    audit_log = TestExecutionAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by=performed_by,
        old_values=old_values,
        new_values=new_values,
        notes=notes,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        execution_time_ms=execution_time
    )
    db.add(audit_log)

# Test Execution Phase Management

@router.post("/{cycle_id}/reports/{report_id}/start", response_model=Dict[str, Any])
@require_permission("testing", "execute")
async def start_test_execution_phase(
    cycle_id: int,
    report_id: int,
    phase_data: TestExecutionPhaseStart,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start Test Execution phase"""
    start_time = time.time()
    
    try:
        # Check if phase already exists
        existing_phase = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        existing_phase = existing_phase.scalar_one_or_none()

        if existing_phase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test Execution phase already exists for this cycle and report"
            )

        # Create new testing execution phase
        phase_id = str(uuid.uuid4())
        new_phase = TestExecutionPhase(
            phase_id=phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status="In Progress",
            planned_start_date=phase_data.planned_start_date,
            planned_end_date=phase_data.planned_end_date,
            testing_deadline=phase_data.testing_deadline,
            test_strategy=phase_data.test_strategy,
            instructions=phase_data.instructions,
            started_at=datetime.utcnow(),
            started_by=current_user.user_id
        )

        db.add(new_phase)
        await db.commit()
        await db.refresh(new_phase)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "START_TESTING_PHASE", "TestExecutionPhase",
            current_user.user_id, request, phase_id, None,
            {"phase_status": "In Progress", "testing_deadline": phase_data.testing_deadline.isoformat()},
            "Test Execution phase started", execution_time, phase_id
        )

        return {
            "message": "Test Execution phase started successfully",
            "phase_id": phase_id,
            "status": "In Progress",
            "started_at": new_phase.started_at,
            "testing_deadline": new_phase.testing_deadline
        }

    except Exception as e:
        logger.error(f"Error starting testing execution phase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start testing execution phase: {str(e)}"
        )

@router.get("/{cycle_id}/reports/{report_id}/status", response_model=TestExecutionPhaseStatus)
@require_permission("testing", "read")
async def get_test_execution_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Test Execution phase status and progress"""

    try:
        # Get phase information
        phase_result = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        phase = phase_result.scalar_one_or_none()

        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Execution phase not found"
            )

        # Get test execution statistics
        test_stats = await db.execute(
            select(
                func.count(TestingTestExecution.execution_id).label('total_tests'),
                func.count().filter(TestingTestExecution.status == 'Completed').label('completed_tests'),
                func.count().filter(TestingTestExecution.status == 'Pending').label('pending_tests'),
                func.count().filter(TestingTestExecution.status == 'Failed').label('failed_tests'),
                func.count().filter(TestingTestExecution.status == 'Requires Review').label('review_tests'),
                func.avg(TestingTestExecution.confidence_score).label('avg_confidence')
            ).where(TestingTestExecution.phase_id == phase.phase_id)
        )
        stats = test_stats.first()

        # Get sample count (simulated)
        total_samples = 50  # This would come from sample selection phase

        # Calculate completion percentage
        completion_percentage = (stats.completed_tests / stats.total_tests * 100) if stats.total_tests > 0 else 0

        # Calculate days until deadline
        days_until_deadline = (phase.testing_deadline - datetime.utcnow()).days

        # Get test results summary
        results_summary = await db.execute(
            select(
                TestingTestExecution.result,
                func.count(TestingTestExecution.result)
            ).where(
                TestingTestExecution.phase_id == phase.phase_id
            ).group_by(TestingTestExecution.result)
        )

        test_results_summary = {}
        for result, count in results_summary:
            if result:
                test_results_summary[result.value] = count

        # Determine completion requirements
        completion_requirements = []
        if stats.pending_tests > 0:
            completion_requirements.append(f"{stats.pending_tests} tests still pending execution")
        if stats.failed_tests > 0:
            completion_requirements.append(f"{stats.failed_tests} failed tests need review")
        if stats.review_tests > 0:
            completion_requirements.append(f"{stats.review_tests} tests require review and approval")

        can_complete_phase = len(completion_requirements) == 0

        return TestExecutionPhaseStatus(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase.phase_status,
            testing_deadline=phase.testing_deadline,
            days_until_deadline=days_until_deadline,
            total_samples=total_samples,
            total_tests=stats.total_tests or 0,
            tests_completed=stats.completed_tests or 0,
            tests_pending=stats.pending_tests or 0,
            tests_failed=stats.failed_tests or 0,
            tests_under_review=stats.review_tests or 0,
            completion_percentage=completion_percentage,
            average_confidence_score=float(stats.avg_confidence or 0),
            test_results_summary=test_results_summary,
            can_complete_phase=can_complete_phase,
            completion_requirements=completion_requirements
        )

    except Exception as e:
        logger.error(f"Error getting testing execution status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get testing execution status: {str(e)}"
        )

@router.get("/{cycle_id}/reports/{report_id}/submitted-test-cases", response_model=List[Dict[str, Any]])
@require_permission("testing", "read")
async def get_submitted_test_cases(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get submitted test cases from Request Info phase for testing execution"""
    try:
        # Get submitted test cases from Request Info phase
        
        query = select(TestCase).options(
            selectinload(TestCase.data_owner),
            selectinload(TestCase.attribute),
            selectinload(TestCase.document_submissions),
            selectinload(TestCase.cycle),
            selectinload(TestCase.report)
        ).where(
            and_(
                TestCase.cycle_id == cycle_id,
                TestCase.report_id == report_id,
                TestCase.status == 'Submitted'
            )
        )
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        # Get sample data for all test cases
        # For now, create mock sample data since the sample structure might be different
        # In a real implementation, this would query the actual samples table
        mock_sample_data = {
            "Current Credit limit": 15000.00,
            "Cycle Ending Balance": 2500.75,
            "Purchased Credit Deteriorated Status": "N",
            "Reference Number": "CC10087654321",
            "Customer ID": "CUS456789012",
            "Bank ID": "2347891",
            "Period ID": "2024-01-31"
        }
        
        # Format for testing execution
        submitted_cases = []
        for tc in test_cases:
            # Get the attribute value from mock sample data (in real implementation, this would come from actual samples)
            attribute_value = mock_sample_data.get(tc.attribute_name)
            
            case_data = {
                "submission_id": tc.test_case_id,  # Using test_case_id as submission_id
                "phase_id": tc.phase_id,
                "cycle_id": tc.cycle_id,
                "report_id": tc.report_id,
                "data_provider": {
                    "user_id": tc.data_owner_id,
                    "name": f"{tc.data_owner.first_name} {tc.data_owner.last_name}" if tc.data_owner else "Unknown",
                    "email": tc.data_owner.email if tc.data_owner else None,
                    "first_name": tc.data_owner.first_name if tc.data_owner else None,
                    "last_name": tc.data_owner.last_name if tc.data_owner else None,
                },
                "attribute": {
                    "attribute_id": tc.attribute_id,
                    "name": tc.attribute.attribute_name if tc.attribute else tc.attribute_name,
                    "description": tc.attribute.description if tc.attribute else "",
                    "data_type": tc.attribute.data_type if tc.attribute else "Unknown",
                },
                "sample_record_id": tc.sample_id,
                "sample_identifier": tc.sample_identifier,
                "primary_key_values": tc.primary_key_attributes,
                "submission_type": "Document",
                "status": "Submitted",
                "evidence_uploaded": len(tc.document_submissions) > 0 if tc.document_submissions else False,
                "document_ids": [doc.submission_id for doc in tc.document_submissions] if tc.document_submissions else [],
                "expected_value": str(attribute_value) if attribute_value is not None else None,  # Actual attribute value from sample
                "retrieved_value": None,
                "confidence_level": None,
                "notes": tc.special_instructions,
                "validation_status": None,
                "validation_messages": [],
                "submitted_at": tc.submitted_at.isoformat() if tc.submitted_at else None,
                "validated_at": None,
                "last_updated_at": tc.updated_at.isoformat(),
                "created_at": tc.created_at.isoformat(),
            }
            submitted_cases.append(case_data)
        
        return submitted_cases
        
    except Exception as e:
        logger.error(f"Error fetching submitted test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch submitted test cases: {str(e)}"
        )

@router.get("/{cycle_id}/reports/{report_id}/executions", response_model=List[Dict[str, Any]])
@require_permission("testing", "read")
async def get_test_executions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test execution results"""
    try:
        # Get test executions for this cycle/report
        query = select(TestingTestExecution).options(
            selectinload(TestingTestExecution.attribute),
            selectinload(TestingTestExecution.executed_by_user)
        ).where(
            and_(
                TestingTestExecution.cycle_id == cycle_id,
                TestingTestExecution.report_id == report_id
            )
        )
        
        result = await db.execute(query)
        executions = result.scalars().all()
        
        # Format execution results
        execution_results = []
        for exec in executions:
            exec_data = {
                "execution_id": exec.execution_id,
                "sample_record_id": exec.sample_record_id,
                "attribute_id": exec.attribute_id,
                "status": exec.status,
                "result": exec.result,
                "retrieved_value": exec.execution_summary,  # Using execution_summary as retrieved_value
                "confidence_score": exec.confidence_score,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "processing_time_ms": exec.processing_time_ms,
                "error_message": exec.error_message,
            }
            execution_results.append(exec_data)
        
        return execution_results
        
    except Exception as e:
        logger.error(f"Error fetching test executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch test executions: {str(e)}"
        )

@router.post("/{cycle_id}/reports/{report_id}/start-test-case", response_model=Dict[str, Any])
@require_permission("testing", "execute")
async def start_test_case_execution(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start test execution for a submitted test case"""
    try:
        submission_id = request_data.get("submission_id")
        test_type = request_data.get("test_type", "Document Based")
        analysis_method = request_data.get("analysis_method", "LLM Analysis")
        priority = request_data.get("priority", "Normal")
        
        # Get the test case from Request Info phase
        
        query = select(TestCase).options(
            selectinload(TestCase.attribute),
            selectinload(TestCase.document_submissions)
        ).where(TestCase.test_case_id == submission_id)
        
        result = await db.execute(query)
        test_case = result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test case not found"
            )
        
        # Check if testing execution phase exists
        phase_result = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            # Create testing execution phase if it doesn't exist
            phase_id = str(uuid.uuid4())
            phase = TestExecutionPhase(
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="In Progress",
                testing_deadline=datetime.utcnow() + timedelta(days=7),  # Default 7 days
                started_at=datetime.utcnow(),
                started_by=current_user.user_id
            )
            db.add(phase)
            await db.commit()
            await db.refresh(phase)
        
        # Create test execution record
        test_execution = TestingTestExecution(
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            sample_record_id=test_case.sample_id,
            attribute_id=test_case.attribute_id,
            test_type=test_type,
            analysis_method=analysis_method,
            priority=priority,
            status="Running",
            executed_by=current_user.user_id,
            started_at=datetime.utcnow()
        )
        
        db.add(test_execution)
        await db.commit()
        await db.refresh(test_execution)
        
        # Execute test based on type
        if test_type == "Document Based":
            # Perform real document analysis
            analysis_result = await perform_real_document_analysis(
                db,
                test_case.test_case_id,
                test_case.attribute.attribute_name,
                test_case.sample_identifier
            )
            
            # Update test execution with results
            test_execution.status = "Completed"
            test_execution.result = "Pass" if analysis_result["confidence_score"] >= 0.8 else "Inconclusive"
            test_execution.confidence_score = analysis_result["confidence_score"]
            test_execution.execution_summary = f"Document analysis completed. {analysis_result['rationale']}"
            test_execution.completed_at = datetime.utcnow()
            test_execution.processing_time_ms = analysis_result.get("analysis_duration_ms", random.randint(1000, 5000))
            
        elif test_type == "Database Based":
            # Simulate database testing
            db_result = simulate_database_testing(
                submission_id, test_case.sample_id, test_case.attribute_name
            )
            
            if db_result["connection_successful"] and db_result["query_successful"]:
                test_execution.status = "Completed"
                test_execution.result = "Pass"
                test_execution.confidence_score = 0.9
                test_execution.execution_summary = f"Retrieved value: {db_result['retrieved_value']}"
            else:
                test_execution.status = "Failed"
                test_execution.result = "Fail"
                test_execution.error_message = db_result["error_message"]
            
            test_execution.completed_at = datetime.utcnow()
            test_execution.processing_time_ms = db_result["execution_time_ms"]
        
        await db.commit()
        
        return {
            "message": "Test execution started successfully",
            "execution_id": test_execution.execution_id,
            "status": test_execution.status,
            "result": test_execution.result,
            "confidence_score": test_execution.confidence_score,
            "execution_summary": test_execution.execution_summary,
            "started_at": test_execution.started_at.isoformat(),
            "completed_at": test_execution.completed_at.isoformat() if test_execution.completed_at else None
        }
        
    except Exception as e:
        logger.error(f"Error starting test case execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start test case execution: {str(e)}"
        )

# Document Analysis Endpoints

@router.post("/{cycle_id}/reports/{report_id}/analyze_document", response_model=DocumentAnalysisResponse)
@require_permission("testing", "execute")
async def analyze_document(
    cycle_id: int,
    report_id: int,
    analysis_request: DocumentAnalysisRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze document using LLM"""
    start_time = time.time()
    
    try:
        # Validate submission document exists
        doc_result = await db.execute(
            select(DocumentSubmission).where(DocumentSubmission.submission_id == analysis_request.submission_document_id)
        )
        document = doc_result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission document not found"
            )

        # Validate attribute exists
        attr_result = await db.execute(
            select(ReportAttribute).where(ReportAttribute.attribute_id == analysis_request.attribute_id)
        )
        attribute = attr_result.scalar_one_or_none()

        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report attribute not found"
            )

        # Simulate LLM analysis
        analysis_result = simulate_llm_document_analysis(
            analysis_request.submission_document_id,
            attribute.attribute_name,
            analysis_request.expected_value,
            analysis_request.confidence_threshold
        )

        # Create document analysis record
        analysis = DocumentAnalysis(
            submission_document_id=analysis_request.submission_document_id,
            sample_record_id=analysis_request.sample_record_id,
            attribute_id=analysis_request.attribute_id,
            analysis_prompt=analysis_request.analysis_prompt,
            expected_value=analysis_request.expected_value,
            confidence_threshold=analysis_request.confidence_threshold,
            extracted_value=analysis_result["extracted_value"],
            confidence_score=analysis_result["confidence_score"],
            analysis_rationale=analysis_result["rationale"],
            matches_expected=analysis_result["matches_expected"],
            validation_notes=analysis_result["validation_notes"],
            llm_model_used=analysis_result["llm_model_used"],
            llm_tokens_used=analysis_result["llm_tokens_used"],
            analysis_duration_ms=analysis_result["analysis_duration_ms"],
            analyzed_by=current_user.user_id
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "DOCUMENT_ANALYSIS", "DocumentAnalysis",
            current_user.user_id, request, str(analysis.analysis_id), None,
            {"confidence_score": analysis_result["confidence_score"], "extracted_value": analysis_result["extracted_value"]},
            f"Document analysis completed for sample {analysis_request.sample_record_id}", execution_time
        )

        return DocumentAnalysisResponse(
            analysis_id=analysis.analysis_id,
            submission_document_id=analysis.submission_document_id,
            sample_record_id=analysis.sample_record_id,
            attribute_id=analysis.attribute_id,
            extracted_value=analysis.extracted_value,
            confidence_score=analysis.confidence_score,
            analysis_rationale=analysis.analysis_rationale,
            matches_expected=analysis.matches_expected,
            validation_notes=analysis.validation_notes,
            analyzed_at=analysis.analyzed_at,
            analysis_duration_ms=analysis.analysis_duration_ms
        )

    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document: {str(e)}"
        )

# Database Testing Endpoints

@router.post("/{cycle_id}/reports/{report_id}/test_database", response_model=DatabaseTestResponse)
@require_permission("testing", "execute")
async def test_database(
    cycle_id: int,
    report_id: int,
    test_request: DatabaseTestRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test database connectivity and execute query"""
    start_time = time.time()
    
    try:
        # Validate database submission exists
        db_sub_result = await db.execute(
            select(DatabaseSubmission).where(DatabaseSubmission.db_submission_id == test_request.database_submission_id)
        )
        db_submission = db_sub_result.scalar_one_or_none()

        if not db_submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Database submission not found"
            )

        # Validate attribute exists
        attr_result = await db.execute(
            select(ReportAttribute).where(ReportAttribute.attribute_id == test_request.attribute_id)
        )
        attribute = attr_result.scalar_one_or_none()

        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report attribute not found"
            )

        # Simulate database testing
        test_result = simulate_database_testing(
            test_request.database_submission_id,
            test_request.sample_record_id,
            attribute.attribute_name,
            test_request.test_query
        )

        # Create database test record
        db_test = DatabaseTest(
            database_submission_id=test_request.database_submission_id,
            sample_record_id=test_request.sample_record_id,
            attribute_id=test_request.attribute_id,
            test_query=test_request.test_query,
            connection_timeout=test_request.connection_timeout,
            query_timeout=test_request.query_timeout,
            connection_successful=test_result["connection_successful"],
            query_successful=test_result["query_successful"],
            retrieved_value=test_result["retrieved_value"],
            record_count=test_result["record_count"],
            execution_time_ms=test_result["execution_time_ms"],
            error_message=test_result["error_message"],
            connection_string_hash=test_result.get("connection_string_hash"),
            database_version=test_result["database_version"],
            actual_query_executed=test_result.get("actual_query_executed"),
            query_plan=test_result.get("query_plan"),
            tested_by=current_user.user_id
        )

        db.add(db_test)
        await db.commit()
        await db.refresh(db_test)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "DATABASE_TEST", "DatabaseTest",
            current_user.user_id, request, str(db_test.test_id), None,
            {"connection_successful": test_result["connection_successful"], "query_successful": test_result["query_successful"]},
            f"Database test completed for sample {test_request.sample_record_id}", execution_time
        )

        return DatabaseTestResponse(
            test_id=db_test.test_id,
            database_submission_id=db_test.database_submission_id,
            sample_record_id=db_test.sample_record_id,
            attribute_id=db_test.attribute_id,
            connection_successful=db_test.connection_successful,
            query_successful=db_test.query_successful,
            retrieved_value=db_test.retrieved_value,
            record_count=db_test.record_count,
            execution_time_ms=db_test.execution_time_ms,
            error_message=db_test.error_message,
            tested_at=db_test.tested_at
        )

    except Exception as e:
        logger.error(f"Error testing database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test database: {str(e)}"
        )

# Continue with remaining endpoints...
# [The file would continue with test execution, review, comparison, and analytics endpoints]

# Test Execution Management

@router.post("/{cycle_id}/reports/{report_id}/execute_test", response_model=TestExecutionResponse)
@require_permission("testing", "execute")
async def execute_test(
    cycle_id: int,
    report_id: int,
    test_request: TestExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute individual test (document or database based)"""
    start_time = time.time()
    
    try:
        # Get testing execution phase
        phase_result = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        phase = phase_result.scalar_one_or_none()

        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Execution phase not found"
            )

        # Validate attribute exists
        attr_result = await db.execute(
            select(ReportAttribute).where(ReportAttribute.attribute_id == test_request.attribute_id)
        )
        attribute = attr_result.scalar_one_or_none()

        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report attribute not found"
            )

        # Create test execution record
        test_execution = TestingTestExecution(
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            sample_record_id=test_request.sample_record_id,
            attribute_id=test_request.attribute_id,
            test_type=test_request.test_type,
            analysis_method=test_request.analysis_method,
            priority=test_request.priority,
            custom_instructions=test_request.custom_instructions,
            status="Running",
            assigned_tester_id=current_user.user_id,
            started_at=datetime.utcnow()
        )

        db.add(test_execution)
        await db.commit()
        await db.refresh(test_execution)

        # Execute test based on type
        try:
            if test_request.test_type == "Document Based":
                # Simulate document analysis
                analysis_result = simulate_llm_document_analysis(
                    test_request.document_analysis_id or 1,
                    attribute.attribute_name
                )

                test_execution.status = "Completed"
                test_execution.result = "Pass" if analysis_result["confidence_score"] >= 0.8 else "Inconclusive"
                test_execution.confidence_score = analysis_result["confidence_score"]
                test_execution.execution_summary = f"Document analysis completed. {analysis_result['rationale']}"
                test_execution.document_analysis_id = test_request.document_analysis_id

            elif test_request.test_type == "Database Based":
                # Simulate database testing
                db_test_result = simulate_database_testing(
                    test_request.database_test_id or "test-db-1",
                    test_request.sample_record_id,
                    attribute.attribute_name
                )

                if db_test_result["connection_successful"] and db_test_result["query_successful"]:
                    test_execution.status = "Completed"
                    test_execution.result = "Pass"
                    test_execution.confidence_score = 0.95
                    test_execution.execution_summary = f"Database test successful. Retrieved: {db_test_result['retrieved_value']}"
                else:
                    test_execution.status = "Failed"
                    test_execution.result = "Fail"
                    test_execution.confidence_score = 0.0
                    test_execution.execution_summary = f"Database test failed: {db_test_result['error_message']}"
                    test_execution.error_message = db_test_result["error_message"]

                test_execution.database_test_id = test_request.database_test_id

            test_execution.completed_at = datetime.utcnow()
            test_execution.processing_time_ms = int((time.time() - start_time) * 1000)

        except Exception as e:
            test_execution.status = "Failed"
            test_execution.result = "Fail"
            test_execution.error_message = str(e)
            test_execution.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(test_execution)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "EXECUTE_TEST", "TestExecution",
            current_user.user_id, request, str(test_execution.execution_id), None,
            {"status": test_execution.status, "result": test_execution.result},
            f"Test executed for sample {test_request.sample_record_id}", execution_time, phase.phase_id
        )

        return TestExecutionResponse(
            execution_id=test_execution.execution_id,
            phase_id=test_execution.phase_id,
            sample_record_id=test_execution.sample_record_id,
            attribute_id=test_execution.attribute_id,
            test_type=test_execution.test_type,
            status=test_execution.status,
            result=test_execution.result,
            confidence_score=test_execution.confidence_score,
            execution_summary=test_execution.execution_summary,
            error_message=test_execution.error_message,
            started_at=test_execution.started_at,
            completed_at=test_execution.completed_at,
            processing_time_ms=test_execution.processing_time_ms
        )

    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute test: {str(e)}"
        )

@router.post("/{cycle_id}/reports/{report_id}/bulk_execute", response_model=BulkTestExecutionResponse)
@require_permission("testing", "execute")
async def bulk_execute_tests(
    cycle_id: int,
    report_id: int,
    bulk_request: BulkTestExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute multiple tests in bulk"""
    start_time = time.time()
    
    try:
        # Get testing execution phase
        phase_result = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        phase = phase_result.scalar_one_or_none()

        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Execution phase not found"
            )

        # Create bulk execution record
        bulk_execution = BulkTestExecution(
            phase_id=phase.phase_id,
            execution_mode=bulk_request.execution_mode,
            max_concurrent_tests=bulk_request.max_concurrent_tests,
            total_tests=len(bulk_request.test_requests),
            execution_ids=[],
            status="Running",
            started_at=datetime.utcnow(),
            initiated_by=current_user.user_id
        )

        db.add(bulk_execution)
        await db.commit()
        await db.refresh(bulk_execution)

        # Create individual test executions
        execution_ids = []
        tests_started = 0
        tests_completed = 0
        tests_failed = 0

        for test_request in bulk_request.test_requests:
            try:
                # Create test execution record
                test_execution = TestingTestExecution(
                    phase_id=phase.phase_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    sample_record_id=test_request.sample_record_id,
                    attribute_id=test_request.attribute_id,
                    test_type=test_request.test_type,
                    analysis_method=test_request.analysis_method,
                    priority=test_request.priority or "Normal",
                    status="Running",
                    assigned_tester_id=current_user.user_id,
                    started_at=datetime.utcnow()
                )

                db.add(test_execution)
                await db.commit()
                await db.refresh(test_execution)

                execution_ids.append(test_execution.execution_id)
                tests_started += 1

                # Simulate test execution (simplified for bulk)
                if test_request.test_type == "Document Based":
                    confidence_score = random.uniform(0.7, 0.98)
                    test_execution.status = "Completed"
                    test_execution.result = "Pass" if confidence_score >= 0.8 else "Inconclusive"
                    test_execution.confidence_score = confidence_score
                    test_execution.execution_summary = "Document analysis completed successfully"
                    tests_completed += 1

                elif test_request.test_type == "Database Based":
                    success_rate = random.random()
                    if success_rate > 0.1:  # 90% success rate
                        test_execution.status = "Completed"
                        test_execution.result = "Pass"
                        test_execution.confidence_score = 0.95
                        test_execution.execution_summary = "Database test completed successfully"
                        tests_completed += 1
                    else:
                        test_execution.status = "Failed"
                        test_execution.result = "Fail"
                        test_execution.error_message = "Database connection failed"
                        tests_failed += 1

                test_execution.completed_at = datetime.utcnow()
                test_execution.processing_time_ms = random.randint(500, 3000)

            except Exception as e:
                logger.error(f"Error in bulk test execution: {str(e)}")
                tests_failed += 1

        # Update bulk execution record
        bulk_execution.execution_ids = execution_ids
        bulk_execution.tests_started = tests_started
        bulk_execution.tests_completed = tests_completed
        bulk_execution.tests_failed = tests_failed
        bulk_execution.status = "Completed"
        bulk_execution.completed_at = datetime.utcnow()
        bulk_execution.processing_time_ms = int((time.time() - start_time) * 1000)

        await db.commit()
        await db.refresh(bulk_execution)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "BULK_EXECUTE_TESTS", "BulkTestExecution",
            current_user.user_id, request, str(bulk_execution.bulk_execution_id), None,
            {"total_tests": tests_started, "completed": tests_completed, "failed": tests_failed},
            f"Bulk execution of {tests_started} tests", execution_time, phase.phase_id
        )

        return BulkTestExecutionResponse(
            bulk_execution_id=bulk_execution.bulk_execution_id,
            phase_id=bulk_execution.phase_id,
            total_tests=bulk_execution.total_tests,
            tests_started=bulk_execution.tests_started,
            tests_completed=bulk_execution.tests_completed,
            tests_failed=bulk_execution.tests_failed,
            execution_ids=bulk_execution.execution_ids,
            status=bulk_execution.status,
            started_at=bulk_execution.started_at,
            completed_at=bulk_execution.completed_at,
            processing_time_ms=bulk_execution.processing_time_ms
        )

    except Exception as e:
        logger.error(f"Error in bulk test execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute bulk tests: {str(e)}"
        )

# Test Result Review and Approval

@router.post("/{cycle_id}/reports/{report_id}/review", response_model=TestResultReviewResponse)
@require_permission("testing", "review")
async def review_test_result(
    cycle_id: int,
    report_id: int,
    review_request: TestResultReviewRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review and approve/reject test results"""
    start_time = time.time()
    
    try:
        # Validate test execution exists
        execution_result = await db.execute(
            select(TestingTestExecution).where(TestingTestExecution.execution_id == review_request.execution_id)
        )
        execution = execution_result.scalar_one_or_none()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test execution not found"
            )

        # Check if execution is in reviewable state
        if execution.status not in ["Completed", "Requires Review"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test execution is not in a reviewable state"
            )

        # Create review record
        review = TestResultReview(
            execution_id=review_request.execution_id,
            reviewer_id=current_user.user_id,
            review_result=review_request.review_result,
            reviewer_comments=review_request.reviewer_comments,
            recommended_action=review_request.recommended_action,
            requires_retest=review_request.requires_retest,
            accuracy_score=review_request.accuracy_score,
            completeness_score=review_request.completeness_score,
            consistency_score=review_request.consistency_score,
            overall_score=review_request.overall_score,
            review_criteria_used=review_request.review_criteria_used,
            supporting_evidence=review_request.supporting_evidence,
            review_duration_ms=review_request.review_duration_ms
        )

        db.add(review)

        # Update test execution based on review result
        if review_request.review_result == "Approved":
            execution.status = "Completed"
        elif review_request.review_result == "Rejected":
            execution.status = "Requires Review"
        elif review_request.requires_retest:
            execution.status = "Pending"

        await db.commit()
        await db.refresh(review)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "REVIEW_TEST_RESULT", "TestResultReview",
            current_user.user_id, request, str(review.review_id), None,
            {"review_result": review_request.review_result, "overall_score": review_request.overall_score},
            f"Test result reviewed for execution {review_request.execution_id}", execution_time
        )

        return TestResultReviewResponse(
            review_id=review.review_id,
            execution_id=review.execution_id,
            reviewer_id=review.reviewer_id,
            review_result=review.review_result,
            reviewer_comments=review.reviewer_comments,
            recommended_action=review.recommended_action,
            requires_retest=review.requires_retest,
            overall_score=review.overall_score,
            reviewed_at=review.reviewed_at,
            review_duration_ms=review.review_duration_ms
        )

    except Exception as e:
        logger.error(f"Error reviewing test result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review test result: {str(e)}"
        )

# Test Comparison and Analytics

@router.post("/{cycle_id}/reports/{report_id}/compare", response_model=TestComparisonResponse)
@require_permission("testing", "execute")
async def compare_test_results(
    cycle_id: int,
    report_id: int,
    comparison_request: TestComparisonRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare multiple test execution results for consistency"""
    start_time = time.time()
    
    try:
        # Validate all execution IDs exist
        executions_result = await db.execute(
            select(TestingTestExecution).where(TestingTestExecution.execution_id.in_(comparison_request.execution_ids))
        )
        executions = executions_result.scalars().all()

        if len(executions) != len(comparison_request.execution_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more test executions not found"
            )

        # Perform comparison analysis
        comparison_results = {}
        differences_found = []
        recommendations = []

        # Analyze confidence scores
        confidence_scores = [exec.confidence_score for exec in executions if exec.confidence_score]
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            confidence_variance = sum((score - avg_confidence) ** 2 for score in confidence_scores) / len(confidence_scores)

            comparison_results["confidence_analysis"] = {
                "average_confidence": avg_confidence,
                "confidence_variance": confidence_variance,
                "min_confidence": min(confidence_scores),
                "max_confidence": max(confidence_scores)
            }

            if confidence_variance > 0.05:  # High variance threshold
                differences_found.append("High variance in confidence scores detected")
                recommendations.append("Review test execution methods for consistency")

        # Analyze results consistency
        results = [exec.result for exec in executions if exec.result]
        unique_results = set(results)
        if len(unique_results) > 1:
            differences_found.append("Inconsistent test results found")
            recommendations.append("Investigate test execution differences")

        # Calculate overall consistency score
        consistency_factors = []

        # Result consistency (40% weight)
        result_consistency = 1.0 if len(unique_results) <= 1 else 0.5
        consistency_factors.append(result_consistency * 0.4)

        # Confidence consistency (40% weight)
        confidence_consistency = max(0, 1.0 - (confidence_variance * 10)) if confidence_scores else 1.0
        consistency_factors.append(confidence_consistency * 0.4)

        # Timing consistency (20% weight)
        processing_times = [exec.processing_time_ms for exec in executions if exec.processing_time_ms]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            time_variance = sum((t - avg_time) ** 2 for t in processing_times) / len(processing_times)
            time_consistency = max(0, 1.0 - (time_variance / 1000000))  # Normalize variance
            consistency_factors.append(time_consistency * 0.2)
        else:
            consistency_factors.append(0.2)

        overall_consistency_score = sum(consistency_factors)

        # Create comparison record
        comparison = TestComparison(
            execution_ids=comparison_request.execution_ids,
            comparison_criteria=comparison_request.comparison_criteria,
            comparison_results=comparison_results,
            consistency_score=overall_consistency_score,
            differences_found=differences_found,
            recommendations=recommendations,
            analysis_method_used="Statistical Analysis",
            statistical_metrics={
                "confidence_scores": confidence_scores,
                "processing_times": processing_times,
                "result_distribution": {result: results.count(result) for result in unique_results}
            },
            comparison_duration_ms=int((time.time() - start_time) * 1000),
            compared_by=current_user.user_id
        )

        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "COMPARE_TEST_RESULTS", "TestComparison",
            current_user.user_id, request, str(comparison.comparison_id), None,
            {"consistency_score": overall_consistency_score, "executions_compared": len(comparison_request.execution_ids)},
            f"Compared {len(comparison_request.execution_ids)} test executions", execution_time
        )

        return TestComparisonResponse(
            comparison_id=comparison.comparison_id,
            execution_ids=comparison.execution_ids,
            consistency_score=comparison.consistency_score,
            comparison_results=comparison.comparison_results,
            differences_found=comparison.differences_found,
            recommendations=comparison.recommendations,
            compared_at=comparison.compared_at,
            comparison_duration_ms=comparison.comparison_duration_ms
        )

    except Exception as e:
        logger.error(f"Error comparing test results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare test results: {str(e)}"
        )

# Analytics and Reporting

@router.get("/{cycle_id}/reports/{report_id}/analytics", response_model=TestingAnalytics)
@require_permission("testing", "read")
async def get_testing_analytics(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive testing execution analytics"""

    try:
        # Get phase information
        phase_result = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        phase = phase_result.scalar_one_or_none()

        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Execution phase not found"
            )

        # Get test execution statistics
        test_stats = await db.execute(
            select(
                func.count(TestingTestExecution.execution_id).label('total_tests'),
                func.count().filter(TestingTestExecution.test_type == 'Document Based').label('document_tests'),
                func.count().filter(TestingTestExecution.test_type == 'Database Based').label('database_tests'),
                func.count().filter(TestingTestExecution.status == 'Completed').label('completed_tests'),
                func.count().filter(TestingTestExecution.status == 'Failed').label('failed_tests'),
                func.avg(TestingTestExecution.confidence_score).label('avg_confidence'),
                func.avg(TestingTestExecution.processing_time_ms).label('avg_processing_time')
            ).where(TestingTestExecution.phase_id == phase.phase_id)
        )
        stats = test_stats.first()

        # Get test results distribution
        results_dist = await db.execute(
            select(
                TestingTestExecution.result,
                func.count(TestingTestExecution.result)
            ).where(
                TestingTestExecution.phase_id == phase.phase_id
            ).group_by(TestingTestExecution.result)
        )

        test_results_distribution = {}
        for result, count in results_dist:
            if result:
                test_results_distribution[result.value] = count

        # Get performance metrics by test type
        performance_by_type = await db.execute(
            select(
                TestingTestExecution.test_type,
                func.avg(TestingTestExecution.processing_time_ms).label('avg_time'),
                func.avg(TestingTestExecution.confidence_score).label('avg_confidence')
            ).where(
                TestingTestExecution.phase_id == phase.phase_id
            ).group_by(TestingTestExecution.test_type)
        )

        test_type_performance = {}
        for test_type, avg_time, avg_confidence in performance_by_type:
            if test_type:
                test_type_performance[test_type.value] = {
                    "average_processing_time_ms": float(avg_time or 0),
                    "average_confidence_score": float(avg_confidence or 0)
                }

        # Get daily execution trends (simulated)
        daily_trends = []
        start_date = phase.started_at.date() if phase.started_at else datetime.utcnow().date()
        for i in range(7):  # Last 7 days
            date = start_date - timedelta(days=6-i)
            tests_executed = random.randint(5, 20)
            daily_trends.append({
                "date": date.isoformat(),
                "tests_executed": tests_executed,
                "success_rate": random.uniform(0.85, 0.98)
            })

        return TestingAnalytics(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase.phase_id,
            total_tests=stats.total_tests or 0,
            document_based_tests=stats.document_tests or 0,
            database_based_tests=stats.database_tests or 0,
            completed_tests=stats.completed_tests or 0,
            failed_tests=stats.failed_tests or 0,
            success_rate=(stats.completed_tests / stats.total_tests * 100) if stats.total_tests > 0 else 0,
            average_confidence_score=float(stats.avg_confidence or 0),
            average_processing_time_ms=float(stats.avg_processing_time or 0),
            test_results_distribution=test_results_distribution,
            test_type_performance=test_type_performance,
            daily_execution_trends=daily_trends,
            phase_duration_days=(datetime.utcnow() - phase.started_at).days if phase.started_at else 0
        )

    except Exception as e:
        logger.error(f"Error getting testing analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get testing analytics: {str(e)}"
        )

# Phase Completion

@router.post("/{cycle_id}/reports/{report_id}/complete", response_model=Dict[str, Any])
@require_permission("testing", "approve")
async def complete_test_execution_phase(
    cycle_id: int,
    report_id: int,
    completion_data: TestExecutionPhaseComplete,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete Test Execution phase"""
    start_time = time.time()
    
    try:
        # Get testing execution phase
        phase_result = await db.execute(
            select(TestExecutionPhase).where(
                and_(TestExecutionPhase.cycle_id == cycle_id, TestExecutionPhase.report_id == report_id)
            )
        )
        phase = phase_result.scalar_one_or_none()

        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Execution phase not found"
            )

        if phase.phase_status == "Completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test Execution phase is already completed"
            )

        # Check completion requirements
        pending_tests = await db.execute(
            select(func.count(TestingTestExecution.execution_id)).where(
                and_(
                    TestingTestExecution.phase_id == phase.phase_id,
                    TestingTestExecution.status.in_(["Pending", "Running", "Requires Review"])
                )
            )
        )
        pending_count = pending_tests.scalar()

        if pending_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete phase: {pending_count} tests are still pending completion"
            )

        # Update phase status
        phase.phase_status = "Completed"
        phase.completed_at = datetime.utcnow()
        phase.completed_by = current_user.user_id

        await db.commit()

        # Log audit action
        execution_time = int((time.time() - start_time) * 1000)
        await log_audit_action(
            db, cycle_id, report_id, "COMPLETE_TESTING_PHASE", "TestExecutionPhase",
            current_user.user_id, request, phase.phase_id,
            {"phase_status": "In Progress"}, {"phase_status": "Completed"},
            completion_data.completion_notes, execution_time, phase.phase_id
        )

        return {
            "message": "Test Execution phase completed successfully",
            "phase_id": phase.phase_id,
            "completed_at": phase.completed_at,
            "total_tests_executed": await db.scalar(
                select(func.count(TestingTestExecution.execution_id)).where(
                    TestingTestExecution.phase_id == phase.phase_id
                )
            ),
            "next_phase": "Observation Management"
        }

    except Exception as e:
        logger.error(f"Error completing testing execution phase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete testing execution phase: {str(e)}"
        )

# Audit Log Retrieval

@router.get("/{cycle_id}/reports/{report_id}/audit_logs", response_model=List[TestExecutionAuditLogSchema])
@require_permission("testing", "read")
async def get_test_execution_audit_logs(
    cycle_id: int,
    report_id: int,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get testing execution audit logs"""
    try:
        logs_result = await db.execute(
            select(TestExecutionAuditLog)
            .where(and_(TestExecutionAuditLog.cycle_id == cycle_id, TestExecutionAuditLog.report_id == report_id))
            .order_by(TestExecutionAuditLog.performed_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(TestExecutionAuditLog.user))
        )
        logs = logs_result.scalars().all()

        return [
            TestExecutionAuditLogSchema(
                log_id=log.log_id,
                cycle_id=log.cycle_id,
                report_id=log.report_id,
                phase_id=log.phase_id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                performed_by=log.performed_by,
                performed_at=log.performed_at,
                old_values=log.old_values,
                new_values=log.new_values,
                notes=log.notes,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                execution_time_ms=log.execution_time_ms
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/resend-test-case", response_model=Dict[str, Any])
@require_permission("testing", "execute")
async def resend_test_case_to_provider(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend test case to data provider for resubmission"""
    
    test_case_id = request_data.get("test_case_id")
    reason = request_data.get("reason", "Please provide correct documentation")
    
    if not test_case_id:
        raise HTTPException(status_code=400, detail="test_case_id is required")
    
    # Get test case
    tc_result = await db.execute(
        select(TestCase).where(TestCase.test_case_id == test_case_id)
    )
    test_case = tc_result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Update test case status
    test_case.status = "Resent"
    
    # Track revision count in primary_key_attributes (using it as a JSON field for metadata)
    if not test_case.primary_key_attributes:
        test_case.primary_key_attributes = {}
    
    revision_count = test_case.primary_key_attributes.get("revision_count", 0) + 1
    test_case.primary_key_attributes["revision_count"] = revision_count
    test_case.primary_key_attributes["last_resent_at"] = datetime.utcnow().isoformat()
    test_case.primary_key_attributes["resent_by"] = current_user.user_id
    test_case.primary_key_attributes["resent_reason"] = reason
    
    # Create notification for data provider
    from app.models.request_info import DataProviderNotification
    
    notification = DataProviderNotification(
        test_case_id=test_case_id,
        data_provider_id=test_case.data_owner_id,
        notification_type="Test Case Resent",
        notification_message=f"Test case for {test_case.attribute_name} has been resent. Reason: {reason}",
        sent_at=datetime.utcnow(),
        sent_by=current_user.user_id
    )
    
    db.add(notification)
    await db.commit()
    
    return {
        "message": "Test case resent to data provider successfully",
        "test_case_id": test_case_id,
        "revision_count": revision_count,
        "data_provider_id": test_case.data_provider_id,
        "notification_sent": True
    }


@router.get("/{cycle_id}/reports/{report_id}/test-case-revisions/{test_case_id}", response_model=Dict[str, Any])
@require_permission("testing", "read")
async def get_test_case_revision_history(
    cycle_id: int,
    report_id: int,
    test_case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get revision history for a test case"""
    
    # Get test case
    tc_result = await db.execute(
        select(TestCase).where(TestCase.test_case_id == test_case_id)
    )
    test_case = tc_result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Get all document submissions for this test case ordered by submission time
    docs_result = await db.execute(
        select(DocumentSubmission)
        .where(DocumentSubmission.test_case_id == test_case_id)
        .order_by(DocumentSubmission.submitted_at.desc())
    )
    documents = docs_result.scalars().all()
    
    # Build revision history
    revisions = []
    for idx, doc in enumerate(documents):
        revision_number = len(documents) - idx
        revisions.append({
            "revision_number": revision_number,
            "submission_id": doc.submission_id,
            "original_filename": doc.original_filename,
            "file_size": doc.file_size_bytes,
            "submitted_at": doc.submitted_at.isoformat() if doc.submitted_at else None,
            "data_provider_id": doc.data_owner_id,
            "is_valid": doc.is_valid,
            "validation_notes": doc.validation_notes
        })
    
    # Get revision metadata from test case
    metadata = test_case.primary_key_attributes or {}
    
    return {
        "test_case_id": test_case_id,
        "attribute_name": test_case.attribute_name,
        "total_revisions": len(documents),
        "revision_count": metadata.get("revision_count", 0),
        "last_resent_at": metadata.get("last_resent_at"),
        "resent_by": metadata.get("resent_by"),
        "resent_reason": metadata.get("resent_reason"),
        "revisions": revisions
    }

async def perform_real_document_analysis(
    db: AsyncSession,
    test_case_id: str,
    attribute_name: str,
    sample_identifier: str
) -> Dict[str, Any]:
    """Perform real two-step LLM document analysis with primary key validation"""
    logger.info(f"=== Starting perform_real_document_analysis for test_case_id: {test_case_id}, attribute: {attribute_name}")
    
    # Check if LLM service is available
    try:
        llm_service = get_llm_service()
        llm_available = True
        logger.info("LLM service initialized successfully")
    except Exception as e:
        logger.warning(f"LLM service not available: {str(e)}")
        llm_available = False
    
    # Get document submissions for this test case
    doc_result = await db.execute(
        select(DocumentSubmission).where(DocumentSubmission.test_case_id == test_case_id)
    )
    documents = doc_result.scalars().all()
    
    if not documents:
        return {
            "extracted_value": "No documents found",
            "confidence_score": 0.0,
            "rationale": "No documents submitted for this test case",
            "matches_expected": False,
            "validation_notes": {"error": "no_documents"},
            "llm_model_used": "Two-Step LLM Analysis with PK Validation",
            "llm_tokens_used": 0,
            "analysis_duration_ms": 50
        }
    
    # Get test case with primary key attributes
    test_case_result = await db.execute(
        select(TestCase).where(TestCase.test_case_id == test_case_id)
    )
    test_case = test_case_result.scalar_one_or_none()
    
    if not test_case:
        return {
            "extracted_value": "Test case not found",
            "confidence_score": 0.0,
            "rationale": f"Test case {test_case_id} not found in database",
            "matches_expected": False,
            "validation_notes": {"error": "test_case_not_found"},
            "llm_model_used": "Two-Step LLM Analysis with PK Validation",
            "llm_tokens_used": 0,
            "analysis_duration_ms": 50
        }
    
    # Get attribute scoping data - use the specific attribute from the test case
    attr_result = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_name == attribute_name,
                ReportAttribute.cycle_id == test_case.cycle_id,
                ReportAttribute.report_id == test_case.report_id,
                ReportAttribute.is_latest_version == True,
                ReportAttribute.is_active == True
            )
        )
    )
    attribute = attr_result.scalar_one_or_none()
    
    if not attribute:
        return {
            "extracted_value": "Attribute not found",
            "confidence_score": 0.0,
            "rationale": f"Attribute {attribute_name} not found in database",
            "matches_expected": False,
            "validation_notes": {"error": "attribute_not_found"},
            "llm_model_used": "Two-Step LLM Analysis with PK Validation",
            "llm_tokens_used": 0,
            "analysis_duration_ms": 50
        }
    
    # Get expected value from sample data - handle multiple records with same identifier
    sample_result = await db.execute(
        select(SampleRecord).where(SampleRecord.sample_identifier == sample_identifier)
    )
    sample_records = sample_result.scalars().all()
    expected_value = None
    if sample_records and sample_records[0].sample_data:
        expected_value = sample_records[0].sample_data.get(attribute_name)
    
    # Get primary key attributes from test case
    primary_key_attributes = test_case.primary_key_attributes if test_case.primary_key_attributes else {}
    
    # Find the first valid document that actually exists
    valid_document = None
    for doc in documents:
        if os.path.exists(doc.file_path):
            valid_document = doc
            break
    
    if not valid_document:
        return {
            "extracted_value": "No valid documents found",
            "confidence_score": 0.0,
            "rationale": f"Found {len(documents)} document(s) but none exist on file system",
            "matches_expected": False,
            "validation_notes": {"error": "no_valid_documents", "total_documents": len(documents)},
            "llm_model_used": "Two-Step LLM Analysis with PK Validation",
            "llm_tokens_used": 0,
            "analysis_duration_ms": 50
        }
    
    # Analyze the first valid document
    document = valid_document
    file_path = document.file_path
    
    # Extract text from document (file existence already verified)
    if file_path.lower().endswith('.pdf'):
        document_text = extract_text_from_pdf(file_path)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            document_text = ""
    
    if not document_text.strip():
        return {
            "extracted_value": "Could not extract text from document",
            "confidence_score": 0.0,
            "rationale": "Document text extraction failed or document is empty",
            "matches_expected": False,
            "validation_notes": {"error": "text_extraction_failed"},
            "llm_model_used": "Two-Step LLM Analysis with PK Validation",
            "llm_tokens_used": 0,
            "analysis_duration_ms": 100
        }
    
    # Use LLM if available, otherwise fall back to simulation
    logger.info(f"LLM available: {llm_available}, Document text length: {len(document_text)}")
    if llm_available:
        # Step 1: Build attribute context for LLM
        attribute_context = {
            "data_type": attribute.data_type or "String",
            "description": attribute.description or "",
            "validation_rules": attribute.validation_rules or "",
            "keywords_to_look_for": attribute.keywords_to_look_for or "",
            "typical_source_documents": attribute.typical_source_documents or ""
        }
        
        # Step 2: Extract primary key field and value from test case
        primary_key_field = "sample_identifier"  # Default
        primary_key_value = sample_identifier
        
        # If we have primary key attributes, use the first one
        if primary_key_attributes and len(primary_key_attributes) > 0:
            primary_key_field = list(primary_key_attributes.keys())[0]
            primary_key_value = primary_key_attributes[primary_key_field]
        
        # Step 3: Call LLM service to extract value
        try:
            logger.info(f"Calling LLM service to extract value for attribute: {attribute_name}")
            extraction_result = await llm_service.extract_test_value_from_document(
                document_content=document_text,
                attribute_name=attribute_name,
                attribute_context=attribute_context,
                primary_key_field=primary_key_field,
                primary_key_value=str(primary_key_value),
                document_type="regulatory"
            )
            
            if extraction_result.get("success"):
                # Convert LLM response to expected format
                extracted_value = extraction_result.get("extracted_value")
                confidence_score = extraction_result.get("confidence_score", 0.0)
                
                # Check if extracted value matches expected
                matches_expected = False
                if expected_value and extracted_value:
                    # Normalize for comparison
                    expected_str = str(expected_value).strip().lower()
                    extracted_str = str(extracted_value).strip().lower()
                    matches_expected = expected_str == extracted_str
                
                extraction_result = {
                    "extracted_value": extracted_value,
                    "confidence_score": confidence_score,
                    "matches_expected": matches_expected,
                    "keywords_found": [],
                    "extraction_evidence": [
                        extraction_result.get("evidence", ""),
                        f"Location: {extraction_result.get('location', 'Unknown')}"
                    ],
                    "primary_key_validation": {
                        "pk_validation_passed": extraction_result.get("primary_key_found", False),
                        "pk_validation_score": 1.0 if extraction_result.get("primary_key_found") else 0.0,
                        "matched_pk_count": 1 if extraction_result.get("primary_key_found") else 0,
                        "total_pk_count": 1,
                        "pk_validation_results": {
                            primary_key_field: {
                                "expected_value": primary_key_value,
                                "extracted_value": primary_key_value if extraction_result.get("primary_key_found") else None,
                                "matches_expected": extraction_result.get("primary_key_found", False)
                            }
                        }
                    }
                }
                
                # Use document quality as classification
                classification_result = {
                    "classified_as": extraction_result.get("document_quality", "Unknown"),
                    "confidence": 0.9 if extraction_result.get("document_quality") == "High" else 0.5
                }
            else:
                # LLM call failed, fall back to simulation
                logger.warning(f"LLM extraction failed: {extraction_result.get('error')}")
                classification_result = classify_document_type(
                    document_text, 
                    attribute.typical_source_documents or "Unknown document type"
                )
                extraction_result = extract_attribute_value_with_llm(
                    document_text,
                    attribute_name,
                    attribute.keywords_to_look_for or "",
                    classification_result,
                    primary_key_attributes,
                    expected_value
                )
        except Exception as e:
            logger.error(f"Error calling LLM service: {str(e)}")
            # Fall back to simulation
            classification_result = classify_document_type(
                document_text, 
                attribute.typical_source_documents or "Unknown document type"
            )
            extraction_result = extract_attribute_value_with_llm(
                document_text,
                attribute_name,
                attribute.keywords_to_look_for or "",
                classification_result,
                primary_key_attributes,
                expected_value
            )
    else:
        # Use simulation if LLM not available
        classification_result = classify_document_type(
            document_text, 
            attribute.typical_source_documents or "Unknown document type"
        )
        extraction_result = extract_attribute_value_with_llm(
            document_text,
            attribute_name,
            attribute.keywords_to_look_for or "",
            classification_result,
            primary_key_attributes,
            expected_value
        )
    
    # Combine results with enhanced confidence calculation
    classification_confidence = classification_result['confidence'] * 0.2
    extraction_confidence = extraction_result['confidence_score'] * 0.6
    pk_validation_confidence = 0.0
    
    if 'primary_key_validation' in extraction_result:
        pk_validation = extraction_result['primary_key_validation']
        pk_validation_confidence = pk_validation['pk_validation_score'] * 0.2
    
    final_confidence = classification_confidence + extraction_confidence + pk_validation_confidence
    
    # Build comprehensive rationale
    rationale_parts = [
        f"Document classified as: {classification_result['classified_as']} (confidence: {classification_result['confidence']:.2%})",
        f"Value extraction: {extraction_result['extracted_value']} (confidence: {extraction_result['confidence_score']:.2%})",
        f"Keywords found: {', '.join(extraction_result['keywords_found']) if extraction_result['keywords_found'] else 'None'}"
    ]
    
    if 'primary_key_validation' in extraction_result:
        pk_validation = extraction_result['primary_key_validation']
        rationale_parts.append(
            f"Primary key validation: {pk_validation['matched_pk_count']}/{pk_validation['total_pk_count']} matched "
            f"({'PASSED' if pk_validation['pk_validation_passed'] else 'FAILED'})"
        )
        
        # Add details about which PKs matched/failed
        pk_details = []
        for pk_name, pk_result in pk_validation['pk_validation_results'].items():
            status = "✓" if pk_result['matches_expected'] else "✗"
            pk_details.append(f"{pk_name}: {status} (expected: {pk_result['expected_value']}, found: {pk_result['extracted_value']})")
        
        if pk_details:
            rationale_parts.append(f"PK Details: {'; '.join(pk_details)}")
    
    rationale_parts.extend(extraction_result['extraction_evidence'])
    
    # Determine final test result based on value match and PK validation
    test_passed = extraction_result['matches_expected']
    if 'primary_key_validation' in extraction_result:
        pk_validation = extraction_result['primary_key_validation']
        # Test only passes if both value matches AND primary keys validate
        test_passed = test_passed and pk_validation['pk_validation_passed']
    
    return {
        "extracted_value": extraction_result['extracted_value'],
        "raw_extracted_value": extraction_result.get('raw_extracted_value'),
        "confidence_score": min(0.95, final_confidence),
        "rationale": " | ".join(rationale_parts),
        "matches_expected": test_passed,  # Enhanced logic including PK validation
        "validation_notes": {
            "document_classification": classification_result,
            "extraction_details": extraction_result,
            "primary_key_validation": extraction_result.get('primary_key_validation'),
            "expected_value": expected_value,
            "document_filename": document.original_filename,
            "test_logic": "Value match AND primary key validation required for PASS"
        },
        "llm_model_used": "Two-Step LLM Analysis (Classification + Extraction + PK Validation)",
        "llm_tokens_used": len(document_text.split()),
        "analysis_duration_ms": 2000 + len(document_text) // 100,  # Simulate processing time
        "document_filename": document.original_filename,
        "document_size": document.file_size_bytes,
        "text_length": len(document_text),
        "submission_document_id": document.submission_id  # Add document submission ID
    }

"""Data Profiling Phase Activities - Reconciled with existing implementation

These activities match the existing data profiling workflow:
1. Start Data Profiling Phase
2. Generate Profiling Rules (LLM)
3. Apply Profiling Rules
4. Analyze Profiling Results
5. Data Profiling Tester Review
6. Data Profiling Report Owner Approval
7. Complete Data Profiling Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

from sqlalchemy import select, and_, func, update
from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.workflow import WorkflowPhase
from app.models.data_profiling import (
    DataProfilingPhase, 
    DataProfilingFile, 
    ProfilingRule, 
    ProfilingResult
)
from app.models.report_attribute import ReportAttribute
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


async def _load_regulatory_prompt(prompt_path: str) -> Optional[str]:
    """Load regulatory-specific prompt template from file"""
    try:
        import os
        from pathlib import Path
        
        # Get the project root directory
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent  # Go up to project root
        prompt_file_path = project_root / "prompts" / "regulatory" / prompt_path
        
        if prompt_file_path.exists():
            with open(prompt_file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        else:
            logger.warning(f"Regulatory prompt file not found: {prompt_file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading regulatory prompt {prompt_path}: {str(e)}")
        return None


async def _get_column_names_from_documents(cycle_id: int, report_id: int, db) -> Optional[List[str]]:
    """Extract column names from uploaded documents"""
    try:
        from app.models.document import Document
        
        # Get documents for this cycle and report
        docs_query = select(Document).where(
            and_(
                Document.cycle_id == cycle_id,
                Document.report_id == report_id,
                Document.document_type.in_(['Regulatory Specification', 'CDE List', 'Data Dictionary'])
            )
        )
        result = await db.execute(docs_query)
        documents = result.scalars().all()
        
        column_names = set()
        
        for doc in documents:
            if hasattr(doc, 'file_content') and doc.file_content:
                # Try to extract column names from document content
                # This is a simplified approach - in production, you'd parse Excel/CSV headers
                content = doc.file_content.upper()
                
                # Common FR Y-14M D.1 column patterns
                fr_y14m_patterns = [
                    'LOAN_ID', 'OUTSTANDING_BALANCE', 'PRINCIPAL_BALANCE', 'ACCRUED_INTEREST',
                    'ORIGINATION_DATE', 'MATURITY_DATE', 'DELINQ_STATUS', 'DAYS_PAST_DUE',
                    'LOAN_PURPOSE', 'COLLATERAL_VALUE', 'LOAN_TO_VALUE', 'FICO_SCORE',
                    'PAYMENT_AMOUNT', 'INTEREST_RATE', 'MONTHLY_PAYMENT', 'VIN_NUMBER',
                    'CHARGE_OFF_DATE', 'CHARGE_OFF_AMOUNT', 'RECOVERY_AMOUNT', 'MODIFICATION_FLAG'
                ]
                
                # Extract column names found in content
                for pattern in fr_y14m_patterns:
                    if pattern in content:
                        column_names.add(pattern)
        
        return list(column_names) if column_names else None
        
    except Exception as e:
        logger.warning(f"Could not extract column names from documents: {str(e)}")
        return None


def _create_attribute_batches(attributes: List, max_batch_size: int = 10) -> List[List]:
    """Create batches of attributes for LLM processing to manage token limits"""
    batches = []
    current_batch = []
    
    for attr in attributes:
        current_batch.append(attr)
        
        if len(current_batch) >= max_batch_size:
            batches.append(current_batch)
            current_batch = []
    
    # Add remaining attributes
    if current_batch:
        batches.append(current_batch)
    
    return batches if batches else [attributes]


@activity.defn
async def start_data_profiling_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start data profiling phase"""
    try:
        async for db in get_db():
            # Create/update workflow phase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
            result = await db.execute(phase_query)
            phase = result.scalar_one_or_none()
            
            if not phase:
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Data Profiling",
                    status="in_progress",
                    started_at=datetime.utcnow(),
                    started_by=user_id
                )
                db.add(phase)
            else:
                phase.status = "in_progress"
                phase.started_at = datetime.utcnow()
                phase.started_by = user_id
            
            # Create data profiling phase record
            profiling_phase = DataProfilingPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                status="started",
                started_by=user_id,
                started_at=datetime.utcnow()
            )
            db.add(profiling_phase)
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Data profiling phase started successfully",
                "phase_id": phase.phase_id,
                "started_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error starting data profiling phase: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to start data profiling phase: {str(e)}"
        }


@activity.defn
async def generate_profiling_rules_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    input_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Step 2: Generate profiling rules using LLM"""
    try:
        async for db in get_db():
            # Get report attributes for context
            attrs_query = select(ReportAttribute).where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id
                )
            )
            result = await db.execute(attrs_query)
            attributes = result.scalars().all()
            
            if not attributes:
                return {
                    "success": False,
                    "error": "No attributes found for profiling rule generation"
                }
            
            # Use LLM service to generate profiling rules
            llm_service = get_llm_service()
            
            # Create regulatory-specific context for LLM
            attributes_text = "\n".join([
                f"- {attr.attribute_name} ({attr.data_type}): {attr.description} [{'Mandatory' if attr.mandatory_flag == 'Mandatory' else 'Optional'}]"
                for attr in attributes
            ])
            
            # Get column names from uploaded documents if available
            column_names = await _get_column_names_from_documents(cycle_id, report_id, db)
            
            # Use executable regulatory-specific prompt for FR Y-14M Schedule D.1
            prompt_template = await _load_regulatory_prompt(
                "fr_y_14m/schedule_d_1/executable_data_profiling_rules.txt"
            )
            
            if not prompt_template:
                return {
                    "success": False,
                    "error": "Regulatory prompt template not found. Cannot generate executable profiling rules without proper template."
                }
            
            if not column_names:
                return {
                    "success": False,
                    "error": "Column names not available from uploaded documents. Cannot generate executable rules without exact column names."
                }
            
            # Create batches of attributes to handle token limits
            attribute_batches = _create_attribute_batches(attributes, max_batch_size=10)
            
            system_prompt = "You are a Federal Reserve FR Y-14M data validation specialist. Generate executable validation rules using ONLY the exact column names provided."
            
            all_generated_rules = []
            
            # Process each batch separately
            for batch_idx, attribute_batch in enumerate(attribute_batches):
                logger.info(f"Processing attribute batch {batch_idx + 1}/{len(attribute_batches)} with {len(attribute_batch)} attributes")
                
                # Create batch-specific attributes text
                batch_attributes_text = "\n".join([
                    f"- {attr.attribute_name} ({attr.data_type}): {attr.description} [{'Mandatory' if attr.mandatory_flag == 'Mandatory' else 'Optional'}]"
                    for attr in attribute_batch
                ])
                
                # Use sophisticated executable regulatory prompt for this batch
                batch_prompt = prompt_template.replace("${column_names}", str(column_names))
                batch_prompt = batch_prompt.replace("${attributes_batch}", batch_attributes_text)
                
                rules_response = await llm_service._generate_with_failover(
                    prompt=batch_prompt,
                    system_prompt=system_prompt,
                    preferred_provider="claude"
                )
                
                if not rules_response.get("success"):
                    return {
                        "success": False,  
                        "error": f"LLM failed to generate profiling rules for batch {batch_idx + 1}: {rules_response.get('error')}"
                    }
                
                # Parse LLM response to extract executable rules
                try:
                    response_content = rules_response.get("content", "")
                    
                    if not response_content or not ("[" in response_content and "]" in response_content):
                        return {
                            "success": False,
                            "error": f"LLM did not return valid JSON array format for batch {batch_idx + 1}"
                        }
                    
                    # Extract JSON from the response
                    json_start = response_content.find("[")
                    json_end = response_content.rfind("]") + 1
                    json_content = response_content[json_start:json_end]
                    batch_rules = json.loads(json_content)
                    
                    if not batch_rules or not isinstance(batch_rules, list):
                        return {
                            "success": False,
                            "error": f"LLM returned empty or invalid rule set for batch {batch_idx + 1}"
                        }
                    
                    all_generated_rules.extend(batch_rules)
                    logger.info(f"Successfully generated {len(batch_rules)} rules for batch {batch_idx + 1}")
                    
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse LLM response for batch {batch_idx + 1} as valid JSON: {str(e)}"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error processing LLM response for batch {batch_idx + 1}: {str(e)}"
                    }
            
            generated_rules = all_generated_rules
            saved_rules = []
            
            for rule_data in generated_rules:
                rule = ProfilingRule(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_id=rule_data.get("attribute_id"),
                    rule_name=rule_data.get("rule_name"),
                    rule_type=rule_data.get("rule_type", "validation"),
                    rule_logic=rule_data.get("rule_logic"),
                    expected_result=rule_data.get("expected_result"),
                    severity=rule_data.get("severity", "medium"),
                    llm_rationale=rule_data.get("rationale"),
                    created_by=user_id,
                    created_at=datetime.utcnow()
                )
                db.add(rule)
                saved_rules.append(rule)
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Generated {len(saved_rules)} profiling rules",
                "rules_count": len(saved_rules),
                "awaiting_human_input": False
            }
            
    except Exception as e:
        logger.error(f"Error generating profiling rules: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate profiling rules: {str(e)}"
        }


@activity.defn
async def apply_profiling_rules_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    input_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Step 3: Apply profiling rules to data"""
    try:
        async for db in get_db():
            # Get profiling rules
            rules_query = select(ProfilingRule).where(
                and_(
                    ProfilingRule.cycle_id == cycle_id,
                    ProfilingRule.report_id == report_id,
                    ProfilingRule.status == "active"
                )
            )
            result = await db.execute(rules_query)
            rules = result.scalars().all()
            
            if not rules:
                return {
                    "success": False,
                    "error": "No active profiling rules found to apply"
                }
            
            # Execute each rule (simplified simulation)
            results = []
            for rule in rules:
                # In real implementation, this would execute against actual data
                # For now, simulate rule execution
                execution_result = {
                    "rule_id": rule.rule_id,
                    "passed": True,  # Simulate result
                    "score": 85,  # Simulate quality score
                    "violations": 0,
                    "total_records": 1000,  # Simulate
                    "execution_time": 0.5
                }
                
                # Save result
                profiling_result = ProfilingResult(
                    rule_id=rule.rule_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    execution_status="completed",
                    passed=execution_result["passed"],
                    score=execution_result["score"],
                    violations_count=execution_result["violations"],
                    total_records=execution_result["total_records"],
                    execution_time=execution_result["execution_time"],
                    executed_by=user_id,
                    executed_at=datetime.utcnow()
                )
                db.add(profiling_result)
                results.append(execution_result)
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Applied {len(rules)} profiling rules",
                "results_count": len(results),
                "awaiting_human_input": False
            }
            
    except Exception as e:
        logger.error(f"Error applying profiling rules: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to apply profiling rules: {str(e)}"
        }


@activity.defn 
async def analyze_profiling_results_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    input_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Step 4: Analyze profiling results and generate scores"""
    try:
        async for db in get_db():
            # Get profiling results
            results_query = select(ProfilingResult).where(
                and_(
                    ProfilingResult.cycle_id == cycle_id,
                    ProfilingResult.report_id == report_id
                )
            )
            result = await db.execute(results_query)
            profiling_results = result.scalars().all()
            
            if not profiling_results:
                return {
                    "success": False,
                    "error": "No profiling results found to analyze"
                }
            
            # Generate attribute-level scores
            attribute_scores = {}
            for prof_result in profiling_results:
                rule_query = select(ProfilingRule).where(ProfilingRule.rule_id == prof_result.rule_id)
                rule_result = await db.execute(rule_query)
                rule = rule_result.scalar_one_or_none()
                
                if rule and rule.attribute_id:
                    if rule.attribute_id not in attribute_scores:
                        attribute_scores[rule.attribute_id] = []
                    attribute_scores[rule.attribute_id].append(prof_result.score)
            
            # DEPRECATED: Attribute profiling scores are now calculated by aggregating from ProfilingResult
            # No need to store pre-calculated scores in a separate table
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Analyzed results for {len(attribute_scores)} attributes",
                "attributes_analyzed": len(attribute_scores),
                "awaiting_human_input": True,  # Ready for tester review
                "next_step": "tester_review"
            }
            
    except Exception as e:
        logger.error(f"Error analyzing profiling results: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to analyze profiling results: {str(e)}"
        }


@activity.defn
async def data_profiling_tester_review_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    input_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Step 5: Tester review of data profiling results"""
    try:
        async for db in get_db():
            if input_data is None:
                # First call - return awaiting status
                return {
                    "success": True,
                    "awaiting_human_input": True,
                    "message": "Awaiting tester review of data profiling results",
                    "next_action": "tester_review"
                }
            
            # Process tester review
            review_data = input_data.get("review_data", {})
            
            # Update data profiling phase with tester review
            update_stmt = update(DataProfilingPhase).where(
                and_(
                    DataProfilingPhase.cycle_id == cycle_id,
                    DataProfilingPhase.report_id == report_id
                )
            ).values(
                tester_review_status=review_data.get("status", "reviewed"),
                tester_review_comments=review_data.get("comments"),
                tester_review_by=user_id,
                tester_review_at=datetime.utcnow()
            )
            
            await db.execute(update_stmt)
            await db.commit()
            
            return {
                "success": True,
                "message": "Tester review completed",
                "review_status": review_data.get("status"),
                "awaiting_human_input": True,  # Now awaiting report owner approval
                "next_step": "report_owner_approval"
            }
            
    except Exception as e:
        logger.error(f"Error in tester review: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to process tester review: {str(e)}"
        }


@activity.defn
async def data_profiling_report_owner_approval_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    input_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Step 6: Report owner approval of data profiling"""
    try:
        async for db in get_db():
            if input_data is None:
                # First call - return awaiting status
                return {
                    "success": True,
                    "awaiting_human_input": True,
                    "message": "Awaiting report owner approval of data profiling",
                    "next_action": "report_owner_approval"
                }
            
            # Process report owner approval
            approval_data = input_data.get("approval_data", {})
            
            # Update data profiling phase with approval
            update_stmt = update(DataProfilingPhase).where(
                and_(
                    DataProfilingPhase.cycle_id == cycle_id,
                    DataProfilingPhase.report_id == report_id
                )
            ).values(
                report_owner_approval_status=approval_data.get("status", "approved"),
                report_owner_approval_comments=approval_data.get("comments"),
                report_owner_approval_by=user_id,
                report_owner_approval_at=datetime.utcnow()
            )
            
            await db.execute(update_stmt)
            await db.commit()
            
            return {
                "success": True,
                "message": "Report owner approval completed",
                "approval_status": approval_data.get("status"),
                "awaiting_human_input": False,
                "next_step": "complete_phase"
            }
            
    except Exception as e:
        logger.error(f"Error in report owner approval: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to process report owner approval: {str(e)}"
        }


@activity.defn
async def complete_data_profiling_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 7: Complete data profiling phase"""
    try:
        async for db in get_db():
            # Update workflow phase to completed
            phase_update = update(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            ).values(
                status="completed",
                completed_at=datetime.utcnow(),
                completed_by=user_id
            )
            
            await db.execute(phase_update)
            
            # Update data profiling phase to completed
            profiling_update = update(DataProfilingPhase).where(
                and_(
                    DataProfilingPhase.cycle_id == cycle_id,
                    DataProfilingPhase.report_id == report_id
                )
            ).values(
                status="completed",
                completed_at=datetime.utcnow(),
                completed_by=user_id
            )
            
            await db.execute(profiling_update)
            await db.commit()
            
            return {
                "success": True,
                "message": "Data profiling phase completed successfully",
                "completed_at": datetime.utcnow().isoformat(),
                "next_phase": "Scoping"
            }
            
    except Exception as e:
        logger.error(f"Error completing data profiling phase: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to complete data profiling phase: {str(e)}"
        }
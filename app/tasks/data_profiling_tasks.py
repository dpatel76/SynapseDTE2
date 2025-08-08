"""
Data Profiling Background Tasks
Handles long-running data profiling operations without blocking the UI
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.data_profiling_service import DataProfilingService
from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule
from app.models.workflow import WorkflowPhase
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def execute_profiling_job_task(
    self,
    job_id: int,
    bg_job_id: str,
    configuration_id: int,
    user_id: int
):
    """Execute data profiling job with background job manager integration"""
    from app.tasks.execute_profiling_job_task import execute_profiling_job_sync
    execute_profiling_job_sync(job_id, bg_job_id, configuration_id, user_id)


@celery_app.task(bind=True, max_retries=3)
def execute_profiling_rules_task(
    self,
    version_id: str,
    executed_by: int,
    execution_config: Optional[Dict] = None
):
    """
    Execute data profiling rules in background
    This task handles the long-running profiling operations outside of database transactions
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _execute_profiling_rules_async(
                version_id, executed_by, execution_config, self.request.id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Data profiling execution failed: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _execute_profiling_rules_async(
    version_id: str,
    executed_by: int,
    execution_config: Optional[Dict] = None,
    celery_task_id: Optional[str] = None
) -> Dict[str, Any]:
    """Async helper for profiling rule execution"""
    
    # Get background job ID if provided
    bg_job_id = execution_config.get("background_job_id") if execution_config else None
    
    # Import Redis job manager for Celery tasks
    job_manager = None
    if bg_job_id:
        from app.core.redis_job_manager import get_redis_job_manager
        job_manager = get_redis_job_manager()
        job_manager.update_job_progress(
            bg_job_id,
            status="running",
            message="Starting rule execution",
            progress_percentage=0
        )
    
    # Create new database session for this task
    async with AsyncSessionLocal() as db:
        try:
            # Get version and rules
            version_result = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Get all rules for this version
            rules_result = await db.execute(
                select(ProfilingRule)
                .where(ProfilingRule.version_id == version_id)
                .order_by(ProfilingRule.execution_order)
            )
            rules = rules_result.scalars().all()
            
            if not rules:
                raise ValueError("No rules found for execution")
            
            # Get profiling service
            profiling_service = DataProfilingService(db)
            
            # Update version execution metadata (keep status as is - likely APPROVED)
            version.execution_started_at = datetime.utcnow()
            version.executed_by = executed_by
            version.background_job_id = bg_job_id if bg_job_id else celery_task_id
            version.execution_job_id = bg_job_id if bg_job_id else celery_task_id
            await db.commit()
            
            # Execute rules
            execution_results = {}
            summary_stats = {
                "total_rules": len(rules),
                "successful_rules": 0,
                "failed_rules": 0,
                "total_records_processed": 0,
                "total_anomalies_found": 0
            }
            
            for idx, rule in enumerate(rules):
                try:
                    # Update progress
                    if bg_job_id:
                        progress = int((idx / len(rules)) * 100)
                        job_manager.update_job_progress(
                            bg_job_id,
                            current_step=f"Executing rule: {rule.rule_name}",
                            progress_percentage=progress,
                            completed_steps=idx,
                            total_steps=len(rules)
                        )
                    
                    # Execute individual rule
                    result = await profiling_service.execute_rule(
                        rule, 
                        execution_config or {}
                    )
                    
                    execution_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "status": "success",
                        "records_processed": result.get("records_processed", 0),
                        "records_passed": result.get("records_passed", 0),
                        "records_failed": result.get("records_failed", 0),
                        "pass_rate": result.get("pass_rate", 0.0),
                        "execution_time_ms": result.get("execution_time_ms", 0),
                        "quality_scores": result.get("quality_scores", {}),
                        "anomaly_details": result.get("anomaly_details", []),
                        "statistical_summary": result.get("statistical_summary", {})
                    }
                    
                    summary_stats["successful_rules"] += 1
                    summary_stats["total_records_processed"] += result.get("records_processed", 0)
                    summary_stats["total_anomalies_found"] += len(result.get("anomaly_details", []))
                    
                    # Save execution result to database
                    from app.models.data_profiling import ProfilingResult
                    execution_result = ProfilingResult(
                        phase_id=rule.phase_id,
                        rule_id=rule.rule_id,
                        attribute_id=rule.attribute_id,
                        execution_status="success",
                        execution_time_ms=result.get("execution_time_ms", 0),
                        passed_count=result.get("records_passed", 0),
                        failed_count=result.get("records_failed", 0),
                        total_count=result.get("records_processed", 0),
                        pass_rate=result.get("pass_rate", 0.0),
                        result_summary=result.get("quality_scores", {}),
                        failed_records=result.get("anomaly_details", []),
                        result_details=json.dumps({
                            "statistical_summary": result.get("statistical_summary", {}),
                            "version_id": str(version_id),
                            "job_id": bg_job_id or celery_task_id
                        }),
                        quality_impact=result.get("quality_impact", 0.0),
                        severity=rule.severity,
                        created_by_id=executed_by,
                        updated_by_id=executed_by
                    )
                    db.add(execution_result)
                    
                    logger.info(f"Rule {rule.rule_name} executed successfully")
                    
                except Exception as rule_error:
                    execution_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "status": "failed",
                        "error": str(rule_error),
                        "execution_time_ms": 0
                    }
                    
                    # Save failed execution result to database
                    from app.models.data_profiling import ProfilingResult
                    failed_result = ProfilingResult(
                        phase_id=rule.phase_id,
                        rule_id=rule.rule_id,
                        attribute_id=rule.attribute_id,
                        execution_status="failed",
                        execution_time_ms=0,
                        passed_count=0,
                        failed_count=0,
                        total_count=0,
                        pass_rate=0.0,
                        result_summary={},
                        failed_records=[],
                        result_details=json.dumps({
                            "error": str(rule_error),
                            "version_id": str(version_id),
                            "job_id": bg_job_id or celery_task_id
                        }),
                        quality_impact=0.0,
                        severity=rule.severity,
                        created_by_id=executed_by,
                        updated_by_id=executed_by
                    )
                    db.add(failed_result)
                    
                    summary_stats["failed_rules"] += 1
                    logger.error(f"Rule {rule.rule_name} failed: {str(rule_error)}")
            
            # Commit all execution results to database
            await db.commit()
            
            # Update version with results (keep status as APPROVED)
            version.execution_completed_at = datetime.utcnow()
            version.total_records_processed = summary_stats["total_records_processed"]
            # Calculate overall quality score as average pass rate
            if summary_stats["total_rules"] > 0:
                total_pass_rate = sum(
                    result.get("pass_rate", 0) 
                    for result in execution_results.values() 
                    if result.get("status") == "success"
                )
                version.overall_quality_score = (total_pass_rate / summary_stats["successful_rules"] * 100) if summary_stats["successful_rules"] > 0 else 0
            
            await db.commit()
            
            # Complete the background job
            if bg_job_id:
                job_manager.complete_job(
                    bg_job_id,
                    result={
                        "status": "success",
                        "version_id": version_id,
                        "summary": summary_stats,
                        "execution_time_seconds": (
                            version.execution_completed_at - version.execution_started_at
                        ).total_seconds()
                    }
                )
            
            return {
                "status": "success",
                "version_id": version_id,
                "summary": summary_stats,
                "task_id": celery_task_id,
                "execution_time_seconds": (
                    version.execution_completed_at - version.execution_started_at
                ).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error in profiling rule execution: {str(e)}")
            
            # Update version status to failed
            try:
                version_result = await db.execute(
                    select(DataProfilingRuleVersion)
                    .where(DataProfilingRuleVersion.version_id == version_id)
                )
                version = version_result.scalar_one_or_none()
                
                if version:
                    # Keep version status as is, just update execution metadata
                    version.execution_completed_at = datetime.utcnow()
                    await db.commit()
                    
            except Exception as update_error:
                logger.error(f"Failed to update version status: {str(update_error)}")
            
            # Fail the background job
            if bg_job_id:
                job_manager.complete_job(bg_job_id, error=str(e))
            
            raise


@celery_app.task(bind=True, max_retries=3)
def generate_profiling_rules_task(
    self,
    version_id: str,
    phase_id: int,
    attributes: List[Dict[str, Any]],
    data_source_config: Dict[str, Any],
    user_id: int,
    background_job_id: Optional[str] = None
):
    """
    Generate profiling rules using LLM in background
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _generate_profiling_rules_async(
                version_id, phase_id, attributes, data_source_config, user_id, background_job_id, self.request.id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Profiling rule generation failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _generate_profiling_rules_async(
    version_id: str,
    phase_id: int,
    attributes: List[Dict[str, Any]],
    data_source_config: Dict[str, Any],
    user_id: int,
    background_job_id: Optional[str] = None,
    celery_task_id: Optional[str] = None
) -> Dict[str, Any]:
    """Async helper for profiling rule generation"""
    
    # Import Redis job manager for Celery tasks
    job_manager = None
    if background_job_id:
        from app.core.redis_job_manager import get_redis_job_manager
        job_manager = get_redis_job_manager()
        job_manager.update_job_progress(
            background_job_id,
            status="running",
            message="Starting LLM rule generation",
            progress_percentage=0,
            current_step="Initializing"
        )
    
    async with AsyncSessionLocal() as db:
        try:
            # Get LLM service
            from app.services.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            # Get version
            version_result = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Generate rules using LLM
            generated_rules = []
            total_attributes = len(attributes)
            
            for idx, attribute in enumerate(attributes):
                try:
                    # Update progress
                    if background_job_id:
                        progress = int((idx / total_attributes) * 80)  # Reserve 20% for final steps
                        job_manager.update_job_progress(
                            background_job_id,
                            current_step=f"Generating rules for {attribute.get('attribute_name')}",
                            progress_percentage=progress,
                            completed_steps=idx,
                            total_steps=total_attributes
                        )
                    
                    # Generate rules for this attribute
                    # Pass attribute data as attribute_context (what the LLM service expects)
                    llm_result = await llm_service.generate_data_profiling_rules(
                        attribute_context=attribute,  # LLM service expects 'attribute_context' not 'attribute'
                        preferred_provider=data_source_config.get("preferred_provider", "claude")
                    )
                    
                    # Create rule records
                    for rule_data in llm_result.get("rules", []):
                        rule = ProfilingRule(
                            version_id=version_id,
                            phase_id=phase_id,
                            attribute_id=attribute.get("attribute_id"),
                            attribute_name=attribute.get("attribute_name"),
                            rule_name=rule_data.get("name"),
                            rule_type=rule_data.get("type"),
                            rule_description=rule_data.get("description"),
                            rule_code=rule_data.get("code"),
                            rule_parameters=rule_data.get("parameters", {}),
                            llm_provider=llm_result.get("model_used"),
                            llm_rationale=rule_data.get("rationale"),
                            llm_confidence_score=rule_data.get("confidence_score"),
                            regulatory_reference=rule_data.get("regulatory_reference"),
                            execution_order=rule_data.get("execution_order", 0),
                            severity=rule_data.get("severity", "medium"),
                            status="pending",
                            created_by_id=user_id
                        )
                        
                        db.add(rule)
                        generated_rules.append(rule)
                        
                except Exception as attr_error:
                    logger.error(f"Failed to generate rules for attribute {attribute.get('attribute_name')}: {str(attr_error)}")
                    continue
            
            # Commit all rules
            await db.commit()
            
            # Update version summary
            version.total_rules = len(generated_rules)
            version.generation_completed_at = datetime.utcnow()
            version.generation_status = "completed"
            await db.commit()
            
            # Complete the background job
            if background_job_id:
                job_manager.update_job_progress(
                    background_job_id,
                    current_step="Finalizing rule generation",
                    progress_percentage=90
                )
                
                job_manager.complete_job(
                    background_job_id,
                    result={
                        "status": "success",
                        "version_id": version_id,
                        "rules_generated": len(generated_rules),
                        "attributes_processed": len(attributes),
                        "total_attributes": total_attributes
                    }
                )
            
            return {
                "status": "success",
                "version_id": version_id,
                "rules_generated": len(generated_rules),
                "attributes_processed": len(attributes),
                "task_id": celery_task_id
            }
            
        except Exception as e:
            logger.error(f"Error in profiling rule generation: {str(e)}")
            
            # Update version status to indicate generation failed
            try:
                version_result = await db.execute(
                    select(DataProfilingRuleVersion)
                    .where(DataProfilingRuleVersion.version_id == version_id)
                )
                version = version_result.scalar_one_or_none()
                
                if version:
                    version.generation_error = str(e)
                    version.generation_completed_at = datetime.utcnow()
                    version.generation_status = "failed"
                    await db.commit()
                    
            except Exception as update_error:
                logger.error(f"Failed to update version generation status: {str(update_error)}")
            
            # Fail the background job
            if background_job_id:
                job_manager.complete_job(background_job_id, error=str(e))
            
            raise


@celery_app.task(bind=True, max_retries=3)
def validate_profiling_rules_task(
    self,
    version_id: str,
    data_source_config: Dict[str, Any],
    user_id: int
):
    """
    Validate profiling rules against data source
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _validate_profiling_rules_async(
                version_id, data_source_config, user_id, self.request.id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Profiling rule validation failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _validate_profiling_rules_async(
    version_id: str,
    data_source_config: Dict[str, Any],
    user_id: int,
    celery_task_id: Optional[str] = None
) -> Dict[str, Any]:
    """Async helper for profiling rule validation"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get rules for validation
            rules_result = await db.execute(
                select(ProfilingRule)
                .where(ProfilingRule.version_id == version_id)
            )
            rules = rules_result.scalars().all()
            
            if not rules:
                raise ValueError("No rules found for validation")
            
            # Get profiling service
            profiling_service = DataProfilingService(db)
            
            validation_results = {}
            
            for rule in rules:
                try:
                    # Validate rule syntax and execution
                    validation_result = await profiling_service.validate_rule(
                        rule, 
                        data_source_config
                    )
                    
                    validation_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "is_valid": validation_result.get("is_valid", False),
                        "validation_errors": validation_result.get("errors", []),
                        "estimated_execution_time": validation_result.get("estimated_execution_time", 0),
                        "resource_requirements": validation_result.get("resource_requirements", {})
                    }
                    
                except Exception as validation_error:
                    validation_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "is_valid": False,
                        "validation_errors": [str(validation_error)],
                        "estimated_execution_time": 0,
                        "resource_requirements": {}
                    }
            
            # Update version with validation results
            version_result = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if version:
                version.validation_results = validation_results
                version.validation_completed_at = datetime.utcnow()
                await db.commit()
            
            return {
                "status": "success",
                "version_id": version_id,
                "validation_results": validation_results,
                "task_id": celery_task_id
            }
            
        except Exception as e:
            logger.error(f"Error in profiling rule validation: {str(e)}")
            raise
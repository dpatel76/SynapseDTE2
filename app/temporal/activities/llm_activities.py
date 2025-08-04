"""Temporal activities for LLM operations"""

from temporalio import activity
from typing import Dict, Any, List
import logging

from app.services.llm_service import get_llm_service
from app.temporal.shared.types import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def generate_test_attributes_activity(
    regulatory_context: str,
    report_type: str,
    preferred_provider: str = None
) -> ActivityResult:
    """Generate test attributes using LLM"""
    try:
        llm_service = get_llm_service()
        
        result = await llm_service.generate_test_attributes(
            regulatory_context=regulatory_context,
            report_type=report_type,
            preferred_provider=preferred_provider
        )
        
        if result.get("success"):
            return ActivityResult(
                success=True,
                data={
                    "attributes": result.get("attributes", []),
                    "method": result.get("method"),
                    "providers_used": result.get("providers_used", {})
                }
            )
        else:
            return ActivityResult(
                success=False,
                data={},
                error_message=result.get("error", "Failed to generate attributes")
            )
            
    except Exception as e:
        logger.error(f"Error in generate_test_attributes_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def suggest_pde_mappings_activity(
    attributes: List[Dict[str, Any]],
    data_sources: List[Dict[str, Any]],
    report_context: Dict[str, Any]
) -> ActivityResult:
    """Generate PDE mapping suggestions using LLM with regulation-specific prompts"""
    try:
        llm_service = get_llm_service()
        
        result = await llm_service.suggest_pde_mappings(
            attributes=attributes,
            data_sources=data_sources,
            report_context=report_context
        )
        
        return ActivityResult(
            success=True,
            data={
                "mapping_suggestions": result,
                "mapped_count": len(result),
                "total_attributes": len(attributes)
            }
        )
            
    except Exception as e:
        logger.error(f"Error in suggest_pde_mappings_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn 
async def apply_pde_mappings_activity(
    cycle_id: int,
    report_id: int,
    mapping_suggestions: List[Dict[str, Any]]
) -> ActivityResult:
    """Apply PDE mapping suggestions to database"""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.report_attribute import ReportAttribute
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select, and_
        
        async with AsyncSessionLocal() as db:
            mapped_count = 0
            
            for suggestion in mapping_suggestions:
                attr_id = suggestion.get('attribute_id')
                if not attr_id:
                    continue
                    
                # Get the attribute
                attribute_query = select(ReportAttribute).join(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.cycle_id == cycle_id,
                        ReportAttribute.id == attr_id
                    )
                )
                
                attribute_result = await db.execute(attribute_query)
                attribute = attribute_result.scalar_one_or_none()
                
                if attribute and not (attribute.source_table and attribute.source_column):
                    # Apply the mapping
                    attribute.source_table = suggestion.get('table_name')
                    attribute.source_column = suggestion.get('column_name')
                    attribute.data_source_name = suggestion.get('data_source_name')
                    mapped_count += 1
            
            await db.commit()
            
        return ActivityResult(
            success=True,
            data={
                "applied_mappings": mapped_count,
                "total_suggestions": len(mapping_suggestions)
            }
        )
            
    except Exception as e:
        logger.error(f"Error in apply_pde_mappings_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def analyze_document_activity(
    document_text: str,
    document_type: str
) -> ActivityResult:
    """Analyze document using LLM"""
    try:
        llm_service = get_llm_service()
        
        result = await llm_service.analyze_regulatory_document(
            document_text=document_text,
            document_type=document_type
        )
        
        return ActivityResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_document_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def recommend_tests_activity(
    attribute_name: str,
    data_type: str,
    regulatory_context: str,
    historical_issues: List[str] = None
) -> ActivityResult:
    """Generate test recommendations using LLM"""
    try:
        llm_service = get_llm_service()
        
        result = await llm_service.recommend_tests(
            attribute_name=attribute_name,
            data_type=data_type,
            regulatory_context=regulatory_context,
            historical_issues=historical_issues or []
        )
        
        return ActivityResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error in recommend_tests_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def analyze_patterns_activity(
    historical_issues: List[str],
    report_context: str
) -> ActivityResult:
    """Analyze historical patterns using LLM"""
    try:
        llm_service = get_llm_service()
        
        result = await llm_service.analyze_historical_patterns(
            historical_issues=historical_issues,
            report_context=report_context
        )
        
        return ActivityResult(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_patterns_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )
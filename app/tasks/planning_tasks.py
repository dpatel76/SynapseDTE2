"""
Planning Phase Background Tasks
Handles long-running planning operations without blocking the UI
"""
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Removed celery_app import - using background jobs manager instead
from app.core.database import AsyncSessionLocal
from app.core.background_jobs import job_manager
from app.services.llm_service import get_llm_service
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Removed Celery task wrapper - _regenerate_pde_mappings_async is called directly from endpoints


async def _regenerate_pde_mappings_async(
    job_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    user_id: int,
    attributes_data: List[Dict[str, Any]],
    data_sources_data: List[Dict[str, Any]],
    existing_mappings_data: List[Dict[str, Any]],
    report_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Async helper for PDE mapping regeneration"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Update job status
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Starting regeneration",
                progress_percentage=0,
                message="Initializing PDE mapping regeneration"
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            updated_count = 0
            
            # Call LLM service for suggestions
            all_suggestions = await llm_service.suggest_pde_mappings(
                attributes=attributes_data,
                data_sources=data_sources_data,
                report_context=report_context,
                job_id=job_id
            )
            
            # Import models
            from app.models.planning import PlanningPDEMapping
            
            # Update each existing mapping with new suggestions
            logger.info(f"Processing {len(all_suggestions)} suggestions from LLM")
            
            for idx, suggestion in enumerate(all_suggestions):
                if suggestion.get('attribute_id'):
                    # Find the existing mapping data
                    attribute_id = suggestion.get('attribute_id')
                    
                    # Convert attribute_id to integer if it's a string
                    if isinstance(attribute_id, str) and attribute_id.isdigit():
                        attribute_id = int(attribute_id)
                    
                    existing_data = None
                    for mapping_data in existing_mappings_data:
                        # Ensure both IDs are the same type for comparison
                        mapping_attr_id = mapping_data['attribute_id']
                        if isinstance(mapping_attr_id, str) and mapping_attr_id.isdigit():
                            mapping_attr_id = int(mapping_attr_id)
                        
                        if mapping_attr_id == attribute_id:
                            existing_data = mapping_data
                            break
                    
                    if existing_data:
                        # Load the actual mapping from database
                        mapping_query = select(PlanningPDEMapping).where(
                            PlanningPDEMapping.id == existing_data['id']
                        )
                        mapping_result = await db.execute(mapping_query)
                        existing = mapping_result.scalar_one_or_none()
                        
                        if existing:
                            logger.info(f"Updating mapping {existing.id} for attribute {attribute_id}")
                            
                            # Update the mapping with new suggestion
                            existing.data_source_id = suggestion.get('data_source_id')
                            existing.source_field = suggestion.get('source_field', '')
                            existing.llm_suggested_mapping = suggestion
                            existing.llm_confidence_score = suggestion.get('confidence_score', 0)
                            existing.llm_mapping_rationale = suggestion.get('rationale', '')
                            
                            # Update classification data
                            existing.information_security_classification = suggestion.get('information_security_classification')
                            existing.criticality = suggestion.get('criticality')
                            existing.risk_level = suggestion.get('risk_level')
                            existing.business_process = suggestion.get('business_process', '')
                            existing.mapping_type = suggestion.get('mapping_type', 'direct')
                            existing.transformation_rule = suggestion.get('transformation_rule', '')
                            
                            # Update metadata
                            existing.updated_at = datetime.utcnow()
                            existing.updated_by_id = user_id
                            
                            db.add(existing)
                            updated_count += 1
                
                # Update progress
                progress = int((idx + 1) / len(all_suggestions) * 90)
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=progress,
                    current_step=f"Updated {updated_count} mappings",
                    message=f"Processing mapping {idx + 1} of {len(all_suggestions)}"
                )
            
            # Commit all changes
            await db.commit()
            logger.info(f"Successfully committed {updated_count} updated mappings")
            
            # Mark job as completed
            job_manager.update_job_progress(
                job_id,
                status="completed",
                progress_percentage=100,
                current_step="Completed",
                message=f"Successfully regenerated {updated_count} PDE mappings",
                result={
                    "updated_count": updated_count,
                    "total_mappings": len(existing_mappings_data)
                }
            )
            
            return {
                "status": "success",
                "updated_count": updated_count,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in PDE mapping regeneration: {str(e)}")
            job_manager.update_job_progress(
                job_id,
                status="failed",
                error=str(e),
                message=f"Failed to regenerate mappings: {str(e)}"
            )
            raise


# Removed Celery task wrapper - _generate_llm_attributes_async is called directly from endpoints


async def _generate_llm_attributes_async(
    job_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    user_id: int,
    document_content: str,
    regulatory_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Async helper for LLM attribute generation"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Update job status
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Analyzing document",
                progress_percentage=10,
                message="Starting LLM attribute generation"
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Generate attributes
            llm_response = await llm_service.generate_test_attributes(
                document_content=document_content,
                regulatory_context=regulatory_context
            )
            
            # Process and save attributes
            from app.models.report_attribute import ReportAttribute
            
            created_count = 0
            attributes = llm_response.get('attributes', [])
            
            for idx, attr_data in enumerate(attributes):
                # Create attribute record
                attribute = ReportAttribute(
                    phase_id=phase_id,
                    attribute_name=attr_data.get('attribute_name'),
                    description=attr_data.get('description'),
                    data_type=attr_data.get('data_type'),
                    mandatory_flag=attr_data.get('mandatory_flag'),
                    validation_rules=attr_data.get('validation_rules'),
                    testing_approach=attr_data.get('testing_approach'),
                    line_item_number=attr_data.get('line_item_number'),
                    technical_line_item_name=attr_data.get('technical_line_item_name'),
                    is_cde=attr_data.get('is_cde', False),
                    is_primary_key=attr_data.get('is_primary_key', False),
                    created_by_id=user_id,
                    updated_by_id=user_id
                )
                
                db.add(attribute)
                created_count += 1
                
                # Update progress
                progress = int(10 + (80 * (idx + 1) / len(attributes)))
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=progress,
                    current_step=f"Creating attribute {idx + 1} of {len(attributes)}",
                    message=f"Processing {attr_data.get('attribute_name')}"
                )
            
            # Commit all changes
            await db.commit()
            
            # Mark job as completed
            job_manager.update_job_progress(
                job_id,
                status="completed",
                progress_percentage=100,
                current_step="Completed",
                message=f"Successfully generated {created_count} attributes",
                result={
                    "created_count": created_count,
                    "attributes": attributes
                }
            )
            
            return {
                "status": "success",
                "created_count": created_count,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in LLM attribute generation: {str(e)}")
            job_manager.update_job_progress(
                job_id,
                status="failed",
                error=str(e),
                message=f"Failed to generate attributes: {str(e)}"
            )
            raise


# Removed Celery task wrapper - _auto_map_pdes_async is called directly from endpoints


async def _auto_map_pdes_async(
    job_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    user_id: int,
    attributes_context: List[Dict[str, Any]],
    data_sources_context: List[Dict[str, Any]],
    report_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Async helper for auto PDE mapping"""
    logger.info(f"🚀 _auto_map_pdes_async STARTED for job {job_id}")
    logger.info(f"📊 Parameters: cycle_id={cycle_id}, report_id={report_id}, phase_id={phase_id}, attributes={len(attributes_context)}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Update job status
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Calling LLM service for PDE mapping suggestions",
                progress_percentage=10,
                message=f"Processing {len(attributes_context)} attributes..."
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            logger.info(f"🤖 Got LLM service, calling suggest_pde_mappings...")
            
            # Call LLM service with ALL attributes - it will handle batching internally
            all_suggestions = await llm_service.suggest_pde_mappings(
                attributes=attributes_context,
                data_sources=data_sources_context,
                report_context=report_context,
                job_id=job_id
            )
            
            logger.info(f"📥 Received {len(all_suggestions)} total suggestions")
            
            # Log first few suggestions to debug
            if all_suggestions:
                logger.info(f"🔍 First suggestion: {all_suggestions[0]}")
                logger.info(f"🔍 Attribute IDs in suggestions: {[s.get('attribute_id') for s in all_suggestions[:5]]}")
                logger.info(f"🔍 Attribute IDs in context: {[a['id'] for a in attributes_context[:5]]}")
            
            # Import models
            from app.models.planning import PlanningPDEMapping
            from app.models.report_attribute import ReportAttribute
            
            total_mapped = 0
            total_failed = 0
            
            # Process all suggestions
            for idx, suggestion in enumerate(all_suggestions):
                try:
                    attr_id = suggestion.get('attribute_id')
                    if not attr_id:
                        logger.warning(f"⚠️ Suggestion missing attribute_id: {suggestion}")
                        continue
                    
                    # Convert attribute_id to integer if it's a string
                    if isinstance(attr_id, str) and attr_id.isdigit():
                        attr_id = int(attr_id)
                        logger.info(f"🔍 Converted attribute_id from string to int: {attr_id}")
                    
                    logger.info(f"🔍 Processing suggestion for attribute_id: {attr_id} (type: {type(attr_id)})")
                    
                    # Skip failed mappings (those with error field or 0 confidence)
                    if suggestion.get('error') or suggestion.get('confidence_score', 0) == 0:
                        logger.warning(f"⚠️ Skipping failed mapping for attribute {attr_id}: {suggestion.get('error', 'No confidence')}")
                        total_failed += 1
                        continue
                    
                    # Check if mapping already exists
                    logger.info(f"🔍 Checking if mapping exists for attribute_id={attr_id}, phase_id={phase_id}")
                    existing_mapping = await db.execute(
                        select(PlanningPDEMapping).where(
                            and_(
                                PlanningPDEMapping.attribute_id == attr_id,
                                PlanningPDEMapping.phase_id == phase_id
                            )
                        )
                    )
                    existing = existing_mapping.scalar_one_or_none()
                    if existing:
                        logger.info(f"Attribute {attr_id} already mapped (mapping id: {existing.id}), skipping")
                        continue
                    else:
                        logger.info(f"No existing mapping found for attribute {attr_id}")
                    
                    logger.info(f"Creating new mapping for attribute {attr_id}")
                    
                    # Find the attribute name from attributes_context
                    # Convert context IDs to match the type of attr_id
                    attr_name = next(
                        (attr['attribute_name'] for attr in attributes_context 
                         if int(attr['id']) == attr_id), 
                        f"Unknown Attribute {attr_id}"
                    )
                    
                    # Extract column name from source field (e.g., "schema.table.column" -> "column")
                    source_field = suggestion.get('source_field', '')
                    column_name = source_field.split('.')[-1] if source_field and '.' in source_field else f"PDE_{attr_id}"
                    
                    # Create mapping
                    mapping = PlanningPDEMapping(
                        phase_id=phase_id,
                        attribute_id=attr_id,
                        data_source_id=suggestion.get('data_source_id'),
                        source_field=source_field,
                        
                        # Required PDE fields - use actual column name as pde_code
                        pde_name=attr_name,
                        pde_code=column_name,  # Use the actual column name from source field
                        pde_description=suggestion.get('description', attr_name),
                        
                        # LLM mapping data
                        llm_suggested_mapping=suggestion,
                        llm_confidence_score=suggestion.get('confidence_score', 0),
                        llm_mapping_rationale=suggestion.get('rationale', ''),
                        
                        # Include classification data
                        information_security_classification=suggestion.get('information_security_classification'),
                        criticality=suggestion.get('criticality'),
                        risk_level=suggestion.get('risk_level'),
                        business_process=suggestion.get('business_process', ''),
                        mapping_type=suggestion.get('mapping_type', 'direct'),
                        transformation_rule=suggestion.get('transformation_rule', ''),
                        
                        # Metadata
                        created_by_id=user_id,
                        updated_by_id=user_id
                    )
                    
                    db.add(mapping)
                    total_mapped += 1
                    logger.info(f"✅ Created mapping for {attr_name} (ID: {attr_id})")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create mapping for attribute {attr_id}: {e}")
                    total_failed += 1
                
                # Update progress periodically
                if idx % 10 == 0:
                    progress = int(10 + (80 * (idx + 1) / len(all_suggestions)))
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=progress,
                        current_step=f"Created {total_mapped} mappings, {total_failed} failed",
                        message=f"Processing suggestion {idx + 1} of {len(all_suggestions)}"
                    )
            
            # Commit all changes
            await db.commit()
            logger.info(f"Committed {total_mapped} new mappings to database")
            
            # Mark job as completed with appropriate status
            if total_mapped == 0 and total_failed > 0:
                # Complete failure
                job_manager.update_job_progress(
                    job_id,
                    status="failed",
                    progress_percentage=100,
                    current_step="Failed",
                    message=f"Failed to map any PDEs. Check LLM service configuration.",
                    result={
                        "total_mapped": total_mapped,
                        "total_failed": total_failed,
                        "total_suggestions": len(all_suggestions)
                    }
                )
            elif total_failed > 0:
                # Partial success
                job_manager.update_job_progress(
                    job_id,
                    status="completed",
                    progress_percentage=100,
                    current_step="Completed with warnings",
                    message=f"Mapped {total_mapped} PDEs successfully. {total_failed} attributes require manual mapping.",
                    result={
                        "total_mapped": total_mapped,
                        "total_failed": total_failed,
                        "total_suggestions": len(all_suggestions),
                        "success_rate": f"{(total_mapped / len(all_suggestions) * 100):.1f}%"
                    }
                )
            else:
                # Complete success
                job_manager.update_job_progress(
                    job_id,
                    status="completed",
                    progress_percentage=100,
                    current_step="Completed",
                    message=f"Successfully mapped all {total_mapped} PDEs",
                    result={
                        "total_mapped": total_mapped,
                        "total_failed": total_failed,
                        "total_suggestions": len(all_suggestions)
                    }
                )
            
            return {
                "status": "success",
                "total_mapped": total_mapped,
                "total_failed": total_failed,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in auto PDE mapping: {str(e)}")
            job_manager.update_job_progress(
                job_id,
                status="failed",
                error=str(e),
                message=f"Failed to auto-map PDEs: {str(e)}"
            )
            raise


# Removed Celery task wrapper - _classify_pdes_batch_async is called directly from endpoints


async def _classify_pdes_batch_async(
    job_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    user_id: int,
    mappings_data: List[Dict[str, Any]],
    report_context: Dict[str, Any],
    cycle_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Async helper for batch PDE classification"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Update job status
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Starting PDE classification",
                progress_percentage=5,
                message=f"Processing {len(mappings_data)} PDEs for classification"
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Call LLM for batch classification
            suggestions = await llm_service.generate_pde_classifications_batch(
                mappings=mappings_data,
                cycle_context=cycle_context,
                report_context=report_context,
                job_id=job_id
            )
            
            # Import models
            from app.models.planning import PlanningPDEMapping
            
            updated_count = 0
            failed_count = 0
            
            # Process each suggestion and update the database
            for idx, suggestion in enumerate(suggestions):
                try:
                    mapping_id = suggestion.get('mapping_id')
                    if not mapping_id:
                        logger.warning(f"No mapping_id in suggestion: {suggestion}")
                        continue
                    
                    # Load the mapping from database
                    mapping_query = select(PlanningPDEMapping).where(
                        PlanningPDEMapping.id == mapping_id
                    )
                    mapping_result = await db.execute(mapping_query)
                    mapping = mapping_result.scalar_one_or_none()
                    
                    if not mapping:
                        logger.warning(f"Mapping {mapping_id} not found")
                        failed_count += 1
                        continue
                    
                    # Update classification fields
                    mapping.information_security_classification = suggestion.get('information_security_classification')
                    mapping.criticality = suggestion.get('criticality')
                    mapping.risk_level = suggestion.get('risk_level')
                    mapping.business_process = suggestion.get('business_process', '')
                    mapping.llm_classification_rationale = suggestion.get('rationale', '')
                    mapping.llm_classification_confidence = suggestion.get('confidence_score', 0)
                    
                    # Update metadata
                    mapping.updated_at = datetime.utcnow()
                    mapping.updated_by_id = user_id
                    
                    db.add(mapping)
                    updated_count += 1
                    
                    # Update progress periodically
                    if idx % 5 == 0:
                        progress = int(5 + (90 * (idx + 1) / len(suggestions)))
                        job_manager.update_job_progress(
                            job_id,
                            progress_percentage=progress,
                            current_step=f"Classified {updated_count} PDEs",
                            message=f"Processing PDE {idx + 1} of {len(suggestions)}"
                        )
                    
                except Exception as e:
                    logger.error(f"Failed to update mapping {mapping_id}: {e}")
                    failed_count += 1
            
            # Commit all changes
            await db.commit()
            logger.info(f"Successfully updated {updated_count} PDE classifications")
            
            # Mark job as completed
            job_manager.update_job_progress(
                job_id,
                status="completed",
                progress_percentage=100,
                current_step="Completed",
                message=f"Successfully classified {updated_count} PDEs",
                result={
                    "updated_count": updated_count,
                    "failed_count": failed_count,
                    "total_processed": len(suggestions)
                }
            )
            
            return {
                "status": "success",
                "updated_count": updated_count,
                "failed_count": failed_count,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in PDE classification batch: {str(e)}")
            job_manager.update_job_progress(
                job_id,
                status="failed",
                error=str(e),
                message=f"Failed to classify PDEs: {str(e)}"
            )
            raise
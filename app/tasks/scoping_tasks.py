"""
Scoping Phase Background Tasks
Handles long-running scoping operations without blocking the UI
"""
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Celery removed - using threading instead
from app.core.database import AsyncSessionLocal
from app.core.background_jobs import job_manager
from app.services.llm_service import get_llm_service
from app.services.scoping_service import ScopingService
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Celery task removed - using threading in the endpoint directly


async def _generate_scoping_recommendations_async(
    job_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    version_id: int,
    user_id: int,
    attributes_to_process: List[Dict[str, Any]],
    report_context: Dict[str, Any],
    cycle_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Async helper for scoping recommendations generation"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Update job status
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Starting LLM recommendation generation",
                progress_percentage=10,
                message=f"Processing {len(attributes_to_process)} attributes..."
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Process attributes in batches for better performance and reliability
            batch_size = 6  # Reduced batch size to avoid LLM context limits
            total_batches = (len(attributes_to_process) + batch_size - 1) // batch_size
            all_recommendations = []
            
            logger.info(f"📊 Processing {len(attributes_to_process)} attributes in {total_batches} batches of {batch_size}")
            
            for batch_idx in range(0, len(attributes_to_process), batch_size):
                batch_attrs = attributes_to_process[batch_idx:batch_idx + batch_size]
                batch_num = (batch_idx // batch_size) + 1
                
                # Update progress for this batch
                base_progress = 10
                batch_progress = int(base_progress + (60 * batch_num / total_batches))
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=batch_progress,
                    current_step=f"Processing batch {batch_num} of {total_batches}",
                    message=f"Generating recommendations for {len(batch_attrs)} attributes"
                )
                
                logger.info(f"Processing batch {batch_num}/{total_batches} with {len(batch_attrs)} attributes")
                
                try:
                    batch_result = await llm_service.generate_scoping_recommendations(
                        attributes=batch_attrs,
                        report_type=report_context.get("report_name")
                    )
                    
                    logger.info(f"🔍 DEBUG: batch_result keys: {list(batch_result.keys())}")
                    logger.info(f"🔍 DEBUG: batch_result: {json.dumps(batch_result, default=str)[:500]}")
                    
                    batch_recommendations = batch_result.get("recommendations", [])
                    all_recommendations.extend(batch_recommendations)
                    
                    logger.info(f"Batch {batch_num}/{total_batches} completed: {len(batch_recommendations)} recommendations received")
                    
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {str(e)}")
                    # Continue with next batch instead of failing entirely
                    continue
            
            logger.info(f"Completed all batches. Total recommendations received: {len(all_recommendations)}")
            
            # Debug log the recommendations
            if all_recommendations:
                logger.info(f"🔍 DEBUG: First recommendation: {json.dumps(all_recommendations[0], default=str)[:500]}")
            else:
                logger.warning("⚠️ WARNING: No recommendations received from LLM!")
            
            # Process and save recommendations
            service = ScopingService(db)
            planning_attr_ids = []
            llm_recommendations = []
            
            for idx, rec in enumerate(all_recommendations):
                # Match attribute by name to get the ID
                attr_name = rec.get("attribute_name")
                attr_id = None
                
                # Find matching attribute in the input list (case-insensitive)
                for attr in attributes_to_process:
                    input_name = attr.get("attribute_name", "")
                    # Try exact match first
                    if input_name == attr_name:
                        attr_id = attr.get("id")
                        break
                    # Try case-insensitive match
                    elif input_name.lower() == attr_name.lower():
                        attr_id = attr.get("id")
                        logger.warning(f"⚠️ Case mismatch: '{attr_name}' matched with '{input_name}'")
                        break
                
                if attr_id and attr_name:
                    planning_attr_ids.append(attr_id)
                    
                    # Convert new regulation-specific format to database format
                    enhanced_rationale = rec.get("enhanced_rationale", {})
                    
                    logger.info(f"✅ Matched recommendation for {attr_name} -> ID: {attr_id}")
                    
                    # Build comprehensive rationale from FR Y-14M response
                    full_rationale = []
                    if enhanced_rationale.get("regulatory_usage"):
                        full_rationale.append(f"**Regulatory Usage**: {enhanced_rationale['regulatory_usage']}")
                    if enhanced_rationale.get("business_impact"):  
                        full_rationale.append(f"**Business Impact**: {enhanced_rationale['business_impact']}")
                    if enhanced_rationale.get("interconnections"):
                        full_rationale.append(f"**Data Interconnections**: {enhanced_rationale['interconnections']}")
                    
                    llm_recommendations.append({
                        "recommendation": "include",  # Standard recommendation value
                        "provider": "anthropic",  # Keep provider name short to avoid DB field truncation
                        "confidence_score": rec.get("risk_score", 50) / 100.0,  # Use risk score as confidence
                        "rationale": "\n\n".join(full_rationale),  # Rich combined rationale
                        "processing_time_ms": rec.get("processing_time_ms", 0),
                        "request_payload": json.dumps({
                            "model": "claude-3-5-sonnet",
                            "temperature": 0.3
                        }),
                        "response_payload": rec,
                        "is_cde": rec.get("is_cde", attr.get("is_cde", False)),
                        "is_primary_key": rec.get("is_primary_key", attr.get("is_primary_key", False)), 
                        "has_historical_issues": rec.get("has_historical_issues", attr.get("has_historical_issues", False)),
                        "risk_factors": json.dumps(rec.get("validation_rules", []))  # Use validation rules as risk factors
                    })
                    
                    logger.info(f"Prepared recommendation for {attr_name} (ID: {attr_id})")
                else:
                    if not attr_name:
                        logger.warning(f"❌ Recommendation missing attribute_name: {json.dumps(rec)[:200]}")
                    else:
                        logger.warning(f"❌ Could not find matching attribute for '{attr_name}'")
                        # Log available attributes for debugging
                        available_names = [a.get("attribute_name") for a in attributes_to_process[:5]]
                        logger.warning(f"   Available attributes (first 5): {available_names}")
                
                # Update progress periodically (70-90% range for processing/saving)
                if idx % 10 == 0:
                    progress = int(70 + (20 * (idx + 1) / len(all_recommendations)))
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=progress,
                        current_step=f"Saving recommendation {idx + 1} of {len(all_recommendations)}",
                        message=f"Processed {len(planning_attr_ids)} recommendations so far"
                    )
            
            # Save all recommendations at once using the existing method
            if planning_attr_ids:
                created_attributes = await service.add_attributes_to_version(
                    version_id=version_id,
                    planning_attribute_ids=planning_attr_ids,
                    llm_recommendations=llm_recommendations,
                    user_id=user_id
                )
                saved_recommendations = len(created_attributes)
                logger.info(f"Successfully saved {saved_recommendations} recommendations")
            else:
                saved_recommendations = 0
                logger.warning("No valid attribute IDs found for recommendations")
            
            # Final progress update before commit
            job_manager.update_job_progress(
                job_id,
                progress_percentage=95,
                current_step="Saving to database",
                message=f"Committing {saved_recommendations} recommendations"
            )
            
            # Commit all changes
            await db.commit()
            logger.info(f"Successfully saved {saved_recommendations} recommendations to version {version_id}")
            
            # Mark job as completed
            job_manager.update_job_progress(
                job_id,
                status="completed",
                progress_percentage=100,
                current_step="Completed",
                message=f"Successfully generated recommendations for {len(all_recommendations)} attributes",
                result={
                    "processed": saved_recommendations,
                    "failed": 0,
                    "total": len(attributes_to_process),
                    "success": True,
                    "test_recommendations": saved_recommendations,
                    "attributes_processed": len(attributes_to_process),
                    "incremental_update": False,
                    "force_regenerate": True
                }
            )
            
            return {
                "status": "success",
                "recommendations_count": len(all_recommendations),
                "version_id": version_id,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in scoping recommendations generation: {str(e)}")
            job_manager.update_job_progress(
                job_id,
                status="failed",
                error=str(e),
                message=f"Failed to generate recommendations: {str(e)}"
            )
            raise
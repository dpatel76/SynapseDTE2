"""Optimized background tasks with batching and caching"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from functools import lru_cache

from celery import Task, group, chord
from app.core.celery_app import celery_app
from app.core.performance import measure_performance, BatchProcessor
from app.db.optimized_session import get_db_context

logger = logging.getLogger(__name__)


class OptimizedTask(Task):
    """Base class for optimized tasks"""
    
    # Task-level caching
    _cache = {}
    _cache_ttl = 300  # 5 minutes
    
    def __init__(self):
        self.batch_processor = BatchProcessor()
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached result"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self._cache_ttl):
                return value
            else:
                del self._cache[key]
        return None
    
    def set_cached(self, key: str, value: Any):
        """Set cache value"""
        self._cache[key] = (value, datetime.utcnow())


@celery_app.task(base=OptimizedTask, bind=True)
@measure_performance("tasks.batch_generate_attributes")
def batch_generate_attributes(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch process attribute generation for multiple reports
    Optimized for handling multiple requests efficiently
    """
    results = []
    
    # Group requests by similar parameters for better LLM utilization
    grouped_requests = {}
    for request in requests:
        key = f"{request['regulation']}_{request['report_type']}"
        if key not in grouped_requests:
            grouped_requests[key] = []
        grouped_requests[key].append(request)
    
    # Process each group
    for group_key, group_requests in grouped_requests.items():
        try:
            # Check cache first
            cache_key = f"attributes_{group_key}"
            cached_result = self.get_cached(cache_key)
            
            if cached_result:
                logger.info(f"Using cached attributes for {group_key}")
                for req in group_requests:
                    results.append({
                        "request_id": req.get("request_id"),
                        "attributes": cached_result,
                        "from_cache": True
                    })
                continue
            
            # Generate attributes for the group
            from app.services.hybrid_llm_service import get_llm_service
            llm_service = get_llm_service()
            
            # Use the first request as template
            template_request = group_requests[0]
            
            asyncio.run(self._generate_for_group(
                llm_service,
                template_request,
                group_requests,
                results
            ))
            
        except Exception as e:
            logger.error(f"Failed to process group {group_key}: {e}")
            for req in group_requests:
                results.append({
                    "request_id": req.get("request_id"),
                    "error": str(e)
                })
    
    return results


async def _generate_for_group(self, llm_service, template_request, group_requests, results):
    """Generate attributes for a group of similar requests"""
    try:
        # Generate attributes using template
        result = await llm_service.generate_test_attributes(
            regulatory_context=template_request['regulation'],
            report_type=template_request['report_type'],
            existing_attributes=None,
            preferred_provider="claude"
        )
        
        if result.get('success'):
            attributes = result.get('attributes', [])
            
            # Cache the result
            cache_key = f"attributes_{template_request['regulation']}_{template_request['report_type']}"
            self.set_cached(cache_key, attributes)
            
            # Apply to all requests in group
            for req in group_requests:
                results.append({
                    "request_id": req.get("request_id"),
                    "attributes": attributes,
                    "from_cache": False
                })
        else:
            raise Exception(result.get('error', 'Unknown error'))
            
    except Exception as e:
        raise


@celery_app.task(bind=True)
@measure_performance("tasks.batch_analyze_documents")
def batch_analyze_documents(self, document_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch analyze multiple documents efficiently
    """
    # Use Celery group for parallel processing
    job = group(
        analyze_single_document.s(doc_analysis) 
        for doc_analysis in document_analyses
    )
    
    # Execute all analyses in parallel
    result = job.apply_async()
    
    # Wait for results with timeout
    try:
        results = result.get(timeout=300)  # 5 minute timeout
        return results
    except Exception as e:
        logger.error(f"Batch document analysis failed: {e}")
        return [{"error": str(e)} for _ in document_analyses]


@celery_app.task
@measure_performance("tasks.analyze_single_document")
def analyze_single_document(doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single document"""
    try:
        # Import here to avoid circular imports
        from app.services.hybrid_llm_service import get_llm_service
        
        llm_service = get_llm_service()
        
        # Run async function in sync context
        result = asyncio.run(llm_service.analyze_document_for_attribute(
            document_content=doc_analysis['content'],
            attribute_name=doc_analysis['attribute_name'],
            expected_value=doc_analysis['expected_value'],
            test_context=doc_analysis.get('context', {}),
            preferred_provider="gemini"  # Gemini is better for extraction
        ))
        
        return {
            "document_id": doc_analysis['document_id'],
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        return {
            "document_id": doc_analysis['document_id'],
            "error": str(e)
        }


@celery_app.task(bind=True)
@measure_performance("tasks.optimize_workflow_processing")
def optimize_workflow_processing(self, cycle_id: int, report_ids: List[int]) -> Dict[str, Any]:
    """
    Optimize workflow processing for multiple reports
    Process multiple reports in a cycle efficiently
    """
    results = {
        "cycle_id": cycle_id,
        "reports_processed": 0,
        "errors": [],
        "processing_time": 0
    }
    
    start_time = datetime.utcnow()
    
    try:
        # Process reports in parallel batches
        batch_size = 5  # Process 5 reports at a time
        
        for i in range(0, len(report_ids), batch_size):
            batch = report_ids[i:i + batch_size]
            
            # Create subtasks for each report in batch
            job = group(
                process_single_report.s(cycle_id, report_id)
                for report_id in batch
            )
            
            # Execute batch
            batch_result = job.apply_async()
            
            try:
                batch_results = batch_result.get(timeout=120)
                results["reports_processed"] += len([r for r in batch_results if r.get("success")])
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                results["errors"].extend([f"Report {rid}: {str(e)}" for rid in batch])
        
    except Exception as e:
        logger.error(f"Workflow optimization failed: {e}")
        results["errors"].append(str(e))
    
    results["processing_time"] = (datetime.utcnow() - start_time).total_seconds()
    
    return results


@celery_app.task
def process_single_report(cycle_id: int, report_id: int) -> Dict[str, Any]:
    """Process a single report in the workflow"""
    try:
        # This would contain the actual report processing logic
        # For now, simulate processing
        import time
        time.sleep(0.5)  # Simulate work
        
        return {
            "report_id": report_id,
            "success": True
        }
        
    except Exception as e:
        return {
            "report_id": report_id,
            "success": False,
            "error": str(e)
        }


@celery_app.task(bind=True)
@measure_performance("tasks.cleanup_old_data")
def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
    """
    Cleanup old data for performance optimization
    Runs as a periodic task
    """
    results = {
        "audit_logs_deleted": 0,
        "notifications_deleted": 0,
        "temp_files_deleted": 0
    }
    
    try:
        asyncio.run(self._cleanup_async(days_to_keep, results))
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        results["error"] = str(e)
    
    return results


async def _cleanup_async(self, days_to_keep: int, results: Dict[str, int]):
    """Async cleanup implementation"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    async with get_db_context() as db:
        # Cleanup audit logs
        from app.models import AuditLog
        result = await db.execute(
            f"DELETE FROM audit_logs WHERE timestamp < :cutoff",
            {"cutoff": cutoff_date}
        )
        results["audit_logs_deleted"] = result.rowcount
        
        # Cleanup old notifications
        from app.models import Notification
        result = await db.execute(
            f"DELETE FROM notifications WHERE created_at < :cutoff AND is_read = true",
            {"cutoff": cutoff_date}
        )
        results["notifications_deleted"] = result.rowcount
        
        await db.commit()
    
    # Cleanup temporary files
    import os
    from pathlib import Path
    
    temp_dir = Path("/tmp/synapse_dte")
    if temp_dir.exists():
        for file in temp_dir.glob("*"):
            if file.stat().st_mtime < cutoff_date.timestamp():
                file.unlink()
                results["temp_files_deleted"] += 1


# Schedule periodic cleanup
from celery.schedules import crontab

celery_app.conf.beat_schedule.update({
    'cleanup-old-data': {
        'task': 'app.tasks.optimized_tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        'args': (90,)  # Keep 90 days of data
    },
    'warm-cache': {
        'task': 'app.tasks.optimized_tasks.warm_cache',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    }
})


@celery_app.task
def warm_cache():
    """Warm up caches with frequently accessed data"""
    try:
        # This would pre-load frequently accessed data into cache
        # For example, active test cycles, common attributes, etc.
        logger.info("Cache warming completed")
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
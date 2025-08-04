"""
Query Performance Monitor
Provides utilities for monitoring and analyzing database query performance
"""

import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.event import listens_for

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Metrics for a database query"""
    query_id: str
    query_type: str  # select, insert, update, delete
    execution_time_ms: float
    rows_returned: Optional[int]
    query_text: str
    timestamp: datetime
    parameters: Optional[Dict[str, Any]] = None
    optimization_used: bool = False
    phase_id_used: bool = False
    join_count: int = 0
    table_count: int = 0

@dataclass 
class QueryPerformanceReport:
    """Performance report for query analysis"""
    total_queries: int
    avg_execution_time_ms: float
    slowest_queries: List[QueryMetrics]
    optimization_usage: Dict[str, int]
    performance_trends: Dict[str, List[float]]
    recommendations: List[str]

class QueryPerformanceMonitor:
    """Monitor and analyze database query performance"""
    
    def __init__(self, slow_query_threshold_ms: float = 1000.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_metrics: List[QueryMetrics] = []
        self.session_metrics: Dict[str, List[QueryMetrics]] = {}
        self._monitoring_enabled = True
        
    def enable_monitoring(self):
        """Enable query monitoring"""
        self._monitoring_enabled = True
        
    def disable_monitoring(self):
        """Disable query monitoring"""
        self._monitoring_enabled = False
        
    @asynccontextmanager
    async def monitor_query(
        self, 
        query_id: str, 
        query_type: str = "select",
        optimization_used: bool = False,
        phase_id_used: bool = False
    ):
        """Context manager for monitoring individual queries"""
        if not self._monitoring_enabled:
            yield
            return
            
        start_time = time.time()
        
        try:
            yield
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Create metrics record
            metrics = QueryMetrics(
                query_id=query_id,
                query_type=query_type,
                execution_time_ms=execution_time_ms,
                rows_returned=None,  # Would need to be set by caller
                query_text="",  # Would need to be set by caller
                timestamp=datetime.utcnow(),
                optimization_used=optimization_used,
                phase_id_used=phase_id_used
            )
            
            self.query_metrics.append(metrics)
            
            # Log slow queries
            if execution_time_ms > self.slow_query_threshold_ms:
                logger.warning(
                    f"Slow query detected: {query_id} took {execution_time_ms:.2f}ms"
                )
    
    async def monitor_service_queries(
        self, 
        service_name: str, 
        operation: Callable,
        *args, 
        **kwargs
    ) -> Any:
        """Monitor all queries for a service operation"""
        session_id = f"{service_name}_{int(time.time())}"
        self.session_metrics[session_id] = []
        
        start_time = time.time()
        
        try:
            result = await operation(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(
                f"Service {service_name} completed in {execution_time:.2f}ms "
                f"with {len(self.session_metrics[session_id])} queries"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Service {service_name} failed: {str(e)}")
            raise
            
    def get_performance_report(
        self, 
        time_window_minutes: int = 60
    ) -> QueryPerformanceReport:
        """Generate comprehensive performance report"""
        
        # Filter metrics by time window
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_metrics = [
            m for m in self.query_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return QueryPerformanceReport(
                total_queries=0,
                avg_execution_time_ms=0.0,
                slowest_queries=[],
                optimization_usage={},
                performance_trends={},
                recommendations=[]
            )
        
        # Calculate basic statistics
        total_queries = len(recent_metrics)
        avg_execution_time = sum(m.execution_time_ms for m in recent_metrics) / total_queries
        
        # Find slowest queries
        slowest_queries = sorted(
            recent_metrics, 
            key=lambda x: x.execution_time_ms, 
            reverse=True
        )[:10]
        
        # Optimization usage statistics
        optimization_usage = {
            "phase_id_queries": sum(1 for m in recent_metrics if m.phase_id_used),
            "optimized_queries": sum(1 for m in recent_metrics if m.optimization_used),
            "legacy_queries": sum(1 for m in recent_metrics if not m.optimization_used),
            "slow_queries": sum(1 for m in recent_metrics if m.execution_time_ms > self.slow_query_threshold_ms)
        }
        
        # Performance trends (by 10-minute buckets)
        performance_trends = self._calculate_performance_trends(recent_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(recent_metrics, optimization_usage)
        
        return QueryPerformanceReport(
            total_queries=total_queries,
            avg_execution_time_ms=avg_execution_time,
            slowest_queries=slowest_queries,
            optimization_usage=optimization_usage,
            performance_trends=performance_trends,
            recommendations=recommendations
        )
    
    def _calculate_performance_trends(
        self, 
        metrics: List[QueryMetrics]
    ) -> Dict[str, List[float]]:
        """Calculate performance trends over time"""
        
        # Group by 10-minute buckets
        buckets = {}
        for metric in metrics:
            bucket_time = metric.timestamp.replace(
                minute=(metric.timestamp.minute // 10) * 10,
                second=0,
                microsecond=0
            )
            
            if bucket_time not in buckets:
                buckets[bucket_time] = []
            buckets[bucket_time].append(metric.execution_time_ms)
        
        # Calculate averages for each bucket
        trends = {
            "avg_response_time": [],
            "query_volume": [],
            "optimization_rate": []
        }
        
        for bucket_time, bucket_metrics in sorted(buckets.items()):
            avg_time = sum(bucket_metrics) / len(bucket_metrics)
            query_count = len(bucket_metrics)
            
            trends["avg_response_time"].append(avg_time)
            trends["query_volume"].append(query_count)
        
        return trends
    
    def _generate_recommendations(
        self, 
        metrics: List[QueryMetrics],
        optimization_usage: Dict[str, int]
    ) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        # Check optimization adoption
        total_queries = len(metrics)
        optimized_percentage = (optimization_usage["optimized_queries"] / total_queries) * 100
        
        if optimized_percentage < 70:
            recommendations.append(
                f"Only {optimized_percentage:.1f}% of queries are using optimizations. "
                "Consider updating remaining services to use phase_id architecture."
            )
        
        # Check slow query percentage
        slow_percentage = (optimization_usage["slow_queries"] / total_queries) * 100
        if slow_percentage > 10:
            recommendations.append(
                f"{slow_percentage:.1f}% of queries are slow (>{self.slow_query_threshold_ms}ms). "
                "Review slow queries for optimization opportunities."
            )
        
        # Check phase_id usage
        phase_id_percentage = (optimization_usage["phase_id_queries"] / total_queries) * 100
        if phase_id_percentage < 50:
            recommendations.append(
                f"Only {phase_id_percentage:.1f}% of queries use phase_id optimization. "
                "Migrate more queries to use direct phase_id lookups."
            )
        
        # Average response time recommendations
        avg_time = sum(m.execution_time_ms for m in metrics) / len(metrics)
        if avg_time > 500:
            recommendations.append(
                f"Average query time is {avg_time:.1f}ms. Consider adding database indexes "
                "or implementing query result caching."
            )
        
        return recommendations
    
    async def analyze_database_performance(self, db: AsyncSession) -> Dict[str, Any]:
        """Analyze database-level performance metrics"""
        
        try:
            # Get query statistics from PostgreSQL
            query_stats = await db.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE query LIKE '%WorkflowPhase%' OR query LIKE '%CycleReport%'
                ORDER BY mean_time DESC 
                LIMIT 20;
            """))
            
            stats_results = query_stats.fetchall()
            
            # Get table sizes
            table_sizes = await db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                AND (tablename LIKE '%workflow%' OR tablename LIKE '%cycle%' OR tablename LIKE '%report%')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """))
            
            size_results = table_sizes.fetchall()
            
            # Get index usage
            index_usage = await db.execute(text("""
                SELECT 
                    indexrelname as index_name,
                    relname as table_name,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes 
                WHERE relname IN ('workflow_phases', 'cycle_reports', 'reports')
                ORDER BY idx_scan DESC;
            """))
            
            index_results = index_usage.fetchall()
            
            return {
                "query_statistics": [dict(row) for row in stats_results],
                "table_sizes": [dict(row) for row in size_results],
                "index_usage": [dict(row) for row in index_results],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing database performance: {str(e)}")
            return {
                "error": str(e),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    def reset_metrics(self):
        """Reset all collected metrics"""
        self.query_metrics.clear()
        self.session_metrics.clear()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics for external analysis"""
        
        report = self.get_performance_report()
        
        if format == "json":
            import json
            return json.dumps({
                "performance_report": {
                    "total_queries": report.total_queries,
                    "avg_execution_time_ms": report.avg_execution_time_ms,
                    "optimization_usage": report.optimization_usage,
                    "recommendations": report.recommendations
                },
                "export_timestamp": datetime.utcnow().isoformat()
            }, indent=2)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                "query_id", "query_type", "execution_time_ms", 
                "optimization_used", "phase_id_used", "timestamp"
            ])
            
            # Write metrics
            for metric in self.query_metrics:
                writer.writerow([
                    metric.query_id,
                    metric.query_type,
                    metric.execution_time_ms,
                    metric.optimization_used,
                    metric.phase_id_used,
                    metric.timestamp.isoformat()
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global monitoring instance
query_monitor = QueryPerformanceMonitor()

# Decorator for monitoring service methods
def monitor_query_performance(
    query_id: str = None,
    optimization_used: bool = False,
    phase_id_used: bool = False
):
    """Decorator to monitor query performance for service methods"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            actual_query_id = query_id or f"{func.__module__}.{func.__name__}"
            
            async with query_monitor.monitor_query(
                actual_query_id,
                optimization_used=optimization_used,
                phase_id_used=phase_id_used
            ):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Factory function
def get_query_monitor() -> QueryPerformanceMonitor:
    """Get the global query performance monitor instance"""
    return query_monitor
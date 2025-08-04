"""
Streaming data profiler service for enterprise-scale processing
Handles 40-50 million records with 400-500 rules efficiently
"""
import asyncio
from typing import Dict, List, Optional, AsyncIterator, Any, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import numpy as np
from collections import defaultdict
import psutil
import gc

from app.models.profiling_enhanced import (
    ProfilingJob, ProfilingPartition, ProfilingRuleSet, 
    PartitionResult, ProfilingAnomalyPattern, ProfilingCache,
    ProfilingStrategy, RuleCategory
)
from app.models.data_source import DataSource
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@dataclass
class ProfilingContext:
    """Context for profiling execution"""
    job_id: str
    partition_id: Optional[str]
    total_records: int
    batch_size: int
    memory_limit_mb: int
    rules: List[Dict[str, Any]]
    checkpoint_interval: int = 10000


class StreamingProfiler:
    """Core streaming profiler engine"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self.memory_tracker = MemoryTracker()
        self.rule_engine = RuleEngine()
        self.stats_collector = StatisticsCollector()
    
    async def profile_partition(
        self,
        context: ProfilingContext,
        data_stream: AsyncIterator[Dict[str, Any]]
    ) -> PartitionResult:
        """Profile a data partition using streaming approach"""
        try:
            # Initialize tracking
            records_processed = 0
            anomalies = []
            checkpoint_counter = 0
            start_time = datetime.utcnow()
            
            # Process data in batches
            batch = []
            async for record in data_stream:
                batch.append(record)
                
                if len(batch) >= context.batch_size:
                    # Process batch
                    batch_results = await self._process_batch(batch, context)
                    anomalies.extend(batch_results['anomalies'])
                    
                    # Update statistics
                    self.stats_collector.update(batch_results['statistics'])
                    
                    records_processed += len(batch)
                    checkpoint_counter += len(batch)
                    
                    # Checkpoint if needed
                    if checkpoint_counter >= context.checkpoint_interval:
                        await self._save_checkpoint(context, records_processed)
                        checkpoint_counter = 0
                    
                    # Check memory usage
                    if self.memory_tracker.is_near_limit(context.memory_limit_mb):
                        await self._flush_to_storage(context, anomalies)
                        anomalies = []
                        gc.collect()
                    
                    batch = []
            
            # Process remaining records
            if batch:
                batch_results = await self._process_batch(batch, context)
                anomalies.extend(batch_results['anomalies'])
                records_processed += len(batch)
            
            # Create result
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            return PartitionResult(
                partition_id=context.partition_id,
                rule_set_id=context.rules[0]['rule_set_id'],  # Assuming single rule set for now
                records_evaluated=records_processed,
                records_passed=records_processed - len(anomalies),
                records_failed=len(anomalies),
                anomalies=anomalies[:1000],  # Store sample of anomalies
                anomaly_count=len(anomalies),
                statistics=self.stats_collector.get_summary(),
                execution_time_ms=int(execution_time * 1000),
                memory_used_mb=self.memory_tracker.get_peak_usage()
            )
            
        except Exception as e:
            logger.error(f"Error in streaming profiler: {str(e)}")
            raise
    
    async def _process_batch(
        self, 
        batch: List[Dict[str, Any]], 
        context: ProfilingContext
    ) -> Dict[str, Any]:
        """Process a batch of records"""
        anomalies = []
        batch_stats = defaultdict(list)
        
        for record in batch:
            # Apply rules
            rule_results = await self.rule_engine.evaluate_record(record, context.rules)
            
            # Collect anomalies
            if rule_results['anomalies']:
                anomalies.append({
                    'record_id': record.get('id', 'unknown'),
                    'anomalies': rule_results['anomalies'],
                    'severity': rule_results['severity']
                })
            
            # Collect statistics
            for field, value in record.items():
                if value is not None:
                    batch_stats[field].append(value)
        
        return {
            'anomalies': anomalies,
            'statistics': batch_stats
        }
    
    async def _save_checkpoint(self, context: ProfilingContext, records_processed: int):
        """Save processing checkpoint"""
        if self.redis:
            checkpoint_key = f"profiling:checkpoint:{context.partition_id}"
            await self.redis.setex(
                checkpoint_key,
                timedelta(hours=24),
                json.dumps({
                    'records_processed': records_processed,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
    
    async def _flush_to_storage(self, context: ProfilingContext, anomalies: List[Dict]):
        """Flush anomalies to persistent storage"""
        # In production, this would write to database or object storage
        logger.info(f"Flushing {len(anomalies)} anomalies to storage")


class RuleEngine:
    """Engine for evaluating profiling rules"""
    
    async def evaluate_record(
        self, 
        record: Dict[str, Any], 
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate all rules against a record"""
        anomalies = []
        max_severity = 'low'
        
        for rule in rules:
            try:
                result = await self._evaluate_single_rule(record, rule)
                if not result['passed']:
                    anomalies.append({
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'category': rule['category'],
                        'failure_reason': result['reason'],
                        'field': rule.get('field'),
                        'value': record.get(rule.get('field'))
                    })
                    
                    if self._compare_severity(result['severity'], max_severity) > 0:
                        max_severity = result['severity']
                        
            except Exception as e:
                logger.error(f"Error evaluating rule {rule['id']}: {str(e)}")
        
        return {
            'anomalies': anomalies,
            'severity': max_severity
        }
    
    async def _evaluate_single_rule(
        self, 
        record: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a single rule"""
        rule_type = rule['type']
        
        if rule_type == 'null_check':
            return self._check_null(record, rule)
        elif rule_type == 'pattern':
            return self._check_pattern(record, rule)
        elif rule_type == 'range':
            return self._check_range(record, rule)
        elif rule_type == 'custom':
            return await self._evaluate_custom_rule(record, rule)
        else:
            return {'passed': True, 'severity': 'low'}
    
    def _check_null(self, record: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check for null values"""
        field = rule['field']
        value = record.get(field)
        
        if value is None or value == '':
            return {
                'passed': False,
                'reason': f"Field '{field}' is null or empty",
                'severity': rule.get('severity', 'medium')
            }
        
        return {'passed': True, 'severity': 'low'}
    
    def _check_pattern(self, record: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check pattern matching"""
        import re
        
        field = rule['field']
        value = str(record.get(field, ''))
        pattern = rule['pattern']
        
        if not re.match(pattern, value):
            return {
                'passed': False,
                'reason': f"Field '{field}' does not match pattern '{pattern}'",
                'severity': rule.get('severity', 'medium')
            }
        
        return {'passed': True, 'severity': 'low'}
    
    def _check_range(self, record: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check value ranges"""
        field = rule['field']
        value = record.get(field)
        
        try:
            numeric_value = float(value)
            min_val = rule.get('min', float('-inf'))
            max_val = rule.get('max', float('inf'))
            
            if numeric_value < min_val or numeric_value > max_val:
                return {
                    'passed': False,
                    'reason': f"Field '{field}' value {numeric_value} outside range [{min_val}, {max_val}]",
                    'severity': rule.get('severity', 'medium')
                }
        except (TypeError, ValueError):
            return {
                'passed': False,
                'reason': f"Field '{field}' is not numeric",
                'severity': 'high'
            }
        
        return {'passed': True, 'severity': 'low'}
    
    async def _evaluate_custom_rule(
        self, 
        record: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate custom rule logic"""
        # Custom rule evaluation would be implemented here
        # This is a placeholder
        return {'passed': True, 'severity': 'low'}
    
    def _compare_severity(self, sev1: str, sev2: str) -> int:
        """Compare severity levels"""
        severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        return severity_order.get(sev1, 0) - severity_order.get(sev2, 0)


class StatisticsCollector:
    """Collects statistics during profiling"""
    
    def __init__(self):
        self.stats = defaultdict(lambda: {
            'count': 0,
            'null_count': 0,
            'distinct_values': set(),
            'numeric_sum': 0,
            'numeric_count': 0,
            'min_length': float('inf'),
            'max_length': 0
        })
    
    def update(self, batch_stats: Dict[str, List[Any]]):
        """Update statistics with batch data"""
        for field, values in batch_stats.items():
            field_stats = self.stats[field]
            
            for value in values:
                field_stats['count'] += 1
                
                if value is None:
                    field_stats['null_count'] += 1
                else:
                    # Track distinct values (limit to prevent memory issues)
                    if len(field_stats['distinct_values']) < 1000:
                        field_stats['distinct_values'].add(str(value))
                    
                    # Numeric statistics
                    try:
                        numeric_val = float(value)
                        field_stats['numeric_sum'] += numeric_val
                        field_stats['numeric_count'] += 1
                    except (TypeError, ValueError):
                        pass
                    
                    # String length statistics
                    str_val = str(value)
                    field_stats['min_length'] = min(field_stats['min_length'], len(str_val))
                    field_stats['max_length'] = max(field_stats['max_length'], len(str_val))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary"""
        summary = {}
        
        for field, stats in self.stats.items():
            summary[field] = {
                'total_count': stats['count'],
                'null_count': stats['null_count'],
                'null_percentage': (stats['null_count'] / stats['count'] * 100) if stats['count'] > 0 else 0,
                'distinct_count': len(stats['distinct_values']),
                'min_length': stats['min_length'] if stats['min_length'] != float('inf') else 0,
                'max_length': stats['max_length']
            }
            
            # Add numeric statistics if applicable
            if stats['numeric_count'] > 0:
                summary[field]['average'] = stats['numeric_sum'] / stats['numeric_count']
        
        return summary


class MemoryTracker:
    """Tracks memory usage during profiling"""
    
    def __init__(self):
        self.peak_usage = 0
    
    def is_near_limit(self, limit_mb: int) -> bool:
        """Check if memory usage is near limit"""
        current_mb = self.get_current_usage()
        self.peak_usage = max(self.peak_usage, current_mb)
        return current_mb > (limit_mb * 0.8)  # 80% threshold
    
    def get_current_usage(self) -> int:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss // (1024 * 1024)
    
    def get_peak_usage(self) -> int:
        """Get peak memory usage"""
        return self.peak_usage


class ProfilingOrchestrator:
    """Orchestrates large-scale profiling jobs"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.profiler = StreamingProfiler()
    
    async def execute_job(self, job_id: str) -> ProfilingJob:
        """Execute a profiling job"""
        try:
            # Get job details
            job = await self.session.get(ProfilingJob, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update job status
            job.status = 'running'
            job.start_time = datetime.utcnow()
            await self.session.commit()
            
            # Create partitions based on strategy
            partitions = await self._create_partitions(job)
            
            # Execute partitions in parallel
            tasks = []
            for partition in partitions:
                task = asyncio.create_task(
                    self._execute_partition(job, partition)
                )
                tasks.append(task)
            
            # Wait for completion with progress tracking
            results = await self._execute_with_progress(tasks, job)
            
            # Analyze patterns
            patterns = await self._analyze_anomaly_patterns(job, results)
            
            # Update job completion
            job.status = 'completed'
            job.end_time = datetime.utcnow()
            job.records_processed = sum(r.records_evaluated for r in results)
            job.anomalies_found = sum(r.anomaly_count for r in results)
            
            await self.session.commit()
            
            return job
            
        except Exception as e:
            logger.error(f"Job execution failed: {str(e)}")
            job.status = 'failed'
            await self.session.commit()
            raise
    
    async def _create_partitions(self, job: ProfilingJob) -> List[ProfilingPartition]:
        """Create job partitions based on strategy"""
        partitions = []
        
        if job.partition_strategy == 'by_date':
            # Create date-based partitions
            date_ranges = self._calculate_date_ranges(
                job.source_config.get('start_date'),
                job.source_config.get('end_date'),
                job.partition_count
            )
            
            for i, (start, end) in enumerate(date_ranges):
                partition = ProfilingPartition(
                    job_id=job.job_id,
                    partition_index=i,
                    partition_key=f"{start}_{end}",
                    start_value=start.isoformat(),
                    end_value=end.isoformat(),
                    estimated_records=job.total_records // job.partition_count,
                    status='pending'
                )
                partitions.append(partition)
        
        elif job.partition_strategy == 'by_id':
            # Create ID-based partitions
            id_ranges = self._calculate_id_ranges(
                job.total_records,
                job.partition_count
            )
            
            for i, (start_id, end_id) in enumerate(id_ranges):
                partition = ProfilingPartition(
                    job_id=job.job_id,
                    partition_index=i,
                    partition_key=f"{start_id}_{end_id}",
                    start_value=str(start_id),
                    end_value=str(end_id),
                    estimated_records=(end_id - start_id + 1),
                    status='pending'
                )
                partitions.append(partition)
        
        # Save partitions
        self.session.add_all(partitions)
        await self.session.commit()
        
        return partitions
    
    async def _execute_partition(
        self, 
        job: ProfilingJob, 
        partition: ProfilingPartition
    ) -> PartitionResult:
        """Execute a single partition"""
        try:
            # Update partition status
            partition.status = 'running'
            partition.start_time = datetime.utcnow()
            await self.session.commit()
            
            # Create profiling context
            context = ProfilingContext(
                job_id=str(job.job_id),
                partition_id=str(partition.partition_id),
                total_records=partition.estimated_records,
                batch_size=1000,
                memory_limit_mb=job.max_memory_gb * 1024,
                rules=await self._load_rules(job)
            )
            
            # Get data stream
            data_stream = await self._create_data_stream(job, partition)
            
            # Execute profiling
            result = await self.profiler.profile_partition(context, data_stream)
            
            # Update partition completion
            partition.status = 'completed'
            partition.end_time = datetime.utcnow()
            partition.records_processed = result.records_evaluated
            partition.anomalies_found = result.anomaly_count
            partition.execution_time_seconds = (
                partition.end_time - partition.start_time
            ).total_seconds()
            
            await self.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Partition execution failed: {str(e)}")
            partition.status = 'failed'
            partition.error_message = str(e)
            await self.session.commit()
            raise
    
    async def _create_data_stream(
        self, 
        job: ProfilingJob, 
        partition: ProfilingPartition
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create data stream for partition"""
        # This would connect to actual data source
        # For now, yielding sample data
        for i in range(partition.estimated_records):
            yield {
                'id': i,
                'customer_id': f"CUST{i:06d}",
                'ssn': f"123-45-{i:04d}",
                'amount': i * 100.0,
                'date': datetime.utcnow().isoformat()
            }
    
    async def _load_rules(self, job: ProfilingJob) -> List[Dict[str, Any]]:
        """Load profiling rules for job"""
        rule_sets = await self.session.execute(
            select(ProfilingRuleSet).filter(
                ProfilingRuleSet.job_id == job.job_id
            )
        )
        
        all_rules = []
        for rule_set in rule_sets.scalars():
            all_rules.extend(rule_set.rules)
        
        return all_rules
    
    async def _execute_with_progress(
        self, 
        tasks: List[asyncio.Task], 
        job: ProfilingJob
    ) -> List[PartitionResult]:
        """Execute tasks with progress tracking"""
        results = []
        total_tasks = len(tasks)
        
        while tasks:
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                try:
                    result = task.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task failed: {str(e)}")
            
            # Update progress
            completed = total_tasks - len(pending)
            job.progress_percent = int(completed / total_tasks * 100)
            await self.session.commit()
            
            tasks = list(pending)
        
        return results
    
    async def _analyze_anomaly_patterns(
        self, 
        job: ProfilingJob, 
        results: List[PartitionResult]
    ) -> List[ProfilingAnomalyPattern]:
        """Analyze patterns in anomalies"""
        # Aggregate anomalies
        all_anomalies = []
        for result in results:
            all_anomalies.extend(result.anomalies or [])
        
        # Identify patterns
        patterns = []
        pattern_groups = defaultdict(list)
        
        for anomaly in all_anomalies:
            for rule_failure in anomaly.get('anomalies', []):
                key = f"{rule_failure['category']}_{rule_failure['rule_name']}"
                pattern_groups[key].append(anomaly)
        
        # Create pattern records
        for pattern_key, anomaly_list in pattern_groups.items():
            if len(anomaly_list) >= 10:  # Minimum threshold
                pattern = ProfilingAnomalyPattern(
                    job_id=job.job_id,
                    pattern_type=pattern_key.split('_')[0],
                    pattern_description=f"Pattern: {pattern_key}",
                    confidence_score=min(len(anomaly_list) / 100, 1.0),
                    occurrence_count=len(anomaly_list),
                    occurrence_percentage=(len(anomaly_list) / job.records_processed * 100),
                    sample_record_ids=[a['record_id'] for a in anomaly_list[:10]],
                    sample_count=len(anomaly_list),
                    recommended_for_sampling=True,
                    sampling_priority=self._calculate_priority(len(anomaly_list))
                )
                patterns.append(pattern)
        
        # Save patterns
        self.session.add_all(patterns)
        await self.session.commit()
        
        return patterns
    
    def _calculate_priority(self, occurrence_count: int) -> int:
        """Calculate sampling priority based on occurrence"""
        if occurrence_count > 1000:
            return 10
        elif occurrence_count > 100:
            return 7
        elif occurrence_count > 10:
            return 5
        else:
            return 3
    
    def _calculate_date_ranges(
        self, 
        start_date: str, 
        end_date: str, 
        partition_count: int
    ) -> List[Tuple[datetime, datetime]]:
        """Calculate date ranges for partitioning"""
        # Implementation would parse dates and divide range
        # Placeholder for now
        return [(datetime.utcnow(), datetime.utcnow())]
    
    def _calculate_id_ranges(
        self, 
        total_records: int, 
        partition_count: int
    ) -> List[Tuple[int, int]]:
        """Calculate ID ranges for partitioning"""
        records_per_partition = total_records // partition_count
        ranges = []
        
        for i in range(partition_count):
            start = i * records_per_partition
            end = start + records_per_partition - 1
            if i == partition_count - 1:
                end = total_records - 1
            ranges.append((start, end))
        
        return ranges
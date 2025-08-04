"""
Intelligent Data Sampling Service
Implements smart sample selection based on data characteristics
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_, func, case
from app.models.workflow import WorkflowPhase
from app.models.sample_selection import SampleSelectionVersion
from app.services.sample_selection_table_service import SampleSelectionTableService
from app.core.logging import get_logger
from app.core.exceptions import BusinessLogicError
from app.core.background_jobs import job_manager

logger = get_logger(__name__)


class IntelligentDataSamplingService:
    """Service for intelligent sample generation from data sources"""
    
    def __init__(self):
        self.table_service = SampleSelectionTableService()
    
    async def generate_intelligent_samples(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        phase_id: int,
        target_attribute: str,
        target_sample_size: int,
        scoped_attributes: List[Dict[str, Any]],
        data_source_config: Dict[str, Any],
        pde_mappings: Dict[str, str],
        distribution: Dict[str, float],
        profiling_rules: Optional[List[Any]] = None,
        job_id: Optional[str] = None,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate intelligent samples focusing on a specific target attribute"""
        
        samples_created = []
        
        try:
            # Parse profiling rules for this attribute
            attribute_rules = []
            regulatory_limits = None
            if profiling_rules:
                # Get attribute ID for matching rules
                target_attr_id = None
                for attr in scoped_attributes:
                    if attr.get('attribute_name') == target_attribute:
                        target_attr_id = attr.get('attribute_id')
                        break
                
                for rule in profiling_rules:
                    # Match by attribute_id or attribute_name
                    if (hasattr(rule, 'attribute_id') and rule.attribute_id == target_attr_id) or \
                       (hasattr(rule, 'attribute_name') and rule.attribute_name == target_attribute):
                        attribute_rules.append(rule)
                        # Check for regulatory limits
                        if hasattr(rule, 'rule_type') and str(rule.rule_type).upper() in ['REGULATORY', 'REGULARITY'] and rule.rule_parameters:
                            params = rule.rule_parameters
                            if 'min_value' in params or 'max_value' in params:
                                regulatory_limits = {
                                    'min': params.get('min_value'),
                                    'max': params.get('max_value'),
                                    'rule_name': rule.rule_name,
                                    'rule_id': str(rule.rule_id)
                                }
                logger.info(f"Found {len(attribute_rules)} profiling rules for {target_attribute}")
                if regulatory_limits:
                    logger.info(f"Using regulatory limits: min={regulatory_limits['min']}, max={regulatory_limits['max']}")
            # Get database configuration
            criteria = data_source_config.get('criteria', {})
            table_name = criteria.get('table_name')
            schema_name = criteria.get('schema_name', 'public')
            
            if not table_name:
                raise BusinessLogicError("Table name not specified")
            
            # Get target attribute column name
            target_column = pde_mappings.get(target_attribute, target_attribute)
            
            # Get all column names
            columns = []
            column_to_attr = {}
            for attr in scoped_attributes:
                attr_name = attr['attribute_name']
                column_name = pde_mappings.get(attr_name, attr_name)
                columns.append(column_name)
                column_to_attr[column_name] = attr_name
            
            # Calculate samples per category
            samples_per_category = {
                'clean': int(target_sample_size * distribution.get('clean', 0.3)),
                'anomaly': int(target_sample_size * distribution.get('anomaly', 0.5)),
                'boundary': int(target_sample_size * distribution.get('boundary', 0.2))
            }
            
            # Ensure exact count
            total_planned = sum(samples_per_category.values())
            if total_planned < target_sample_size:
                samples_per_category['anomaly'] += target_sample_size - total_planned
            
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Analyzing data distribution",
                    progress_percentage=30
                )
            
            # 1. Analyze target attribute distribution with advanced statistics
            stats_query = f"""
                WITH value_counts AS (
                    SELECT 
                        "{target_column}" as value,
                        COUNT(*) as frequency,
                        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {schema_name}.{table_name}) as frequency_pct
                    FROM {schema_name}.{table_name}
                    GROUP BY "{target_column}"
                ),
                numeric_stats AS (
                    SELECT 
                        MIN(CAST("{target_column}" AS NUMERIC)) as min_val,
                        MAX(CAST("{target_column}" AS NUMERIC)) as max_val,
                        AVG(CAST("{target_column}" AS NUMERIC)) as avg_val,
                        STDDEV(CAST("{target_column}" AS NUMERIC)) as stddev_val,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY CAST("{target_column}" AS NUMERIC)) as q1,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST("{target_column}" AS NUMERIC)) as median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY CAST("{target_column}" AS NUMERIC)) as q3,
                        COUNT(*) as total_count,
                        COUNT(DISTINCT "{target_column}") as distinct_count,
                        COUNT("{target_column}") as non_null_count
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" IS NOT NULL
                ),
                frequency_stats AS (
                    SELECT 
                        MAX(frequency) as max_frequency,
                        MIN(frequency) as min_frequency,
                        AVG(frequency) as avg_frequency,
                        STDDEV(frequency) as stddev_frequency,
                        MAX(frequency_pct) as max_frequency_pct,
                        MIN(frequency_pct) as min_frequency_pct
                    FROM value_counts
                    WHERE value IS NOT NULL
                ),
                high_frequency_values AS (
                    SELECT value, frequency, frequency_pct
                    FROM value_counts
                    WHERE frequency > (SELECT avg_frequency + 2 * stddev_frequency FROM frequency_stats)
                    ORDER BY frequency DESC
                    LIMIT 5
                ),
                low_frequency_values AS (
                    SELECT value, frequency, frequency_pct
                    FROM value_counts
                    WHERE frequency <= 2 AND value IS NOT NULL
                    ORDER BY value
                    LIMIT 5
                )
                SELECT 
                    ns.*,
                    fs.max_frequency,
                    fs.min_frequency,
                    fs.avg_frequency,
                    fs.stddev_frequency,
                    fs.max_frequency_pct,
                    (SELECT COUNT(*) FROM {schema_name}.{table_name} WHERE "{target_column}" IS NULL) as null_count,
                    (SELECT json_agg(row_to_json(hf)) FROM high_frequency_values hf) as high_freq_values,
                    (SELECT json_agg(row_to_json(lf)) FROM low_frequency_values lf) as low_freq_values
                FROM numeric_stats ns, frequency_stats fs
            """
            
            stats_result = await db.execute(text(stats_query))
            stats = stats_result.fetchone()
            
            if not stats:
                raise BusinessLogicError("Unable to analyze data distribution")
            
            min_val = float(stats.min_val) if stats.min_val else 0
            max_val = float(stats.max_val) if stats.max_val else 0
            avg_val = float(stats.avg_val) if stats.avg_val else 0
            stddev_val = float(stats.stddev_val) if stats.stddev_val else 0
            q1 = float(stats.q1) if stats.q1 else 0
            median = float(stats.median) if stats.median else 0
            q3 = float(stats.q3) if stats.q3 else 0
            iqr = q3 - q1  # Interquartile range
            max_frequency = int(stats.max_frequency) if stats.max_frequency else 0
            avg_frequency = float(stats.avg_frequency) if stats.avg_frequency else 0
            stddev_frequency = float(stats.stddev_frequency) if stats.stddev_frequency else 0
            max_frequency_pct = float(stats.max_frequency_pct) if stats.max_frequency_pct else 0
            null_count = int(stats.null_count) if stats.null_count else 0
            distinct_count = int(stats.distinct_count) if stats.distinct_count else 0
            high_freq_values = stats.high_freq_values if stats.high_freq_values else []
            low_freq_values = stats.low_freq_values if stats.low_freq_values else []
            
            logger.info(f"Data stats for {target_attribute}: min={min_val}, max={max_val}, median={median}, IQR={iqr}, distinct={distinct_count}")
            logger.info(f"Frequency stats: max_freq={max_frequency} ({max_frequency_pct:.1f}%), avg_freq={avg_frequency:.1f}, stddev={stddev_frequency:.1f}")
            if high_freq_values:
                logger.info(f"High frequency values detected: {len(high_freq_values)} values appear unusually often")
            if low_freq_values:
                logger.info(f"Low frequency values detected: {len(low_freq_values)} rare values")
            
            # Track selected values to avoid duplicates
            selected_values = set()
            
            # 2. Generate BOUNDARY samples
            if samples_per_category['boundary'] > 0:
                if job_id:
                    job_manager.update_job_progress(
                        job_id,
                        current_step="Selecting boundary samples",
                        progress_percentage=40
                    )
                
                boundary_samples = []
                
                # If we have regulatory limits, prioritize those
                if regulatory_limits:
                    # Get sample closest to regulatory minimum
                    if regulatory_limits['min'] is not None:
                        reg_min_query = f"""
                            SELECT {', '.join([f'"{col}"' for col in columns])},
                                   ABS(CAST("{target_column}" AS NUMERIC) - {regulatory_limits['min']}) as distance
                            FROM {schema_name}.{table_name}
                            WHERE "{target_column}" IS NOT NULL
                            ORDER BY distance
                            LIMIT 1
                        """
                        reg_min_result = await db.execute(text(reg_min_query))
                        reg_min_row = reg_min_result.fetchone()
                        
                        if reg_min_row:
                            actual_val = reg_min_row[columns.index(target_column)]
                            boundary_samples.append((
                                reg_min_row[:len(columns)], 
                                f"Regulatory minimum boundary for {target_attribute}: {actual_val} (regulatory limit: {regulatory_limits['min']})"
                            ))
                    
                    # Get sample closest to regulatory maximum
                    if regulatory_limits['max'] is not None:
                        reg_max_query = f"""
                            SELECT {', '.join([f'"{col}"' for col in columns])},
                                   ABS(CAST("{target_column}" AS NUMERIC) - {regulatory_limits['max']}) as distance
                            FROM {schema_name}.{table_name}
                            WHERE "{target_column}" IS NOT NULL
                            ORDER BY distance
                            LIMIT 1
                        """
                        reg_max_result = await db.execute(text(reg_max_query))
                        reg_max_row = reg_max_result.fetchone()
                        
                        if reg_max_row:
                            actual_val = reg_max_row[columns.index(target_column)]
                            boundary_samples.append((
                                reg_max_row[:len(columns)], 
                                f"Regulatory maximum boundary for {target_attribute}: {actual_val} (regulatory limit: {regulatory_limits['max']})"
                            ))
                
                # Always include actual data boundaries
                # Get minimum value sample
                min_query = f"""
                    SELECT {', '.join([f'"{col}"' for col in columns])}
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" = (
                        SELECT MIN(CAST("{target_column}" AS NUMERIC))
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NOT NULL
                    )
                    LIMIT 1
                """
                min_result = await db.execute(text(min_query))
                min_row = min_result.fetchone()
                
                if min_row:
                    boundary_samples.append((min_row, f"Minimum value for {target_attribute}: {min_val}"))
                
                # Get maximum value sample
                max_query = f"""
                    SELECT {', '.join([f'"{col}"' for col in columns])}
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" = (
                        SELECT MAX(CAST("{target_column}" AS NUMERIC))
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NOT NULL
                    )
                    LIMIT 1
                """
                max_result = await db.execute(text(max_query))
                max_row = max_result.fetchone()
                
                if max_row:
                    boundary_samples.append((max_row, f"Maximum value for {target_attribute}: {max_val}"))
                
                # Add boundary samples
                for row, rationale in boundary_samples[:samples_per_category['boundary']]:
                    sample = self._create_sample_from_row(
                        row, columns, column_to_attr, scoped_attributes,
                        'boundary', rationale, schema_name, table_name, target_attribute
                    )
                    if sample['data_row_snapshot'].get(target_attribute) not in selected_values:
                        samples_created.append(sample)
                        selected_values.add(sample['data_row_snapshot'].get(target_attribute))
            
            # 3. Generate ANOMALY samples
            if samples_per_category['anomaly'] > 0:
                if job_id:
                    job_manager.update_job_progress(
                        job_id,
                        current_step="Identifying anomalies",
                        progress_percentage=60
                    )
                
                anomaly_samples = []
                anomaly_quota = samples_per_category['anomaly']
                
                # Allocate anomaly types
                null_quota = min(null_count, anomaly_quota // 4) if null_count > 0 else 0
                high_freq_quota = min(len(high_freq_values), anomaly_quota // 4) if high_freq_values else 0
                low_freq_quota = min(len(low_freq_values), anomaly_quota // 4) if low_freq_values else 0
                outlier_quota = anomaly_quota - null_quota - high_freq_quota - low_freq_quota
                
                # 1. NULL values
                if null_quota > 0:
                    null_query = f"""
                        SELECT {', '.join([f'"{col}"' for col in columns])}
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NULL
                        LIMIT {null_quota}
                    """
                    null_result = await db.execute(text(null_query))
                    null_rows = null_result.fetchall()
                    
                    for row in null_rows:
                        anomaly_samples.append((row, f"NULL value for {target_attribute} - missing required data"))
                
                # 2. High frequency values (appear too many times)
                if high_freq_quota > 0 and high_freq_values:
                    for idx, hf_val in enumerate(high_freq_values[:high_freq_quota]):
                        val = hf_val.get('value')
                        freq = hf_val.get('frequency', 0)
                        freq_pct = hf_val.get('frequency_pct', 0)
                        
                        hf_query = f"""
                            SELECT {', '.join([f'"{col}"' for col in columns])}
                            FROM {schema_name}.{table_name}
                            WHERE "{target_column}" = '{val}'
                            LIMIT 1
                        """
                        hf_result = await db.execute(text(hf_query))
                        hf_row = hf_result.fetchone()
                        
                        if hf_row:
                            rationale = f"High frequency anomaly: {target_attribute} value '{val}' appears {freq} times ({freq_pct:.1f}% of data) - significantly above normal"
                            anomaly_samples.append((hf_row, rationale))
                
                # 3. Low frequency values (rare occurrences)
                if low_freq_quota > 0 and low_freq_values:
                    for idx, lf_val in enumerate(low_freq_values[:low_freq_quota]):
                        val = lf_val.get('value')
                        freq = lf_val.get('frequency', 0)
                        
                        lf_query = f"""
                            SELECT {', '.join([f'"{col}"' for col in columns])}
                            FROM {schema_name}.{table_name}
                            WHERE "{target_column}" = '{val}'
                            LIMIT 1
                        """
                        lf_result = await db.execute(text(lf_query))
                        lf_row = lf_result.fetchone()
                        
                        if lf_row:
                            rationale = f"Rare value anomaly: {target_attribute} value '{val}' appears only {freq} time(s) - unusual occurrence"
                            anomaly_samples.append((lf_row, rationale))
                
                # 4. DQ rule violators (samples that would fail profiling rules)
                # Prioritize rules with low pass rates as they indicate issues
                rules_by_failure = sorted([r for r in attribute_rules if hasattr(r, 'pass_rate')], 
                                        key=lambda x: x.pass_rate or 100)
                
                dq_violator_quota = min(outlier_quota // 2, len(rules_by_failure)) if rules_by_failure else 0
                
                if dq_violator_quota > 0 and rules_by_failure:
                    for rule_idx, rule in enumerate(rules_by_failure[:dq_violator_quota]):
                        # Log rule with low pass rate
                        logger.info(f"Checking DQ rule '{rule.rule_name}' with pass rate {rule.pass_rate}%")
                        
                        # Check if we have failed records from the profiling result
                        if hasattr(rule, 'result_summary') and rule.result_summary:
                            summary = rule.result_summary
                            if isinstance(summary, dict) and 'failed_values' in summary:
                                # Use actual failed values from profiling
                                failed_vals = summary['failed_values'][:1]  # Get first failed value
                                for failed_val in failed_vals:
                                    failed_query = f"""
                                        SELECT {', '.join([f'"{col}"' for col in columns])}
                                        FROM {schema_name}.{table_name}
                                        WHERE "{target_column}" = '{failed_val}'
                                        LIMIT 1
                                    """
                                    try:
                                        failed_result = await db.execute(text(failed_query))
                                        failed_row = failed_result.fetchone()
                                        if failed_row:
                                            anomaly_samples.append((
                                                failed_row,
                                                f"DQ rule failure: {target_attribute} value '{failed_val}' failed {rule.rule_name} (pass rate: {rule.pass_rate}%)",
                                                str(rule.rule_id)
                                            ))
                                    except Exception as e:
                                        logger.warning(f"Could not fetch failed value: {str(e)}")
                        
                        # Parse rule to find violations
                        elif hasattr(rule, 'rule_parameters') and rule.rule_parameters:
                            params = rule.rule_parameters
                            
                            # Check for validity rules with patterns
                            if rule.rule_type == 'validity' and 'pattern' in params:
                                pattern = params['pattern']
                                # Find values that don't match the pattern
                                violator_query = f"""
                                    SELECT {', '.join([f'"{col}"' for col in columns])}
                                    FROM {schema_name}.{table_name}
                                    WHERE "{target_column}" IS NOT NULL
                                    AND "{target_column}"::text NOT SIMILAR TO '{pattern}'
                                    AND "{target_column}" NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                                    LIMIT 1
                                """
                                try:
                                    violator_result = await db.execute(text(violator_query))
                                    violator_row = violator_result.fetchone()
                                    if violator_row:
                                        val = violator_row[columns.index(target_column)]
                                        anomaly_samples.append((
                                            violator_row,
                                            f"DQ rule violation: {target_attribute} value '{val}' fails {rule.rule_name} (pattern validation)",
                                            str(rule.rule_id)
                                        ))
                                except Exception as e:
                                    logger.warning(f"Could not check pattern rule: {str(e)}")
                            
                            # Check for range rules
                            elif 'min_value' in params or 'max_value' in params:
                                conditions = []
                                if 'min_value' in params:
                                    conditions.append(f"CAST(\"{target_column}\" AS NUMERIC) < {params['min_value']}")
                                if 'max_value' in params:
                                    conditions.append(f"CAST(\"{target_column}\" AS NUMERIC) > {params['max_value']}")
                                
                                if conditions:
                                    violator_query = f"""
                                        SELECT {', '.join([f'"{col}"' for col in columns])}
                                        FROM {schema_name}.{table_name}
                                        WHERE "{target_column}" IS NOT NULL
                                        AND ({' OR '.join(conditions)})
                                        AND "{target_column}" NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                                        LIMIT 1
                                    """
                                    try:
                                        violator_result = await db.execute(text(violator_query))
                                        violator_row = violator_result.fetchone()
                                        if violator_row:
                                            val = violator_row[columns.index(target_column)]
                                            anomaly_samples.append((
                                                violator_row,
                                                f"DQ rule violation: {target_attribute} value '{val}' fails {rule.rule_name} (range validation)",
                                                str(rule.rule_id)
                                            ))
                                    except Exception as e:
                                        logger.warning(f"Could not check range rule: {str(e)}")
                    
                    # Adjust outlier quota based on DQ violators found
                    outlier_quota = outlier_quota - len([s for s in anomaly_samples if 'DQ rule violation' in s[1]])
                
                # 5. Statistical outliers (values beyond 2 standard deviations or IQR method)
                if outlier_quota > 0 and stddev_val > 0:
                    # Use both standard deviation and IQR methods
                    outlier_query = f"""
                        SELECT {', '.join([f'"{col}"' for col in columns])}
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NOT NULL 
                        AND "{target_column}"::text ~ '^[0-9.]+$'
                        AND (
                            -- Standard deviation method
                            CAST("{target_column}" AS NUMERIC) < {avg_val - 2 * stddev_val}
                            OR CAST("{target_column}" AS NUMERIC) > {avg_val + 2 * stddev_val}
                            -- IQR method for additional outliers
                            OR CAST("{target_column}" AS NUMERIC) < {q1 - 1.5 * iqr}
                            OR CAST("{target_column}" AS NUMERIC) > {q3 + 1.5 * iqr}
                        )
                        AND "{target_column}" NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                        ORDER BY RANDOM()
                        LIMIT {outlier_quota}
                    """
                    outlier_result = await db.execute(text(outlier_query))
                    outlier_rows = outlier_result.fetchall()
                    
                    for row in outlier_rows:
                        val = float(row[columns.index(target_column)])
                        # Determine outlier type and create appropriate rationale
                        if val < q1 - 1.5 * iqr:
                            rationale = f"Extreme low outlier: {target_attribute} ({val}) is far below Q1 ({q1:.2f})"
                        elif val > q3 + 1.5 * iqr:
                            rationale = f"Extreme high outlier: {target_attribute} ({val}) is far above Q3 ({q3:.2f})"
                        elif val < avg_val - 2 * stddev_val:
                            rationale = f"Statistical outlier: {target_attribute} ({val}) is >2 std deviations below mean ({avg_val:.2f})"
                        else:
                            rationale = f"Statistical outlier: {target_attribute} ({val}) is >2 std deviations above mean ({avg_val:.2f})"
                        anomaly_samples.append((row, rationale))
                
                # Add anomaly samples
                for sample_data in anomaly_samples[:samples_per_category['anomaly']]:
                    # Handle both 2-tuple and 3-tuple formats
                    if len(sample_data) == 3:
                        row, rationale, dq_rule_id = sample_data
                    else:
                        row, rationale = sample_data
                        dq_rule_id = None
                    
                    sample = self._create_sample_from_row(
                        row, columns, column_to_attr, scoped_attributes,
                        'anomaly', rationale, schema_name, table_name, target_attribute, dq_rule_id
                    )
                    val = sample['data_row_snapshot'].get(target_attribute)
                    if val not in selected_values:
                        samples_created.append(sample)
                        selected_values.add(val)
            
            # 4. Generate CLEAN samples
            if samples_per_category['clean'] > 0:
                if job_id:
                    job_manager.update_job_progress(
                        job_id,
                        current_step="Selecting clean samples",
                        progress_percentage=80
                    )
                
                clean_samples = []
                clean_quota = samples_per_category['clean']
                
                # Diversify clean samples: near mean, median, and mode values
                strategies = []
                
                # 1. Values near the mean (most typical)
                if clean_quota > 0:
                    strategies.append({
                        'name': 'near_mean',
                        'query': f"""
                            SELECT {', '.join([f'"{col}"' for col in columns])},
                                   ABS(CAST("{target_column}" AS NUMERIC) - {avg_val}) as distance
                            FROM {schema_name}.{table_name}
                            WHERE "{target_column}" IS NOT NULL 
                            AND CAST("{target_column}" AS NUMERIC) BETWEEN {avg_val - 0.5 * stddev_val} AND {avg_val + 0.5 * stddev_val}
                            AND "{target_column}"::text NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                            ORDER BY distance
                            LIMIT {clean_quota // 3 + 1}
                        """,
                        'rationale_fn': lambda val: f"Typical value near mean: {target_attribute} ({val}) is close to average ({avg_val:.2f})"
                    })
                
                # 2. Values near the median (central tendency)
                if clean_quota > 1 and median != avg_val:
                    strategies.append({
                        'name': 'near_median',
                        'query': f"""
                            SELECT {', '.join([f'"{col}"' for col in columns])},
                                   ABS(CAST("{target_column}" AS NUMERIC) - {median}) as distance
                            FROM {schema_name}.{table_name}
                            WHERE "{target_column}" IS NOT NULL 
                            AND ABS(CAST("{target_column}" AS NUMERIC) - {median}) < {0.25 * iqr if iqr > 0 else stddev_val}
                            AND "{target_column}"::text NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                            ORDER BY distance
                            LIMIT {clean_quota // 3}
                        """,
                        'rationale_fn': lambda val: f"Typical value near median: {target_attribute} ({val}) represents the middle 50% of data"
                    })
                
                # 3. Most common values (excluding high frequency anomalies)
                if clean_quota > 2:
                    strategies.append({
                        'name': 'common_values',
                        'query': f"""
                            WITH value_freqs AS (
                                SELECT "{target_column}", COUNT(*) as freq
                                FROM {schema_name}.{table_name}
                                WHERE "{target_column}" IS NOT NULL
                                GROUP BY "{target_column}"
                                HAVING COUNT(*) >= {avg_frequency - stddev_frequency}
                                AND COUNT(*) <= {avg_frequency + stddev_frequency}
                            )
                            SELECT {', '.join([f't."{col}"' for col in columns])}
                            FROM {schema_name}.{table_name} t
                            JOIN value_freqs vf ON t."{target_column}" = vf."{target_column}"
                            WHERE t."{target_column}" NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                            ORDER BY vf.freq DESC, RANDOM()
                            LIMIT {clean_quota - (clean_quota // 3 + 1) - (clean_quota // 3)}
                        """,
                        'rationale_fn': lambda val: f"Common value with normal frequency: {target_attribute} ({val}) appears with typical frequency"
                    })
                
                # Execute strategies and collect samples
                for strategy in strategies:
                    try:
                        result = await db.execute(text(strategy['query']))
                        rows = result.fetchall()
                        
                        for row in rows:
                            # Extract value for rationale
                            val = row[columns.index(target_column)]
                            if val and val not in selected_values:
                                rationale = strategy['rationale_fn'](val)
                                clean_samples.append((row[:len(columns)], rationale))
                    except Exception as e:
                        logger.warning(f"Clean sample strategy {strategy['name']} failed: {str(e)}")
                        continue
                
                # Apply DQ rule filtering to clean samples - they should pass all rules with good pass rates
                high_pass_rules = [r for r in attribute_rules if hasattr(r, 'pass_rate') and r.pass_rate >= 80]
                if high_pass_rules:
                    dq_conditions = []
                    for rule in high_pass_rules:
                        if hasattr(rule, 'rule_parameters') and rule.rule_parameters:
                            params = rule.rule_parameters
                            # Add range conditions
                            if 'min_value' in params:
                                dq_conditions.append(f"CAST(\"{target_column}\" AS NUMERIC) >= {params['min_value']}")
                            if 'max_value' in params:
                                dq_conditions.append(f"CAST(\"{target_column}\" AS NUMERIC) <= {params['max_value']}")
                            # Add pattern conditions
                            if rule.rule_type == 'validity' and 'pattern' in params:
                                dq_conditions.append(f"\"{target_column}\"::text SIMILAR TO '{params['pattern']}'")
                
                # If we need more samples, fall back to general clean query
                if len(clean_samples) < clean_quota:
                    # Build fallback query with DQ conditions
                    dq_where_clause = f" AND {' AND '.join(dq_conditions)}" if dq_conditions else ""
                    
                    fallback_query = f"""
                        SELECT {', '.join([f'"{col}"' for col in columns])}
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NOT NULL 
                        AND "{target_column}"::text ~ '^[0-9.]+$'
                        AND CAST("{target_column}" AS NUMERIC) BETWEEN {q1} AND {q3}
                        AND "{target_column}" NOT IN ({','.join([f"'{v}'" for v in selected_values if v])})
                        {dq_where_clause}
                        ORDER BY RANDOM()
                        LIMIT {clean_quota - len(clean_samples)}
                    """
                    
                    fallback_result = await db.execute(text(fallback_query))
                    fallback_rows = fallback_result.fetchall()
                    
                    for row in fallback_rows:
                        val = float(row[columns.index(target_column)])
                        rationale = f"Normal value within IQR: {target_attribute} ({val}) is in the typical range (Q1-Q3)"
                        clean_samples.append((row, rationale))
                
                # Add clean samples
                for row, rationale in clean_samples[:samples_per_category['clean']]:
                    sample = self._create_sample_from_row(
                        row, columns, column_to_attr, scoped_attributes,
                        'clean', rationale, schema_name, table_name, target_attribute
                    )
                    if sample['data_row_snapshot'].get(target_attribute) not in selected_values:
                        samples_created.append(sample)
                        selected_values.add(sample['data_row_snapshot'].get(target_attribute))
            
            # Get or create version
            version = await self.table_service.get_or_create_version(
                db, phase_id, current_user_id or 1
            )
            
            # Update version with target attribute info
            version.intelligent_sampling_config = {
                "target_attribute": target_attribute,
                "target_attribute_stats": {
                    "min": min_val,
                    "max": max_val,
                    "avg": avg_val,
                    "stddev": stddev_val,
                    "median": median,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "distinct_values": distinct_count,
                    "null_count": null_count,
                    "max_frequency": max_frequency,
                    "max_frequency_pct": max_frequency_pct,
                    "high_freq_values_count": len(high_freq_values),
                    "low_freq_values_count": len(low_freq_values)
                },
                "sampling_strategy": "intelligent",
                "anomaly_detection": {
                    "null_anomalies": null_count > 0,
                    "frequency_anomalies": len(high_freq_values) > 0 or len(low_freq_values) > 0,
                    "statistical_outliers": True if stddev_val > 0 else False,
                    "dq_rule_violations": len(attribute_rules) > 0,
                    "methods_used": ["null_detection", "frequency_analysis", "statistical_outliers", "iqr_method", "dq_rule_validation"]
                },
                "dq_integration": {
                    "profiling_rules_count": len(attribute_rules),
                    "regulatory_limits_applied": regulatory_limits is not None,
                    "regulatory_rule": regulatory_limits['rule_name'] if regulatory_limits else None,
                    "rules_factored": [rule.rule_name for rule in attribute_rules] if attribute_rules else []
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            version.target_sample_size = target_sample_size
            
            # Create sample records
            if samples_created and version:
                await self.table_service.create_samples_from_generation(
                    db, version.version_id, samples_created, current_user_id or 1
                )
            
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Sample generation complete",
                    progress_percentage=100,
                    status="completed"
                )
            
            return {
                'samples': samples_created,
                'generation_summary': {
                    'total_samples': len(samples_created),
                    'target_attribute': target_attribute,
                    'unique_values': len(selected_values),
                    'distribution_achieved': {
                        'clean': len([s for s in samples_created if s['sample_category'] == 'clean']),
                        'anomaly': len([s for s in samples_created if s['sample_category'] == 'anomaly']),
                        'boundary': len([s for s in samples_created if s['sample_category'] == 'boundary'])
                    },
                    'data_source': 'database',
                    'generation_method': 'Intelligent Sampling',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in intelligent sampling: {str(e)}")
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step=f"Error: {str(e)}",
                    status="failed"
                )
            raise
    
    def _create_sample_from_row(
        self,
        row: Any,
        columns: List[str],
        column_to_attr: Dict[str, str],
        scoped_attributes: List[Dict[str, Any]],
        category: str,
        rationale: str,
        schema_name: str,
        table_name: str,
        target_attribute: str,
        dq_rule_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a sample dict from a database row"""
        
        # Create data snapshot
        data_snapshot = {}
        pk_value = 'UNKNOWN'
        
        for idx, col in enumerate(columns):
            value = row[idx]
            # Convert non-serializable types
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'to_eng_string'):  # Decimal type
                value = str(value)
            elif value is None:
                value = None
            else:
                value = str(value)
            
            # Use attribute name as key
            attr_name = column_to_attr.get(col, col)
            data_snapshot[attr_name] = value
            
            # Check if this is a primary key
            for attr in scoped_attributes:
                if attr['attribute_name'] == attr_name and attr.get('is_primary_key'):
                    pk_value = value or f'SAMPLE_{idx}'
                    break
        
        return {
            # Don't auto-assign LOB - let tester assign it
            'primary_attribute_value': str(pk_value),
            'data_row_snapshot': data_snapshot,
            'sample_category': category,
            'sample_source': 'tester',
            'generation_method': 'Intelligent Sampling',
            'risk_score': self._calculate_risk_score(category),
            'confidence_score': 0.95,
            'metadata': {
                'source': 'database',
                'table': f'{schema_name}.{table_name}',
                'category': category,
                'target_attribute': target_attribute,
                'rationale': rationale,
                'dq_rule_id': dq_rule_id,
                'query_timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _calculate_risk_score(self, category: str) -> float:
        """Calculate risk score based on category"""
        risk_scores = {
            'clean': 0.2,
            'anomaly': 0.8,
            'boundary': 0.6
        }
        return risk_scores.get(category, 0.5)
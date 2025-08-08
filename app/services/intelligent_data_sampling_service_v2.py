"""
Intelligent Data Sampling Service V2
Implements proper stratified random sampling with 30/50/20 distribution
Priority: Anomalies first, then boundaries, fill remainder with clean samples
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
import random

logger = get_logger(__name__)


class IntelligentDataSamplingServiceV2:
    """Service for intelligent sample generation with proper stratified sampling"""
    
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
        """
        Generate intelligent samples with proper stratified sampling
        Priority: Anomalies (50%) -> Boundaries (20%) -> Clean (30%)
        If categories have insufficient samples, fill with clean samples
        """
        
        samples_created = []
        
        try:
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
            
            # Calculate target samples per category based on distribution
            # Default: 30% clean, 50% anomaly, 20% boundary
            # For small sample sizes, ensure at least some representation of each category
            if target_sample_size <= 10:
                # For small samples, use more balanced distribution
                target_anomaly = max(1, int(target_sample_size * 0.4))  # 40% anomaly
                target_boundary = max(1, int(target_sample_size * 0.2))  # 20% boundary
                target_clean = target_sample_size - target_anomaly - target_boundary  # Rest clean
            else:
                target_clean = int(target_sample_size * distribution.get('clean', 30) / 100)
                target_anomaly = int(target_sample_size * distribution.get('anomaly', 50) / 100)
                target_boundary = int(target_sample_size * distribution.get('boundary', 20) / 100)
                
                # Ensure exact count
                total_planned = target_clean + target_anomaly + target_boundary
                if total_planned < target_sample_size:
                    # Add remainder to anomaly (highest priority)
                    target_anomaly += target_sample_size - total_planned
            
            logger.info(f"Target distribution: {target_anomaly} anomalies, {target_boundary} boundaries, {target_clean} clean samples")
            
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Analyzing data distribution",
                    progress_percentage=20
                )
            
            # Parse profiling rules for this attribute
            attribute_rules = []
            regulatory_limits = None
            if profiling_rules:
                target_attr_id = None
                for attr in scoped_attributes:
                    if attr.get('attribute_name') == target_attribute:
                        target_attr_id = attr.get('attribute_id')
                        break
                
                for rule in profiling_rules:
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
            
            # Analyze data distribution
            stats_query = f"""
                WITH stats AS (
                    SELECT 
                        MIN(CAST("{target_column}" AS NUMERIC)) as min_val,
                        MAX(CAST("{target_column}" AS NUMERIC)) as max_val,
                        AVG(CAST("{target_column}" AS NUMERIC)) as avg_val,
                        STDDEV(CAST("{target_column}" AS NUMERIC)) as stddev_val,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY CAST("{target_column}" AS NUMERIC)) as q1,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST("{target_column}" AS NUMERIC)) as median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY CAST("{target_column}" AS NUMERIC)) as q3,
                        COUNT(*) as total_count,
                        COUNT(DISTINCT "{target_column}") as distinct_count
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" IS NOT NULL
                )
                SELECT * FROM stats
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
            iqr = q3 - q1
            
            logger.info(f"Data stats: min={min_val}, max={max_val}, median={median}, IQR={iqr}")
            
            # Track selected values to avoid duplicates
            selected_values = set()
            all_samples = []
            
            # PHASE 1: COLLECT ALL POSSIBLE ANOMALIES (Priority 1)
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Finding anomaly samples",
                    progress_percentage=30
                )
            
            anomaly_candidates = []
            
            # 1a. DQ Rule Violations (highest priority anomalies)
            for rule in attribute_rules:
                if hasattr(rule, 'pass_rate') and rule.pass_rate < 100:
                    # Find samples that fail this rule
                    if hasattr(rule, 'rule_parameters') and rule.rule_parameters:
                        params = rule.rule_parameters
                        
                        # Range violations
                        if 'min_value' in params or 'max_value' in params:
                            conditions = []
                            if 'min_value' in params:
                                conditions.append(f"CAST(\"{target_column}\" AS NUMERIC) < {params['min_value']}")
                            if 'max_value' in params:
                                conditions.append(f"CAST(\"{target_column}\" AS NUMERIC) > {params['max_value']}")
                            
                            if conditions:
                                violation_query = f"""
                                    SELECT {', '.join([f'"{col}"' for col in columns])}
                                    FROM {schema_name}.{table_name}
                                    WHERE "{target_column}" IS NOT NULL
                                    AND ({' OR '.join(conditions)})
                                    ORDER BY RANDOM()
                                    LIMIT 50
                                """
                                try:
                                    result = await db.execute(text(violation_query))
                                    for row in result.fetchall():
                                        val = row[columns.index(target_column)]
                                        if val not in selected_values:
                                            anomaly_candidates.append({
                                                'row': row,
                                                'category': 'anomaly',
                                                'priority': 1,  # Highest priority
                                                'rationale': f"DQ rule violation: {target_attribute} value '{val}' fails {rule.rule_name} (range check)",
                                                'value': val
                                            })
                                except Exception as e:
                                    logger.warning(f"Error finding range violations: {e}")
            
            # 1b. Statistical Outliers (medium priority anomalies)
            if stddev_val > 0:
                outlier_query = f"""
                    SELECT {', '.join([f'"{col}"' for col in columns])}
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" IS NOT NULL 
                    AND "{target_column}"::text ~ '^[0-9.-]+$'
                    AND (
                        CAST("{target_column}" AS NUMERIC) < {avg_val - 2 * stddev_val}
                        OR CAST("{target_column}" AS NUMERIC) > {avg_val + 2 * stddev_val}
                        OR CAST("{target_column}" AS NUMERIC) < {q1 - 1.5 * iqr}
                        OR CAST("{target_column}" AS NUMERIC) > {q3 + 1.5 * iqr}
                    )
                    ORDER BY RANDOM()
                    LIMIT 100
                """
                try:
                    result = await db.execute(text(outlier_query))
                    for row in result.fetchall():
                        val = float(row[columns.index(target_column)])
                        if val not in selected_values:
                            # Determine outlier type
                            if val < q1 - 1.5 * iqr:
                                rationale = f"Extreme low outlier: {target_attribute} ({val}) is far below Q1 ({q1:.2f})"
                            elif val > q3 + 1.5 * iqr:
                                rationale = f"Extreme high outlier: {target_attribute} ({val}) is far above Q3 ({q3:.2f})"
                            elif val < avg_val - 2 * stddev_val:
                                rationale = f"Statistical outlier: {target_attribute} ({val}) is >2 std deviations below mean ({avg_val:.2f})"
                            else:
                                rationale = f"Statistical outlier: {target_attribute} ({val}) is >2 std deviations above mean ({avg_val:.2f})"
                            
                            anomaly_candidates.append({
                                'row': row,
                                'category': 'anomaly',
                                'priority': 2,
                                'rationale': rationale,
                                'value': val
                            })
                except Exception as e:
                    logger.warning(f"Error finding outliers: {e}")
            
            # 1c. Null values (if they exist)
            null_query = f"""
                SELECT {', '.join([f'"{col}"' for col in columns])}
                FROM {schema_name}.{table_name}
                WHERE "{target_column}" IS NULL
                LIMIT 10
            """
            try:
                result = await db.execute(text(null_query))
                for row in result.fetchall():
                    anomaly_candidates.append({
                        'row': row,
                        'category': 'anomaly',
                        'priority': 3,
                        'rationale': f"Missing value: {target_attribute} is NULL",
                        'value': None
                    })
            except Exception as e:
                logger.warning(f"Error finding null values: {e}")
            
            # PHASE 2: COLLECT ALL POSSIBLE BOUNDARIES (Priority 2)
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Finding boundary samples",
                    progress_percentage=50
                )
            
            boundary_candidates = []
            
            # 2a. Regulatory boundaries (if defined)
            if regulatory_limits:
                if regulatory_limits['min'] is not None:
                    reg_min_query = f"""
                        SELECT {', '.join([f'"{col}"' for col in columns])},
                               ABS(CAST("{target_column}" AS NUMERIC) - {regulatory_limits['min']}) as distance
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NOT NULL
                        ORDER BY distance
                        LIMIT 5
                    """
                    try:
                        result = await db.execute(text(reg_min_query))
                        for row in result.fetchall():
                            val = row[columns.index(target_column)]
                            if val not in selected_values:
                                boundary_candidates.append({
                                    'row': row[:len(columns)],
                                    'category': 'boundary',
                                    'priority': 1,
                                    'rationale': f"Regulatory minimum boundary: {target_attribute} ({val}) near limit {regulatory_limits['min']}",
                                    'value': val
                                })
                    except Exception as e:
                        logger.warning(f"Error finding regulatory min: {e}")
                
                if regulatory_limits['max'] is not None:
                    reg_max_query = f"""
                        SELECT {', '.join([f'"{col}"' for col in columns])},
                               ABS(CAST("{target_column}" AS NUMERIC) - {regulatory_limits['max']}) as distance
                        FROM {schema_name}.{table_name}
                        WHERE "{target_column}" IS NOT NULL
                        ORDER BY distance
                        LIMIT 5
                    """
                    try:
                        result = await db.execute(text(reg_max_query))
                        for row in result.fetchall():
                            val = row[columns.index(target_column)]
                            if val not in selected_values:
                                boundary_candidates.append({
                                    'row': row[:len(columns)],
                                    'category': 'boundary',
                                    'priority': 1,
                                    'rationale': f"Regulatory maximum boundary: {target_attribute} ({val}) near limit {regulatory_limits['max']}",
                                    'value': val
                                })
                    except Exception as e:
                        logger.warning(f"Error finding regulatory max: {e}")
            
            # 2b. Data boundaries (min/max values)
            # Minimum values
            min_query = f"""
                SELECT {', '.join([f'"{col}"' for col in columns])}
                FROM {schema_name}.{table_name}
                WHERE CAST("{target_column}" AS NUMERIC) = {min_val}
                LIMIT 5
            """
            try:
                result = await db.execute(text(min_query))
                for row in result.fetchall():
                    val = row[columns.index(target_column)]
                    if val not in selected_values:
                        boundary_candidates.append({
                            'row': row,
                            'category': 'boundary',
                            'priority': 2,
                            'rationale': f"Data minimum: {target_attribute} = {min_val}",
                            'value': val
                        })
            except Exception as e:
                logger.warning(f"Error finding min values: {e}")
            
            # Maximum values
            max_query = f"""
                SELECT {', '.join([f'"{col}"' for col in columns])}
                FROM {schema_name}.{table_name}
                WHERE CAST("{target_column}" AS NUMERIC) = {max_val}
                LIMIT 5
            """
            try:
                result = await db.execute(text(max_query))
                for row in result.fetchall():
                    val = row[columns.index(target_column)]
                    if val not in selected_values:
                        boundary_candidates.append({
                            'row': row,
                            'category': 'boundary',
                            'priority': 2,
                            'rationale': f"Data maximum: {target_attribute} = {max_val}",
                            'value': val
                        })
            except Exception as e:
                logger.warning(f"Error finding max values: {e}")
            
            # 2c. Quartile boundaries
            for quartile, value in [('Q1', q1), ('Q3', q3)]:
                quartile_query = f"""
                    SELECT {', '.join([f'"{col}"' for col in columns])},
                           ABS(CAST("{target_column}" AS NUMERIC) - {value}) as distance
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" IS NOT NULL
                    ORDER BY distance
                    LIMIT 3
                """
                try:
                    result = await db.execute(text(quartile_query))
                    for row in result.fetchall():
                        val = row[columns.index(target_column)]
                        if val not in selected_values:
                            boundary_candidates.append({
                                'row': row[:len(columns)],
                                'category': 'boundary',
                                'priority': 3,
                                'rationale': f"{quartile} boundary: {target_attribute} ({val}) near {quartile} value {value:.2f}",
                                'value': val
                            })
                except Exception as e:
                    logger.warning(f"Error finding {quartile} values: {e}")
            
            # PHASE 3: COLLECT CLEAN SAMPLES (Priority 3)
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Finding clean samples",
                    progress_percentage=70
                )
            
            clean_candidates = []
            
            # 3a. Values near mean (typical values)
            mean_query = f"""
                SELECT {', '.join([f'"{col}"' for col in columns])},
                       ABS(CAST("{target_column}" AS NUMERIC) - {avg_val}) as distance
                FROM {schema_name}.{table_name}
                WHERE "{target_column}" IS NOT NULL 
                AND CAST("{target_column}" AS NUMERIC) BETWEEN {avg_val - stddev_val} AND {avg_val + stddev_val}
                ORDER BY distance
                LIMIT 100
            """
            try:
                result = await db.execute(text(mean_query))
                for row in result.fetchall():
                    val = row[columns.index(target_column)]
                    if val not in selected_values:
                        clean_candidates.append({
                            'row': row[:len(columns)],
                            'category': 'clean',
                            'priority': 1,
                            'rationale': f"Typical value near mean: {target_attribute} ({val}) close to average {avg_val:.2f}",
                            'value': val
                        })
            except Exception as e:
                logger.warning(f"Error finding mean values: {e}")
            
            # 3b. Values near median
            median_query = f"""
                SELECT {', '.join([f'"{col}"' for col in columns])},
                       ABS(CAST("{target_column}" AS NUMERIC) - {median}) as distance
                FROM {schema_name}.{table_name}
                WHERE "{target_column}" IS NOT NULL 
                ORDER BY distance
                LIMIT 100
            """
            try:
                result = await db.execute(text(median_query))
                for row in result.fetchall():
                    val = row[columns.index(target_column)]
                    if val not in selected_values:
                        clean_candidates.append({
                            'row': row[:len(columns)],
                            'category': 'clean',
                            'priority': 2,
                            'rationale': f"Typical value near median: {target_attribute} ({val}) close to median {median:.2f}",
                            'value': val
                        })
            except Exception as e:
                logger.warning(f"Error finding median values: {e}")
            
            # 3c. Random clean samples within normal range
            clean_query = f"""
                SELECT {', '.join([f'"{col}"' for col in columns])}
                FROM {schema_name}.{table_name}
                WHERE "{target_column}" IS NOT NULL 
                AND CAST("{target_column}" AS NUMERIC) BETWEEN {q1} AND {q3}
                ORDER BY RANDOM()
                LIMIT 200
            """
            try:
                result = await db.execute(text(clean_query))
                for row in result.fetchall():
                    val = row[columns.index(target_column)]
                    if val not in selected_values:
                        clean_candidates.append({
                            'row': row,
                            'category': 'clean',
                            'priority': 3,
                            'rationale': f"Clean sample: {target_attribute} ({val}) within normal range",
                            'value': val
                        })
            except Exception as e:
                logger.warning(f"Error finding clean values: {e}")
            
            # PHASE 4: STRATIFIED SAMPLING WITH PROPER DISTRIBUTION
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Performing stratified sampling",
                    progress_percentage=80
                )
            
            logger.info(f"Candidates found: {len(anomaly_candidates)} anomalies, {len(boundary_candidates)} boundaries, {len(clean_candidates)} clean")
            
            # Sort candidates by priority within each category
            anomaly_candidates.sort(key=lambda x: x['priority'])
            boundary_candidates.sort(key=lambda x: x['priority'])
            clean_candidates.sort(key=lambda x: x['priority'])
            
            # Select samples according to priority: Anomalies -> Boundaries -> Clean
            final_samples = []
            
            # 1. Select anomalies first (up to target_anomaly)
            anomalies_selected = 0
            for candidate in anomaly_candidates:
                if anomalies_selected < target_anomaly and candidate['value'] not in selected_values:
                    final_samples.append(candidate)
                    selected_values.add(candidate['value'])
                    anomalies_selected += 1
            
            # 2. Select boundaries (up to target_boundary)
            boundaries_selected = 0
            for candidate in boundary_candidates:
                if boundaries_selected < target_boundary and candidate['value'] not in selected_values:
                    final_samples.append(candidate)
                    selected_values.add(candidate['value'])
                    boundaries_selected += 1
            
            # 3. Calculate how many clean samples we need
            # This includes original target_clean plus any shortfall from anomalies and boundaries
            anomaly_shortfall = target_anomaly - anomalies_selected
            boundary_shortfall = target_boundary - boundaries_selected
            clean_needed = target_clean + anomaly_shortfall + boundary_shortfall
            
            logger.info(f"Selected: {anomalies_selected}/{target_anomaly} anomalies, {boundaries_selected}/{target_boundary} boundaries")
            logger.info(f"Need {clean_needed} clean samples (including {anomaly_shortfall + boundary_shortfall} to fill shortfalls)")
            
            # 4. Select clean samples to fill the rest
            clean_selected = 0
            for candidate in clean_candidates:
                if clean_selected < clean_needed and candidate['value'] not in selected_values:
                    final_samples.append(candidate)
                    selected_values.add(candidate['value'])
                    clean_selected += 1
            
            # 5. If we still don't have enough samples, add more random clean samples
            if len(final_samples) < target_sample_size:
                additional_needed = target_sample_size - len(final_samples)
                logger.info(f"Need {additional_needed} additional samples")
                
                # Get more random samples
                additional_query = f"""
                    SELECT {', '.join([f'"{col}"' for col in columns])}
                    FROM {schema_name}.{table_name}
                    WHERE "{target_column}" IS NOT NULL
                    AND "{target_column}" NOT IN ({','.join([f"'{v}'" for v in selected_values if v is not None])})
                    ORDER BY RANDOM()
                    LIMIT {additional_needed * 2}
                """
                try:
                    result = await db.execute(text(additional_query))
                    for row in result.fetchall():
                        if len(final_samples) < target_sample_size:
                            val = row[columns.index(target_column)]
                            if val not in selected_values:
                                final_samples.append({
                                    'row': row,
                                    'category': 'clean',
                                    'priority': 4,
                                    'rationale': f"Additional clean sample: {target_attribute} = {val}",
                                    'value': val
                                })
                                selected_values.add(val)
                except Exception as e:
                    logger.warning(f"Error getting additional samples: {e}")
            
            # PHASE 5: CREATE VERSION AND SAVE SAMPLES
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Saving samples to database",
                    progress_percentage=90
                )
            
            # Create new version
            version = await self.table_service.create_version(
                db=db,
                phase_id=phase_id,
                user_id=current_user_id,
                generation_method='Intelligent Sampling',
                change_reason=f"Generated {len(final_samples)} samples using stratified sampling"
            )
            
            # Update version with additional metadata
            version.target_sample_size = target_sample_size
            version.actual_sample_size = len(final_samples)
            version.data_source_name = f"{schema_name}.{table_name}"
            version.selection_criteria = {
                'target_attribute': target_attribute,
                'distribution': distribution,
                'anomalies_found': anomalies_selected,
                'boundaries_found': boundaries_selected,
                'clean_used': clean_selected,
                'distribution_requested': {
                    'clean': distribution.get('clean', 30),
                    'anomaly': distribution.get('anomaly', 50),
                    'boundary': distribution.get('boundary', 20)
                }
            }
            
            # Prepare samples for batch creation
            samples_to_create = []
            for i, sample_data in enumerate(final_samples):
                sample_number = i + 1
                row = sample_data['row']
                
                # Create data row snapshot
                data_row = {}
                for j, col in enumerate(columns):
                    attr_name = column_to_attr.get(col, col)
                    value = row[j]
                    # Convert Decimal to float for JSON serialization
                    if isinstance(value, Decimal):
                        value = float(value)
                    data_row[attr_name] = value
                
                # Determine sample category
                actual_category = sample_data['category']
                
                # Map to SampleCategory enum values (lowercase in model)
                category_map = {
                    'clean': 'clean',
                    'anomaly': 'anomaly', 
                    'boundary': 'boundary'
                }
                
                # Get primary key value for sample identifier
                primary_value = str(sample_data.get('value', sample_number))
                
                samples_to_create.append({
                    'sample_number': sample_number,
                    'primary_attribute_value': primary_value,
                    'sample_category': category_map.get(actual_category, 'clean'),
                    'sample_source': 'tester',
                    'generation_method': 'Intelligent Sampling',
                    'sample_rationale': sample_data['rationale'],
                    'data_row_snapshot': data_row,
                    'attribute_focus': target_attribute,
                    'source_table': f"{schema_name}.{table_name}",
                    'metadata': {
                        'sample_rationale': sample_data['rationale'],
                        'attribute_focus': target_attribute,
                        'generation_method': 'Intelligent Sampling',
                        'source_table': f"{schema_name}.{table_name}"
                    }
                })
                
                samples_created.append({
                    'sample_number': sample_number,
                    'sample_type': actual_category,
                    'data_row_snapshot': data_row,
                    'sample_rationale': sample_data['rationale']
                })
            
            # Create all samples at once
            await self.table_service.create_samples_from_generation(
                db=db,
                version_id=version.version_id,
                generated_samples=samples_to_create,
                user_id=current_user_id
            )
            
            await db.commit()
            
            # Calculate actual distribution achieved
            actual_distribution = {
                'clean': 0,
                'anomaly': 0,
                'boundary': 0
            }
            
            for sample in samples_created:
                actual_distribution[sample['sample_type']] += 1
            
            distribution_achieved = {}
            if len(samples_created) > 0:
                for category, count in actual_distribution.items():
                    distribution_achieved[category] = (count / len(samples_created)) * 100
            
            logger.info(f"Final distribution achieved: {distribution_achieved}")
            logger.info(f"Anomalies: {actual_distribution['anomaly']}, Boundaries: {actual_distribution['boundary']}, Clean: {actual_distribution['clean']}")
            
            return {
                'samples': samples_created,
                'generation_summary': {
                    'total_samples': len(samples_created),
                    'target_attribute': target_attribute,
                    'distribution_achieved': distribution_achieved,
                    'actual_counts': actual_distribution,
                    'version_id': str(version.version_id),
                    'version_number': version.version_number
                }
            }
            
        except Exception as e:
            logger.error(f"Error in intelligent sampling: {str(e)}")
            raise BusinessLogicError(f"Failed to generate samples: {str(e)}")
    
    def _create_sample_from_row(
        self, row, columns, column_to_attr, scoped_attributes,
        sample_type, rationale, schema_name, table_name, target_attribute, dq_rule_id=None
    ):
        """Helper to create sample from database row"""
        data_row = {}
        for i, col in enumerate(columns):
            attr_name = column_to_attr.get(col, col)
            value = row[i]
            # Handle decimal/numeric types
            if isinstance(value, Decimal):
                value = float(value)
            data_row[attr_name] = value
        
        sample = {
            'sample_type': sample_type,
            'data_row_snapshot': data_row,
            'sample_rationale': rationale,
            'attribute_focus': target_attribute,
            'source_table': f"{schema_name}.{table_name}"
        }
        
        if dq_rule_id:
            sample['dq_rule_id'] = dq_rule_id
        
        return sample
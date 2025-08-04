"""add enhancement tables for data sources profiling and sampling

Revision ID: enhancement_001
Revises: clean_versioning
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhancement_001'
down_revision = 'temporal_versioning_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhancement tables for practical application features"""
    
    # Create ENUMs first
    op.execute("CREATE TYPE datasourcetype AS ENUM ('POSTGRESQL', 'MYSQL', 'ORACLE', 'SQLSERVER', 'SNOWFLAKE', 'BIGQUERY', 'REDSHIFT', 'FILE')")
    op.execute("CREATE TYPE securityclassification AS ENUM ('HRCI', 'Confidential', 'Proprietary', 'Public')")
    op.execute("CREATE TYPE profilingstrategy AS ENUM ('full_scan', 'sampling', 'streaming', 'partitioned', 'incremental')")
    op.execute("CREATE TYPE rulecategory AS ENUM ('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', 'timeliness', 'anomaly', 'custom')")
    op.execute("CREATE TYPE samplingstrategy AS ENUM ('random', 'stratified', 'anomaly_based', 'boundary', 'risk_based', 'systematic', 'cluster', 'hybrid')")
    op.execute("CREATE TYPE samplecategory AS ENUM ('normal', 'anomaly', 'boundary_high', 'boundary_low', 'outlier', 'edge_case', 'high_risk')")
    
    # Data Sources v2 (enhanced)
    op.create_table('data_sources_v2',
        sa.Column('data_source_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('source_type', postgresql.ENUM('POSTGRESQL', 'MYSQL', 'ORACLE', 'SQLSERVER', 'SNOWFLAKE', 'BIGQUERY', 'REDSHIFT', 'FILE', name='datasourcetype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('connection_config', sa.Text(), nullable=False),  # Encrypted JSON
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_validated', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_error', sa.Text(), nullable=True),
        sa.Column('default_date_column', sa.String(255), nullable=True),
        sa.Column('default_schema', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('data_source_id'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_datasource_report', 'data_sources_v2', ['report_id', 'is_active'])
    
    # Attribute Mappings
    op.create_table('attribute_mappings',
        sa.Column('mapping_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(), nullable=False),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('data_type', sa.String(100), nullable=True),
        sa.Column('security_classification', postgresql.ENUM('HRCI', 'Confidential', 'Proprietary', 'Public', name='securityclassification'), nullable=False, default='Public'),
        sa.Column('is_primary_key', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, default=True),
        sa.Column('column_description', sa.Text(), nullable=True),
        sa.Column('mapping_confidence', sa.Integer(), nullable=True),
        sa.Column('llm_suggested', sa.Boolean(), nullable=False, default=False),
        sa.Column('manual_override', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False, default=False),
        sa.Column('validation_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('mapping_id'),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'], ),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources_v2.data_source_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_mapping_attribute', 'attribute_mappings', ['attribute_id'])
    op.create_index('idx_mapping_source', 'attribute_mappings', ['data_source_id'])
    op.create_index('idx_mapping_security', 'attribute_mappings', ['security_classification'])
    
    # Data Queries
    op.create_table('data_queries',
        sa.Column('query_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('data_source_id', postgresql.UUID(), nullable=False),
        sa.Column('query_name', sa.String(255), nullable=False),
        sa.Column('query_type', sa.String(50), nullable=False),
        sa.Column('query_template', sa.Text(), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('estimated_rows', sa.Integer(), nullable=True),
        sa.Column('execution_timeout_seconds', sa.Integer(), nullable=False, default=300),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('query_id'),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources_v2.data_source_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_query_source_type', 'data_queries', ['data_source_id', 'query_type'])
    
    # Profiling Jobs
    op.create_table('profiling_jobs',
        sa.Column('job_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(255), nullable=False),
        sa.Column('strategy', postgresql.ENUM('full_scan', 'sampling', 'streaming', 'partitioned', 'incremental', name='profilingstrategy'), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_config', postgresql.JSONB(), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('total_rules', sa.Integer(), nullable=True),
        sa.Column('estimated_runtime_minutes', sa.Integer(), nullable=True),
        sa.Column('partition_strategy', sa.String(50), nullable=True),
        sa.Column('partition_count', sa.Integer(), nullable=False, default=1),
        sa.Column('max_memory_gb', sa.Integer(), nullable=False, default=8),
        sa.Column('max_cpu_cores', sa.Integer(), nullable=False, default=4),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('progress_percent', sa.Integer(), nullable=False, default=0),
        sa.Column('records_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('rules_executed', sa.Integer(), nullable=False, default=0),
        sa.Column('anomalies_found', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('job_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_profiling_job_status', 'profiling_jobs', ['status', 'priority'])
    op.create_index('idx_profiling_job_cycle', 'profiling_jobs', ['cycle_id', 'report_id'])
    
    # Profiling Partitions
    op.create_table('profiling_partitions',
        sa.Column('partition_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(), nullable=False),
        sa.Column('partition_index', sa.Integer(), nullable=False),
        sa.Column('partition_key', sa.String(255), nullable=True),
        sa.Column('start_value', sa.String(255), nullable=True),
        sa.Column('end_value', sa.String(255), nullable=True),
        sa.Column('estimated_records', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('assigned_worker', sa.String(255), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('last_checkpoint', sa.String(255), nullable=True),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('anomalies_found', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('partition_id'),
        sa.ForeignKeyConstraint(['job_id'], ['profiling_jobs.job_id'], )
    )
    op.create_index('idx_partition_job_status', 'profiling_partitions', ['job_id', 'status'])
    op.create_index('idx_partition_worker', 'profiling_partitions', ['assigned_worker', 'status'])
    
    # Profiling Rule Sets
    op.create_table('profiling_rule_sets',
        sa.Column('rule_set_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(), nullable=False),
        sa.Column('rule_set_name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', 'timeliness', 'anomaly', 'custom', name='rulecategory'), nullable=False),
        sa.Column('rules', postgresql.JSONB(), nullable=False),
        sa.Column('rule_count', sa.Integer(), nullable=False),
        sa.Column('execution_order', sa.Integer(), nullable=False, default=1),
        sa.Column('can_parallelize', sa.Boolean(), nullable=False, default=True),
        sa.Column('fail_fast', sa.Boolean(), nullable=False, default=False),
        sa.Column('estimated_cost', sa.Integer(), nullable=True),
        sa.Column('requires_full_scan', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('rule_set_id'),
        sa.ForeignKeyConstraint(['job_id'], ['profiling_jobs.job_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_ruleset_job_category', 'profiling_rule_sets', ['job_id', 'category'])
    
    # Partition Results
    op.create_table('partition_results',
        sa.Column('result_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('partition_id', postgresql.UUID(), nullable=False),
        sa.Column('rule_set_id', postgresql.UUID(), nullable=False),
        sa.Column('records_evaluated', sa.Integer(), nullable=False),
        sa.Column('records_passed', sa.Integer(), nullable=False),
        sa.Column('records_failed', sa.Integer(), nullable=False),
        sa.Column('anomalies', postgresql.JSONB(), nullable=True),
        sa.Column('anomaly_count', sa.Integer(), nullable=False, default=0),
        sa.Column('statistics', postgresql.JSONB(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('memory_used_mb', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('result_id'),
        sa.ForeignKeyConstraint(['partition_id'], ['profiling_partitions.partition_id'], ),
        sa.ForeignKeyConstraint(['rule_set_id'], ['profiling_rule_sets.rule_set_id'], )
    )
    op.create_index('idx_partition_result', 'partition_results', ['partition_id', 'rule_set_id'])
    
    # Profiling Anomaly Patterns
    op.create_table('profiling_anomaly_patterns',
        sa.Column('pattern_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(), nullable=False),
        sa.Column('pattern_type', sa.String(100), nullable=False),
        sa.Column('pattern_description', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('affected_columns', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('pattern_rules', postgresql.JSONB(), nullable=True),
        sa.Column('sample_record_ids', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=True),
        sa.Column('occurrence_count', sa.Integer(), nullable=True),
        sa.Column('occurrence_percentage', sa.Float(), nullable=True),
        sa.Column('recommended_for_sampling', sa.Boolean(), nullable=False, default=True),
        sa.Column('sampling_priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('pattern_id'),
        sa.ForeignKeyConstraint(['job_id'], ['profiling_jobs.job_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_anomaly_pattern_job', 'profiling_anomaly_patterns', ['job_id', 'pattern_type'])
    op.create_index('idx_anomaly_pattern_sampling', 'profiling_anomaly_patterns', ['recommended_for_sampling', 'sampling_priority'])
    
    # Profiling Cache
    op.create_table('profiling_cache',
        sa.Column('cache_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('cache_key', sa.String(500), nullable=False, unique=True),
        sa.Column('cache_type', sa.String(50), nullable=False),
        sa.Column('cache_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False, default=True),
        sa.Column('source_identifier', sa.String(255), nullable=True),
        sa.Column('source_version', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('cache_id')
    )
    op.create_index('idx_cache_key_valid', 'profiling_cache', ['cache_key', 'is_valid', 'expires_at'])
    op.create_index('idx_cache_source', 'profiling_cache', ['source_identifier', 'cache_type'])
    
    # Intelligent Sampling Jobs
    op.create_table('intelligent_sampling_jobs',
        sa.Column('job_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('profiling_job_id', postgresql.UUID(), nullable=False),
        sa.Column('target_sample_size', sa.Integer(), nullable=False),
        sa.Column('sampling_strategies', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('normal_percentage', sa.Integer(), nullable=False, default=40),
        sa.Column('anomaly_percentage', sa.Integer(), nullable=False, default=30),
        sa.Column('boundary_percentage', sa.Integer(), nullable=False, default=20),
        sa.Column('edge_case_percentage', sa.Integer(), nullable=False, default=10),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_criteria', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_samples_selected', sa.Integer(), nullable=False, default=0),
        sa.Column('selection_quality_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('job_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['profiling_job_id'], ['profiling_jobs.job_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_sampling_job_cycle', 'intelligent_sampling_jobs', ['cycle_id', 'report_id'])
    op.create_index('idx_sampling_job_profiling', 'intelligent_sampling_jobs', ['profiling_job_id'])
    
    # Sample Pools
    op.create_table('sample_pools',
        sa.Column('pool_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(), nullable=False),
        sa.Column('category', postgresql.ENUM('normal', 'anomaly', 'boundary_high', 'boundary_low', 'outlier', 'edge_case', 'high_risk', name='samplecategory'), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('total_candidates', sa.Integer(), nullable=False),
        sa.Column('selection_criteria', postgresql.JSONB(), nullable=True),
        sa.Column('diversity_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('candidate_ids', postgresql.JSONB(), nullable=True),
        sa.Column('candidate_metadata', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('pool_id'),
        sa.ForeignKeyConstraint(['job_id'], ['intelligent_sampling_jobs.job_id'], )
    )
    op.create_index('idx_sample_pool_job_category', 'sample_pools', ['job_id', 'category'])
    
    # Intelligent Samples
    op.create_table('intelligent_samples',
        sa.Column('sample_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(), nullable=False),
        sa.Column('pool_id', postgresql.UUID(), nullable=False),
        sa.Column('record_identifier', sa.String(500), nullable=False),
        sa.Column('record_data', postgresql.JSONB(), nullable=False),
        sa.Column('category', postgresql.ENUM('normal', 'anomaly', 'boundary_high', 'boundary_low', 'outlier', 'edge_case', 'high_risk', name='samplecategory'), nullable=False),
        sa.Column('selection_reason', sa.Text(), nullable=True),
        sa.Column('anomaly_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('anomaly_rules', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.Column('boundary_attributes', postgresql.JSONB(), nullable=True),
        sa.Column('boundary_values', postgresql.JSONB(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        sa.Column('selection_strategy', postgresql.ENUM('random', 'stratified', 'anomaly_based', 'boundary', 'risk_based', 'systematic', 'cluster', 'hybrid', name='samplingstrategy'), nullable=False),
        sa.Column('selection_rank', sa.Integer(), nullable=True),
        sa.Column('testing_priority', sa.Integer(), nullable=True),
        sa.Column('must_test', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('sample_id'),
        sa.ForeignKeyConstraint(['job_id'], ['intelligent_sampling_jobs.job_id'], ),
        sa.ForeignKeyConstraint(['pool_id'], ['sample_pools.pool_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_intelligent_sample_job', 'intelligent_samples', ['job_id', 'category'])
    op.create_index('idx_intelligent_sample_priority', 'intelligent_samples', ['testing_priority', 'must_test'])
    op.create_index('idx_intelligent_sample_identifier', 'intelligent_samples', ['record_identifier'])
    
    # Sampling Rules
    op.create_table('sampling_rules',
        sa.Column('rule_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('rule_definition', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        sa.Column('applicable_attributes', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('applicable_categories', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('estimated_cost', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('rule_id'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_sampling_rule_report', 'sampling_rules', ['report_id', 'is_active'])
    op.create_index('idx_sampling_rule_type', 'sampling_rules', ['rule_type', 'priority'])
    
    # Sample Lineage
    op.create_table('sample_lineage',
        sa.Column('lineage_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('sample_id', postgresql.UUID(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_reference', sa.String(500), nullable=True),
        sa.Column('selection_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('selection_criteria', postgresql.JSONB(), nullable=True),
        sa.Column('changes_from_source', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('lineage_id'),
        sa.ForeignKeyConstraint(['sample_id'], ['intelligent_samples.sample_id'], )
    )
    op.create_index('idx_sample_lineage_sample', 'sample_lineage', ['sample_id'])
    op.create_index('idx_sample_lineage_source', 'sample_lineage', ['source_type', 'source_reference'])
    
    # Profiling Executions
    op.create_table('profiling_executions',
        sa.Column('execution_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(), nullable=True),
        sa.Column('execution_type', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('profiling_criteria', postgresql.JSONB(), nullable=False),
        sa.Column('total_records_profiled', sa.Integer(), nullable=True),
        sa.Column('total_rules_executed', sa.Integer(), nullable=True),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('records_per_second', sa.Integer(), nullable=True),
        sa.Column('peak_memory_mb', sa.Integer(), nullable=True),
        sa.Column('rules_passed', sa.Integer(), nullable=True),
        sa.Column('rules_failed', sa.Integer(), nullable=True),
        sa.Column('anomalies_detected', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('execution_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources_v2.data_source_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_profiling_exec_cycle', 'profiling_executions', ['cycle_id', 'report_id'])
    op.create_index('idx_profiling_exec_status', 'profiling_executions', ['status', 'start_time'])
    
    # Secure Data Access Logs
    op.create_table('secure_data_access_logs',
        sa.Column('access_id', postgresql.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('record_identifier', sa.String(255), nullable=True),
        sa.Column('security_classification', postgresql.ENUM('HRCI', 'Confidential', 'Proprietary', 'Public', name='securityclassification'), nullable=False),
        sa.Column('access_type', sa.String(50), nullable=False),
        sa.Column('access_reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('access_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    op.create_index('idx_secure_access_user', 'secure_data_access_logs', ['user_id', 'accessed_at'])
    op.create_index('idx_secure_access_classification', 'secure_data_access_logs', ['security_classification', 'accessed_at'])


def downgrade() -> None:
    """Remove enhancement tables"""
    # Drop indexes first
    op.drop_index('idx_secure_access_classification', 'secure_data_access_logs')
    op.drop_index('idx_secure_access_user', 'secure_data_access_logs')
    op.drop_index('idx_profiling_exec_status', 'profiling_executions')
    op.drop_index('idx_profiling_exec_cycle', 'profiling_executions')
    op.drop_index('idx_sample_lineage_source', 'sample_lineage')
    op.drop_index('idx_sample_lineage_sample', 'sample_lineage')
    op.drop_index('idx_sampling_rule_type', 'sampling_rules')
    op.drop_index('idx_sampling_rule_report', 'sampling_rules')
    op.drop_index('idx_intelligent_sample_identifier', 'intelligent_samples')
    op.drop_index('idx_intelligent_sample_priority', 'intelligent_samples')
    op.drop_index('idx_intelligent_sample_job', 'intelligent_samples')
    op.drop_index('idx_sample_pool_job_category', 'sample_pools')
    op.drop_index('idx_sampling_job_profiling', 'intelligent_sampling_jobs')
    op.drop_index('idx_sampling_job_cycle', 'intelligent_sampling_jobs')
    op.drop_index('idx_cache_source', 'profiling_cache')
    op.drop_index('idx_cache_key_valid', 'profiling_cache')
    op.drop_index('idx_anomaly_pattern_sampling', 'profiling_anomaly_patterns')
    op.drop_index('idx_anomaly_pattern_job', 'profiling_anomaly_patterns')
    op.drop_index('idx_partition_result', 'partition_results')
    op.drop_index('idx_ruleset_job_category', 'profiling_rule_sets')
    op.drop_index('idx_partition_worker', 'profiling_partitions')
    op.drop_index('idx_partition_job_status', 'profiling_partitions')
    op.drop_index('idx_profiling_job_cycle', 'profiling_jobs')
    op.drop_index('idx_profiling_job_status', 'profiling_jobs')
    op.drop_index('idx_query_source_type', 'data_queries')
    op.drop_index('idx_mapping_security', 'attribute_mappings')
    op.drop_index('idx_mapping_source', 'attribute_mappings')
    op.drop_index('idx_mapping_attribute', 'attribute_mappings')
    op.drop_index('idx_datasource_report', 'data_sources_v2')
    
    # Drop tables in reverse order
    op.drop_table('secure_data_access_logs')
    op.drop_table('profiling_executions')
    op.drop_table('sample_lineage')
    op.drop_table('sampling_rules')
    op.drop_table('intelligent_samples')
    op.drop_table('sample_pools')
    op.drop_table('intelligent_sampling_jobs')
    op.drop_table('profiling_cache')
    op.drop_table('profiling_anomaly_patterns')
    op.drop_table('partition_results')
    op.drop_table('profiling_rule_sets')
    op.drop_table('profiling_partitions')
    op.drop_table('profiling_jobs')
    op.drop_table('data_queries')
    op.drop_table('attribute_mappings')
    op.drop_table('data_sources_v2')
    
    # Drop ENUMs
    op.execute("DROP TYPE samplecategory")
    op.execute("DROP TYPE samplingstrategy")
    op.execute("DROP TYPE rulecategory")
    op.execute("DROP TYPE profilingstrategy")
    op.execute("DROP TYPE securityclassification")
    op.execute("DROP TYPE datasourcetype")
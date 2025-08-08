#!/usr/bin/env python3
"""
Apply enhancement tables directly using SQL
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def apply_migration():
    """Apply the enhancement migration directly"""
    database_url = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
    engine = create_async_engine(database_url, echo=False)
    
    print("Enhancement Tables Migration - Direct SQL")
    print("=" * 50)
    
    try:
        async with engine.begin() as conn:
            # Check if types already exist
            type_check = await conn.execute(text("""
                SELECT typname FROM pg_type WHERE typname IN (
                    'datasourcetype', 'securityclassification', 'profilingstrategy',
                    'rulecategory', 'samplingstrategy', 'samplecategory'
                )
            """))
            existing_types = [row[0] for row in type_check]
            
            # Create missing ENUMs
            if 'datasourcetype' not in existing_types:
                await conn.execute(text("CREATE TYPE datasourcetype AS ENUM ('POSTGRESQL', 'MYSQL', 'ORACLE', 'SQLSERVER', 'SNOWFLAKE', 'BIGQUERY', 'REDSHIFT', 'FILE')"))
                print("✓ Created datasourcetype enum")
            
            if 'securityclassification' not in existing_types:
                await conn.execute(text("CREATE TYPE securityclassification AS ENUM ('HRCI', 'Confidential', 'Proprietary', 'Public')"))
                print("✓ Created securityclassification enum")
            
            if 'profilingstrategy' not in existing_types:
                await conn.execute(text("CREATE TYPE profilingstrategy AS ENUM ('full_scan', 'sampling', 'streaming', 'partitioned', 'incremental')"))
                print("✓ Created profilingstrategy enum")
            
            if 'rulecategory' not in existing_types:
                await conn.execute(text("CREATE TYPE rulecategory AS ENUM ('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', 'timeliness', 'anomaly', 'custom')"))
                print("✓ Created rulecategory enum")
            
            if 'samplingstrategy' not in existing_types:
                await conn.execute(text("CREATE TYPE samplingstrategy AS ENUM ('random', 'stratified', 'anomaly_based', 'boundary', 'risk_based', 'systematic', 'cluster', 'hybrid')"))
                print("✓ Created samplingstrategy enum")
            
            if 'samplecategory' not in existing_types:
                await conn.execute(text("CREATE TYPE samplecategory AS ENUM ('normal', 'anomaly', 'boundary_high', 'boundary_low', 'outlier', 'edge_case', 'high_risk')"))
                print("✓ Created samplecategory enum")
            
            print("\nCreating tables...")
            
            # Data Sources v2
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_sources_v2 (
                    data_source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    source_name VARCHAR(255) NOT NULL,
                    source_type datasourcetype NOT NULL,
                    description TEXT,
                    connection_config TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    is_validated BOOLEAN NOT NULL DEFAULT false,
                    last_validated_at TIMESTAMP WITH TIME ZONE,
                    validation_error TEXT,
                    default_date_column VARCHAR(255),
                    default_schema VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created data_sources_v2")
            
            # Attribute Mappings
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS attribute_mappings (
                    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    attribute_id INTEGER NOT NULL REFERENCES report_attributes(attribute_id),
                    data_source_id UUID NOT NULL REFERENCES data_sources_v2(data_source_id),
                    table_name VARCHAR(255) NOT NULL,
                    column_name VARCHAR(255) NOT NULL,
                    data_type VARCHAR(100),
                    security_classification securityclassification NOT NULL DEFAULT 'Public',
                    is_primary_key BOOLEAN NOT NULL DEFAULT false,
                    is_nullable BOOLEAN NOT NULL DEFAULT true,
                    column_description TEXT,
                    mapping_confidence INTEGER,
                    llm_suggested BOOLEAN NOT NULL DEFAULT false,
                    manual_override BOOLEAN NOT NULL DEFAULT false,
                    is_validated BOOLEAN NOT NULL DEFAULT false,
                    validation_error TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created attribute_mappings")
            
            # Data Queries
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_queries (
                    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    data_source_id UUID NOT NULL REFERENCES data_sources_v2(data_source_id),
                    query_name VARCHAR(255) NOT NULL,
                    query_type VARCHAR(50) NOT NULL,
                    query_template TEXT NOT NULL,
                    parameters JSONB,
                    estimated_rows INTEGER,
                    execution_timeout_seconds INTEGER NOT NULL DEFAULT 300,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created data_queries")
            
            # Profiling Jobs
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiling_jobs (
                    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    job_name VARCHAR(255) NOT NULL,
                    strategy profilingstrategy NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 5,
                    source_type VARCHAR(50) NOT NULL,
                    source_config JSONB NOT NULL,
                    total_records INTEGER,
                    total_rules INTEGER,
                    estimated_runtime_minutes INTEGER,
                    partition_strategy VARCHAR(50),
                    partition_count INTEGER NOT NULL DEFAULT 1,
                    max_memory_gb INTEGER NOT NULL DEFAULT 8,
                    max_cpu_cores INTEGER NOT NULL DEFAULT 4,
                    status VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    progress_percent INTEGER NOT NULL DEFAULT 0,
                    records_processed INTEGER NOT NULL DEFAULT 0,
                    rules_executed INTEGER NOT NULL DEFAULT 0,
                    anomalies_found INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created profiling_jobs")
            
            # Profiling Partitions
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiling_partitions (
                    partition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID NOT NULL REFERENCES profiling_jobs(job_id),
                    partition_index INTEGER NOT NULL,
                    partition_key VARCHAR(255),
                    start_value VARCHAR(255),
                    end_value VARCHAR(255),
                    estimated_records INTEGER,
                    status VARCHAR(50) NOT NULL,
                    assigned_worker VARCHAR(255),
                    start_time TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    records_processed INTEGER NOT NULL DEFAULT 0,
                    last_checkpoint VARCHAR(255),
                    execution_time_seconds INTEGER,
                    anomalies_found INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT
                )
            """))
            print("✓ Created profiling_partitions")
            
            # Profiling Rule Sets
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiling_rule_sets (
                    rule_set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID NOT NULL REFERENCES profiling_jobs(job_id),
                    rule_set_name VARCHAR(255) NOT NULL,
                    category rulecategory NOT NULL,
                    rules JSONB NOT NULL,
                    rule_count INTEGER NOT NULL,
                    execution_order INTEGER NOT NULL DEFAULT 1,
                    can_parallelize BOOLEAN NOT NULL DEFAULT true,
                    fail_fast BOOLEAN NOT NULL DEFAULT false,
                    estimated_cost INTEGER,
                    requires_full_scan BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created profiling_rule_sets")
            
            # Partition Results
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS partition_results (
                    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    partition_id UUID NOT NULL REFERENCES profiling_partitions(partition_id),
                    rule_set_id UUID NOT NULL REFERENCES profiling_rule_sets(rule_set_id),
                    records_evaluated INTEGER NOT NULL,
                    records_passed INTEGER NOT NULL,
                    records_failed INTEGER NOT NULL,
                    anomalies JSONB,
                    anomaly_count INTEGER NOT NULL DEFAULT 0,
                    statistics JSONB,
                    execution_time_ms INTEGER,
                    memory_used_mb INTEGER
                )
            """))
            print("✓ Created partition_results")
            
            # Profiling Anomaly Patterns
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiling_anomaly_patterns (
                    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID NOT NULL REFERENCES profiling_jobs(job_id),
                    pattern_type VARCHAR(100) NOT NULL,
                    pattern_description TEXT,
                    confidence_score FLOAT,
                    affected_columns TEXT[],
                    pattern_rules JSONB,
                    sample_record_ids TEXT[],
                    sample_count INTEGER,
                    occurrence_count INTEGER,
                    occurrence_percentage FLOAT,
                    recommended_for_sampling BOOLEAN NOT NULL DEFAULT true,
                    sampling_priority INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created profiling_anomaly_patterns")
            
            # Profiling Cache
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiling_cache (
                    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    cache_key VARCHAR(500) NOT NULL UNIQUE,
                    cache_type VARCHAR(50) NOT NULL,
                    cache_data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    is_valid BOOLEAN NOT NULL DEFAULT true,
                    source_identifier VARCHAR(255),
                    source_version VARCHAR(50)
                )
            """))
            print("✓ Created profiling_cache")
            
            # Intelligent Sampling Jobs
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS intelligent_sampling_jobs (
                    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    profiling_job_id UUID NOT NULL REFERENCES profiling_jobs(job_id),
                    target_sample_size INTEGER NOT NULL,
                    sampling_strategies TEXT[] NOT NULL,
                    normal_percentage INTEGER NOT NULL DEFAULT 40,
                    anomaly_percentage INTEGER NOT NULL DEFAULT 30,
                    boundary_percentage INTEGER NOT NULL DEFAULT 20,
                    edge_case_percentage INTEGER NOT NULL DEFAULT 10,
                    source_type VARCHAR(50) NOT NULL,
                    source_criteria JSONB NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    total_samples_selected INTEGER NOT NULL DEFAULT 0,
                    selection_quality_score FLOAT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created intelligent_sampling_jobs")
            
            # Sample Pools
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_pools (
                    pool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID NOT NULL REFERENCES intelligent_sampling_jobs(job_id),
                    category samplecategory NOT NULL,
                    subcategory VARCHAR(100),
                    total_candidates INTEGER NOT NULL,
                    selection_criteria JSONB,
                    diversity_score FLOAT,
                    relevance_score FLOAT,
                    candidate_ids JSONB,
                    candidate_metadata JSONB
                )
            """))
            print("✓ Created sample_pools")
            
            # Intelligent Samples
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS intelligent_samples (
                    sample_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID NOT NULL REFERENCES intelligent_sampling_jobs(job_id),
                    pool_id UUID NOT NULL REFERENCES sample_pools(pool_id),
                    record_identifier VARCHAR(500) NOT NULL,
                    record_data JSONB NOT NULL,
                    category samplecategory NOT NULL,
                    selection_reason TEXT,
                    anomaly_types TEXT[],
                    anomaly_rules TEXT[],
                    anomaly_score FLOAT,
                    boundary_attributes JSONB,
                    boundary_values JSONB,
                    risk_score FLOAT,
                    risk_factors JSONB,
                    selection_strategy samplingstrategy NOT NULL,
                    selection_rank INTEGER,
                    testing_priority INTEGER,
                    must_test BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created intelligent_samples")
            
            # Sampling Rules
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sampling_rules (
                    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    rule_name VARCHAR(255) NOT NULL,
                    rule_type VARCHAR(50) NOT NULL,
                    rule_definition JSONB NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    priority INTEGER NOT NULL DEFAULT 5,
                    applicable_attributes TEXT[],
                    applicable_categories TEXT[],
                    estimated_cost INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created sampling_rules")
            
            # Sample Lineage
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_lineage (
                    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    sample_id UUID NOT NULL REFERENCES intelligent_samples(sample_id),
                    source_type VARCHAR(50) NOT NULL,
                    source_reference VARCHAR(500),
                    selection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    selection_criteria JSONB,
                    changes_from_source JSONB
                )
            """))
            print("✓ Created sample_lineage")
            
            # Profiling Executions
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiling_executions (
                    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    data_source_id UUID REFERENCES data_sources_v2(data_source_id),
                    execution_type VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_time TIMESTAMP WITH TIME ZONE,
                    status VARCHAR(50) NOT NULL,
                    profiling_criteria JSONB NOT NULL,
                    total_records_profiled INTEGER,
                    total_rules_executed INTEGER,
                    execution_time_seconds INTEGER,
                    records_per_second INTEGER,
                    peak_memory_mb INTEGER,
                    rules_passed INTEGER,
                    rules_failed INTEGER,
                    anomalies_detected INTEGER,
                    error_message TEXT,
                    error_details JSONB,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created profiling_executions")
            
            # Secure Data Access Logs
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS secure_data_access_logs (
                    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    table_name VARCHAR(255) NOT NULL,
                    column_name VARCHAR(255) NOT NULL,
                    record_identifier VARCHAR(255),
                    security_classification securityclassification NOT NULL,
                    access_type VARCHAR(50) NOT NULL,
                    access_reason TEXT,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(500),
                    accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(user_id),
                    updated_by INTEGER REFERENCES users(user_id)
                )
            """))
            print("✓ Created secure_data_access_logs")
            
            # Create indexes
            print("\nCreating indexes...")
            
            # Indexes for data_sources_v2
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_datasource_report ON data_sources_v2(report_id, is_active)"))
            
            # Indexes for attribute_mappings
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_mapping_attribute ON attribute_mappings(attribute_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_mapping_source ON attribute_mappings(data_source_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_mapping_security ON attribute_mappings(security_classification)"))
            
            # Indexes for data_queries
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_query_source_type ON data_queries(data_source_id, query_type)"))
            
            # Indexes for profiling_jobs
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_profiling_job_status ON profiling_jobs(status, priority)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_profiling_job_cycle ON profiling_jobs(cycle_id, report_id)"))
            
            # Indexes for profiling_partitions
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_partition_job_status ON profiling_partitions(job_id, status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_partition_worker ON profiling_partitions(assigned_worker, status)"))
            
            # Indexes for profiling_rule_sets
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ruleset_job_category ON profiling_rule_sets(job_id, category)"))
            
            # Indexes for partition_results
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_partition_result ON partition_results(partition_id, rule_set_id)"))
            
            # Indexes for profiling_anomaly_patterns
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_anomaly_pattern_job ON profiling_anomaly_patterns(job_id, pattern_type)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_anomaly_pattern_sampling ON profiling_anomaly_patterns(recommended_for_sampling, sampling_priority)"))
            
            # Indexes for profiling_cache
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cache_key_valid ON profiling_cache(cache_key, is_valid, expires_at)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cache_source ON profiling_cache(source_identifier, cache_type)"))
            
            # Indexes for intelligent_sampling_jobs
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sampling_job_cycle ON intelligent_sampling_jobs(cycle_id, report_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sampling_job_profiling ON intelligent_sampling_jobs(profiling_job_id)"))
            
            # Indexes for sample_pools
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sample_pool_job_category ON sample_pools(job_id, category)"))
            
            # Indexes for intelligent_samples
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intelligent_sample_job ON intelligent_samples(job_id, category)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intelligent_sample_priority ON intelligent_samples(testing_priority, must_test)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intelligent_sample_identifier ON intelligent_samples(record_identifier)"))
            
            # Indexes for sampling_rules
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sampling_rule_report ON sampling_rules(report_id, is_active)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sampling_rule_type ON sampling_rules(rule_type, priority)"))
            
            # Indexes for sample_lineage
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sample_lineage_sample ON sample_lineage(sample_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sample_lineage_source ON sample_lineage(source_type, source_reference)"))
            
            # Indexes for profiling_executions
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_profiling_exec_cycle ON profiling_executions(cycle_id, report_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_profiling_exec_status ON profiling_executions(status, start_time)"))
            
            # Indexes for secure_data_access_logs
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_secure_access_user ON secure_data_access_logs(user_id, accessed_at)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_secure_access_classification ON secure_data_access_logs(security_classification, accessed_at)"))
            
            print("✓ Created all indexes")
            
            print("\n" + "=" * 50)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        raise
    finally:
        await engine.dispose()


def main():
    """Main entry point"""
    asyncio.run(apply_migration())


if __name__ == "__main__":
    main()
-- Enhanced Data Profiling Tables Migration

-- Create enums if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'profilingsourcetype') THEN
        CREATE TYPE profilingsourcetype AS ENUM ('file_upload', 'database_direct', 'api', 'streaming');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'profilingstatus') THEN
        CREATE TYPE profilingstatus AS ENUM ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'profilingmode') THEN
        CREATE TYPE profilingmode AS ENUM ('full_scan', 'sample_based', 'incremental', 'streaming');
    END IF;
END $$;

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS attribute_profile_results CASCADE;
DROP TABLE IF EXISTS data_profiling_jobs CASCADE;
DROP TABLE IF EXISTS data_profiling_configurations CASCADE;
DROP TABLE IF EXISTS data_profiling_uploads CASCADE;

-- Create data_profiling_uploads table first
CREATE TABLE data_profiling_uploads (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create data_profiling_configurations table
CREATE TABLE data_profiling_configurations (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    
    -- Profiling configuration
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type profilingsourcetype NOT NULL,
    profiling_mode profilingmode DEFAULT 'sample_based',
    
    -- Data source configuration
    data_source_id INTEGER,
    file_upload_id INTEGER,
    
    -- Timeframe selection for database profiling
    use_timeframe BOOLEAN DEFAULT FALSE,
    timeframe_start TIMESTAMP,
    timeframe_end TIMESTAMP,
    timeframe_column VARCHAR(255),
    
    -- Sampling configuration
    sample_size BIGINT,
    sample_percentage FLOAT,
    sample_method VARCHAR(50),
    
    -- Performance optimization
    partition_column VARCHAR(255),
    partition_count INTEGER DEFAULT 10,
    max_memory_mb INTEGER DEFAULT 1024,
    
    -- Query configuration for database profiling
    custom_query TEXT,
    table_name VARCHAR(255),
    schema_name VARCHAR(255),
    where_clause TEXT,
    exclude_columns JSON,
    include_columns JSON,
    
    -- Advanced settings
    profile_relationships BOOLEAN DEFAULT TRUE,
    profile_distributions BOOLEAN DEFAULT TRUE,
    profile_patterns BOOLEAN DEFAULT TRUE,
    detect_anomalies BOOLEAN DEFAULT TRUE,
    
    -- Scheduling
    is_scheduled BOOLEAN DEFAULT FALSE,
    schedule_cron VARCHAR(100),
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    updated_by_id INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    FOREIGN KEY (data_source_id) REFERENCES cycle_report_data_sources(id) ON DELETE SET NULL,
    FOREIGN KEY (file_upload_id) REFERENCES data_profiling_uploads(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create data_profiling_jobs table
CREATE TABLE data_profiling_jobs (
    id SERIAL PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    
    -- Job details
    job_id VARCHAR(255) UNIQUE NOT NULL,
    status profilingstatus DEFAULT 'pending' NOT NULL,
    
    -- Execution details
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Data volume
    total_records BIGINT,
    records_processed BIGINT,
    records_failed BIGINT,
    
    -- Performance metrics
    processing_rate FLOAT,
    memory_peak_mb INTEGER,
    cpu_peak_percent FLOAT,
    
    -- Results
    profile_results JSON,
    anomalies_detected INTEGER,
    data_quality_score FLOAT,
    
    -- Error handling
    error_message TEXT,
    error_details JSON,
    retry_count INTEGER DEFAULT 0,
    
    -- Checkpointing for large jobs
    checkpoint_data JSON,
    last_checkpoint_at TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    updated_by_id INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (configuration_id) REFERENCES data_profiling_configurations(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create attribute_profile_results table
CREATE TABLE attribute_profile_results (
    id SERIAL PRIMARY KEY,
    profiling_job_id INTEGER NOT NULL,
    attribute_id INTEGER NOT NULL,
    
    -- Basic statistics
    total_values BIGINT,
    null_count BIGINT,
    null_percentage FLOAT,
    distinct_count BIGINT,
    distinct_percentage FLOAT,
    
    -- Data type analysis
    detected_data_type VARCHAR(50),
    type_consistency FLOAT,
    
    -- Numeric statistics (if applicable)
    min_value FLOAT,
    max_value FLOAT,
    mean_value FLOAT,
    median_value FLOAT,
    std_deviation FLOAT,
    percentile_25 FLOAT,
    percentile_75 FLOAT,
    
    -- String statistics (if applicable)
    min_length INTEGER,
    max_length INTEGER,
    avg_length FLOAT,
    
    -- Pattern analysis
    common_patterns JSON,
    pattern_coverage FLOAT,
    
    -- Value distribution
    top_values JSON,
    value_distribution JSON,
    
    -- Data quality indicators
    completeness_score FLOAT,
    validity_score FLOAT,
    consistency_score FLOAT,
    uniqueness_score FLOAT,
    overall_quality_score FLOAT,
    
    -- Anomalies
    anomaly_count INTEGER,
    anomaly_examples JSON,
    anomaly_rules_triggered JSON,
    
    -- Outliers
    outliers_detected INTEGER,
    outlier_examples JSON,
    
    -- Profiling metadata
    profiling_duration_ms INTEGER,
    sampling_applied BOOLEAN,
    sample_size_used BIGINT,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    updated_by_id INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (profiling_job_id) REFERENCES data_profiling_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (attribute_id) REFERENCES cycle_report_planning_attributes(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create indexes for performance
CREATE INDEX idx_profiling_configs_cycle_report 
ON data_profiling_configurations(cycle_id, report_id);

CREATE INDEX idx_profiling_jobs_configuration 
ON data_profiling_jobs(configuration_id);

CREATE INDEX idx_profiling_jobs_status 
ON data_profiling_jobs(status);

CREATE INDEX idx_attribute_profiles_job 
ON attribute_profile_results(profiling_job_id);

CREATE INDEX idx_attribute_profiles_attribute 
ON attribute_profile_results(attribute_id);

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS update_data_profiling_configurations_updated_at ON data_profiling_configurations;
DROP TRIGGER IF EXISTS update_data_profiling_jobs_updated_at ON data_profiling_jobs;
DROP TRIGGER IF EXISTS update_attribute_profile_results_updated_at ON attribute_profile_results;

-- Create triggers for updated_at
CREATE TRIGGER update_data_profiling_configurations_updated_at 
BEFORE UPDATE ON data_profiling_configurations 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_profiling_jobs_updated_at 
BEFORE UPDATE ON data_profiling_jobs 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attribute_profile_results_updated_at 
BEFORE UPDATE ON attribute_profile_results 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
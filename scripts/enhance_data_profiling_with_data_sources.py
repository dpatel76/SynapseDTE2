"""
Enhancement script to update data profiling to support both uploaded files and data sources
"""

# SQL script to add data source support to data profiling
sql_updates = """
-- Add data source reference to profiling phases
ALTER TABLE workflow_data_profiling_phases
ADD COLUMN IF NOT EXISTS use_data_source BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS data_source_config JSON;

-- Add data source tracking to profiling files
ALTER TABLE cycle_report_data_profiling_files
ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'file',
ADD COLUMN IF NOT EXISTS data_source_id UUID REFERENCES data_sources_v2(data_source_id),
ADD COLUMN IF NOT EXISTS query_config JSON;

-- Create a view to check data source availability
CREATE OR REPLACE VIEW v_data_profiling_source_status AS
SELECT 
    p.phase_id,
    p.cycle_id,
    p.report_id,
    p.status as phase_status,
    -- Check for uploaded files
    COUNT(DISTINCT f.file_id) as uploaded_files_count,
    -- Check for data sources via attribute mappings
    COUNT(DISTINCT am.data_source_id) as mapped_data_sources_count,
    -- Determine if data source is available
    CASE 
        WHEN COUNT(DISTINCT am.data_source_id) > 0 THEN true
        ELSE false
    END as has_data_source,
    -- Determine if files are uploaded
    CASE 
        WHEN COUNT(DISTINCT f.file_id) > 0 THEN true
        ELSE false
    END as has_uploaded_files,
    -- Determine preferred source
    CASE 
        WHEN COUNT(DISTINCT am.data_source_id) > 0 THEN 'data_source'
        WHEN COUNT(DISTINCT f.file_id) > 0 THEN 'uploaded_files'
        ELSE 'none'
    END as preferred_source
FROM workflow_data_profiling_phases p
LEFT JOIN cycle_report_data_profiling_files f 
    ON f.phase_id = p.phase_id
    AND f.is_deleted = false
LEFT JOIN cycle_report_planning_attributes ra
    ON ra.cycle_id = p.cycle_id
    AND ra.report_id = p.report_id
    AND ra.is_active = true
LEFT JOIN attribute_mappings am
    ON am.attribute_id = ra.id
GROUP BY p.phase_id, p.cycle_id, p.report_id, p.status;

-- Add function to get sample data from data source
CREATE OR REPLACE FUNCTION get_attribute_sample_data(
    p_attribute_id INTEGER,
    p_sample_size INTEGER DEFAULT 100
) RETURNS JSON AS $$
DECLARE
    v_mapping RECORD;
    v_sample_data JSON;
BEGIN
    -- Get attribute mapping
    SELECT 
        am.*,
        ds.source_type,
        ds.connection_config
    INTO v_mapping
    FROM attribute_mappings am
    JOIN data_sources_v2 ds ON ds.data_source_id = am.data_source_id
    WHERE am.attribute_id = p_attribute_id
    AND ds.is_active = true
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- For now, return mock data
    -- In production, this would query the actual data source
    RETURN json_build_object(
        'source_type', 'data_source',
        'table_name', v_mapping.table_name,
        'column_name', v_mapping.column_name,
        'sample_count', p_sample_size,
        'sample_values', ARRAY['value1', 'value2', 'value3']
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_attribute_sample_data IS 'Get sample data for an attribute from its mapped data source';
"""

# Python code updates for the data profiling endpoint
python_updates = '''
# Add this to the data profiling endpoint

async def get_attribute_context_with_data_source(
    attr: ReportAttribute,
    files: List[DataProfilingFile],
    db: AsyncSession
) -> Dict[str, Any]:
    """Build attribute context using either uploaded files or data source"""
    
    # Check if attribute has a data source mapping
    mapping_query = select(AttributeMapping).join(
        DataSource
    ).where(
        and_(
            AttributeMapping.attribute_id == attr.id,
            DataSource.is_active == True
        )
    )
    mapping_result = await db.execute(mapping_query)
    mapping = mapping_result.scalar_one_or_none()
    
    sample_data = []
    data_source_info = None
    
    if mapping:
        # Use data source
        logger.info(f"Using data source for attribute {attr.attribute_name}")
        
        # Get sample data from data source
        # This is a simplified version - real implementation would query the actual source
        sample_query = f"""
        SELECT DISTINCT {mapping.column_name}
        FROM {mapping.table_name}
        WHERE {mapping.column_name} IS NOT NULL
        LIMIT 100
        """
        
        # For now, use mock data
        sample_data = [f"sample_{i}" for i in range(10)]
        
        data_source_info = {
            "type": "data_source",
            "table": mapping.table_name,
            "column": mapping.column_name,
            "data_type": mapping.data_type
        }
        
    elif files:
        # Use uploaded files
        logger.info(f"Using uploaded files for attribute {attr.attribute_name}")
        
        # Extract sample data from files
        for file in files[:1]:  # Use first file for sample
            try:
                if file.file_path.endswith('.csv'):
                    import pandas as pd
                    df = pd.read_csv(file.file_path, nrows=100)
                    
                    # Try to find matching column
                    matching_cols = [col for col in df.columns 
                                   if attr.attribute_name.lower() in col.lower()]
                    
                    if matching_cols:
                        col = matching_cols[0]
                        sample_data = df[col].dropna().unique()[:10].tolist()
                        
            except Exception as e:
                logger.error(f"Error reading file {file.file_path}: {e}")
        
        data_source_info = {
            "type": "uploaded_files",
            "file_count": len(files)
        }
    
    # Build enhanced context
    context = {
        "attribute_name": attr.attribute_name,
        "description": attr.description,
        "data_type": attr.data_type,
        "is_mandatory": attr.mandatory_flag == "Mandatory",
        "is_cde": attr.cde_flag,
        "has_issues": attr.historical_issues_flag,
        "sample_data": sample_data,
        "data_source": data_source_info,
        "validation_rules": attr.validation_rules,
        "typical_source_documents": attr.typical_source_documents,
        "keywords_to_look_for": attr.keywords_to_look_for,
        "testing_approach": attr.testing_approach,
    }
    
    return context

# Update the generate rules endpoint
@router.post("/cycles/{cycle_id}/reports/{report_id}/generate-rules-enhanced")
async def generate_profiling_rules_enhanced(
    cycle_id: int,
    report_id: int,
    preferred_provider: str = "claude",
    use_data_source: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Generate profiling rules using either uploaded files or data sources"""
    
    # Get phase
    phase_query = select(DataProfilingPhase).where(
        and_(
            DataProfilingPhase.cycle_id == cycle_id,
            DataProfilingPhase.report_id == report_id
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Data profiling phase not found")
    
    # Get attributes
    attributes_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    )
    attributes_result = await db.execute(attributes_query)
    attributes = attributes_result.scalars().all()
    
    # Get uploaded files if any
    files_query = select(DataProfilingFile).where(
        and_(
            DataProfilingFile.phase_id == phase.phase_id,
            DataProfilingFile.is_deleted == False
        )
    )
    files_result = await db.execute(files_query)
    files = files_result.scalars().all()
    
    # Check data source availability
    data_source_available = False
    if use_data_source:
        mapping_check = select(AttributeMapping).join(
            ReportAttribute
        ).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        )
        mapping_result = await db.execute(mapping_check)
        data_source_available = mapping_result.scalar_one_or_none() is not None
    
    # Log source selection
    logger.info(f"Profiling rule generation - Data source available: {data_source_available}, Files available: {len(files) > 0}")
    
    if not data_source_available and len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="No data source configured and no files uploaded. Please upload files or configure a data source."
        )
    
    # Start background job
    job_id = str(uuid.uuid4())
    job_manager.jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": "Initializing profiling rule generation",
        "attribute_count": len(attributes),
        "using_data_source": data_source_available and use_data_source
    }
    
    # Run job in background
    asyncio.create_task(
        job_manager.run_job(
            job_id,
            _generate_profiling_rules_enhanced_task,
            phase.phase_id, attributes, files, preferred_provider, 
            current_user.user_id, use_data_source and data_source_available
        )
    )
    
    return {
        "job_id": job_id,
        "message": "Profiling rule generation started",
        "attributes_to_process": len(attributes),
        "using_data_source": data_source_available and use_data_source
    }
'''

print("Enhancement script created. This script provides:")
print("1. SQL updates to support data sources in data profiling")
print("2. Python code updates for the enhanced endpoint")
print("3. Logic to automatically use data sources when available")
print("4. Fallback to uploaded files when no data source is configured")
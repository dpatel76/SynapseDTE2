"""
Data Profiling Failed Records API Endpoint
Provides detailed failed records with primary key attributes
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
import json
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.data_profiling import ProfilingResult, ProfilingRule, DataProfilingRuleVersion
from app.models.report_attribute import ReportAttribute
from app.models.planning import PlanningPDEMapping
from app.models.cycle_report_data_source import CycleReportDataSource
from app.models.workflow import WorkflowPhase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data-profiling-failed-records"])


@router.get("/results/{result_id}/failed-records")
async def get_failed_records(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip")
) -> Dict[str, Any]:
    """
    Get failed records for a profiling result with primary key attributes
    """
    logger.info(f"Getting failed records for result_id: {result_id}")
    
    # Get the profiling result
    result = await db.get(ProfilingResult, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Profiling result not found")
    
    # Get the rule associated with this result
    rule = await db.get(ProfilingRule, result.rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Profiling rule not found")
    
    # Get the phase from the rule
    phase = await db.get(WorkflowPhase, rule.phase_id)
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # Get the planning phase for this cycle/report to get attributes
    planning_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == phase.cycle_id,
            WorkflowPhase.report_id == phase.report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    planning_phase_result = await db.execute(planning_phase_query)
    planning_phase = planning_phase_result.scalar_one_or_none()
    
    if not planning_phase:
        return {
            "result_id": result_id,
            "rule_name": rule.rule_name,
            "attribute_tested": rule.attribute_name,
            "total_failed": result.failed_count,
            "error": "Planning phase not found - cannot retrieve attributes",
            "failed_records": []
        }
    
    # Get the attribute being tested from planning phase
    attribute_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.phase_id == planning_phase.phase_id,
            ReportAttribute.attribute_name == rule.attribute_name
        )
    )
    attribute_result = await db.execute(attribute_query)
    attribute = attribute_result.scalar_one_or_none()
    
    if not attribute:
        raise HTTPException(status_code=404, detail=f"Attribute '{rule.attribute_name}' not found in planning phase")
    
    # Get all primary key attributes from planning phase
    pk_attributes_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.phase_id == planning_phase.phase_id,
            ReportAttribute.is_primary_key == True
        )
    ).order_by(ReportAttribute.primary_key_order.nulls_last(), ReportAttribute.attribute_name)
    
    pk_attributes_result = await db.execute(pk_attributes_query)
    pk_attributes = pk_attributes_result.scalars().all()
    
    # Get PDE mappings for all attributes (PK + tested attribute)
    all_attributes = pk_attributes + ([attribute] if attribute not in pk_attributes else [])
    attribute_ids = [attr.id for attr in all_attributes]
    
    # Get PDE mappings
    pde_mappings_query = select(PlanningPDEMapping).where(
        and_(
            PlanningPDEMapping.phase_id == planning_phase.phase_id,
            PlanningPDEMapping.attribute_id.in_(attribute_ids)
        )
    )
    pde_mappings_result = await db.execute(pde_mappings_query)
    pde_mappings = {m.attribute_id: m for m in pde_mappings_result.scalars().all()}
    
    # Get data source
    tested_attr_mapping = pde_mappings.get(attribute.id)
    if not tested_attr_mapping or not tested_attr_mapping.data_source_id:
        return {
            "result_id": result_id,
            "rule_name": rule.rule_name,
            "attribute_tested": attribute.attribute_name,
            "total_failed": result.failed_count,
            "error": "No data source configured for attribute",
            "failed_records": []
        }
    
    data_source = await db.get(CycleReportDataSource, tested_attr_mapping.data_source_id)
    if not data_source:
        return {
            "result_id": result_id,
            "rule_name": rule.rule_name,
            "attribute_tested": attribute.attribute_name,
            "total_failed": result.failed_count,
            "error": "Data source not found",
            "failed_records": []
        }
    
    # Build column mapping
    column_mapping = {}
    pk_columns = []
    
    for attr in pk_attributes:
        mapping = pde_mappings.get(attr.id)
        if mapping and mapping.pde_code:  # pde_code contains the actual column name
            column_mapping[attr.attribute_name] = mapping.pde_code
            pk_columns.append(mapping.pde_code)
    
    # Add the tested attribute column
    tested_column = tested_attr_mapping.pde_code
    column_mapping[attribute.attribute_name] = tested_column
    
    # Get failed records based on data source type
    failed_records = []
    
    if data_source.source_type == 'postgresql':
        try:
            import psycopg2
            
            connection_config = data_source.connection_config or {}
            host = connection_config.get('host', 'localhost')
            port = connection_config.get('port', '5432')
            database = connection_config.get('database', 'synapse_dt')
            user = connection_config.get('user', 'synapse_user')
            password = connection_config.get('password', 'synapse_password')
            
            conn_str = f"host={host} port={port} dbname={database} user={user} password={password}"
            
            with psycopg2.connect(conn_str) as conn:
                table_name = connection_config.get('table_name', 'data_table')
                schema_name = connection_config.get('schema', 'public')
                
                # Re-execute the rule to identify failed records
                # This is a simplified version - in production, you'd want to cache this
                import pandas as pd
                import numpy as np
                
                # Get all columns needed
                all_columns = list(set(pk_columns + [tested_column]))
                columns_str = ', '.join(all_columns)
                
                # Also try to get a row identifier column if available
                check_id_query = f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = '{schema_name}' 
                    AND table_name = '{table_name}'
                    AND column_name IN ('id', 'row_id', 'record_id', '_row_number')
                    LIMIT 1
                """
                
                with conn.cursor() as cur:
                    cur.execute(check_id_query)
                    id_result = cur.fetchone()
                    id_column = id_result[0] if id_result else None
                    
                    if id_column and id_column not in all_columns:
                        all_columns.append(id_column)
                        columns_str = ', '.join(all_columns)
                
                # Query to get data
                query = f"SELECT {columns_str} FROM {schema_name}.{table_name}"
                
                # Execute query and load into pandas
                import pandas.io.sql as sqlio
                df = sqlio.read_sql_query(query, conn)
                
                # Convert numeric columns
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass
                
                # Execute the rule code to identify failed records
                exec_globals = {
                    'pd': pd,
                    'np': np,
                    'df': df,
                    'column_name': tested_column,
                    're': __import__('re'),
                    'datetime': __import__('datetime')
                }
                exec_locals = {}
                
                # Execute the rule code
                if rule.rule_code and rule.rule_code.strip().startswith('def check_rule'):
                    exec(rule.rule_code, exec_globals, exec_locals)
                    
                    # Call the function to get pass/fail for each record
                    # Modified approach: get row-by-row results
                    check_rule = exec_locals.get('check_rule')
                    if check_rule:
                        # Create a mask for failed records
                        def check_single_value(x):
                            try:
                                # Create a single-row DataFrame for checking
                                single_df = pd.DataFrame({tested_column: [x]})
                                result = check_rule(single_df, tested_column)
                                return result.get('failed', 0) == 0  # True if passed
                            except:
                                return False  # If check fails, consider it failed
                        
                        # Apply check to each value
                        df['_passed'] = df[tested_column].apply(check_single_value)
                        failed_df = df[~df['_passed']].drop('_passed', axis=1)
                    else:
                        # No check_rule function found
                        failed_df = pd.DataFrame()
                else:
                    # For non-function rules, use a simple null check as fallback
                    failed_df = df[df[tested_column].isna()]
                
                # Convert failed records to dict format
                for idx, row in failed_df.head(limit).iterrows():
                    record = {
                        "row_number": idx + 1,
                        "primary_key_values": {},
                        "tested_attribute": {
                            "name": attribute.attribute_name,
                            "column": tested_column,
                            "value": row[tested_column] if tested_column in row else None
                        },
                        "failure_reason": f"Value failed {rule.rule_type} validation"
                    }
                    
                    # Add primary key values
                    for attr in pk_attributes:
                        col = column_mapping.get(attr.attribute_name)
                        if col and col in row:
                            record["primary_key_values"][attr.attribute_name] = row[col]
                    
                    # Add row identifier if available
                    if id_column and id_column in row:
                        record["record_id"] = row[id_column]
                    
                    failed_records.append(record)
                
        except Exception as e:
            logger.error(f"Error retrieving failed records: {str(e)}")
            return {
                "result_id": result_id,
                "rule_name": rule.rule_name,
                "attribute_tested": attribute.attribute_name,
                "total_failed": result.failed_count,
                "error": f"Error retrieving failed records: {str(e)}",
                "failed_records": []
            }
            
    elif data_source.source_type in ['csv', 'excel']:
        # For file sources, we'd need to re-read the file
        # This is a placeholder - implement file reading logic
        logger.warning(f"File-based failed records not implemented yet for {data_source.source_type}")
    
    return {
        "result_id": result_id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "attribute_tested": attribute.attribute_name,
        "primary_key_attributes": [attr.attribute_name for attr in pk_attributes],
        "total_failed": result.failed_count,
        "records_returned": len(failed_records),
        "limit": limit,
        "offset": offset,
        "failed_records": failed_records
    }
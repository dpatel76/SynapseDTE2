#!/usr/bin/env python3
"""
Sample Selection Phase Database Migration
Creates tables, enums, and indexes for the sample selection phase
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def create_sample_selection_tables():
    """Create sample selection phase tables and enums"""
    
    # Database connection
    DATABASE_URL = 'postgresql://synapse_user:synapse_secure_2024@localhost:5432/synapse_dt'
    
    # Create database connection
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print('Creating sample selection tables and enums...')
        
        # Create ENUM types first
        await conn.execute('''
            DO $$ BEGIN
                CREATE TYPE sample_generation_method_enum AS ENUM (
                    'LLM Generated',
                    'Manual Upload', 
                    'Hybrid'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        ''')
        
        await conn.execute('''
            DO $$ BEGIN
                CREATE TYPE sample_status_enum AS ENUM (
                    'Draft',
                    'Pending Approval',
                    'Approved',
                    'Rejected',
                    'Revision Required'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        ''')
        
        await conn.execute('''
            DO $$ BEGIN
                CREATE TYPE sample_validation_status_enum AS ENUM (
                    'Valid',
                    'Invalid',
                    'Warning',
                    'Needs Review'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        ''')
        
        await conn.execute('''
            DO $$ BEGIN
                CREATE TYPE sample_type_enum AS ENUM (
                    'Population Sample',
                    'Targeted Sample',
                    'Exception Sample',
                    'Control Sample'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        ''')
        
        print('Sample selection ENUM types created successfully')
        
        # Create sample_sets table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_sets (
                set_id VARCHAR(36) PRIMARY KEY,
                cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                report_id INTEGER NOT NULL REFERENCES reports(report_id),
                set_name VARCHAR(255) NOT NULL,
                description TEXT,
                generation_method sample_generation_method_enum NOT NULL,
                sample_type sample_type_enum NOT NULL,
                status sample_status_enum NOT NULL DEFAULT 'Draft',
                target_sample_size INTEGER,
                actual_sample_size INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER NOT NULL REFERENCES users(user_id),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                approved_by INTEGER REFERENCES users(user_id),
                approved_at TIMESTAMP WITH TIME ZONE,
                approval_notes TEXT,
                generation_rationale TEXT,
                selection_criteria JSONB,
                quality_score FLOAT,
                sample_metadata JSONB
            );
        ''')
        
        # Create sample_records table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_records (
                record_id VARCHAR(36) PRIMARY KEY,
                set_id VARCHAR(36) NOT NULL REFERENCES sample_sets(set_id),
                sample_identifier VARCHAR(255) NOT NULL,
                primary_key_value VARCHAR(255) NOT NULL,
                sample_data JSONB NOT NULL,
                risk_score FLOAT,
                validation_status sample_validation_status_enum NOT NULL DEFAULT 'Needs Review',
                validation_score FLOAT,
                selection_rationale TEXT,
                data_source_info JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        ''')
        
        # Create sample_validation_results table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_validation_results (
                validation_id VARCHAR(36) PRIMARY KEY,
                set_id VARCHAR(36) NOT NULL REFERENCES sample_sets(set_id),
                validation_type VARCHAR(100) NOT NULL,
                validation_rules JSONB NOT NULL,
                overall_status sample_validation_status_enum NOT NULL,
                total_samples INTEGER NOT NULL,
                valid_samples INTEGER NOT NULL,
                invalid_samples INTEGER NOT NULL,
                warning_samples INTEGER NOT NULL,
                overall_quality_score FLOAT NOT NULL,
                validation_summary JSONB,
                recommendations JSONB,
                validated_by INTEGER NOT NULL REFERENCES users(user_id),
                validated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        ''')
        
        # Create sample_validation_issues table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_validation_issues (
                issue_id VARCHAR(36) PRIMARY KEY,
                validation_id VARCHAR(36) NOT NULL REFERENCES sample_validation_results(validation_id),
                record_id VARCHAR(36) NOT NULL REFERENCES sample_records(record_id),
                issue_type VARCHAR(100) NOT NULL,
                severity VARCHAR(50) NOT NULL,
                field_name VARCHAR(255),
                issue_description TEXT NOT NULL,
                suggested_fix TEXT,
                is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
                resolved_at TIMESTAMP WITH TIME ZONE,
                resolved_by INTEGER REFERENCES users(user_id)
            );
        ''')
        
        # Create sample_approval_history table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_approval_history (
                approval_id VARCHAR(36) PRIMARY KEY,
                set_id VARCHAR(36) NOT NULL REFERENCES sample_sets(set_id),
                approval_step VARCHAR(100) NOT NULL,
                decision VARCHAR(50) NOT NULL,
                approved_by INTEGER NOT NULL REFERENCES users(user_id),
                approved_at TIMESTAMP WITH TIME ZONE NOT NULL,
                feedback TEXT,
                requested_changes JSONB,
                conditional_approval BOOLEAN NOT NULL DEFAULT FALSE,
                approval_conditions JSONB,
                previous_status sample_status_enum,
                new_status sample_status_enum NOT NULL
            );
        ''')
        
        # Create llm_sample_generations table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS llm_sample_generations (
                generation_id VARCHAR(36) PRIMARY KEY,
                set_id VARCHAR(36) NOT NULL REFERENCES sample_sets(set_id),
                cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                report_id INTEGER NOT NULL REFERENCES reports(report_id),
                requested_sample_size INTEGER NOT NULL,
                actual_samples_generated INTEGER NOT NULL,
                generation_prompt TEXT,
                selection_criteria JSONB NOT NULL,
                risk_focus_areas JSONB,
                exclude_criteria JSONB,
                include_edge_cases BOOLEAN NOT NULL DEFAULT TRUE,
                randomization_seed INTEGER,
                llm_model_used VARCHAR(100),
                generation_rationale TEXT NOT NULL,
                confidence_score FLOAT NOT NULL,
                risk_coverage JSONB,
                estimated_testing_time INTEGER,
                llm_metadata JSONB,
                generated_by INTEGER NOT NULL REFERENCES users(user_id),
                generated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        ''')
        
        # Create sample_upload_history table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_upload_history (
                upload_id VARCHAR(36) PRIMARY KEY,
                set_id VARCHAR(36) NOT NULL REFERENCES sample_sets(set_id),
                upload_method VARCHAR(50) NOT NULL,
                original_filename VARCHAR(255),
                file_size_bytes INTEGER,
                total_rows INTEGER NOT NULL,
                valid_rows INTEGER NOT NULL,
                invalid_rows INTEGER NOT NULL,
                primary_key_column VARCHAR(255) NOT NULL,
                data_mapping JSONB,
                validation_rules_applied JSONB,
                data_quality_score FLOAT NOT NULL,
                upload_summary JSONB,
                processing_time_ms INTEGER NOT NULL,
                uploaded_by INTEGER NOT NULL REFERENCES users(user_id),
                uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        ''')
        
        # Create sample_selection_audit_log table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sample_selection_audit_log (
                audit_id VARCHAR(36) PRIMARY KEY,
                cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                report_id INTEGER NOT NULL REFERENCES reports(report_id),
                set_id VARCHAR(36) REFERENCES sample_sets(set_id),
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(36),
                performed_by INTEGER NOT NULL REFERENCES users(user_id),
                performed_at TIMESTAMP WITH TIME ZONE NOT NULL,
                old_values JSONB,
                new_values JSONB,
                notes TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                session_id VARCHAR(100)
            );
        ''')
        
        print('Sample selection tables created successfully')
        
        # Create indexes
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_sample_sets_cycle_report ON sample_sets(cycle_id, report_id);',
            'CREATE INDEX IF NOT EXISTS idx_sample_sets_status ON sample_sets(status);',
            'CREATE INDEX IF NOT EXISTS idx_sample_sets_created_at ON sample_sets(created_at);',
            'CREATE INDEX IF NOT EXISTS idx_sample_sets_set_name ON sample_sets(set_name);',
            
            'CREATE INDEX IF NOT EXISTS idx_sample_records_set_id ON sample_records(set_id);',
            'CREATE INDEX IF NOT EXISTS idx_sample_records_identifier ON sample_records(sample_identifier);',
            'CREATE INDEX IF NOT EXISTS idx_sample_records_validation_status ON sample_records(validation_status);',
            
            'CREATE INDEX IF NOT EXISTS idx_validation_issues_severity ON sample_validation_issues(severity);',
            'CREATE INDEX IF NOT EXISTS idx_validation_issues_resolved ON sample_validation_issues(is_resolved);',
            
            'CREATE INDEX IF NOT EXISTS idx_approval_history_set_id ON sample_approval_history(set_id);',
            'CREATE INDEX IF NOT EXISTS idx_approval_history_decision ON sample_approval_history(decision);',
            'CREATE INDEX IF NOT EXISTS idx_approval_history_approved_at ON sample_approval_history(approved_at);',
            
            'CREATE INDEX IF NOT EXISTS idx_llm_generations_cycle_report ON llm_sample_generations(cycle_id, report_id);',
            'CREATE INDEX IF NOT EXISTS idx_llm_generations_generated_at ON llm_sample_generations(generated_at);',
            
            'CREATE INDEX IF NOT EXISTS idx_upload_history_uploaded_at ON sample_upload_history(uploaded_at);',
            'CREATE INDEX IF NOT EXISTS idx_upload_history_method ON sample_upload_history(upload_method);',
            
            'CREATE INDEX IF NOT EXISTS idx_sample_audit_cycle_report ON sample_selection_audit_log(cycle_id, report_id);',
            'CREATE INDEX IF NOT EXISTS idx_sample_audit_action ON sample_selection_audit_log(action);',
            'CREATE INDEX IF NOT EXISTS idx_sample_audit_performed_at ON sample_selection_audit_log(performed_at);',
            'CREATE INDEX IF NOT EXISTS idx_sample_audit_entity ON sample_selection_audit_log(entity_type, entity_id);'
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        print(f'Created {len(indexes)} indexes for sample selection tables')
        
        # Count total tables
        tables_result = await conn.fetch('''
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE '%sample%'
        ''')
        sample_table_count = tables_result[0]['count']
        
        total_tables_result = await conn.fetch('''
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        ''')
        total_table_count = total_tables_result[0]['count']
        
        print(f'Database now has {sample_table_count} sample selection tables')
        print(f'Total database tables: {total_table_count}')
        print('Sample selection database migration completed successfully!')
        
    except Exception as e:
        print(f'Error during migration: {e}')
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_sample_selection_tables()) 
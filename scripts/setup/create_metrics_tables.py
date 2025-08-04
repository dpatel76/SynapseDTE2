#!/usr/bin/env python3
"""
Script to create metrics tables directly in the database
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_metrics_tables():
    """Create the metrics tables"""
    try:
        # Database connection
        conn = psycopg2.connect(
            host='localhost',
            database='synapse_dt',
            user='synapse_user',
            password='synapse_password'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print('✅ Creating metrics tables...')
        
        # Create phase_metrics table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS phase_metrics (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                cycle_id INTEGER NOT NULL,
                report_id INTEGER NOT NULL,
                phase_name VARCHAR(50) NOT NULL,
                lob_name VARCHAR(100),
                total_attributes INTEGER DEFAULT 0,
                approved_attributes INTEGER DEFAULT 0,
                attributes_with_issues INTEGER DEFAULT 0,
                primary_keys INTEGER DEFAULT 0,
                non_pk_attributes INTEGER DEFAULT 0,
                total_samples INTEGER DEFAULT 0,
                approved_samples INTEGER DEFAULT 0,
                failed_samples INTEGER DEFAULT 0,
                total_test_cases INTEGER DEFAULT 0,
                completed_test_cases INTEGER DEFAULT 0,
                passed_test_cases INTEGER DEFAULT 0,
                failed_test_cases INTEGER DEFAULT 0,
                total_observations INTEGER DEFAULT 0,
                approved_observations INTEGER DEFAULT 0,
                completion_time_minutes FLOAT,
                on_time_completion BOOLEAN,
                submissions_for_approval INTEGER DEFAULT 0,
                data_providers_assigned INTEGER DEFAULT 0,
                changes_to_data_providers INTEGER DEFAULT 0,
                rfi_sent INTEGER DEFAULT 0,
                rfi_completed INTEGER DEFAULT 0,
                rfi_pending INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY(cycle_id) REFERENCES test_cycles(cycle_id),
                FOREIGN KEY(report_id) REFERENCES reports(report_id)
            );
        """)
        print('  ✅ Created phase_metrics table')
        
        # Create execution_metrics table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS execution_metrics (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                cycle_id INTEGER NOT NULL,
                report_id INTEGER NOT NULL,
                execution_run_id UUID NOT NULL,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                document_tests INTEGER DEFAULT 0,
                database_tests INTEGER DEFAULT 0,
                execution_time_seconds FLOAT,
                error_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY(cycle_id) REFERENCES test_cycles(cycle_id),
                FOREIGN KEY(report_id) REFERENCES reports(report_id)
            );
        """)
        print('  ✅ Created execution_metrics table')
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_phase_metrics_cycle_id ON phase_metrics(cycle_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_phase_metrics_report_id ON phase_metrics(report_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_phase_metrics_phase_name ON phase_metrics(phase_name);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_execution_metrics_cycle_id ON execution_metrics(cycle_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_execution_metrics_report_id ON execution_metrics(report_id);")
        print('  ✅ Created indexes')
        
        cur.close()
        conn.close()
        print('✅ Metrics tables creation completed!')
        
    except Exception as e:
        print(f'❌ Error creating metrics tables: {str(e)}')

if __name__ == "__main__":
    create_metrics_tables()
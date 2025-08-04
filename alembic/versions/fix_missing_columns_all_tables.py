"""Fix missing columns in all refactored tables

Revision ID: fix_missing_columns_2025
Revises: 
Create Date: 2025-07-11 17:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_missing_columns_2025'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Fix cycle_report_attributes_planning table
    # Add is_active column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='is_active'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;
            END IF;
        END $$;
    """)
    
    # Add is_latest_version column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='is_latest_version'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN is_latest_version BOOLEAN DEFAULT TRUE NOT NULL;
            END IF;
        END $$;
    """)
    
    # Add version column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='version'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN version INTEGER DEFAULT 1 NOT NULL;
            END IF;
        END $$;
    """)
    
    # Add master_attribute_id column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='master_attribute_id'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN master_attribute_id INTEGER;
                
                -- Add foreign key constraint
                ALTER TABLE cycle_report_planning_attributes
                ADD CONSTRAINT fk_master_attribute 
                FOREIGN KEY (master_attribute_id) 
                REFERENCES cycle_report_planning_attributes(id);
                
                -- Add index
                CREATE INDEX idx_master_attribute_id 
                ON cycle_report_attributes_planning(master_attribute_id);
            END IF;
        END $$;
    """)
    
    # Add version_notes column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='version_notes'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN version_notes TEXT;
            END IF;
        END $$;
    """)
    
    # Add change_reason column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='change_reason'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN change_reason VARCHAR(100);
            END IF;
        END $$;
    """)
    
    # Add replaced_attribute_id column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='replaced_attribute_id'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN replaced_attribute_id INTEGER;
                
                -- Add foreign key constraint
                ALTER TABLE cycle_report_planning_attributes
                ADD CONSTRAINT fk_replaced_attribute 
                FOREIGN KEY (replaced_attribute_id) 
                REFERENCES cycle_report_planning_attributes(id);
            END IF;
        END $$;
    """)
    
    # Add version timestamps
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='version_created_at'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN version_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='version_created_by'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN version_created_by INTEGER NOT NULL DEFAULT 1;
                
                -- Add foreign key constraint
                ALTER TABLE cycle_report_planning_attributes
                ADD CONSTRAINT fk_version_created_by 
                FOREIGN KEY (version_created_by) 
                REFERENCES users(user_id);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='approved_at'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN approved_at TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='approved_by'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN approved_by INTEGER;
                
                -- Add foreign key constraint
                ALTER TABLE cycle_report_planning_attributes
                ADD CONSTRAINT fk_approved_by 
                FOREIGN KEY (approved_by) 
                REFERENCES users(user_id);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='archived_at'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN archived_at TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='cycle_report_attributes_planning' 
                AND column_name='archived_by'
            ) THEN
                ALTER TABLE cycle_report_planning_attributes 
                ADD COLUMN archived_by INTEGER;
                
                -- Add foreign key constraint
                ALTER TABLE cycle_report_planning_attributes
                ADD CONSTRAINT fk_archived_by 
                FOREIGN KEY (archived_by) 
                REFERENCES users(user_id);
            END IF;
        END $$;
    """)
    
    # Create attribute_version_change_logs table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS attribute_version_change_logs (
            log_id SERIAL PRIMARY KEY,
            attribute_id INTEGER NOT NULL,
            change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('created', 'updated', 'approved', 'rejected', 'archived', 'restored')),
            version_number INTEGER NOT NULL,
            change_notes TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            changed_by INTEGER NOT NULL,
            field_changes TEXT,
            impact_assessment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (attribute_id) REFERENCES cycle_report_planning_attributes(id),
            FOREIGN KEY (changed_by) REFERENCES users(user_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id),
            FOREIGN KEY (updated_by) REFERENCES users(user_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_version_change_logs_attribute_id 
        ON attribute_version_change_logs(attribute_id);
    """)
    
    # Create attribute_version_comparisons table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS attribute_version_comparisons (
            comparison_id SERIAL PRIMARY KEY,
            version_a_id INTEGER NOT NULL,
            version_b_id INTEGER NOT NULL,
            differences_found INTEGER NOT NULL DEFAULT 0,
            comparison_summary TEXT,
            impact_score FLOAT,
            compared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            compared_by INTEGER NOT NULL,
            comparison_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (version_a_id) REFERENCES cycle_report_planning_attributes(id),
            FOREIGN KEY (version_b_id) REFERENCES cycle_report_planning_attributes(id),
            FOREIGN KEY (compared_by) REFERENCES users(user_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id),
            FOREIGN KEY (updated_by) REFERENCES users(user_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_version_comparisons_versions 
        ON attribute_version_comparisons(version_a_id, version_b_id);
    """)


def downgrade():
    # Drop added columns and tables
    op.execute("""
        ALTER TABLE cycle_report_planning_attributes 
        DROP COLUMN IF EXISTS is_active,
        DROP COLUMN IF EXISTS is_latest_version,
        DROP COLUMN IF EXISTS version,
        DROP COLUMN IF EXISTS master_attribute_id,
        DROP COLUMN IF EXISTS version_notes,
        DROP COLUMN IF EXISTS change_reason,
        DROP COLUMN IF EXISTS replaced_attribute_id,
        DROP COLUMN IF EXISTS version_created_at,
        DROP COLUMN IF EXISTS version_created_by,
        DROP COLUMN IF EXISTS approved_at,
        DROP COLUMN IF EXISTS approved_by,
        DROP COLUMN IF EXISTS archived_at,
        DROP COLUMN IF EXISTS archived_by;
        
        DROP TABLE IF EXISTS attribute_version_comparisons;
        DROP TABLE IF EXISTS attribute_version_change_logs;
    """)
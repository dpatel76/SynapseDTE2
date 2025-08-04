"""reorder_all_tables_audit_before_timestamps

Revision ID: 82bb9fe518b2
Revises: 6fffe97de05c
Create Date: 2025-08-04 13:31:27.090878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '82bb9fe518b2'
down_revision: Union[str, None] = '6fffe97de05c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_column_info(table_name: str):
    """Get detailed column information from the database."""
    query = text("""
        SELECT 
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            c.udt_name
        FROM information_schema.columns c
        WHERE c.table_name = :table_name 
        AND c.table_schema = 'public'
        ORDER BY c.ordinal_position
    """)
    
    conn = op.get_bind()
    result = conn.execute(query, {"table_name": table_name})
    return result.fetchall()


def get_constraints(table_name: str):
    """Get all constraints for a table."""
    conn = op.get_bind()
    
    # Get primary key
    pk_query = text("""
        SELECT constraint_name, column_name
        FROM information_schema.key_column_usage
        WHERE table_name = :table_name
        AND constraint_name IN (
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = :table_name 
            AND constraint_type = 'PRIMARY KEY'
        )
        ORDER BY ordinal_position
    """)
    pk_result = conn.execute(pk_query, {"table_name": table_name})
    pk_info = pk_result.fetchall()
    
    # Get foreign keys
    fk_query = text("""
        SELECT 
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.referential_constraints AS rc
            ON rc.constraint_name = tc.constraint_name
        WHERE tc.table_name = :table_name
        AND tc.constraint_type = 'FOREIGN KEY'
    """)
    fk_result = conn.execute(fk_query, {"table_name": table_name})
    fk_info = fk_result.fetchall()
    
    # Get unique constraints
    uc_query = text("""
        SELECT constraint_name, string_agg(column_name, ', ' ORDER BY ordinal_position) as columns
        FROM information_schema.key_column_usage
        WHERE table_name = :table_name
        AND constraint_name IN (
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = :table_name 
            AND constraint_type = 'UNIQUE'
        )
        GROUP BY constraint_name
    """)
    uc_result = conn.execute(uc_query, {"table_name": table_name})
    uc_info = uc_result.fetchall()
    
    # Get indexes
    idx_query = text("""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = :table_name
        AND schemaname = 'public'
        AND indexname NOT IN (
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = :table_name
        )
    """)
    idx_result = conn.execute(idx_query, {"table_name": table_name})
    idx_info = idx_result.fetchall()
    
    return {
        'primary_key': pk_info,
        'foreign_keys': fk_info,
        'unique_constraints': uc_info,
        'indexes': idx_info
    }


def categorize_columns(columns):
    """Categorize columns according to the ordering rules."""
    primary_keys = []
    foreign_keys = []
    data_columns = []
    status_columns = []
    json_columns = []
    audit_columns = []
    timestamp_columns = []
    
    for col in columns:
        col_name = col.column_name
        col_type = col.data_type
        
        # Primary keys (usually end with _id and are first in table)
        if col_name.endswith('_id') and col.is_nullable == 'NO' and col.column_default and 'nextval' in str(col.column_default):
            primary_keys.append(col)
        # Foreign keys (end with _id but are nullable or don't have sequence)
        elif col_name.endswith('_id'):
            foreign_keys.append(col)
        # Audit columns
        elif col_name in ('created_by_id', 'updated_by_id'):
            audit_columns.append(col)
        # Timestamp columns
        elif col_name in ('created_at', 'updated_at'):
            timestamp_columns.append(col)
        # Status/flag columns (boolean or specific names)
        elif col_type == 'boolean' or col_name.startswith('is_') or col_name in ('status', 'state', 'active'):
            status_columns.append(col)
        # JSON columns
        elif col_type in ('json', 'jsonb'):
            json_columns.append(col)
        # All other data columns
        else:
            data_columns.append(col)
    
    # Return in the specified order
    return (primary_keys + foreign_keys + data_columns + 
            status_columns + json_columns + audit_columns + timestamp_columns)


def format_column_def(col):
    """Format column definition for CREATE TABLE."""
    col_def = f"{col.column_name} "
    
    # Handle data type
    if col.udt_name == 'varchar':
        if col.character_maximum_length:
            col_def += f"VARCHAR({col.character_maximum_length})"
        else:
            # Use TEXT for VARCHAR without length or VARCHAR with default PostgreSQL max
            col_def += "TEXT"
    elif col.udt_name == 'int4':
        col_def += "INTEGER"
    elif col.udt_name == 'int8':
        col_def += "BIGINT"
    elif col.udt_name == 'bool':
        col_def += "BOOLEAN"
    elif col.udt_name == 'timestamptz':
        col_def += "TIMESTAMP WITH TIME ZONE"
    elif col.udt_name == 'timestamp':
        col_def += "TIMESTAMP"
    elif col.udt_name == 'json':
        col_def += "JSON"
    elif col.udt_name == 'jsonb':
        col_def += "JSONB"
    elif col.udt_name == 'text':
        col_def += "TEXT"
    elif col.udt_name == 'uuid':
        col_def += "UUID"
    elif col.udt_name == 'numeric':
        if col.numeric_precision and col.numeric_scale:
            col_def += f"NUMERIC({col.numeric_precision},{col.numeric_scale})"
        else:
            col_def += "NUMERIC"
    elif col.udt_name == 'date':
        col_def += "DATE"
    elif col.udt_name == 'float8' or col.data_type == 'double precision':
        col_def += "DOUBLE PRECISION"
    else:
        # Handle user-defined types (enums)
        col_def += col.udt_name.upper()
    
    # Handle nullable
    if col.is_nullable == 'NO':
        col_def += " NOT NULL"
    
    # Handle default
    if col.column_default:
        if 'nextval' in str(col.column_default):
            # Skip sequence defaults, will be handled by PRIMARY KEY
            pass
        elif col.column_default == 'now()':
            col_def += " DEFAULT NOW()"
        elif col.column_default == 'CURRENT_TIMESTAMP':
            col_def += " DEFAULT CURRENT_TIMESTAMP"
        elif col.column_default.startswith("'"):
            col_def += f" DEFAULT {col.column_default}"
        else:
            col_def += f" DEFAULT {col.column_default}"
    
    return col_def


def reorder_table(table_name: str):
    """Reorder a single table."""
    print(f"Reordering table: {table_name}")
    
    # Get column information
    columns = get_column_info(table_name)
    constraints = get_constraints(table_name)
    
    # Skip if no columns (shouldn't happen)
    if not columns:
        print(f"  No columns found for {table_name}, skipping")
        return
    
    # Categorize and reorder columns
    reordered_columns = categorize_columns(columns)
    
    # Create new table definition
    temp_table = f"{table_name}_reorder_temp"
    
    # Build column definitions
    column_defs = []
    for col in reordered_columns:
        column_defs.append(format_column_def(col))
    
    # Add primary key constraint
    if constraints['primary_key']:
        pk_cols = [row.column_name for row in constraints['primary_key']]
        column_defs.append(f"PRIMARY KEY ({', '.join(pk_cols)})")
    
    # Create new table
    create_sql = f"""
        CREATE TABLE {temp_table} (
            {',\n            '.join(column_defs)}
        )
    """
    op.execute(create_sql)
    
    # Copy data
    col_names = [col.column_name for col in columns]
    op.execute(f"""
        INSERT INTO {temp_table} ({', '.join(col_names)})
        SELECT {', '.join(col_names)} FROM {table_name}
    """)
    
    # Drop old table
    op.execute(f"DROP TABLE {table_name} CASCADE")
    
    # Rename new table
    op.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
    
    # Recreate sequences for primary keys
    for col in columns:
        if col.column_default and 'nextval' in str(col.column_default):
            # Extract sequence name from default value
            default_str = str(col.column_default)
            if '::regclass' in default_str:
                # Format: nextval('sequence_name'::regclass)
                seq_name = default_str.split("'")[1]
            else:
                # Format: nextval('sequence_name')
                seq_name = default_str.split("'")[1].split("'")[0]
            
            # Check if sequence exists, if not create it
            seq_check = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_sequences 
                    WHERE schemaname = 'public' 
                    AND sequencename = :seq_name
                )
            """)
            seq_exists = op.get_bind().execute(seq_check, {"seq_name": seq_name}).scalar()
            
            if not seq_exists:
                # Create sequence
                op.execute(f"CREATE SEQUENCE {seq_name}")
                # Set the sequence value based on max id
                op.execute(f"""
                    SELECT setval('{seq_name}', 
                        COALESCE((SELECT MAX({col.column_name}) FROM {table_name}), 1)
                    )
                """)
            
            # Set default
            op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {col.column_name} SET DEFAULT nextval('{seq_name}'::regclass)")
    
    # Recreate foreign keys
    for fk in constraints['foreign_keys']:
        delete_rule = f"ON DELETE {fk.delete_rule}" if fk.delete_rule != 'NO ACTION' else ''
        op.execute(f"""
            ALTER TABLE {table_name} 
            ADD CONSTRAINT {fk.constraint_name} 
            FOREIGN KEY ({fk.column_name}) 
            REFERENCES {fk.foreign_table_name}({fk.foreign_column_name})
            {delete_rule}
        """)
    
    # Recreate unique constraints
    for uc in constraints['unique_constraints']:
        op.execute(f"""
            ALTER TABLE {table_name}
            ADD CONSTRAINT {uc.constraint_name}
            UNIQUE ({uc.columns})
        """)
    
    # Recreate indexes
    for idx in constraints['indexes']:
        op.execute(idx.indexdef)


def upgrade() -> None:
    """Reorder columns in all tables according to the standard ordering."""
    
    # Get all tables with audit columns
    query = text("""
        SELECT DISTINCT table_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND column_name IN ('created_by_id', 'updated_by_id', 'created_at', 'updated_at')
        AND table_name NOT IN ('alembic_version', 'lobs')  -- Skip alembic_version and already reordered lobs
        ORDER BY table_name
    """)
    
    conn = op.get_bind()
    result = conn.execute(query)
    tables = [row.table_name for row in result]
    
    print(f"Found {len(tables)} tables to reorder")
    
    # Store foreign key constraints that reference tables we're modifying
    all_referencing_fks = {}
    for table in tables:
        fk_query = text("""
            SELECT 
                tc.table_name AS referencing_table,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints AS rc
                ON rc.constraint_name = tc.constraint_name
            WHERE ccu.table_name = :table_name
            AND tc.table_name != :table_name
            AND tc.constraint_type = 'FOREIGN KEY'
        """)
        result = conn.execute(fk_query, {"table_name": table})
        all_referencing_fks[table] = result.fetchall()
    
    # Drop all referencing foreign keys
    for table, fks in all_referencing_fks.items():
        for fk in fks:
            try:
                op.execute(f"ALTER TABLE {fk.referencing_table} DROP CONSTRAINT {fk.constraint_name}")
            except:
                pass  # Constraint might not exist
    
    # Reorder each table
    for table in tables:
        try:
            reorder_table(table)
            print(f"  ✓ Successfully reordered {table}")
        except Exception as e:
            print(f"  ✗ Failed to reorder {table}: {str(e)}")
            raise
    
    # Recreate all referencing foreign keys
    for table, fks in all_referencing_fks.items():
        for fk in fks:
            delete_rule = f"ON DELETE {fk.delete_rule}" if fk.delete_rule != 'NO ACTION' else ''
            try:
                op.execute(f"""
                    ALTER TABLE {fk.referencing_table}
                    ADD CONSTRAINT {fk.constraint_name}
                    FOREIGN KEY ({fk.column_name})
                    REFERENCES {fk.referenced_table}({fk.referenced_column})
                    {delete_rule}
                """)
            except:
                pass  # Constraint might already exist


def downgrade() -> None:
    """Downgrade is not supported for this migration."""
    raise NotImplementedError("Downgrade is not supported for comprehensive table reordering. Please restore from backup.")
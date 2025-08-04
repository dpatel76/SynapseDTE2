"""
Final migration script to move all role-specific assignments to universal assignments
and remove role-specific tables
"""

import asyncio
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine
from app.core.logging import get_logger
import json

logger = get_logger(__name__)


async def migrate_report_owner_assignments(session: AsyncSession):
    """Migrate report_owner_assignments to universal_assignments"""
    logger.info("Starting migration of report_owner_assignments...")
    
    try:
        # Check if report_owner_assignments table exists
        check_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'report_owner_assignments'
            );
        """)
        result = await session.execute(check_query)
        if not result.scalar():
            logger.info("report_owner_assignments table does not exist, skipping...")
            return 0
        
        # Get all report_owner_assignments
        query = text("""
            SELECT 
                roa.id,
                roa.cycle_id,
                roa.report_id,
                roa.report_owner_id,
                roa.phase_name,
                roa.assignment_type,
                roa.title,
                roa.description,
                roa.priority,
                roa.status,
                roa.due_date,
                roa.completed_at,
                roa.created_at,
                roa.created_by_id,
                r.report_name
            FROM report_owner_assignments roa
            LEFT JOIN reports r ON r.id = roa.report_id
            WHERE NOT EXISTS (
                SELECT 1 FROM universal_assignments ua
                WHERE ua.legacy_assignment_id = roa.id
                AND ua.legacy_assignment_type = 'report_owner_assignment'
            )
        """)
        
        result = await session.execute(query)
        assignments = result.fetchall()
        
        count = 0
        for assignment in assignments:
            # Create universal assignment
            insert_query = text("""
                INSERT INTO universal_assignments (
                    assignment_type,
                    from_role,
                    to_role,
                    to_user_id,
                    title,
                    description,
                    task_instructions,
                    context_type,
                    context_data,
                    priority,
                    status,
                    due_date,
                    completed_at,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by,
                    legacy_assignment_id,
                    legacy_assignment_type
                ) VALUES (
                    :assignment_type,
                    'TESTER',
                    'REPORT_OWNER',
                    :to_user_id,
                    :title,
                    :description,
                    :task_instructions,
                    'phase_assignment',
                    :context_data,
                    :priority,
                    :status,
                    :due_date,
                    :completed_at,
                    :created_at,
                    :created_by,
                    CURRENT_TIMESTAMP,
                    :created_by,
                    :legacy_id,
                    'report_owner_assignment'
                )
            """)
            
            context_data = {
                "cycle_id": assignment.cycle_id,
                "report_id": assignment.report_id,
                "report_name": assignment.report_name or f"Report {assignment.report_id}",
                "phase_name": assignment.phase_name,
                "original_assignment_type": assignment.assignment_type
            }
            
            await session.execute(insert_query, {
                "assignment_type": f"{assignment.phase_name}_{assignment.assignment_type}".upper().replace(" ", "_"),
                "to_user_id": assignment.report_owner_id,
                "title": assignment.title or f"{assignment.phase_name} - {assignment.assignment_type}",
                "description": assignment.description,
                "task_instructions": f"Complete {assignment.assignment_type} for {assignment.phase_name}",
                "context_data": json.dumps(context_data),
                "priority": assignment.priority or "Medium",
                "status": assignment.status,
                "due_date": assignment.due_date,
                "completed_at": assignment.completed_at,
                "created_at": assignment.created_at,
                "created_by": assignment.created_by_id,
                "legacy_id": assignment.id
            })
            count += 1
        
        await session.commit()
        logger.info(f"Migrated {count} report_owner_assignments to universal_assignments")
        return count
        
    except Exception as e:
        logger.error(f"Error migrating report_owner_assignments: {e}")
        await session.rollback()
        raise


async def migrate_data_owner_assignments(session: AsyncSession):
    """Migrate data_owner_assignments to universal_assignments"""
    logger.info("Starting migration of data_owner_assignments...")
    
    try:
        # Check if data_owner_assignments table exists
        check_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'data_owner_assignments'
            );
        """)
        result = await session.execute(check_query)
        if not result.scalar():
            logger.info("data_owner_assignments table does not exist, skipping...")
            return 0
        
        # Get all data_owner_assignments
        query = text("""
            SELECT 
                doa.id,
                doa.cycle_id,
                doa.report_id,
                doa.attribute_id,
                doa.lob_id,
                doa.data_owner_id,
                doa.assignment_type,
                doa.status,
                doa.assigned_by_id,
                doa.assigned_at,
                doa.completed_at,
                doa.created_at,
                doa.created_by_id,
                r.report_name,
                ra.attribute_name,
                l.lob_name,
                u.full_name as data_owner_name
            FROM data_owner_assignments doa
            LEFT JOIN reports r ON r.id = doa.report_id
            LEFT JOIN report_attributes ra ON ra.id = doa.attribute_id
            LEFT JOIN lobs l ON l.lob_id = doa.lob_id
            LEFT JOIN users u ON u.user_id = doa.data_owner_id
            WHERE NOT EXISTS (
                SELECT 1 FROM universal_assignments ua
                WHERE ua.legacy_assignment_id = doa.id
                AND ua.legacy_assignment_type = 'data_owner_assignment'
            )
        """)
        
        result = await session.execute(query)
        assignments = result.fetchall()
        
        count = 0
        for assignment in assignments:
            # Determine from_role based on assignment_type
            from_role = 'CDO' if assignment.assignment_type == 'cdo_assigned' else 'SYSTEM'
            
            # Create universal assignment
            insert_query = text("""
                INSERT INTO universal_assignments (
                    assignment_type,
                    from_role,
                    to_role,
                    to_user_id,
                    title,
                    description,
                    task_instructions,
                    context_type,
                    context_data,
                    priority,
                    status,
                    due_date,
                    completed_at,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by,
                    legacy_assignment_id,
                    legacy_assignment_type
                ) VALUES (
                    'DATA_OWNER_IDENTIFICATION',
                    :from_role,
                    'DATA_OWNER',
                    :to_user_id,
                    :title,
                    :description,
                    :task_instructions,
                    'attribute_assignment',
                    :context_data,
                    'Medium',
                    :status,
                    NULL,
                    :completed_at,
                    :created_at,
                    :created_by,
                    CURRENT_TIMESTAMP,
                    :created_by,
                    :legacy_id,
                    'data_owner_assignment'
                )
            """)
            
            context_data = {
                "cycle_id": assignment.cycle_id,
                "report_id": assignment.report_id,
                "report_name": assignment.report_name or f"Report {assignment.report_id}",
                "attribute_id": assignment.attribute_id,
                "attribute_name": assignment.attribute_name or f"Attribute {assignment.attribute_id}",
                "lob_id": assignment.lob_id,
                "lob_name": assignment.lob_name,
                "phase_name": "Data Owner Identification",
                "original_assignment_type": assignment.assignment_type
            }
            
            title = f"Data Owner Assignment - {assignment.attribute_name or 'Attribute'}"
            if assignment.lob_name:
                title += f" ({assignment.lob_name})"
            
            await session.execute(insert_query, {
                "from_role": from_role,
                "to_user_id": assignment.data_owner_id,
                "title": title,
                "description": f"Provide data for {assignment.attribute_name} in {assignment.report_name}",
                "task_instructions": "Review the attribute and provide the requested data by the due date.",
                "context_data": json.dumps(context_data),
                "status": assignment.status,
                "completed_at": assignment.completed_at,
                "created_at": assignment.created_at or assignment.assigned_at,
                "created_by": assignment.created_by_id or assignment.assigned_by_id,
                "legacy_id": assignment.id
            })
            count += 1
        
        await session.commit()
        logger.info(f"Migrated {count} data_owner_assignments to universal_assignments")
        return count
        
    except Exception as e:
        logger.error(f"Error migrating data_owner_assignments: {e}")
        await session.rollback()
        raise


async def update_model_relationships(session: AsyncSession):
    """Update model relationships to remove role-specific assignment references"""
    logger.info("Updating model relationships...")
    
    try:
        # Remove foreign key constraints first
        constraints_to_drop = [
            "ALTER TABLE report_attributes DROP CONSTRAINT IF EXISTS fk_report_attributes_data_owner_assignment",
            "ALTER TABLE test_cycles DROP CONSTRAINT IF EXISTS fk_test_cycles_report_owner_assignments",
            "ALTER TABLE reports DROP CONSTRAINT IF EXISTS fk_reports_report_owner_assignments"
        ]
        
        for constraint_sql in constraints_to_drop:
            await session.execute(text(constraint_sql))
        
        await session.commit()
        logger.info("Updated model relationships")
        
    except Exception as e:
        logger.error(f"Error updating relationships: {e}")
        await session.rollback()
        raise


async def archive_role_specific_tables(session: AsyncSession):
    """Archive role-specific assignment tables"""
    logger.info("Archiving role-specific assignment tables...")
    
    try:
        # Create archive schema if it doesn't exist
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS archive"))
        
        # Move tables to archive schema
        tables_to_archive = [
            "report_owner_assignments",
            "data_owner_assignments"
        ]
        
        for table in tables_to_archive:
            # Check if table exists
            check_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
            """)
            result = await session.execute(check_query)
            if result.scalar():
                # Move table to archive schema
                await session.execute(text(f"ALTER TABLE {table} SET SCHEMA archive"))
                logger.info(f"Archived table {table} to archive schema")
            else:
                logger.info(f"Table {table} does not exist, skipping...")
        
        await session.commit()
        logger.info("Completed archiving role-specific tables")
        
    except Exception as e:
        logger.error(f"Error archiving tables: {e}")
        await session.rollback()
        raise


async def main():
    """Run the complete migration"""
    logger.info("Starting final migration to universal assignments...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Migrate report_owner_assignments
            ro_count = await migrate_report_owner_assignments(session)
            
            # Step 2: Migrate data_owner_assignments
            do_count = await migrate_data_owner_assignments(session)
            
            # Step 3: Update model relationships
            await update_model_relationships(session)
            
            # Step 4: Archive old tables
            await archive_role_specific_tables(session)
            
            logger.info(f"""
            Migration completed successfully!
            - Migrated {ro_count} report_owner_assignments
            - Migrated {do_count} data_owner_assignments
            - Updated model relationships
            - Archived role-specific tables to 'archive' schema
            
            Next steps:
            1. Update all code to use universal_assignments
            2. Remove role-specific models and services
            3. Update frontend to use universal assignment APIs
            """)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
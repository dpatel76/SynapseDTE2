#!/usr/bin/env python3
"""
Migration script to migrate data from old observation management tables to new unified structure
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import get_db
# Observation enhanced models removed - use observation_management models
from app.models.observation_management import ObservationRecord
# Observation enhanced models removed - use observation_management models
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObservationDataMigrator:
    """Migrates observation data from old structure to new unified structure"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.migration_stats = {
            'legacy_records_found': 0,
            'enhanced_groups_found': 0,
            'unified_groups_created': 0,
            'unified_observations_created': 0,
            'errors': []
        }
    
    def migrate_all_data(self):
        """Main migration method"""
        try:
            logger.info("Starting observation data migration...")
            
            # Step 1: Migrate from legacy observation_records table
            self.migrate_legacy_observation_records()
            
            # Step 2: Migrate from enhanced observation_groups table
            self.migrate_enhanced_observation_groups()
            
            # Step 3: Print migration summary
            self.print_migration_summary()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.migration_stats['errors'].append(str(e))
            return False
    
    def migrate_legacy_observation_records(self):
        """Migrate data from legacy observation_records table"""
        try:
            # Query legacy observation records
            legacy_records = self.db.query(ObservationRecord).all()
            self.migration_stats['legacy_records_found'] = len(legacy_records)
            
            logger.info(f"Found {len(legacy_records)} legacy observation records")
            
            # Group legacy records by attribute and LOB
            grouped_records = self.group_legacy_records_by_attribute_lob(legacy_records)
            
            # Create unified observation groups
            for group_key, records in grouped_records.items():
                try:
                    self.create_unified_group_from_legacy_records(group_key, records)
                except Exception as e:
                    error_msg = f"Failed to migrate legacy group {group_key}: {str(e)}"
                    logger.error(error_msg)
                    self.migration_stats['errors'].append(error_msg)
                    
        except Exception as e:
            logger.error(f"Error migrating legacy records: {str(e)}")
            raise
    
    def migrate_enhanced_observation_groups(self):
        """Migrate data from enhanced observation_groups table"""
        try:
            # Query enhanced observation groups
            enhanced_groups = self.db.query(EnhancedObservationRecord).all()
            self.migration_stats['enhanced_groups_found'] = len(enhanced_groups)
            
            logger.info(f"Found {len(enhanced_groups)} enhanced observation groups")
            
            # Create unified groups from enhanced groups
            for enhanced_group in enhanced_groups:
                try:
                    self.create_unified_group_from_enhanced_group(enhanced_group)
                except Exception as e:
                    error_msg = f"Failed to migrate enhanced group {enhanced_group.id}: {str(e)}"
                    logger.error(error_msg)
                    self.migration_stats['errors'].append(error_msg)
                    
        except Exception as e:
            logger.error(f"Error migrating enhanced groups: {str(e)}")
            raise
    
    def group_legacy_records_by_attribute_lob(self, records: List[ObservationRecord]) -> Dict[tuple, List[ObservationRecord]]:
        """Group legacy records by attribute and LOB combination"""
        grouped = {}
        
        for record in records:
            # Try to extract attribute and LOB info from record
            # This is a simplified approach - you may need to adjust based on actual data structure
            attribute_id = getattr(record, 'attribute_id', None) or self.infer_attribute_from_record(record)
            lob_id = getattr(record, 'lob_id', None) or self.infer_lob_from_record(record)
            
            if attribute_id and lob_id:
                group_key = (attribute_id, lob_id)
                if group_key not in grouped:
                    grouped[group_key] = []
                grouped[group_key].append(record)
        
        return grouped
    
    def infer_attribute_from_record(self, record: ObservationRecord) -> Optional[int]:
        """Infer attribute ID from observation record"""
        # This is a placeholder - implement based on your actual data structure
        # You might need to look at related tables or extract from observation description
        return 1  # Default attribute ID
    
    def infer_lob_from_record(self, record: ObservationRecord) -> Optional[int]:
        """Infer LOB ID from observation record"""
        # This is a placeholder - implement based on your actual data structure
        # You might need to look at related tables or extract from observation description
        return 1  # Default LOB ID
    
    def create_unified_group_from_legacy_records(self, group_key: tuple, records: List[ObservationRecord]):
        """Create unified observation group from legacy records"""
        attribute_id, lob_id = group_key
        
        # Check if group already exists
        existing_group = self.db.query(ObservationRecord).filter(
            ObservationRecord.attribute_id == attribute_id,
            ObservationRecord.lob_id == lob_id
        ).first()
        
        if existing_group:
            logger.info(f"Group for attribute {attribute_id} and LOB {lob_id} already exists")
            return existing_group
        
        # Create new unified group
        group = ObservationRecord(
            phase_id=records[0].phase_id if hasattr(records[0], 'phase_id') else 1,
            cycle_id=records[0].cycle_id if hasattr(records[0], 'cycle_id') else 1,
            report_id=records[0].report_id if hasattr(records[0], 'report_id') else 1,
            attribute_id=attribute_id,
            lob_id=lob_id,
            group_name=f"Migrated Group - Attribute {attribute_id} LOB {lob_id}",
            group_description="Migrated from legacy observation records",
            issue_summary=self.generate_issue_summary_from_records(records),
            severity_level=self.determine_severity_from_records(records),
            issue_type='data_quality',  # Default type
            status='draft',
            detection_method='manual_review',
            detected_by=records[0].created_by if hasattr(records[0], 'created_by') else 1,
            detected_at=records[0].created_at if hasattr(records[0], 'created_at') else datetime.utcnow(),
            created_by=records[0].created_by if hasattr(records[0], 'created_by') else 1,
            updated_by=records[0].created_by if hasattr(records[0], 'created_by') else 1
        )
        
        self.db.add(group)
        self.db.flush()  # Get the ID
        
        # Create individual observations
        for record in records:
            observation = Observation(
                group_id=group.id,
                test_execution_id=getattr(record, 'test_execution_id', 1),
                test_case_id=getattr(record, 'test_case_id', f'legacy_{record.id}'),
                attribute_id=attribute_id,
                sample_id=getattr(record, 'sample_id', f'sample_{record.id}'),
                lob_id=lob_id,
                observation_title=getattr(record, 'observation_title', f'Legacy Observation {record.id}'),
                observation_description=getattr(record, 'observation_description', 'Migrated from legacy record'),
                confidence_level=getattr(record, 'confidence_level', 0.8),
                created_by=getattr(record, 'created_by', 1),
                updated_by=getattr(record, 'updated_by', 1)
            )
            self.db.add(observation)
        
        self.db.commit()
        self.migration_stats['unified_groups_created'] += 1
        self.migration_stats['unified_observations_created'] += len(records)
        
        logger.info(f"Created unified group {group.id} with {len(records)} observations")
        return group
    
    def create_unified_group_from_enhanced_group(self, enhanced_group: EnhancedObservationRecord):
        """Create unified observation group from enhanced group"""
        # Check if group already exists
        existing_group = self.db.query(ObservationRecord).filter(
            ObservationRecord.id == enhanced_group.id
        ).first()
        
        if existing_group:
            logger.info(f"Unified group {enhanced_group.id} already exists")
            return existing_group
        
        # Create new unified group
        group = ObservationRecord(
            id=enhanced_group.id,  # Preserve original ID
            phase_id=getattr(enhanced_group, 'phase_id', 1),
            cycle_id=getattr(enhanced_group, 'cycle_id', 1),
            report_id=getattr(enhanced_group, 'report_id', 1),
            attribute_id=getattr(enhanced_group, 'attribute_id', 1),
            lob_id=getattr(enhanced_group, 'lob_id', 1),
            group_name=getattr(enhanced_group, 'group_name', f'Enhanced Group {enhanced_group.id}'),
            group_description=getattr(enhanced_group, 'group_description', 'Migrated from enhanced group'),
            issue_summary=getattr(enhanced_group, 'issue_summary', 'Enhanced group migration'),
            severity_level=getattr(enhanced_group, 'severity_level', 'medium'),
            issue_type='data_quality',
            status='draft',
            detection_method='manual_review',
            detected_by=getattr(enhanced_group, 'created_by', 1),
            detected_at=getattr(enhanced_group, 'created_at', datetime.utcnow()),
            created_by=getattr(enhanced_group, 'created_by', 1),
            updated_by=getattr(enhanced_group, 'updated_by', 1)
        )
        
        self.db.add(group)
        self.db.commit()
        self.migration_stats['unified_groups_created'] += 1
        
        logger.info(f"Created unified group {group.id} from enhanced group")
        return group
    
    def generate_issue_summary_from_records(self, records: List[ObservationRecord]) -> str:
        """Generate issue summary from multiple records"""
        if not records:
            return "No records found"
        
        total_count = len(records)
        return f"Migrated observation group with {total_count} observations from legacy system"
    
    def determine_severity_from_records(self, records: List[ObservationRecord]) -> str:
        """Determine severity level from multiple records"""
        # Simple heuristic - can be improved based on actual data
        if len(records) > 10:
            return 'high'
        elif len(records) > 5:
            return 'medium'
        else:
            return 'low'
    
    def print_migration_summary(self):
        """Print migration summary"""
        logger.info("\n" + "="*50)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Legacy records found: {self.migration_stats['legacy_records_found']}")
        logger.info(f"Enhanced groups found: {self.migration_stats['enhanced_groups_found']}")
        logger.info(f"Unified groups created: {self.migration_stats['unified_groups_created']}")
        logger.info(f"Unified observations created: {self.migration_stats['unified_observations_created']}")
        logger.info(f"Errors encountered: {len(self.migration_stats['errors'])}")
        
        if self.migration_stats['errors']:
            logger.info("\nErrors:")
            for error in self.migration_stats['errors']:
                logger.info(f"  - {error}")
        
        logger.info("="*50)


def main():
    """Main migration function"""
    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create and run migrator
        migrator = ObservationDataMigrator(db)
        success = migrator.migrate_all_data()
        
        if success:
            logger.info("Migration completed successfully!")
            return 0
        else:
            logger.error("Migration failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())
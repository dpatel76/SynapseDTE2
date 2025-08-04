"""
Versioning system for SynapseDTE
Provides mixin and models for tracking version history
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID, JSONBUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr, relationship
from sqlalchemy.ext.declarative import declared_attr

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class VersionedMixin:
    """
    Mixin for adding versioning capability to any model.
    
    Usage:
        class MyModel(Base, VersionedMixin):
            __tablename__ = "my_table"
            __versioned__ = True  # Enable versioning
            
            # Your model fields...
    """
    
    # Version tracking fields
    version_number = Column(Integer, default=1, nullable=False)
    is_latest_version = Column(Boolean, default=True, nullable=False)
    version_created_at = Column(DateTime(timezone=True), default=func.now())
    version_created_by = Column(String(255), nullable=True)
    version_notes = Column(Text, nullable=True)
    change_reason = Column(String(500), nullable=True)
    parent_version_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Approval tracking
    version_status = Column(String(50), default="draft")  # draft, submitted, approved, rejected
    approved_version_id = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    @declared_attr
    def __mapper_args__(cls):
        """Mapper arguments for versioned models"""
        return {
            "version_id_col": cls.version_number,
            "confirm_deleted_rows": False
        }
    
    def create_new_version(
        self,
        reason: str,
        user_id: str,
        notes: Optional[str] = None,
        auto_approve: bool = False
    ) -> "VersionedMixin":
        """
        Create a new version of this record.
        
        Args:
            reason: Reason for creating new version
            user_id: User creating the version
            notes: Optional notes about changes
            auto_approve: Whether to auto-approve this version
            
        Returns:
            New version instance
        """
        # Mark current version as not latest
        self.is_latest_version = False
        
        # Create new instance with copied data
        new_version = self.__class__()
        
        # Copy all non-version fields
        for column in self.__table__.columns:
            if column.name not in [
                'id', 'version_number', 'is_latest_version', 
                'version_created_at', 'version_created_by',
                'version_notes', 'change_reason', 'parent_version_id',
                'version_status', 'approved_version_id', 
                'approved_at', 'approved_by'
            ]:
                setattr(new_version, column.name, getattr(self, column.name))
        
        # Set version fields
        new_version.version_number = self.version_number + 1
        new_version.is_latest_version = True
        new_version.version_created_at = datetime.utcnow()
        new_version.version_created_by = user_id
        new_version.version_notes = notes
        new_version.change_reason = reason
        new_version.parent_version_id = self.id
        new_version.version_status = "approved" if auto_approve else "draft"
        
        if auto_approve:
            new_version.approved_version_id = new_version.id
            new_version.approved_at = datetime.utcnow()
            new_version.approved_by = user_id
        
        return new_version
    
    def approve_version(self, user_id: str) -> None:
        """Approve this version"""
        self.version_status = "approved"
        self.approved_version_id = self.id
        self.approved_at = datetime.utcnow()
        self.approved_by = user_id
    
    def reject_version(self, user_id: str, reason: str) -> None:
        """Reject this version"""
        self.version_status = "rejected"
        self.version_notes = f"{self.version_notes}\nRejected: {reason}" if self.version_notes else f"Rejected: {reason}"


class VersionHistory(CustomPKModel, AuditMixin):
    """
    Centralized version history tracking for all versioned entities.
    Records all version changes across the system.
    """
    
    __tablename__ = "version_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Entity identification
    entity_type = Column(String(50), nullable=False)  # e.g., "ReportAttribute", "SampleSet"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String(255), nullable=True)  # Human-readable name
    
    # Version information
    version_number = Column(Integer, nullable=False)
    change_type = Column(String(50), nullable=False)  # created, updated, approved, rejected
    change_reason = Column(Text, nullable=True)
    
    # Change tracking
    changed_by = Column(String(255), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Change details (stores before/after for specific fields)
    change_details = Column(JSONB, nullable=True)
    
    # Context
    cycle_id = Column(UUID(as_uuid=True), nullable=True)
    report_id = Column(UUID(as_uuid=True), nullable=True)
    phase_name = Column(String(50), nullable=True)
    
    # Relationships could be added here if needed
    
    @classmethod
    def record_change(
        cls,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        version_number: int,
        change_type: str,
        changed_by: str,
        change_reason: Optional[str] = None,
        change_details: Optional[Dict[str, Any]] = None,
        cycle_id: Optional[str] = None,
        report_id: Optional[str] = None,
        phase_name: Optional[str] = None
    ) -> "VersionHistory":
        """Create a version history record"""
        return cls(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            version_number=version_number,
            change_type=change_type,
            change_reason=change_reason,
            changed_by=changed_by,
            change_details=change_details,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase_name
        )


class VersionComparison:
    """Utility class for comparing versions"""
    
    @staticmethod
    def compare_versions(
        version1: VersionedMixin,
        version2: VersionedMixin,
        fields_to_compare: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Compare two versions of an entity.
        
        Args:
            version1: First version
            version2: Second version
            fields_to_compare: Specific fields to compare (None = all fields)
            
        Returns:
            Dictionary with differences
        """
        differences = {
            "version1_number": version1.version_number,
            "version2_number": version2.version_number,
            "changes": {}
        }
        
        # Get fields to compare
        if fields_to_compare is None:
            # Compare all non-version fields
            fields_to_compare = [
                column.name for column in version1.__table__.columns
                if not column.name.startswith('version_') and
                column.name not in ['id', 'is_latest_version', 'parent_version_id']
            ]
        
        # Compare each field
        for field in fields_to_compare:
            val1 = getattr(version1, field, None)
            val2 = getattr(version2, field, None)
            
            if val1 != val2:
                differences["changes"][field] = {
                    "old_value": val1,
                    "new_value": val2
                }
        
        return differences


# Event listeners for automatic history tracking
@event.listens_for(VersionedMixin, 'after_insert', propagate=True)
def receive_after_insert(mapper, connection, target):
    """Automatically create history record on insert"""
    if hasattr(target, '__versioned__') and target.__versioned__:
        # Create history record
        history = VersionHistory.record_change(
            entity_type=target.__class__.__name__,
            entity_id=str(target.id),
            entity_name=getattr(target, 'name', str(target.id)),
            version_number=target.version_number,
            change_type="created",
            changed_by=target.version_created_by or "system",
            change_reason=target.change_reason,
            cycle_id=getattr(target, 'cycle_id', None),
            report_id=getattr(target, 'report_id', None),
            phase_name=getattr(target, 'phase_name', None)
        )
        
        # Note: In async context, we'd need to handle this differently
        # This is a simplified example


@event.listens_for(VersionedMixin, 'after_update', propagate=True)
def receive_after_update(mapper, connection, target):
    """Automatically create history record on update"""
    if hasattr(target, '__versioned__') and target.__versioned__:
        # Check if version status changed
        history_attrs = mapper.attrs
        if 'version_status' in history_attrs and history_attrs['version_status'].history.has_changes():
            old_status = history_attrs['version_status'].history.deleted[0] if history_attrs['version_status'].history.deleted else None
            new_status = target.version_status
            
            if old_status != new_status and new_status in ['approved', 'rejected']:
                # Create history record for approval/rejection
                history = VersionHistory.record_change(
                    entity_type=target.__class__.__name__,
                    entity_id=str(target.id),
                    entity_name=getattr(target, 'name', str(target.id)),
                    version_number=target.version_number,
                    change_type=new_status,
                    changed_by=getattr(target, f'{new_status}_by', 'system'),
                    change_reason=target.version_notes,
                    cycle_id=getattr(target, 'cycle_id', None),
                    report_id=getattr(target, 'report_id', None),
                    phase_name=getattr(target, 'phase_name', None)
                )


# Migration helper for existing tables
def add_versioning_to_table(table_name: str, engine):
    """
    Add versioning columns to an existing table.
    This would be used in Alembic migrations.
    """
    from sqlalchemy import text
    
    versioning_columns = [
        "ALTER TABLE {table} ADD COLUMN version_number INTEGER DEFAULT 1",
        "ALTER TABLE {table} ADD COLUMN is_latest_version BOOLEAN DEFAULT TRUE",
        "ALTER TABLE {table} ADD COLUMN version_created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "ALTER TABLE {table} ADD COLUMN version_created_by VARCHAR(255)",
        "ALTER TABLE {table} ADD COLUMN version_notes TEXT",
        "ALTER TABLE {table} ADD COLUMN change_reason VARCHAR(500)",
        "ALTER TABLE {table} ADD COLUMN parent_version_id UUID",
        "ALTER TABLE {table} ADD COLUMN version_status VARCHAR(50) DEFAULT 'approved'",
        "ALTER TABLE {table} ADD COLUMN approved_version_id UUID",
        "ALTER TABLE {table} ADD COLUMN approved_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE {table} ADD COLUMN approved_by VARCHAR(255)"
    ]
    
    with engine.connect() as conn:
        for sql in versioning_columns:
            try:
                conn.execute(text(sql.format(table=table_name)))
                conn.commit()
            except Exception as e:
                print(f"Column might already exist: {e}")
                conn.rollback()
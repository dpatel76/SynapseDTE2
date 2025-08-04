"""
Pydantic schemas for Versioning Management
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CreateVersionRequest(BaseModel):
    """Request model for creating a new version"""
    entity_type: str = Field(..., description="Type of entity (e.g., ReportAttribute, SampleSet)")
    entity_id: str = Field(..., description="ID of the entity to version")
    reason: str = Field(..., description="Reason for creating new version")
    notes: Optional[str] = Field(None, description="Optional notes about the changes")
    auto_approve: bool = Field(False, description="Whether to auto-approve this version")


class VersionHistoryItem(BaseModel):
    """Single version history entry"""
    version_number: int = Field(..., description="Version number")
    change_type: str = Field(..., description="Type of change (created, updated, approved, rejected)")
    change_reason: Optional[str] = Field(None, description="Reason for the change")
    changed_by: str = Field(..., description="User who made the change")
    changed_at: str = Field(..., description="When the change was made")
    change_details: Optional[Dict[str, Any]] = Field(None, description="Detailed changes")


class VersionHistoryResponse(BaseModel):
    """Response model for version history"""
    entity_type: str = Field(..., description="Type of entity")
    entity_id: str = Field(..., description="ID of the entity")
    history: List[VersionHistoryItem] = Field(..., description="Version history entries")


class VersionChange(BaseModel):
    """Single field change between versions"""
    old_value: Any = Field(..., description="Value in older version")
    new_value: Any = Field(..., description="Value in newer version")


class VersionComparisonResponse(BaseModel):
    """Response model for version comparison"""
    version1_number: int = Field(..., description="First version number")
    version2_number: int = Field(..., description="Second version number")
    changes: Dict[str, VersionChange] = Field(..., description="Changes between versions")


class RevertVersionRequest(BaseModel):
    """Request model for reverting to a previous version"""
    entity_type: str = Field(..., description="Type of entity")
    entity_id: str = Field(..., description="ID of the entity")
    target_version_number: int = Field(..., description="Version number to revert to")
    reason: str = Field(..., description="Reason for reverting")


class VersionInfo(BaseModel):
    """Basic version information"""
    version_id: str = Field(..., description="Version ID")
    version_number: int = Field(..., description="Version number")
    status: str = Field(..., description="Version status (draft, submitted, approved, rejected)")
    created_at: str = Field(..., description="When version was created")
    created_by: str = Field(..., description="Who created the version")
    change_reason: Optional[str] = Field(None, description="Reason for version")
    notes: Optional[str] = Field(None, description="Version notes")


class VersionListResponse(BaseModel):
    """Response model for listing versions"""
    entity_type: str = Field(..., description="Type of entity")
    entity_id: str = Field(..., description="ID of the entity")
    versions: List[VersionInfo] = Field(..., description="List of versions")
    total_versions: int = Field(..., description="Total number of versions")


class VersionApprovalRequest(BaseModel):
    """Request model for approving/rejecting a version"""
    notes: Optional[str] = Field(None, description="Approval/rejection notes")
    reason: Optional[str] = Field(None, description="Reason for rejection (required for rejection)")


class VersionDiff(BaseModel):
    """Detailed diff between versions"""
    field_name: str = Field(..., description="Name of the changed field")
    field_type: str = Field(..., description="Data type of the field")
    old_value: Any = Field(..., description="Previous value")
    new_value: Any = Field(..., description="New value")
    change_type: str = Field(..., description="Type of change (added, modified, removed)")


class VersionDetailResponse(BaseModel):
    """Detailed version information"""
    version_info: VersionInfo = Field(..., description="Basic version information")
    entity_data: Dict[str, Any] = Field(..., description="Full entity data for this version")
    parent_version: Optional[VersionInfo] = Field(None, description="Parent version info if exists")
    child_versions: List[VersionInfo] = Field(default_factory=list, description="Child versions")
    approval_info: Optional[Dict[str, Any]] = Field(None, description="Approval information if approved")


class BulkVersionRequest(BaseModel):
    """Request for bulk version operations"""
    entity_type: str = Field(..., description="Type of entity")
    entity_ids: List[str] = Field(..., description="List of entity IDs")
    reason: str = Field(..., description="Reason for bulk operation")
    operation: str = Field(..., description="Operation type (create_version, approve, reject)")


class VersionSearchRequest(BaseModel):
    """Request for searching versions"""
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    created_by: Optional[str] = Field(None, description="Filter by creator")
    status: Optional[str] = Field(None, description="Filter by status")
    date_from: Optional[datetime] = Field(None, description="Filter by creation date from")
    date_to: Optional[datetime] = Field(None, description="Filter by creation date to")
    cycle_id: Optional[str] = Field(None, description="Filter by cycle")
    report_id: Optional[str] = Field(None, description="Filter by report")
    limit: int = Field(50, description="Maximum results to return")
    offset: int = Field(0, description="Offset for pagination")


class VersionMetrics(BaseModel):
    """Version metrics and statistics"""
    total_versions: int = Field(..., description="Total number of versions")
    approved_versions: int = Field(..., description="Number of approved versions")
    rejected_versions: int = Field(..., description="Number of rejected versions")
    draft_versions: int = Field(..., description="Number of draft versions")
    avg_approval_time_hours: float = Field(..., description="Average time to approval in hours")
    top_creators: List[Dict[str, Any]] = Field(..., description="Top version creators")
    version_trends: List[Dict[str, Any]] = Field(..., description="Version creation trends")
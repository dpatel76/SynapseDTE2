"""
Adapter functions to bridge legacy sample selection endpoints with new version-based system
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.workflow import WorkflowPhase
import logging

logger = logging.getLogger(__name__)


async def get_or_create_current_version(
    db: AsyncSession,
    phase_id: int,
    phase_data: Dict[str, Any],
    user_id: int
) -> Dict[str, Any]:
    """
    Get the current version or create a new one if none exists.
    Returns version metadata.
    """
    versions = phase_data.get("versions", [])
    
    # Find current version (draft or pending_approval)
    current_version = None
    for version in versions:
        if version.get("version_status") in ["draft", "pending_approval"]:
            current_version = version
            break
    
    if not current_version:
        # Create new version
        version_number = max([v.get("version_number", 0) for v in versions], default=0) + 1
        current_version = {
            "version_id": str(uuid.uuid4()),
            "version_number": version_number,
            "version_status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
            "total_samples": 0,
            "approved_samples": 0,
            "rejected_samples": 0,
            "pending_samples": 0
        }
        
        if "versions" not in phase_data:
            phase_data["versions"] = []
        phase_data["versions"].append(current_version)
        
        logger.info(f"Created new version {version_number} for phase {phase_id}")
    
    return current_version


async def convert_submission_to_version(
    submission: Dict[str, Any],
    phase_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Convert a legacy submission to version format.
    """
    if not submission:
        return None
    
    # Find or create corresponding version
    version_number = submission.get("version_number", 1)
    versions = phase_data.get("versions", [])
    
    # Look for existing version with this number
    version = None
    for v in versions:
        if v.get("version_number") == version_number:
            version = v
            break
    
    if not version:
        # Create version from submission data
        version = {
            "version_id": submission.get("submission_id", str(uuid.uuid4())),
            "version_number": version_number,
            "version_status": "pending_approval" if submission.get("status") == "pending" else "approved",
            "created_at": submission.get("submitted_at"),
            "created_by": submission.get("submitted_by_id"),
            "submitted_at": submission.get("submitted_at"),
            "submitted_by": submission.get("submitted_by_id"),
            "submission_notes": submission.get("notes"),
            "total_samples": submission.get("total_samples", 0),
            "approved_samples": submission.get("included_samples", 0),
            "rejected_samples": submission.get("excluded_samples", 0),
            "pending_samples": submission.get("pending_samples", 0)
        }
        
        if "versions" not in phase_data:
            phase_data["versions"] = []
        phase_data["versions"].append(version)
    
    return version


async def sync_submission_status_to_version(
    phase_data: Dict[str, Any],
    submission_id: str,
    new_status: str
) -> Optional[Dict[str, Any]]:
    """
    Sync submission status changes to corresponding version.
    """
    # Find submission
    submission = None
    for sub in phase_data.get("submissions", []):
        if sub.get("submission_id") == submission_id:
            submission = sub
            break
    
    if not submission:
        return None
    
    # Convert submission status to version status
    version_status_map = {
        "pending": "pending_approval",
        "approved": "approved",
        "rejected": "rejected",
        "revision_required": "rejected"
    }
    
    # Update corresponding version
    version_number = submission.get("version_number", 1)
    versions = phase_data.get("versions", [])
    
    for version in versions:
        if version.get("version_number") == version_number:
            version["version_status"] = version_status_map.get(new_status, new_status)
            if new_status == "approved":
                version["approved_at"] = datetime.utcnow().isoformat()
            return version
    
    return None


async def get_samples_for_version(
    phase_data: Dict[str, Any],
    version_id: str
) -> List[Dict[str, Any]]:
    """
    Get all samples for a specific version.
    """
    # Find version
    version = None
    for v in phase_data.get("versions", []):
        if v.get("version_id") == version_id:
            version = v
            break
    
    if not version:
        return []
    
    # Get samples for this version number
    version_number = version.get("version_number", 1)
    all_samples = phase_data.get("cycle_report_sample_selection_samples", [])
    
    return [
        sample for sample in all_samples
        if sample.get("version_number", 1) == version_number
    ]


async def update_sample_counts_for_version(
    phase_data: Dict[str, Any],
    version_id: str
) -> None:
    """
    Update sample counts for a version based on current sample states.
    """
    samples = await get_samples_for_version(phase_data, version_id)
    
    # Find version
    for version in phase_data.get("versions", []):
        if version.get("version_id") == version_id:
            version["total_samples"] = len(samples)
            version["approved_samples"] = len([s for s in samples if s.get("report_owner_decision") == "approved"])
            version["rejected_samples"] = len([s for s in samples if s.get("report_owner_decision") == "rejected"]) 
            version["pending_samples"] = len([s for s in samples if not s.get("report_owner_decision")])
            break
"""Workflow Versioning API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.core.dependencies import require_roles
from app.temporal.workflow_versioning import (
    WorkflowVersionManager,
    WorkflowCompatibilityChecker,
    get_workflow_version_from_id
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/versions")
async def get_workflow_versions(
    current_user: User = Depends(require_roles(["Test Manager", "Report Owner Executive"]))
) -> Dict[str, Any]:
    """Get all workflow version information"""
    version_manager = WorkflowVersionManager()
    return version_manager.get_version_info()


@router.get("/versions/current")
async def get_current_version(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the current workflow version"""
    version_manager = WorkflowVersionManager()
    return {
        "version": version_manager.current_version.value,
        "release_date": datetime(2024, 2, 1).isoformat(),
        "features": WorkflowCompatibilityChecker.FEATURE_MATRIX.get(
            version_manager.current_version, {}
        )
    }


@router.get("/versions/{version}/features")
async def get_version_features(
    version: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get features supported by a specific version"""
    version_manager = WorkflowVersionManager()
    
    if not version_manager.check_version_compatibility(version):
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found"
        )
    
    from app.temporal.workflow_versioning import WorkflowVersion
    try:
        workflow_version = WorkflowVersion(version)
        features = WorkflowCompatibilityChecker.FEATURE_MATRIX.get(workflow_version, {})
        return {
            "version": version,
            "features": features,
            "is_current": version == version_manager.current_version.value
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Invalid version: {version}")


@router.post("/versions/check-compatibility")
async def check_version_compatibility(
    workflow_id: str,
    target_version: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Check if a workflow is compatible with a target version"""
    version_manager = WorkflowVersionManager()
    
    # Extract version from workflow ID
    current_version = get_workflow_version_from_id(workflow_id)
    if not current_version:
        current_version = "1.0.0"  # Default for old workflows
    
    if target_version is None:
        target_version = version_manager.current_version.value
    
    needs_migration = version_manager.needs_migration(current_version, target_version)
    
    return {
        "workflow_id": workflow_id,
        "current_version": current_version,
        "target_version": target_version,
        "compatible": version_manager.check_version_compatibility(current_version),
        "needs_migration": needs_migration,
        "migration_notes": f"Migration {'required' if needs_migration else 'not required'} from {current_version} to {target_version}"
    }


@router.get("/versions/migration-history")
async def get_migration_history(
    workflow_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(require_roles(["Test Manager"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get workflow migration history"""
    # Query migration history from database
    query = "SELECT * FROM workflow_migration_history"
    params = {}
    
    if workflow_id:
        query += " WHERE workflow_id = :workflow_id"
        params["workflow_id"] = workflow_id
    
    query += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit
    
    result = await db.execute(query, params)
    migrations = result.fetchall()
    
    return {
        "count": len(migrations),
        "migrations": [
            {
                "migration_id": m.migration_id,
                "workflow_id": m.workflow_id,
                "from_version": m.from_version,
                "to_version": m.to_version,
                "status": m.migration_status,
                "started_at": m.migration_started_at.isoformat() if m.migration_started_at else None,
                "completed_at": m.migration_completed_at.isoformat() if m.migration_completed_at else None,
                "notes": m.migration_notes
            }
            for m in migrations
        ]
    }


@router.post("/versions/migrate/{workflow_id}")
async def migrate_workflow_version(
    workflow_id: str,
    target_version: str,
    current_user: User = Depends(require_roles(["Test Manager"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Migrate a workflow to a different version (admin only)"""
    version_manager = WorkflowVersionManager()
    
    # Validate target version
    if not version_manager.check_version_compatibility(target_version):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target version: {target_version}"
        )
    
    # Get current version
    current_version = get_workflow_version_from_id(workflow_id)
    if not current_version:
        current_version = "1.0.0"
    
    if current_version == target_version:
        return {
            "message": "Workflow is already at the target version",
            "version": target_version
        }
    
    # Record migration attempt
    await db.execute(
        """
        INSERT INTO workflow_migration_history 
        (workflow_id, from_version, to_version, migration_status, migration_started_at, performed_by)
        VALUES (:workflow_id, :from_version, :to_version, 'scheduled', :started_at, :user_id)
        """,
        {
            "workflow_id": workflow_id,
            "from_version": current_version,
            "to_version": target_version,
            "started_at": datetime.utcnow(),
            "user_id": current_user.user_id
        }
    )
    await db.commit()
    
    # In a real implementation, this would trigger the actual migration
    return {
        "message": "Workflow migration scheduled",
        "workflow_id": workflow_id,
        "from_version": current_version,
        "to_version": target_version,
        "status": "scheduled",
        "notes": "Migration will be performed at the next safe checkpoint"
    }


@router.get("/features/{feature}/required-version")
async def get_required_version_for_feature(
    feature: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the minimum version required for a specific feature"""
    required_version = WorkflowCompatibilityChecker.get_required_version_for_feature(feature)
    
    if not required_version:
        raise HTTPException(
            status_code=404,
            detail=f"Feature '{feature}' not found"
        )
    
    return {
        "feature": feature,
        "required_version": required_version,
        "available_features": list(WorkflowCompatibilityChecker.FEATURE_MATRIX.get(
            WorkflowVersion(required_version), {}
        ).keys())
    }
"""
Workflow Versioning and Migration Support

This module provides versioning support for Temporal workflows to handle
schema changes and workflow evolution over time.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import logging

from temporalio import workflow
from temporalio.workflow import Info

logger = logging.getLogger(__name__)


class WorkflowVersion(Enum):
    """Workflow version identifiers"""
    V1_0_0 = "1.0.0"  # Initial 8-phase workflow
    V1_1_0 = "1.1.0"  # Added phase timing instrumentation
    V1_2_0 = "1.2.0"  # Added parallel phase support
    V2_0_0 = "2.0.0"  # Major refactor with new phase structure


@dataclass
class VersionChangeLog:
    """Track version changes and migrations"""
    from_version: str
    to_version: str
    change_date: datetime
    description: str
    breaking_changes: List[str]
    migration_required: bool


class WorkflowVersionManager:
    """Manages workflow versions and migrations"""
    
    def __init__(self):
        self.current_version = WorkflowVersion.V1_2_0
        self.version_history: List[VersionChangeLog] = [
            VersionChangeLog(
                from_version=WorkflowVersion.V1_0_0.value,
                to_version=WorkflowVersion.V1_1_0.value,
                change_date=datetime(2024, 1, 15),
                description="Added phase timing instrumentation",
                breaking_changes=[],
                migration_required=False
            ),
            VersionChangeLog(
                from_version=WorkflowVersion.V1_1_0.value,
                to_version=WorkflowVersion.V1_2_0.value,
                change_date=datetime(2024, 2, 1),
                description="Added parallel phase execution support",
                breaking_changes=["Phase dependencies restructured"],
                migration_required=True
            )
        ]
        
        # Migration strategies
        self.migration_strategies: Dict[str, Callable] = {
            f"{WorkflowVersion.V1_1_0.value}->{WorkflowVersion.V1_2_0.value}": self._migrate_v1_1_to_v1_2
        }
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get current version information"""
        return {
            "current_version": self.current_version.value,
            "supported_versions": [v.value for v in WorkflowVersion],
            "version_history": [
                {
                    "from": log.from_version,
                    "to": log.to_version,
                    "date": log.change_date.isoformat(),
                    "description": log.description,
                    "breaking_changes": log.breaking_changes,
                    "migration_required": log.migration_required
                }
                for log in self.version_history
            ]
        }
    
    def check_version_compatibility(self, workflow_version: str) -> bool:
        """Check if a workflow version is compatible with current version"""
        try:
            version = WorkflowVersion(workflow_version)
            # For now, we support all versions with migration
            return True
        except ValueError:
            return False
    
    def needs_migration(self, from_version: str, to_version: str = None) -> bool:
        """Check if migration is needed between versions"""
        if to_version is None:
            to_version = self.current_version.value
        
        if from_version == to_version:
            return False
        
        # Check version history for migration requirements
        for log in self.version_history:
            if log.from_version == from_version and log.to_version == to_version:
                return log.migration_required
        
        return True  # Default to requiring migration for unknown transitions
    
    def migrate_workflow_data(self, data: Dict[str, Any], from_version: str, to_version: str = None) -> Dict[str, Any]:
        """Migrate workflow data from one version to another"""
        if to_version is None:
            to_version = self.current_version.value
        
        if from_version == to_version:
            return data
        
        migration_key = f"{from_version}->{to_version}"
        if migration_key in self.migration_strategies:
            logger.info(f"Migrating workflow data from {from_version} to {to_version}")
            return self.migration_strategies[migration_key](data)
        else:
            logger.warning(f"No migration strategy found for {migration_key}, returning data as-is")
            return data
    
    def _migrate_v1_1_to_v1_2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from v1.1.0 to v1.2.0"""
        # Add support for parallel phases
        if "phase_dependencies" not in data:
            data["phase_dependencies"] = {
                "Planning": [],
                "Scoping": ["Planning"],
                "Sample Selection": ["Scoping"],
                "Data Owner Identification": ["Scoping"],  # Now parallel with Sample Selection
                "Request for Information": ["Sample Selection", "Data Owner Identification"],
                "Test Execution": ["Request for Information"],
                "Observation Management": ["Test Execution"],
                "Finalize Test Report": ["Observation Management"]
            }
        
        # Add phase timing structure if missing
        if "phase_timings" not in data:
            data["phase_timings"] = {}
        
        return data


class VersionedWorkflowMixin:
    """Mixin for adding versioning support to workflows"""
    
    async def _get_workflow_version(self) -> str:
        """Get the version of the current workflow execution"""
        info = workflow.info()
        # Version can be stored in workflow memo or search attributes
        memo = info.memo or {}
        return memo.get("workflow_version", WorkflowVersion.V1_0_0.value)
    
    async def _set_workflow_version(self, version: str):
        """Set the workflow version in memo"""
        # In Temporal, we can't modify memo after workflow starts
        # This would need to be handled differently in production
        pass
    
    async def _handle_version_upgrade(self, target_version: str = None):
        """Handle workflow version upgrades"""
        current_version = await self._get_workflow_version()
        if target_version is None:
            target_version = WorkflowVersion.V1_2_0.value
        
        if current_version != target_version:
            version_manager = WorkflowVersionManager()
            if version_manager.needs_migration(current_version, target_version):
                logger.info(f"Workflow version upgrade needed: {current_version} -> {target_version}")
                # In a real implementation, this would handle data migration
                # Note: Can't modify memo after workflow starts


def get_workflow_version_from_id(workflow_id: str) -> Optional[str]:
    """Extract version from workflow ID if encoded"""
    # Example: test-cycle-workflow-v1.2.0-abc123
    parts = workflow_id.split("-")
    for part in parts:
        if part.startswith("v") and "." in part:
            return part[1:]  # Remove 'v' prefix
    return None


def create_versioned_workflow_id(base_id: str, version: str = None) -> str:
    """Create a workflow ID with version information"""
    if version is None:
        version = WorkflowVersion.V1_2_0.value
    return f"{base_id}-v{version}"


# Workflow migration utilities
async def migrate_running_workflow(workflow_id: str, target_version: str) -> Dict[str, Any]:
    """Migrate a running workflow to a new version (requires admin privileges)"""
    # This would interact with Temporal's management API
    # to safely migrate running workflows
    return {
        "workflow_id": workflow_id,
        "status": "migration_scheduled",
        "target_version": target_version,
        "notes": "Workflow will be migrated at next safe checkpoint"
    }


class WorkflowCompatibilityChecker:
    """Check compatibility between workflow versions and features"""
    
    FEATURE_MATRIX = {
        WorkflowVersion.V1_0_0: {
            "parallel_phases": False,
            "phase_timing": False,
            "activity_retry": True,
            "custom_timeouts": False,
            "phase_skipping": False
        },
        WorkflowVersion.V1_1_0: {
            "parallel_phases": False,
            "phase_timing": True,
            "activity_retry": True,
            "custom_timeouts": True,
            "phase_skipping": False
        },
        WorkflowVersion.V1_2_0: {
            "parallel_phases": True,
            "phase_timing": True,
            "activity_retry": True,
            "custom_timeouts": True,
            "phase_skipping": True
        }
    }
    
    @classmethod
    def is_feature_supported(cls, version: str, feature: str) -> bool:
        """Check if a feature is supported in a given version"""
        try:
            workflow_version = WorkflowVersion(version)
            return cls.FEATURE_MATRIX.get(workflow_version, {}).get(feature, False)
        except ValueError:
            return False
    
    @classmethod
    def get_required_version_for_feature(cls, feature: str) -> Optional[str]:
        """Get the minimum version required for a feature"""
        for version in WorkflowVersion:
            if cls.FEATURE_MATRIX.get(version, {}).get(feature, False):
                return version.value
        return None
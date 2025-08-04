"""
RBAC Configuration - Central definition of resources, actions, and default permissions
"""

from typing import Dict, List, Set
from enum import Enum


class ResourceType(str, Enum):
    """Types of resources in the system"""
    SYSTEM = "system"
    WORKFLOW = "workflow"
    MODULE = "module"
    ENTITY = "entity"


class Action(str, Enum):
    """Standard actions that can be performed on resources"""
    # CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Workflow operations
    EXECUTE = "execute"
    SUBMIT = "submit"
    APPROVE = "approve"
    REVIEW = "review"
    OVERRIDE = "override"
    COMPLETE = "complete"
    
    # Management operations
    ASSIGN = "assign"
    MANAGE = "manage"
    ESCALATE = "escalate"
    
    # Data operations
    UPLOAD = "upload"
    DOWNLOAD = "download"
    GENERATE = "generate"
    PROVIDE = "provide"
    
    # Special operations
    ADMIN = "admin"
    IDENTIFY = "identify"


# Define all resources in the system
RESOURCES = {
    # System resources
    "system": {
        "display_name": "System Administration",
        "type": ResourceType.SYSTEM,
        "description": "Core system administration",
        "actions": [Action.ADMIN]
    },
    "permissions": {
        "display_name": "Permissions Management",
        "type": ResourceType.MODULE,
        "description": "Manage roles and permissions",
        "actions": [Action.MANAGE]
    },
    
    # Entity resources
    "cycles": {
        "display_name": "Test Cycles",
        "type": ResourceType.ENTITY,
        "description": "Test cycle management",
        "actions": [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.ASSIGN]
    },
    "reports": {
        "display_name": "Reports",
        "type": ResourceType.ENTITY,
        "description": "Report management",
        "actions": [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, 
                   Action.ASSIGN, Action.APPROVE, Action.OVERRIDE]
    },
    "users": {
        "display_name": "Users",
        "type": ResourceType.ENTITY,
        "description": "User management",
        "actions": [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.ASSIGN]
    },
    "lobs": {
        "display_name": "Lines of Business",
        "type": ResourceType.ENTITY,
        "description": "LOB management",
        "actions": [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.MANAGE]
    },
    
    # Workflow resources
    "workflow": {
        "display_name": "Workflow",
        "type": ResourceType.WORKFLOW,
        "description": "Overall workflow management",
        "actions": [Action.READ, Action.APPROVE, Action.OVERRIDE]
    },
    
    # Phase 1: Planning
    "planning": {
        "display_name": "Planning Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 1 - Document upload and attribute definition",
        "actions": [Action.EXECUTE, Action.UPLOAD, Action.CREATE, Action.UPDATE, 
                   Action.DELETE, Action.COMPLETE]
    },
    
    # Phase 2: Scoping
    "scoping": {
        "display_name": "Scoping Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 2 - Attribute scoping and recommendations",
        "actions": [Action.EXECUTE, Action.GENERATE, Action.SUBMIT, Action.APPROVE, 
                   Action.COMPLETE]
    },
    
    # Phase 3: Data Provider
    "data_owner": {
        "display_name": "Data Provider ID Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 3 - Identify and assign data providers",
        "actions": [Action.EXECUTE, Action.IDENTIFY, Action.ASSIGN, Action.UPLOAD, 
                   Action.ESCALATE, Action.COMPLETE]
    },
    
    # Phase 4: Sample Selection
    "sample_selection": {
        "display_name": "Sample Selection Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 4 - Generate and approve test samples",
        "actions": [Action.EXECUTE, Action.GENERATE, Action.UPLOAD, Action.APPROVE, 
                   Action.COMPLETE]
    },
    
    # Phase 5: Request Info
    "request_info": {
        "display_name": "Request Information Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 5 - Request and collect data",
        "actions": [Action.EXECUTE, Action.UPLOAD, Action.PROVIDE, Action.REVIEW, Action.COMPLETE]
    },
    
    # Phase 6: Testing
    "testing": {
        "display_name": "Test Execution Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 6 - Execute tests on samples",
        "actions": [Action.EXECUTE, Action.SUBMIT, Action.REVIEW, Action.APPROVE, 
                   Action.COMPLETE]
    },
    
    # Phase 7: Observations
    "observations": {
        "display_name": "Observation Management Phase",
        "type": ResourceType.MODULE,
        "description": "Phase 7 - Manage and resolve observations",
        "actions": [Action.CREATE, Action.UPDATE, Action.SUBMIT, Action.REVIEW, Action.APPROVE, 
                   Action.OVERRIDE, Action.COMPLETE, Action.DELETE]
    },
    
    # Analytics and Metrics
    "metrics": {
        "display_name": "Metrics and Analytics",
        "type": ResourceType.MODULE,
        "description": "System metrics, KPIs, and analytics",
        "actions": [Action.READ, Action.GENERATE]
    }
}


# Define which resources support resource-level permissions
RESOURCE_LEVEL_PERMISSIONS = {
    "report": ["reports"],      # Can grant access to specific reports
    "cycle": ["cycles"],        # Can grant access to specific cycles
    "lob": ["lobs"],           # Can grant access to specific LOBs
    "user": ["users"]          # Can grant permissions on specific users
}


# Define default role permissions (for migration)
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "Admin": ["*:*"],  # All permissions
    
    "Test Executive": [
        "cycles:create", "cycles:read", "cycles:update", "cycles:delete", "cycles:assign",
        "reports:create", "reports:read", "reports:assign",
        "users:read", "users:assign",
        "lobs:read",
        "workflow:read", "workflow:approve",
        "planning:read", "scoping:read", "testing:read", "observations:read",
        "metrics:read"
    ],
    
    "Tester": [
        "cycles:read",
        "reports:read",
        "planning:execute", "planning:upload", "planning:create", "planning:update", 
        "planning:delete", "planning:complete",
        "scoping:execute", "scoping:generate", "scoping:submit", "scoping:complete",
        "data_owner:execute", "data_owner:upload",
        "sample_selection:execute", "sample_selection:generate", "sample_selection:upload", 
        "sample_selection:complete",
        "request_info:execute", "request_info:review", "request_info:complete",
        "testing:execute", "testing:submit", "testing:complete",
        "observations:create", "observations:submit", "observations:update",
        "workflow:read",
        "lobs:read"
    ],
    
    "Report Owner": [
        "cycles:read",
        "reports:read", "reports:approve",
        "scoping:approve",
        "sample_selection:approve",
        "testing:review", "testing:approve",
        "observations:review", "observations:approve",
        "workflow:read", "workflow:approve",
        "metrics:read"
    ],
    
    "Report Owner Executive": [
        "reports:read", "reports:override",
        "workflow:read", "workflow:override",
        "observations:override",
        "cycles:read",
        "testing:read",
        "scoping:read",
        "metrics:read"
    ],
    
    "Data Owner": [
        "data_owner:execute", "data_owner:upload",
        "request_info:provide", "request_info:upload",
        "workflow:read"
    ],
    
    "Data Executive": [
        "lobs:read", "lobs:manage",
        "data_owner:identify", "data_owner:assign", "data_owner:escalate",
        "users:read",
        "cycles:read", "reports:read",
        "workflow:read",
        "metrics:read"
    ]
}


def get_all_permissions() -> Set[str]:
    """Get all possible permissions in the system"""
    permissions = set()
    for resource, config in RESOURCES.items():
        for action in config["actions"]:
            permissions.add(f"{resource}:{action}")
    return permissions


def get_resource_actions(resource: str) -> List[str]:
    """Get all valid actions for a resource"""
    if resource in RESOURCES:
        return [action.value for action in RESOURCES[resource]["actions"]]
    return []


def is_valid_permission(resource: str, action: str) -> bool:
    """Check if a resource:action combination is valid"""
    if resource not in RESOURCES:
        return False
    return action in [a.value for a in RESOURCES[resource]["actions"]]


def get_resource_info(resource: str) -> dict:
    """Get information about a resource"""
    return RESOURCES.get(resource, {})
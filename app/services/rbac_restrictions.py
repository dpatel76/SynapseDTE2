#!/usr/bin/env python3
"""
RBAC permission restriction service

This module enforces business logic restrictions on what permissions 
each role can have based on the actual permissions in the database.
"""

from typing import Dict, List, Set, Optional
from enum import Enum

class RoleType(str, Enum):
    """System role types"""
    ADMIN = "Admin"
    TEST_EXECUTIVE = "Test Executive"
    TESTER = "Tester"
    REPORT_OWNER = "Report Owner"
    REPORT_OWNER_EXECUTIVE = "Report Owner Executive"
    DATA_OWNER = "Data Owner"
    DATA_EXECUTIVE = "Data Executive"

# Define permission restrictions for each role based on actual database permissions
ROLE_PERMISSION_RESTRICTIONS = {
    RoleType.ADMIN: {
        # Admin can have all permissions - no restrictions
        "allowed_permissions": [],  # Empty means all allowed
        "forbidden_permissions": [],
        "description": "System administrator with full access to all resources and actions"
    },
    
    RoleType.TEST_EXECUTIVE: {
        "allowed_permissions": [
            # Cycles management
            "cycles:assign", "cycles:create", "cycles:delete", "cycles:read", "cycles:update",
            # Reports management  
            "reports:assign", "reports:read", "reports:update",
            # Observations management
            "observations:create", "observations:review", "observations:submit",
            # User management (limited)
            "users:read", "users:assign",
            # LOB access for reports and cycle coordination
            "lobs:read",
            # Planning and testing coordination
            "planning:complete", "planning:create", "planning:execute", "planning:update",
            "testing:approve", "testing:review",
            # Workflow oversight
            "workflow:read",
            # CycleReportSampleSelectionSamples selection and scoping
            "sample_selection:execute", "sample_selection:generate",
            "scoping:execute", "scoping:generate", "scoping:submit"
        ],
        "forbidden_permissions": [
            "system:admin", "permissions:manage",
            "users:create", "users:delete", "users:update",
            "reports:approve", "reports:override", "reports:delete",
            "lobs:manage", "data_provider:identify"
        ],
        "description": "Test Executive manages test cycles and coordinates testing activities"
    },
    
    RoleType.TESTER: {
        "allowed_permissions": [
            # Basic cycle access
            "cycles:read",
            # Limited report access
            "reports:read", "reports:create", "reports:update",
            # Observations 
            "observations:create", "observations:submit", "observations:review",
            # Planning and testing execution
            "planning:complete", "planning:execute", "planning:upload",
            "testing:complete", "testing:execute", "testing:submit",
            # CycleReportSampleSelectionSamples selection and scoping
            "sample_selection:complete", "sample_selection:execute", "sample_selection:upload",
            "scoping:complete", "scoping:execute", "scoping:submit",
            # Request info
            "request_info:provide", "request_info:upload",
            # Data provider permissions (for executing and completing data provider phase)
            "data_provider:execute", "data_provider:complete", "data_provider:read",
            # LOB read access (needed for sample LOB assignment)
            "lobs:read"
        ],
        "forbidden_permissions": [
            "system:admin", "permissions:manage",
            "users:create", "users:update", "users:delete", "users:assign",
            "cycles:create", "cycles:delete", "cycles:assign",
            "reports:approve", "reports:override", "reports:delete", "reports:assign",
            "lobs:manage", "data_provider:identify",
            "workflow:approve", "workflow:override"
        ],
        "description": "Executes tests and provides testing data"
    },
    
    RoleType.REPORT_OWNER: {
        "allowed_permissions": [
            # Read access to cycles
            "cycles:read",
            # Report approval and management
            "reports:read", "reports:approve", "reports:update",
            # Observations review
            "observations:approve", "observations:review",
            # Workflow oversight
            "workflow:read", "workflow:approve",
            # CycleReportSampleSelectionSamples selection and scoping approval
            "sample_selection:approve",
            "scoping:approve"
        ],
        "forbidden_permissions": [
            "system:admin", "permissions:manage",
            "users:create", "users:update", "users:delete", "users:assign",
            "cycles:create", "cycles:delete", "cycles:assign",
            "reports:create", "reports:delete", "reports:override", "reports:assign",
            "lobs:manage", "data_provider:identify",
            "testing:execute", "planning:execute"
        ],
        "description": "Reviews and approves reports for their area of responsibility"
    },
    
    RoleType.REPORT_OWNER_EXECUTIVE: {
        "allowed_permissions": [
            # Report oversight and override
            "reports:read", "reports:override", "reports:approve",
            # Workflow control
            "workflow:read", "workflow:override", "workflow:approve",
            # Observations oversight
            "observations:override", "observations:approve"
        ],
        "forbidden_permissions": [
            "system:admin", "permissions:manage",
            "users:create", "users:update", "users:delete", "users:assign",
            "cycles:create", "cycles:update", "cycles:delete", "cycles:assign",
            "reports:create", "reports:update", "reports:delete", "reports:assign",
            "lobs:manage", "data_provider:identify",
            "testing:execute", "planning:execute"
        ],
        "description": "Executive level access to override report approvals when necessary"
    },
    
    RoleType.DATA_OWNER: {
        "allowed_permissions": [
            # Data provider specific (using data_provider resource name)
            "data_provider:execute", "data_provider:upload", "data_provider:complete", "data_provider:read",
            # Request info handling
            "request_info:provide", "request_info:upload", "request_info:complete", "request_info:execute",
            # Read access to cycles and reports (needed for navigation)
            "cycles:read", "reports:read"
        ],
        "forbidden_permissions": [
            "system:admin", "permissions:manage",
            "users:create", "users:update", "users:delete", "users:assign",
            "cycles:create", "cycles:update", "cycles:delete", "cycles:assign",
            "reports:create", "reports:update", "reports:delete", "reports:approve", "reports:override", "reports:assign",
            "observations:create", "observations:update", "observations:approve", "observations:override",
            "lobs:manage", "workflow:approve", "workflow:override",
            "planning:execute", "testing:execute"
        ],
        "description": "Data Owner provides data and responds to information requests"
    },
    
    RoleType.DATA_EXECUTIVE: {
        "allowed_permissions": [
            # LOB management
            "lobs:create", "lobs:delete", "lobs:manage", "lobs:read", "lobs:update",
            # Data provider oversight (using data_provider resource name)
            "data_provider:identify", "data_provider:assign", "data_provider:escalate", "data_provider:read",
            # User assignment (but not creation/deletion)
            "users:read", "users:assign",
            # Cycle and report overview
            "cycles:read", "reports:read"
        ],
        "forbidden_permissions": [
            "system:admin", "permissions:manage",
            "users:create", "users:delete", "users:update",
            "cycles:create", "cycles:update", "cycles:delete", "cycles:assign",
            "reports:create", "reports:update", "reports:delete", "reports:approve", "reports:override", "reports:assign",
            "observations:create", "observations:update", "observations:approve", "observations:override",
            "workflow:approve", "workflow:override",
            "planning:execute", "testing:execute"
        ],
        "description": "Data Executive with LOB management and data owner oversight"
    }
}

def get_allowed_permissions_for_role(role_name: str, all_permissions: Optional[List[str]] = None) -> Set[str]:
    """Get all allowed permissions for a role"""
    if role_name not in [r.value for r in RoleType]:
        raise ValueError(f"Unknown role: {role_name}")
    
    role_type = RoleType(role_name)
    restrictions = ROLE_PERMISSION_RESTRICTIONS[role_type]
    
    # Admin has all permissions
    if role_type == RoleType.ADMIN:
        if all_permissions:
            return set(all_permissions)
        else:
            # Return a large set if no specific permissions provided
            return set()
    
    # For other roles, return their specifically allowed permissions
    allowed = set(restrictions["allowed_permissions"])
    forbidden = set(restrictions["forbidden_permissions"])
    
    # Remove any forbidden permissions from allowed (safety check)
    return allowed - forbidden

def get_forbidden_permissions_for_role(role_name: str) -> Set[str]:
    """Get all forbidden permissions for a role"""
    if role_name not in [r.value for r in RoleType]:
        raise ValueError(f"Unknown role: {role_name}")
    
    role_type = RoleType(role_name)
    return set(ROLE_PERMISSION_RESTRICTIONS[role_type]["forbidden_permissions"])

def is_permission_allowed_for_role(role_name: str, permission: str, all_permissions: Optional[List[str]] = None) -> bool:
    """Check if a permission is allowed for a specific role"""
    try:
        # Admin has no restrictions
        if role_name == RoleType.ADMIN.value:
            return True
        
        role_type = RoleType(role_name)
        restrictions = ROLE_PERMISSION_RESTRICTIONS[role_type]
        
        # Check if explicitly forbidden
        if permission in restrictions["forbidden_permissions"]:
            return False
        
        # Check if explicitly allowed
        if permission in restrictions["allowed_permissions"]:
            return True
        
        # If not in either list, it's not allowed (whitelist approach)
        return False
    except ValueError:
        return False

def validate_role_permissions(role_name: str, permissions: List[str], all_permissions: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """
    Validate a list of permissions for a role
    Returns dict with 'allowed' and 'forbidden' lists
    """
    allowed = []
    forbidden = []
    
    for permission in permissions:
        if is_permission_allowed_for_role(role_name, permission, all_permissions):
            allowed.append(permission)
        else:
            forbidden.append(permission)
    
    return {
        "allowed": allowed,
        "forbidden": forbidden
    }

def get_role_description(role_name: str) -> str:
    """Get description for a role"""
    if role_name not in [r.value for r in RoleType]:
        return "Unknown role"
    
    role_type = RoleType(role_name)
    return ROLE_PERMISSION_RESTRICTIONS[role_type]["description"]

def filter_permissions_for_role(role_name: str, permissions: List[str]) -> List[str]:
    """Filter a list of permissions to only include those allowed for the role"""
    return [perm for perm in permissions if is_permission_allowed_for_role(role_name, perm)]

def get_restricted_permissions_for_role(role_name: str, all_permissions: List[str]) -> Dict[str, List[str]]:
    """
    Get allowed and forbidden permissions for a role from a complete list
    Returns dict with 'allowed' and 'forbidden' lists
    """
    if role_name == RoleType.ADMIN.value:
        return {
            "allowed": all_permissions,
            "forbidden": []
        }
    
    allowed = []
    forbidden = []
    
    for permission in all_permissions:
        if is_permission_allowed_for_role(role_name, permission):
            allowed.append(permission)
        else:
            forbidden.append(permission)
    
    return {
        "allowed": allowed,
        "forbidden": forbidden
    } 
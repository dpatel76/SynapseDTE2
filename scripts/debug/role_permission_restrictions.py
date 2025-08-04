#!/usr/bin/env python3
"""
Role-based permission restriction system

This module defines what permissions each role can have based on business logic and security requirements.
"""

from typing import Dict, List, Set
from enum import Enum

class ResourceType(str, Enum):
    """Resource types in the system"""
    SYSTEM = "system"
    PERMISSIONS = "permissions"
    USERS = "users"
    CYCLES = "cycles"
    REPORTS = "reports"
    OBSERVATIONS = "observations"
    LOBS = "lobs"
    SLA = "sla"
    PLANNING = "planning"
    TESTING = "testing"
    WORKFLOW = "workflow"
    DATA_PROVIDER = "data_owner"
    REQUEST_INFO = "request_info"

class ActionType(str, Enum):
    """Action types in the system"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"
    ASSIGN = "assign"
    EXECUTE = "execute"
    APPROVE = "approve"
    OVERRIDE = "override"
    UPLOAD = "upload"
    IDENTIFY = "identify"
    PROVIDE = "provide"
    ADMIN = "admin"

class RoleType(str, Enum):
    """System role types"""
    ADMIN = "Admin"
    TEST_EXECUTIVE = "Test Executive"
    TESTER = "Tester"
    REPORT_OWNER = "Report Owner"
    REPORT_OWNER_EXECUTIVE = "Report Owner Executive"
    DATA_OWNER = "Data Owner"
    DATA_EXECUTIVE = "Data Executive"

# Define permission restrictions for each role
ROLE_PERMISSION_RESTRICTIONS = {
    RoleType.ADMIN: {
        # Admin can have all permissions - no restrictions
        "allowed_resources": [r.value for r in ResourceType],
        "allowed_actions": [a.value for a in ActionType],
        "forbidden_permissions": [],  # No restrictions for admin
        "description": "System administrator with full access to all resources and actions"
    },
    
    RoleType.TEST_MANAGER: {
        "allowed_resources": [
            ResourceType.CYCLES,
            ResourceType.REPORTS,
            ResourceType.OBSERVATIONS,
            ResourceType.USERS,
            ResourceType.LOBS,
            ResourceType.PLANNING,
            ResourceType.TESTING,
            ResourceType.WORKFLOW,
            ResourceType.SLA
        ],
        "allowed_actions": [
            ActionType.READ,
            ActionType.CREATE,
            ActionType.UPDATE,
            ActionType.DELETE,
            ActionType.ASSIGN,
            ActionType.EXECUTE,
            ActionType.MANAGE
        ],
        "forbidden_permissions": [
            "system:admin",
            "permissions:manage",
            "users:delete",  # Can't delete users
            "lobs:manage",   # Can't manage LOBs directly
            "data_owner:identify"  # Can't identify data providers
        ],
        "description": "Manages test cycles and coordinates testing activities"
    },
    
    RoleType.TESTER: {
        "allowed_resources": [
            ResourceType.CYCLES,
            ResourceType.REPORTS,
            ResourceType.OBSERVATIONS,
            ResourceType.PLANNING,
            ResourceType.TESTING,
            ResourceType.WORKFLOW,
            ResourceType.REQUEST_INFO
        ],
        "allowed_actions": [
            ActionType.READ,
            ActionType.CREATE,
            ActionType.UPDATE,
            ActionType.EXECUTE,
            ActionType.PROVIDE
        ],
        "forbidden_permissions": [
            "system:admin",
            "permissions:manage",
            "users:create",
            "users:update", 
            "users:delete",
            "users:manage",
            "cycles:delete",  # Can't delete cycles
            "reports:delete", # Can't delete reports
            "reports:approve", # Can't approve reports
            "reports:override", # Can't override reports
            "lobs:manage",
            "sla:manage",
            "data_owner:identify"
        ],
        "description": "Executes tests and provides testing data"
    },
    
    RoleType.REPORT_OWNER: {
        "allowed_resources": [
            ResourceType.CYCLES,
            ResourceType.REPORTS,
            ResourceType.OBSERVATIONS,
            ResourceType.WORKFLOW,
            ResourceType.SLA
        ],
        "allowed_actions": [
            ActionType.READ,
            ActionType.UPDATE,
            ActionType.APPROVE,
            ActionType.MANAGE
        ],
        "forbidden_permissions": [
            "system:admin",
            "permissions:manage",
            "users:create",
            "users:update",
            "users:delete",
            "users:manage",
            "cycles:create",
            "cycles:delete",
            "reports:create",  # Reports are created by system/testers
            "reports:delete",
            "reports:override", # Can't override, only approve
            "lobs:manage",
            "data_owner:identify",
            "testing:execute",
            "planning:execute"
        ],
        "description": "Reviews and approves reports for their area of responsibility"
    },
    
    RoleType.REPORT_OWNER_EXECUTIVE: {
        "allowed_resources": [
            ResourceType.REPORTS,
            ResourceType.WORKFLOW,
            ResourceType.SLA,
            ResourceType.OBSERVATIONS
        ],
        "allowed_actions": [
            ActionType.READ,
            ActionType.OVERRIDE,
            ActionType.APPROVE
        ],
        "forbidden_permissions": [
            "system:admin",
            "permissions:manage",
            "users:create",
            "users:update",
            "users:delete",
            "users:manage",
            "cycles:create",
            "cycles:update",
            "cycles:delete",
            "cycles:assign",
            "reports:create",
            "reports:update",
            "reports:delete",
            "lobs:manage",
            "data_owner:identify",
            "testing:execute",
            "planning:execute"
        ],
        "description": "Executive level access to override report approvals when necessary"
    },
    
    RoleType.DATA_PROVIDER: {
        "allowed_resources": [
            ResourceType.DATA_PROVIDER,
            ResourceType.REQUEST_INFO,
            ResourceType.CYCLES,
            ResourceType.REPORTS
        ],
        "allowed_actions": [
            ActionType.READ,
            ActionType.EXECUTE,
            ActionType.UPLOAD,
            ActionType.PROVIDE
        ],
        "forbidden_permissions": [
            "system:admin",
            "permissions:manage",
            "users:create",
            "users:update",
            "users:delete",
            "users:manage",
            "cycles:create",
            "cycles:update",
            "cycles:delete",
            "cycles:assign",
            "reports:create",
            "reports:update",
            "reports:delete",
            "reports:approve",
            "reports:override",
            "observations:create",
            "observations:update",
            "observations:delete",
            "lobs:manage",
            "sla:manage",
            "workflow:update",
            "planning:execute",
            "testing:execute"
        ],
        "description": "Provides data and responds to information requests"
    },
    
    RoleType.CDO: {
        "allowed_resources": [
            ResourceType.LOBS,
            ResourceType.DATA_PROVIDER,
            ResourceType.USERS,
            ResourceType.CYCLES,
            ResourceType.REPORTS,
            ResourceType.SLA
        ],
        "allowed_actions": [
            ActionType.READ,
            ActionType.MANAGE,
            ActionType.IDENTIFY,
            ActionType.ASSIGN
        ],
        "forbidden_permissions": [
            "system:admin",
            "permissions:manage",
            "users:create",  # Can identify/assign but not create users
            "users:delete",
            "cycles:create",
            "cycles:update",
            "cycles:delete",
            "reports:create",
            "reports:update",
            "reports:delete",
            "reports:approve",
            "reports:override",
            "observations:create",
            "observations:update",
            "observations:delete",
            "workflow:update",
            "planning:execute",
            "testing:execute"
        ],
        "description": "Chief Data Officer with LOB management and data provider oversight"
    }
}

def get_allowed_permissions_for_role(role_name: str) -> Set[str]:
    """Get all allowed permissions for a role"""
    if role_name not in [r.value for r in RoleType]:
        raise ValueError(f"Unknown role: {role_name}")
    
    role_type = RoleType(role_name)
    restrictions = ROLE_PERMISSION_RESTRICTIONS[role_type]
    
    # Admin has all permissions
    if role_type == RoleType.ADMIN:
        # Generate all possible permissions
        all_permissions = set()
        for resource in [r.value for r in ResourceType]:
            for action in [a.value for a in ActionType]:
                all_permissions.add(f"{resource}:{action}")
        return all_permissions
    
    # Generate permissions based on allowed resources and actions
    allowed_permissions = set()
    for resource in restrictions["allowed_resources"]:
        for action in restrictions["allowed_actions"]:
            permission = f"{resource}:{action}"
            # Only add if not explicitly forbidden
            if permission not in restrictions["forbidden_permissions"]:
                allowed_permissions.add(permission)
    
    return allowed_permissions

def get_forbidden_permissions_for_role(role_name: str) -> Set[str]:
    """Get all forbidden permissions for a role"""
    if role_name not in [r.value for r in RoleType]:
        raise ValueError(f"Unknown role: {role_name}")
    
    role_type = RoleType(role_name)
    return set(ROLE_PERMISSION_RESTRICTIONS[role_type]["forbidden_permissions"])

def is_permission_allowed_for_role(role_name: str, permission: str) -> bool:
    """Check if a permission is allowed for a specific role"""
    try:
        allowed = get_allowed_permissions_for_role(role_name)
        forbidden = get_forbidden_permissions_for_role(role_name)
        
        # Admin has no restrictions
        if role_name == RoleType.ADMIN.value:
            return True
        
        # Check if explicitly forbidden
        if permission in forbidden:
            return False
        
        # Check if in allowed set
        return permission in allowed
    except ValueError:
        return False

def validate_role_permissions(role_name: str, permissions: List[str]) -> Dict[str, List[str]]:
    """
    Validate a list of permissions for a role
    Returns dict with 'allowed' and 'forbidden' lists
    """
    allowed = []
    forbidden = []
    
    for permission in permissions:
        if is_permission_allowed_for_role(role_name, permission):
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

if __name__ == "__main__":
    # Test the restrictions
    print("Role Permission Restrictions Test")
    print("=" * 50)
    
    for role in RoleType:
        print(f"\n{role.value}:")
        print(f"Description: {get_role_description(role.value)}")
        allowed = get_allowed_permissions_for_role(role.value)
        forbidden = get_forbidden_permissions_for_role(role.value)
        print(f"Allowed permissions: {len(allowed)}")
        print(f"Forbidden permissions: {len(forbidden)}")
        
        # Test specific permissions that should exist for each role
        if role.value == "Admin":
            test_permissions = ["system:admin", "cycles:read", "reports:approve", "users:manage"]
        elif role.value == "Test Executive":
            test_permissions = ["cycles:read", "cycles:create", "reports:read", "users:read"]
        elif role.value == "Tester":
            test_permissions = ["cycles:read", "testing:execute", "observations:create", "reports:read"]
        elif role.value == "Report Owner":
            test_permissions = ["cycles:read", "reports:read", "reports:approve", "workflow:read"]
        elif role.value == "Report Owner Executive":
            test_permissions = ["reports:read", "reports:override", "workflow:read", "sla:read"]
        elif role.value == "Data Owner":
            test_permissions = ["data_owner:execute", "request_info:provide", "cycles:read", "reports:read"]
        elif role.value == "Data Executive":
            test_permissions = ["lobs:manage", "data_owner:identify", "users:read", "reports:read"]
        else:
            test_permissions = []
            
        for perm in test_permissions:
            allowed_status = is_permission_allowed_for_role(role.value, perm)
            print(f"  {perm}: {'✅ Allowed' if allowed_status else '❌ Forbidden'}")
        
        # Show a few forbidden permissions for non-admin roles
        if role.value != "Admin" and forbidden:
            print(f"  Sample forbidden: {list(forbidden)[:3]}") 
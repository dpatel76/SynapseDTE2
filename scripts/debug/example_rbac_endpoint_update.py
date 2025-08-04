#!/usr/bin/env python3
"""
Example: How to update endpoints to use new RBAC system
"""

# BEFORE: Using hardcoded role checks
"""
@router.post("/", response_model=TestCycleResponse)
async def create_test_cycle(
    cycle_data: TestCycleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Old way - hardcoded role check
    RoleChecker([UserRoles.TEST_EXECUTIVE])(current_user)
    
    # Create cycle...
    return cycle
"""

# AFTER: Using flexible permission system
"""
from app.core.permissions import require_permission

@router.post("/", response_model=TestCycleResponse)
@require_permission("cycles", "create")
async def create_test_cycle(
    cycle_data: TestCycleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Permission already checked by decorator
    # Create cycle...
    return cycle
"""

# Example conversions for common endpoints:

CONVERSION_MAP = {
    # Cycles endpoints
    "RoleChecker([UserRoles.TEST_EXECUTIVE])": '@require_permission("cycles", "create")',
    "require_management": '@require_permission("cycles", "read")',
    
    # Planning endpoints  
    "RoleChecker(tester_roles)": '@require_permission("planning", "execute")',
    "assigned tester check": '@require_permission("planning", "execute", resource_id_param="report_id")',
    
    # Reports endpoints
    "RoleChecker([UserRoles.REPORT_OWNER])": '@require_permission("reports", "approve")',
    "RoleChecker([UserRoles.REPORT_OWNER_EXECUTIVE])": '@require_permission("reports", "override")',
    
    # Admin endpoints
    "require_admin": '@require_permission("system", "admin")'
}

# Full example of updating planning endpoint:

print("""
=== EXAMPLE: Update Planning Endpoint ===

File: app/api/v1/endpoints/planning.py

Changes needed:

1. Import the permission decorator:
   from app.core.permissions import require_permission

2. Replace role checks:

   OLD:
   @router.post("/{cycle_id}/reports/{report_id}/attributes")
   async def create_attribute(
       ...
       current_user: User = Depends(get_current_user)
   ):
       # Check if user is assigned tester
       RoleChecker(tester_roles)(current_user)
       
   NEW:
   @router.post("/{cycle_id}/reports/{report_id}/attributes")
   @require_permission("planning", "create", resource_id_param="report_id")
   async def create_attribute(
       ...
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)  # Required for permission check
   ):
       # Permission already checked

3. For resource-specific checks:
   - Use resource_id_param to specify which parameter contains the resource ID
   - This enables checking if user has permission for that specific report/cycle

4. For multiple permission requirements:
   @require_all_permissions(("reports", "read"), ("reports", "approve"))
   
5. For any-of permissions:
   @require_any_permission(("reports", "update"), ("reports", "approve"))
""")
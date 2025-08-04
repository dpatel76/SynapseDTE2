"""
Admin endpoints for RBAC management
"""

from typing import List, Optional, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.core.logging import get_logger
from app.models.user import User
from app.models.rbac import (
    Permission, Role, RolePermission, UserRole,
    UserPermission, ResourcePermission, PermissionAuditLog
)
from app.services.permission_service import get_permission_service
from app.services.rbac_restrictions import (
    is_permission_allowed_for_role, validate_role_permissions,
    get_restricted_permissions_for_role, get_role_description
)
from app.schemas.rbac import (
    PermissionSchema, PermissionCreate,
    RoleSchema, RoleCreate, RoleUpdate,
    UserRoleAssignment, UserPermissionGrant,
    ResourcePermissionGrant, PermissionAuditSchema,
    UserPermissionsResponse, RolePermissionsUpdate
)

logger = get_logger(__name__)
router = APIRouter()


# Permission Management

@router.get("/permissions", response_model=List[PermissionSchema])
async def list_permissions(
    resource: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all available permissions with optional filtering"""
    query = select(Permission)
    
    if resource:
        query = query.where(Permission.resource == resource)
    if action:
        query = query.where(Permission.action == action)
    
    query = query.offset(skip).limit(limit).order_by(Permission.resource, Permission.action)
    
    result = await db.execute(query)
    permissions = result.scalars().all()
    
    return permissions


@router.post("/permissions", response_model=PermissionSchema)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new permission"""
    # Check if already exists
    existing = await db.execute(
        select(Permission).where(
            and_(
                Permission.resource == permission_data.resource,
                Permission.action == permission_data.action
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission {permission_data.resource}:{permission_data.action} already exists"
        )
    
    permission = Permission(**permission_data.dict())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    
    logger.info(f"Permission created: {permission.permission_string} by {current_user.email}")
    
    return permission


@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a permission (cascades to all assignments)"""
    permission = await db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    perm_string = permission.permission_string
    await db.delete(permission)
    await db.commit()
    
    logger.info(f"Permission deleted: {perm_string} by {current_user.email}")
    
    return {"message": f"Permission {perm_string} deleted successfully"}


# Role Permission Management

@router.get("/roles/{role_id}/permissions/restrictions")
async def get_role_permission_restrictions(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get allowed and forbidden permissions for a specific role"""
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get all permissions
    all_permissions_result = await db.execute(select(Permission))
    all_permissions = [p.permission_string for p in all_permissions_result.scalars()]
    
    # Get restrictions for this role
    restrictions = get_restricted_permissions_for_role(role.role_name, all_permissions)
    
    return {
        "role_name": role.role_name,
        "role_description": get_role_description(role.role_name),
        "total_permissions": len(all_permissions),
        "allowed_count": len(restrictions["allowed"]),
        "forbidden_count": len(restrictions["forbidden"]),
        "allowed_permissions": restrictions["allowed"],
        "forbidden_permissions": restrictions["forbidden"]
    }

@router.get("/roles/{role_id}/permissions", response_model=List[PermissionSchema])
async def get_role_permissions(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions for a role"""
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    result = await db.execute(
        select(Permission).join(RolePermission).where(
            RolePermission.role_id == role_id
        )
    )
    permissions = result.scalars().all()
    
    return permissions


# Role Management

@router.get("/roles")
async def list_roles(
    include_permissions: bool = Query(False, description="Include permissions for each role"),
    include_user_count: bool = Query(False, description="Include user count for each role"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all roles"""
    query = select(Role).where(Role.is_active == True)
    
    if include_permissions:
        query = query.options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    
    query = query.offset(skip).limit(limit).order_by(Role.role_name)
    
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # Build response data manually
    response_data = []
    for role in roles:
        role_data = {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
        
        # Add permissions if requested
        if include_permissions:
            if hasattr(role, 'role_permissions') and role.role_permissions:
                role_data["permissions"] = [
                    {
                        "permission_id": rp.permission.permission_id,
                        "resource": rp.permission.resource,
                        "action": rp.permission.action,
                        "description": rp.permission.description,
                        "permission_string": rp.permission.permission_string,
                        "created_at": rp.permission.created_at,
                        "updated_at": rp.permission.updated_at
                    }
                    for rp in role.role_permissions
                ]
            else:
                role_data["permissions"] = []
        
        # Add user count if requested
        if include_user_count:
            count_result = await db.execute(
                select(func.count(UserRole.user_id)).where(
                    and_(
                        UserRole.role_id == role.role_id,
                        or_(
                            UserRole.expires_at.is_(None),
                            UserRole.expires_at > datetime.utcnow()
                        )
                    )
                )
            )
            role_data["user_count"] = count_result.scalar()
        
        response_data.append(role_data)
    
    return response_data


@router.post("/roles", response_model=RoleSchema)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role"""
    # Check if already exists
    existing = await db.execute(
        select(Role).where(Role.role_name == role_data.role_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {role_data.role_name} already exists"
        )
    
    role = Role(**role_data.dict())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    logger.info(f"Role created: {role.role_name} by {current_user.email}")
    
    return role


@router.put("/roles/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a role"""
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Don't allow modification of system roles (except description)
    if role.is_system and role_data.role_name and role_data.role_name != role.role_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rename system roles"
        )
    
    update_data = role_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    
    role.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(role)
    
    logger.info(f"Role updated: {role.role_name} by {current_user.email}")
    
    return role


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a role (soft delete by setting is_active=False)"""
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles"
        )
    
    role.is_active = False
    role.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Role deactivated: {role.role_name} by {current_user.email}")
    
    return {"message": f"Role {role.role_name} deactivated successfully"}


# Role Permission Management

@router.put("/roles/{role_id}/permissions", response_model=RoleSchema)
async def update_role_permissions(
    role_id: int,
    permission_update: RolePermissionsUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update all permissions for a role (replaces existing) with validation"""
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get all permissions to validate against
    all_permissions_result = await db.execute(select(Permission))
    all_permissions = [p.permission_string for p in all_permissions_result.scalars()]
    
    # Get the permissions being requested
    requested_permission_ids = permission_update.permission_ids
    requested_permissions_result = await db.execute(
        select(Permission).where(Permission.permission_id.in_(requested_permission_ids))
    )
    requested_permissions = [p.permission_string for p in requested_permissions_result.scalars()]
    
    # Validate permissions for this role
    validation_result = validate_role_permissions(role.role_name, requested_permissions)
    
    if validation_result["forbidden"]:
        forbidden_perms = ", ".join(validation_result["forbidden"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following permissions are not allowed for role '{role.role_name}': {forbidden_perms}"
        )
    
    # Get permission service
    permission_service = await get_permission_service(db)
    
    # Remove all existing permissions
    await db.execute(
        select(RolePermission).where(RolePermission.role_id == role_id)
    )
    
    # Add new permissions (only the allowed ones)
    for perm_id in requested_permission_ids:
        # Double-check each permission is in the allowed list
        perm_result = await db.execute(
            select(Permission).where(Permission.permission_id == perm_id)
        )
        perm = perm_result.scalar_one_or_none()
        if perm and perm.permission_string in validation_result["allowed"]:
            await permission_service.grant_permission_to_role(
                role_id, perm_id, current_user.user_id
            )
    
    # Refresh role with permissions
    result = await db.execute(
        select(Role).options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        ).where(Role.role_id == role_id)
    )
    role = result.scalar_one()
    
    logger.info(f"Role permissions updated: {role.role_name} by {current_user.email}")
    
    return role


@router.post("/roles/{role_id}/permissions/{permission_id}")
async def grant_permission_to_role(
    role_id: int,
    permission_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Grant a specific permission to a role with validation"""
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permission = await db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Validate permission for this role
    if not is_permission_allowed_for_role(role.role_name, permission.permission_string):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission '{permission.permission_string}' is not allowed for role '{role.role_name}'"
        )
    
    permission_service = await get_permission_service(db)
    
    success = await permission_service.grant_permission_to_role(
        role_id, permission_id, current_user.user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to grant permission"
        )
    
    return {"message": "Permission granted successfully"}


@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a specific permission from a role"""
    permission_service = await get_permission_service(db)
    
    success = await permission_service.revoke_permission_from_role(
        role_id, permission_id, current_user.user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission assignment not found"
        )
    
    return {"message": "Permission revoked successfully"}


# User Permission Management

@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions for a user (direct + role-based)"""
    # Users can only access their own permissions unless they're admin
    if user_id != current_user.user_id and current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Users can only view their own permissions."
        )
    permission_service = await get_permission_service(db)
    
    # Get all permissions
    all_permissions = await permission_service.get_user_permissions(user_id)
    
    # Get direct permissions
    direct_result = await db.execute(
        select(Permission).join(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.granted == True,
                or_(
                    UserPermission.expires_at.is_(None),
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
    )
    direct_permissions = [p.permission_string for p in direct_result.scalars()]
    
    # Get user roles with their permissions properly loaded
    roles_result = await db.execute(
        select(Role)
        .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        .join(UserRole)
        .where(
            and_(
                UserRole.user_id == user_id,
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.utcnow()
                )
            )
        )
    )
    roles_from_db = list(roles_result.scalars())
    
    # Convert roles to serializable format to avoid greenlet issues
    roles_data = []
    for role in roles_from_db:
        role_dict = {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
            "permissions": [
                {
                    "permission_id": rp.permission.permission_id,
                    "resource": rp.permission.resource,
                    "action": rp.permission.action,
                    "description": rp.permission.description,
                    "permission_string": rp.permission.permission_string,
                    "created_at": rp.permission.created_at.isoformat() if rp.permission.created_at else None,
                    "updated_at": rp.permission.updated_at.isoformat() if rp.permission.updated_at else None
                }
                for rp in role.role_permissions
            ] if hasattr(role, 'role_permissions') and role.role_permissions else []
        }
        roles_data.append(role_dict)
    
    # Return raw dictionary to avoid Pydantic validation issues
    return {
        "user_id": user_id,
        "all_permissions": list(all_permissions),
        "direct_permissions": direct_permissions,
        "roles": roles_data
    }


@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: int,
    assignment: UserRoleAssignment,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a user"""
    permission_service = await get_permission_service(db)
    
    success = await permission_service.assign_role_to_user(
        user_id,
        assignment.role_id,
        current_user.user_id,
        assignment.expires_at
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role"
        )
    
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Remove a role from a user"""
    result = await db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        )
    )
    user_role = result.scalar_one_or_none()
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role assignment not found"
        )
    
    await db.delete(user_role)
    
    # Add audit log
    audit = PermissionAuditLog(
        action_type='revoke',
        target_type='user',
        target_id=user_id,
        role_id=role_id,
        performed_by=current_user.user_id
    )
    db.add(audit)
    
    await db.commit()
    
    return {"message": "Role removed successfully"}


@router.post("/users/{user_id}/permissions")
async def grant_permission_to_user(
    user_id: int,
    grant: UserPermissionGrant,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Grant a permission directly to a user"""
    permission_service = await get_permission_service(db)
    
    success = await permission_service.grant_permission_to_user(
        user_id,
        grant.permission_id,
        current_user.user_id,
        grant.expires_at
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to grant permission"
        )
    
    return {"message": "Permission granted successfully"}


# Resource Permission Management

@router.post("/resource-permissions")
async def grant_resource_permission(
    grant: ResourcePermissionGrant,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Grant permission for a specific resource to a user"""
    # Validate permission exists
    permission = await db.get(Permission, grant.permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check if already exists
    existing = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.user_id == grant.user_id,
                ResourcePermission.resource_type == grant.resource_type,
                ResourcePermission.resource_id == grant.resource_id,
                ResourcePermission.permission_id == grant.permission_id
            )
        )
    )
    
    resource_perm = existing.scalar_one_or_none()
    if resource_perm:
        # Update existing
        resource_perm.granted = True
        resource_perm.granted_by = current_user.user_id
        resource_perm.granted_at = datetime.utcnow()
        resource_perm.expires_at = grant.expires_at
    else:
        # Create new
        resource_perm = ResourcePermission(
            user_id=grant.user_id,
            resource_type=grant.resource_type,
            resource_id=grant.resource_id,
            permission_id=grant.permission_id,
            granted=True,
            granted_by=current_user.user_id,
            expires_at=grant.expires_at
        )
        db.add(resource_perm)
    
    await db.commit()
    
    logger.info(
        f"Resource permission granted: user={grant.user_id}, "
        f"{grant.resource_type}:{grant.resource_id}, "
        f"permission={permission.permission_string} by {current_user.email}"
    )
    
    return {"message": "Resource permission granted successfully"}


# Audit Log

@router.get("/audit-log", response_model=List[PermissionAuditSchema])
async def get_permission_audit_log(
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    performed_by: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get permission change audit log"""
    query = select(PermissionAuditLog).options(
        selectinload(PermissionAuditLog.permission),
        selectinload(PermissionAuditLog.role),
        selectinload(PermissionAuditLog.performer)
    )
    
    if target_type:
        query = query.where(PermissionAuditLog.target_type == target_type)
    if target_id:
        query = query.where(PermissionAuditLog.target_id == target_id)
    if performed_by:
        query = query.where(PermissionAuditLog.performed_by == performed_by)
    
    query = query.order_by(PermissionAuditLog.performed_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    audit_logs = result.scalars().all()
    
    return audit_logs
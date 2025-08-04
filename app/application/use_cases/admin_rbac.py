"""
Use cases for Admin RBAC functionality
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessRuleViolation, ResourceNotFound
from app.core.logging import get_logger
from app.models.user import User
from app.models.rbac import (
    Permission, Role, RolePermission, UserRole,
    UserPermission, ResourcePermission, PermissionAuditLog
)
from app.services.permission_service import get_permission_service, PermissionService
from app.services.rbac_restrictions import (
    is_permission_allowed_for_role, validate_role_permissions,
    get_restricted_permissions_for_role, get_role_description
)
from app.application.dtos.admin_rbac import (
    # Permission Management
    PermissionDTO,
    CreatePermissionRequestDTO,
    PermissionListResponseDTO,
    DeletePermissionResponseDTO,
    # Role Management
    RoleDTO,
    CreateRoleRequestDTO,
    UpdateRoleRequestDTO,
    RoleListResponseDTO,
    DeleteRoleResponseDTO,
    # Role Permission Management
    RolePermissionRestrictionsDTO,
    UpdateRolePermissionsRequestDTO,
    GrantRolePermissionResponseDTO,
    RevokeRolePermissionResponseDTO,
    # User Permission Management
    UserPermissionsDTO,
    AssignRoleToUserRequestDTO,
    AssignRoleToUserResponseDTO,
    RemoveRoleFromUserResponseDTO,
    GrantPermissionToUserRequestDTO,
    GrantPermissionToUserResponseDTO,
    # Resource Permission Management
    GrantResourcePermissionRequestDTO,
    GrantResourcePermissionResponseDTO,
    # Audit Log
    PermissionAuditLogDTO,
    PermissionAuditLogListResponseDTO
)

logger = get_logger(__name__)


# Base class for Admin RBAC use cases
class AdminRBACUseCase:
    """Base class for admin RBAC use cases with common dependencies"""
    def __init__(self, db: AsyncSession, current_user: User, **services):
        self.db = db
        self.current_user = current_user
        # Store all provided services
        for service_name, service in services.items():
            setattr(self, service_name, service)


# Permission Management Use Cases
class ListPermissionsUseCase(AdminRBACUseCase):
    """Use case for listing permissions"""
    
    async def execute(self, params: Dict[str, Any]) -> PermissionListResponseDTO:
        resource = params.get('resource')
        action = params.get('action')
        skip = params.get('skip', 0)
        limit = params.get('limit', 100)
        
        query = select(Permission)
        
        if resource:
            query = query.where(Permission.resource == resource)
        if action:
            query = query.where(Permission.action == action)
        
        # Get total count before applying pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        filtered_count = total_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Permission.resource, Permission.action)
        
        result = await self.db.execute(query)
        permissions = result.scalars().all()
        
        # Convert to DTOs
        permission_dtos = [
            PermissionDTO(
                permission_id=p.permission_id,
                resource=p.resource,
                action=p.action,
                description=p.description,
                permission_string=p.permission_string,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in permissions
        ]
        
        return PermissionListResponseDTO(
            permissions=permission_dtos,
            total_count=filtered_count,
            filtered_count=len(permission_dtos)
        )


class CreatePermissionUseCase(AdminRBACUseCase):
    """Use case for creating a permission"""
    
    async def execute(self, request: CreatePermissionRequestDTO) -> PermissionDTO:
        # Check if already exists
        existing = await self.db.execute(
            select(Permission).where(
                and_(
                    Permission.resource == request.resource,
                    Permission.action == request.action
                )
            )
        )
        if existing.scalar_one_or_none():
            raise BusinessRuleViolation(
                f"Permission {request.resource}:{request.action} already exists"
            )
        
        permission = Permission(
            resource=request.resource,
            action=request.action,
            description=request.description
        )
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        
        logger.info(f"Permission created: {permission.permission_string} by {self.current_user.email}")
        
        return PermissionDTO(
            permission_id=permission.permission_id,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
            permission_string=permission.permission_string,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )


class DeletePermissionUseCase(AdminRBACUseCase):
    """Use case for deleting a permission"""
    
    async def execute(self, permission_id: int) -> DeletePermissionResponseDTO:
        permission = await self.db.get(Permission, permission_id)
        if not permission:
            raise ResourceNotFound("Permission not found")
        
        perm_string = permission.permission_string
        await self.db.delete(permission)
        await self.db.commit()
        
        logger.info(f"Permission deleted: {perm_string} by {self.current_user.email}")
        
        return DeletePermissionResponseDTO(
            message=f"Permission {perm_string} deleted successfully",
            permission_string=perm_string
        )


# Role Management Use Cases
class ListRolesUseCase(AdminRBACUseCase):
    """Use case for listing roles"""
    
    async def execute(self, params: Dict[str, Any]) -> RoleListResponseDTO:
        include_permissions = params.get('include_permissions', False)
        include_user_count = params.get('include_user_count', False)
        skip = params.get('skip', 0)
        limit = params.get('limit', 100)
        
        query = select(Role).where(Role.is_active == True)
        
        if include_permissions:
            query = query.options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        
        query = query.offset(skip).limit(limit).order_by(Role.role_name)
        
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        # Build response data
        role_dtos = []
        for role in roles:
            role_dto = RoleDTO(
                role_id=role.role_id,
                role_name=role.role_name,
                description=role.description,
                is_system=role.is_system,
                is_active=role.is_active,
                created_at=role.created_at,
                updated_at=role.updated_at
            )
            
            # Add permissions if requested
            if include_permissions and hasattr(role, 'role_permissions'):
                role_dto.permissions = [
                    PermissionDTO(
                        permission_id=rp.permission.permission_id,
                        resource=rp.permission.resource,
                        action=rp.permission.action,
                        description=rp.permission.description,
                        permission_string=rp.permission.permission_string,
                        created_at=rp.permission.created_at,
                        updated_at=rp.permission.updated_at
                    )
                    for rp in role.role_permissions
                ]
            
            # Add user count if requested
            if include_user_count:
                count_result = await self.db.execute(
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
                role_dto.user_count = count_result.scalar()
            
            role_dtos.append(role_dto)
        
        return RoleListResponseDTO(
            roles=role_dtos,
            total_count=len(role_dtos)
        )


class CreateRoleUseCase(AdminRBACUseCase):
    """Use case for creating a role"""
    
    async def execute(self, request: CreateRoleRequestDTO) -> RoleDTO:
        # Check if already exists
        existing = await self.db.execute(
            select(Role).where(Role.role_name == request.role_name)
        )
        if existing.scalar_one_or_none():
            raise BusinessRuleViolation(f"Role {request.role_name} already exists")
        
        role = Role(
            role_name=request.role_name,
            description=request.description,
            is_system=request.is_system
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        
        logger.info(f"Role created: {role.role_name} by {self.current_user.email}")
        
        return RoleDTO(
            role_id=role.role_id,
            role_name=role.role_name,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at
        )


class UpdateRoleUseCase(AdminRBACUseCase):
    """Use case for updating a role"""
    
    async def execute(self, role_id: int, request: UpdateRoleRequestDTO) -> RoleDTO:
        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFound("Role not found")
        
        # Don't allow modification of system roles (except description)
        if role.is_system and request.role_name and request.role_name != role.role_name:
            raise BusinessRuleViolation("Cannot rename system roles")
        
        # Update fields
        if request.role_name is not None:
            role.role_name = request.role_name
        if request.description is not None:
            role.description = request.description
        if request.is_active is not None:
            role.is_active = request.is_active
        
        role.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(role)
        
        logger.info(f"Role updated: {role.role_name} by {self.current_user.email}")
        
        return RoleDTO(
            role_id=role.role_id,
            role_name=role.role_name,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at
        )


class DeleteRoleUseCase(AdminRBACUseCase):
    """Use case for deleting a role (soft delete)"""
    
    async def execute(self, role_id: int) -> DeleteRoleResponseDTO:
        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFound("Role not found")
        
        if role.is_system:
            raise BusinessRuleViolation("Cannot delete system roles")
        
        role.is_active = False
        role.updated_at = datetime.utcnow()
        await self.db.commit()
        
        logger.info(f"Role deactivated: {role.role_name} by {self.current_user.email}")
        
        return DeleteRoleResponseDTO(
            message=f"Role {role.role_name} deactivated successfully",
            role_name=role.role_name
        )


# Role Permission Management Use Cases
class GetRolePermissionRestrictionsUseCase(AdminRBACUseCase):
    """Use case for getting role permission restrictions"""
    
    async def execute(self, role_id: int) -> RolePermissionRestrictionsDTO:
        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFound("Role not found")
        
        # Get all permissions
        all_permissions_result = await self.db.execute(select(Permission))
        all_permissions = [p.permission_string for p in all_permissions_result.scalars()]
        
        # Get restrictions for this role
        restrictions = get_restricted_permissions_for_role(role.role_name, all_permissions)
        
        return RolePermissionRestrictionsDTO(
            role_name=role.role_name,
            role_description=get_role_description(role.role_name),
            total_permissions=len(all_permissions),
            allowed_count=len(restrictions["allowed"]),
            forbidden_count=len(restrictions["forbidden"]),
            allowed_permissions=restrictions["allowed"],
            forbidden_permissions=restrictions["forbidden"]
        )


class GetRolePermissionsUseCase(AdminRBACUseCase):
    """Use case for getting permissions for a role"""
    
    async def execute(self, role_id: int) -> List[PermissionDTO]:
        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFound("Role not found")
        
        result = await self.db.execute(
            select(Permission).join(RolePermission).where(
                RolePermission.role_id == role_id
            )
        )
        permissions = result.scalars().all()
        
        return [
            PermissionDTO(
                permission_id=p.permission_id,
                resource=p.resource,
                action=p.action,
                description=p.description,
                permission_string=p.permission_string,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in permissions
        ]


class UpdateRolePermissionsUseCase(AdminRBACUseCase):
    """Use case for updating all permissions for a role"""
    
    async def execute(self, role_id: int, request: UpdateRolePermissionsRequestDTO) -> RoleDTO:
        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFound("Role not found")
        
        # Get all permissions to validate against
        all_permissions_result = await self.db.execute(select(Permission))
        all_permissions = [p.permission_string for p in all_permissions_result.scalars()]
        
        # Get the permissions being requested
        requested_permissions_result = await self.db.execute(
            select(Permission).where(Permission.permission_id.in_(request.permission_ids))
        )
        requested_permissions = [p.permission_string for p in requested_permissions_result.scalars()]
        
        # Validate permissions for this role
        validation_result = validate_role_permissions(role.role_name, requested_permissions)
        
        if validation_result["forbidden"]:
            forbidden_perms = ", ".join(validation_result["forbidden"])
            raise BusinessRuleViolation(
                f"The following permissions are not allowed for role '{role.role_name}': {forbidden_perms}"
            )
        
        # Get permission service
        permission_service: PermissionService = self.permission_service
        
        # Remove all existing permissions
        await self.db.execute(
            select(RolePermission).where(RolePermission.role_id == role_id)
        )
        
        # Add new permissions (only the allowed ones)
        for perm_id in request.permission_ids:
            # Double-check each permission is in the allowed list
            perm_result = await self.db.execute(
                select(Permission).where(Permission.permission_id == perm_id)
            )
            perm = perm_result.scalar_one_or_none()
            if perm and perm.permission_string in validation_result["allowed"]:
                await permission_service.grant_permission_to_role(
                    role_id, perm_id, self.current_user.user_id
                )
        
        # Refresh role with permissions
        result = await self.db.execute(
            select(Role).options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            ).where(Role.role_id == role_id)
        )
        role = result.scalar_one()
        
        logger.info(f"Role permissions updated: {role.role_name} by {self.current_user.email}")
        
        # Convert to DTO
        permissions = [
            PermissionDTO(
                permission_id=rp.permission.permission_id,
                resource=rp.permission.resource,
                action=rp.permission.action,
                description=rp.permission.description,
                permission_string=rp.permission.permission_string,
                created_at=rp.permission.created_at,
                updated_at=rp.permission.updated_at
            )
            for rp in role.role_permissions
        ] if hasattr(role, 'role_permissions') else []
        
        return RoleDTO(
            role_id=role.role_id,
            role_name=role.role_name,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=permissions
        )


class GrantPermissionToRoleUseCase(AdminRBACUseCase):
    """Use case for granting a permission to a role"""
    
    async def execute(self, role_id: int, permission_id: int) -> GrantRolePermissionResponseDTO:
        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFound("Role not found")
        
        permission = await self.db.get(Permission, permission_id)
        if not permission:
            raise ResourceNotFound("Permission not found")
        
        # Validate permission for this role
        if not is_permission_allowed_for_role(role.role_name, permission.permission_string):
            raise BusinessRuleViolation(
                f"Permission '{permission.permission_string}' is not allowed for role '{role.role_name}'"
            )
        
        permission_service: PermissionService = self.permission_service
        
        success = await permission_service.grant_permission_to_role(
            role_id, permission_id, self.current_user.user_id
        )
        
        if not success:
            raise BusinessRuleViolation("Failed to grant permission")
        
        return GrantRolePermissionResponseDTO(
            message="Permission granted successfully",
            success=True
        )


class RevokePermissionFromRoleUseCase(AdminRBACUseCase):
    """Use case for revoking a permission from a role"""
    
    async def execute(self, role_id: int, permission_id: int) -> RevokeRolePermissionResponseDTO:
        permission_service: PermissionService = self.permission_service
        
        success = await permission_service.revoke_permission_from_role(
            role_id, permission_id, self.current_user.user_id
        )
        
        if not success:
            raise ResourceNotFound("Permission assignment not found")
        
        return RevokeRolePermissionResponseDTO(
            message="Permission revoked successfully",
            success=True
        )


# User Permission Management Use Cases
class GetUserPermissionsUseCase(AdminRBACUseCase):
    """Use case for getting all permissions for a user"""
    
    async def execute(self, user_id: int) -> UserPermissionsDTO:
        permission_service: PermissionService = self.permission_service
        
        # Get all permissions
        all_permissions = await permission_service.get_user_permissions(user_id)
        
        # Get direct permissions
        direct_result = await self.db.execute(
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
        
        # Get user roles with their permissions
        roles_result = await self.db.execute(
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
        
        # Convert roles to serializable format
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
        
        return UserPermissionsDTO(
            user_id=user_id,
            all_permissions=list(all_permissions),
            direct_permissions=direct_permissions,
            roles=roles_data
        )


class AssignRoleToUserUseCase(AdminRBACUseCase):
    """Use case for assigning a role to a user"""
    
    async def execute(self, user_id: int, request: AssignRoleToUserRequestDTO) -> AssignRoleToUserResponseDTO:
        permission_service: PermissionService = self.permission_service
        
        success = await permission_service.assign_role_to_user(
            user_id,
            request.role_id,
            self.current_user.user_id,
            request.expires_at
        )
        
        if not success:
            raise BusinessRuleViolation("Failed to assign role")
        
        return AssignRoleToUserResponseDTO(
            message="Role assigned successfully",
            success=True
        )


class RemoveRoleFromUserUseCase(AdminRBACUseCase):
    """Use case for removing a role from a user"""
    
    async def execute(self, user_id: int, role_id: int) -> RemoveRoleFromUserResponseDTO:
        result = await self.db.execute(
            select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            )
        )
        user_role = result.scalar_one_or_none()
        
        if not user_role:
            raise ResourceNotFound("User role assignment not found")
        
        await self.db.delete(user_role)
        
        # Add audit log
        audit = PermissionAuditLog(
            action_type='revoke',
            target_type='user',
            target_id=user_id,
            role_id=role_id,
            performed_by=self.current_user.user_id
        )
        self.db.add(audit)
        
        await self.db.commit()
        
        return RemoveRoleFromUserResponseDTO(
            message="Role removed successfully",
            success=True
        )


class GrantPermissionToUserUseCase(AdminRBACUseCase):
    """Use case for granting permission to user"""
    
    async def execute(self, user_id: int, request: GrantPermissionToUserRequestDTO) -> GrantPermissionToUserResponseDTO:
        permission_service: PermissionService = self.permission_service
        
        success = await permission_service.grant_permission_to_user(
            user_id,
            request.permission_id,
            self.current_user.user_id,
            request.expires_at
        )
        
        if not success:
            raise BusinessRuleViolation("Failed to grant permission")
        
        return GrantPermissionToUserResponseDTO(
            message="Permission granted successfully",
            success=True
        )


# Resource Permission Management Use Cases
class GrantResourcePermissionUseCase(AdminRBACUseCase):
    """Use case for granting resource-level permission"""
    
    async def execute(self, request: GrantResourcePermissionRequestDTO) -> GrantResourcePermissionResponseDTO:
        # Validate permission exists
        permission = await self.db.get(Permission, request.permission_id)
        if not permission:
            raise ResourceNotFound("Permission not found")
        
        # Check if already exists
        existing = await self.db.execute(
            select(ResourcePermission).where(
                and_(
                    ResourcePermission.user_id == request.user_id,
                    ResourcePermission.resource_type == request.resource_type,
                    ResourcePermission.resource_id == request.resource_id,
                    ResourcePermission.permission_id == request.permission_id
                )
            )
        )
        
        resource_perm = existing.scalar_one_or_none()
        if resource_perm:
            # Update existing
            resource_perm.granted = True
            resource_perm.granted_by = self.current_user.user_id
            resource_perm.granted_at = datetime.utcnow()
            resource_perm.expires_at = request.expires_at
        else:
            # Create new
            resource_perm = ResourcePermission(
                user_id=request.user_id,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                permission_id=request.permission_id,
                granted=True,
                granted_by=self.current_user.user_id,
                expires_at=request.expires_at
            )
            self.db.add(resource_perm)
        
        await self.db.commit()
        
        logger.info(
            f"Resource permission granted: user={request.user_id}, "
            f"{request.resource_type}:{request.resource_id}, "
            f"permission={permission.permission_string} by {self.current_user.email}"
        )
        
        return GrantResourcePermissionResponseDTO(
            message="Resource permission granted successfully",
            success=True
        )


# Audit Log Use Cases
class GetPermissionAuditLogUseCase(AdminRBACUseCase):
    """Use case for getting permission audit log"""
    
    async def execute(self, params: Dict[str, Any]) -> PermissionAuditLogListResponseDTO:
        target_type = params.get('target_type')
        target_id = params.get('target_id')
        performed_by = params.get('performed_by')
        skip = params.get('skip', 0)
        limit = params.get('limit', 100)
        
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
        
        result = await self.db.execute(query)
        audit_logs = result.scalars().all()
        
        # Convert to DTOs
        audit_log_dtos = []
        for log in audit_logs:
            permission_dto = None
            if log.permission:
                permission_dto = PermissionDTO(
                    permission_id=log.permission.permission_id,
                    resource=log.permission.resource,
                    action=log.permission.action,
                    description=log.permission.description,
                    permission_string=log.permission.permission_string,
                    created_at=log.permission.created_at,
                    updated_at=log.permission.updated_at
                )
            
            role_dto = None
            if log.role:
                role_dto = RoleDTO(
                    role_id=log.role.role_id,
                    role_name=log.role.role_name,
                    description=log.role.description,
                    is_system=log.role.is_system,
                    is_active=log.role.is_active,
                    created_at=log.role.created_at,
                    updated_at=log.role.updated_at
                )
            
            audit_log_dtos.append(PermissionAuditLogDTO(
                audit_id=log.audit_id,
                action_type=log.action_type,
                target_type=log.target_type,
                target_id=log.target_id,
                permission=permission_dto,
                role=role_dto,
                performed_by=log.performed_by,
                performed_at=log.performed_at,
                reason=log.reason
            ))
        
        return PermissionAuditLogListResponseDTO(
            audit_logs=audit_log_dtos,
            total_count=len(audit_log_dtos),
            filters_applied={
                "target_type": target_type,
                "target_id": target_id,
                "performed_by": performed_by
            }
        )
"""
Clean Architecture Users API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.core.auth import get_password_hash
from app.infrastructure.di import get_repository, get_use_case
from app.application.dtos import UserDTO, UserCreateDTO, UserUpdateDTO, UserResponseDTO, UserListResponseDTO

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=UserListResponseDTO)
@require_permission("users", "read")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = None,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all users with pagination and filters"""
    
    # Get repository
    user_repository = get_repository("user_repository")
    
    if not user_repository:
        # Fallback to direct implementation
        from app.models.user import User
        from sqlalchemy import func
        
        # Build query
        query = select(User)
        conditions = []
        
        if active_only:
            conditions.append(User.is_active == True)
        
        if role:
            conditions.append(User.role == role)
        
        # Get total count
        count_query = select(func.count(User.user_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
            query = query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return UserListResponseDTO(
            users=[
                UserDTO(
                    user_id=u.user_id,
                    email=u.email,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    role=u.role,
                    lob_id=u.lob_id,
                    is_active=u.is_active,
                    created_at=u.created_at,
                    updated_at=u.updated_at
                )
                for u in users
            ],
            total=total,
            skip=skip,
            limit=limit
        )
    
    # Use clean architecture implementation
    users = await user_repository.get_all(
        skip=skip,
        limit=limit,
        role=role,
        active_only=active_only,
        db=db
    )
    
    # Get total count
    total = await user_repository.count(
        role=role,
        active_only=active_only,
        db=db
    )
    
    return UserListResponseDTO(
        users=users,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/me", response_model=UserResponseDTO)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    
    return UserResponseDTO(
        user_id=current_user.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/me/permissions")
async def get_current_user_permissions(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's permissions and roles"""
    try:
        # Import User model
        from app.models.user import User
        
        # Get user with roles
        user = await db.get(User, current_user.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get all permissions for the user's role
        all_permissions = []
        roles = []
        
        if user.role:
            # Get role permissions from RBAC system
            from app.models.rbac import Role, RolePermission, Permission
            
            role = await db.execute(
                select(Role).where(Role.role_name == user.role)
            )
            role = role.scalar_one_or_none()
            
            if role:
                roles.append({
                    "role_id": role.role_id,
                    "role_name": role.role_name
                })
                
                # Get permissions for this role
                role_permissions = await db.execute(
                    select(Permission)
                    .join(RolePermission)
                    .where(RolePermission.role_id == role.role_id)
                )
                
                for permission in role_permissions.scalars():
                    all_permissions.append(f"{permission.resource}:{permission.action}")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "roles": roles,
            "all_permissions": all_permissions
        }
    except Exception as e:
        logger.error(f"Error getting user permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report-owners", response_model=List[UserDTO])
@require_permission("users", "read")
async def get_report_owners(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all users who can be report owners (Report Owner and Report Executive roles)"""
    
    from app.models.user import User
    
    # Query for users with report owner roles
    result = await db.execute(
        select(User).where(
            and_(
                User.role.in_(["Report Owner", "Report Executive"]),
                User.is_active == True
            )
        ).order_by(User.first_name, User.last_name)
    )
    users = result.scalars().all()
    
    return [
        UserDTO(
            user_id=u.user_id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role,
            lob_id=u.lob_id,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserDTO)
@require_permission("users", "read")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific user by ID"""
    
    # Get repository
    user_repository = get_repository("user_repository")
    
    if not user_repository:
        # Fallback to direct implementation
        from app.models.user import User
        
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserDTO(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            lob_id=user.lob_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    # Use clean architecture implementation
    user = await user_repository.get_by_id(user_id, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/", response_model=UserDTO)
@require_permission("users", "create")
async def create_user(
    user_data: UserCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new user"""
    
    # Get use case
    create_user_use_case = get_use_case("create_user")
    
    if not create_user_use_case:
        # Fallback to direct implementation
        from app.models.user import User
        
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            lob_id=user_data.lob_id,
            is_active=True,
            created_by=current_user.user_id
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return UserDTO(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            lob_id=user.lob_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    # Use clean architecture implementation
    try:
        user = await create_user_use_case.execute(
            user_data=user_data,
            created_by=current_user.user_id,
            db=db
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserDTO)
@require_permission("users", "update")
async def update_user(
    user_id: int,
    user_data: UserUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing user"""
    
    # Get use case
    update_user_use_case = get_use_case("update_user")
    
    if not update_user_use_case:
        # Fallback to direct implementation
        from app.models.user import User
        from datetime import datetime
        
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.lob_id is not None:
            user.lob_id = user_data.lob_id
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        
        user.updated_at = datetime.utcnow()
        user.updated_by = current_user.user_id
        
        await db.commit()
        await db.refresh(user)
        
        return UserDTO(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            lob_id=user.lob_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    # Use clean architecture implementation
    try:
        user = await update_user_use_case.execute(
            user_id=user_id,
            user_data=user_data,
            updated_by=current_user.user_id,
            db=db
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}")
@require_permission("users", "delete")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a user (soft delete)"""
    
    # Prevent self-deletion
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Get use case
    delete_user_use_case = get_use_case("delete_user")
    
    if not delete_user_use_case:
        # Fallback to direct implementation
        from app.models.user import User
        from datetime import datetime
        
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        user.deleted_by = current_user.user_id
        
        await db.commit()
        
        return {"message": "User deleted successfully"}
    
    # Use clean architecture implementation
    try:
        await delete_user_use_case.execute(
            user_id=user_id,
            deleted_by=current_user.user_id,
            db=db
        )
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/roles/list", response_model=List[str])
async def get_available_roles(
    current_user = Depends(get_current_user)
):
    """Get list of available user roles"""
    
    from app.core.auth import UserRoles
    
    return UserRoles.all_roles()
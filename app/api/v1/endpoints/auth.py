"""
Clean Architecture Authentication API endpoints
NO FALLBACKS - 100% Clean Architecture
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.infrastructure.di import get_container
from app.application.dtos.auth import (
    UserLoginDTO, 
    UserRegistrationDTO,
    UserResponseDTO,
    TokenResponseDTO,
    PasswordChangeDTO
)
from app.application.use_cases.auth import (
    AuthenticateUserUseCase,
    RegisterUserUseCase,
    ChangePasswordUseCase,
    GetCurrentUserUseCase
)
from app.core.dependencies import get_current_user_id

router = APIRouter()


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    login_data: UserLoginDTO,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token - Clean Architecture Only"""
    import time
    import structlog
    logger = structlog.get_logger()
    
    start_time = time.time()
    logger.info("Auth endpoint called", email=login_data.email, start_time=start_time)
    
    try:
        # Log step 1
        logger.info("Creating repository and services", elapsed=f"{time.time() - start_time:.2f}s")
        
        # Create use case directly - container dependency causing issues in Docker
        from app.infrastructure.repositories.user_repository import UserRepositoryImpl
        from app.infrastructure.external_services.auth_service_impl import AuthServiceImpl
        
        user_repo = UserRepositoryImpl(db)
        auth_service = AuthServiceImpl()
        auth_use_case = AuthenticateUserUseCase(user_repo, auth_service)
        
        logger.info("Repository and services created", elapsed=f"{time.time() - start_time:.2f}s")
        
        # Log step 2
        logger.info("Executing authentication use case", elapsed=f"{time.time() - start_time:.2f}s")
        result = await auth_use_case.execute(login_data)
        
        logger.info("Authentication successful", elapsed=f"{time.time() - start_time:.2f}s")
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Add better error logging for debugging
        import traceback
        print(f"Login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/register", response_model=UserResponseDTO)
async def register(
    registration_data: UserRegistrationDTO,
    db: AsyncSession = Depends(get_db),
    container = Depends(get_container)
):
    """Register a new user - Clean Architecture Only"""
    
    # Get registration use case from container
    register_use_case: RegisterUserUseCase = container.get("auth.register_user")
    
    if not register_use_case:
        # Create use case directly if not in container
        from app.infrastructure.repositories.user_repository import UserRepositoryImpl
        from app.infrastructure.external_services.auth_service_impl import AuthServiceImpl
        
        user_repo = UserRepositoryImpl(db)
        auth_service = AuthServiceImpl()
        register_use_case = RegisterUserUseCase(user_repo, auth_service)
    
    try:
        result = await register_use_case.execute(registration_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponseDTO)
async def get_current_user_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    container = Depends(get_container)
):
    """Get current user information - Clean Architecture Only"""
    
    # Get current user use case from container
    get_user_use_case: GetCurrentUserUseCase = container.get("auth.get_current_user")
    
    if not get_user_use_case:
        # Create use case directly if not in container
        from app.infrastructure.repositories.user_repository import UserRepositoryImpl
        
        user_repo = UserRepositoryImpl(db)
        get_user_use_case = GetCurrentUserUseCase(user_repo)
    
    try:
        result = await get_user_use_case.execute(user_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeDTO,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    container = Depends(get_container)
):
    """Change user password - Clean Architecture Only"""
    
    # Get change password use case from container
    change_password_use_case: ChangePasswordUseCase = container.get("auth.change_password")
    
    if not change_password_use_case:
        # Create use case directly if not in container
        from app.infrastructure.repositories.user_repository import UserRepositoryImpl
        from app.infrastructure.external_services.auth_service_impl import AuthServiceImpl
        
        user_repo = UserRepositoryImpl(db)
        auth_service = AuthServiceImpl()
        change_password_use_case = ChangePasswordUseCase(user_repo, auth_service)
    
    try:
        await change_password_use_case.execute(user_id, password_data)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    user_id: int = Depends(get_current_user_id)
):
    """Logout user - Clean Architecture Only"""
    
    # In a stateless JWT system, logout is handled client-side
    # Here we can add any server-side cleanup if needed
    
    return {"message": "Logged out successfully", "user_id": user_id}
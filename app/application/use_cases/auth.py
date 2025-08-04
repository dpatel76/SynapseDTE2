"""
Authentication Use Cases - Clean Architecture
"""

from typing import Optional
from datetime import timedelta

from app.application.interfaces.repositories import UserRepository
from app.application.interfaces.external_services import IAuthService
from app.application.dtos.auth import (
    UserLoginDTO,
    UserRegistrationDTO,
    UserResponseDTO,
    TokenResponseDTO,
    PasswordChangeDTO
)
from app.domain.entities.user import UserEntity
from app.domain.value_objects import Email, Password
from app.core.config import settings


class AuthenticateUserUseCase:
    """Use case for user authentication"""
    
    def __init__(self, user_repository: UserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self, login_data: UserLoginDTO) -> TokenResponseDTO:
        """Execute user authentication"""
        import time
        import structlog
        logger = structlog.get_logger()
        
        start = time.time()
        logger.info("AuthenticateUserUseCase.execute started", email=login_data.email)
        
        # Find user by email
        logger.info("Finding user by email", elapsed=f"{time.time() - start:.2f}s")
        user = await self.user_repository.find_by_email(login_data.email)
        logger.info(f"User found: {user is not None}", elapsed=f"{time.time() - start:.2f}s")
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        logger.info("Verifying password", elapsed=f"{time.time() - start:.2f}s")
        password_valid = self.auth_service.verify_password(login_data.password, user.hashed_password)
        logger.info(f"Password valid: {password_valid}", elapsed=f"{time.time() - start:.2f}s")
        
        if not password_valid:
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = self.auth_service.create_access_token(
            data={"sub": str(user.user_id)},
            expires_delta=access_token_expires
        )
        
        # Create response
        return TokenResponseDTO(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponseDTO(
                user_id=user.user_id,
                email=user.email.value,  # Extract string value from Email value object
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )


class RegisterUserUseCase:
    """Use case for user registration"""
    
    def __init__(self, user_repository: UserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self, registration_data: UserRegistrationDTO) -> UserResponseDTO:
        """Execute user registration"""
        
        # Check if user already exists
        existing_user = await self.user_repository.find_by_email(registration_data.email)
        
        if existing_user:
            raise ValueError("Email already registered")
        
        # Create user entity
        user_entity = UserEntity(
            user_id=None,  # Will be assigned by database
            email=Email(registration_data.email),
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            role=registration_data.role or "Tester",
            is_active=True,
            hashed_password=self.auth_service.hash_password(registration_data.password)
        )
        
        # Save user
        saved_user = await self.user_repository.create(user_entity)
        
        # Return response
        return UserResponseDTO(
            user_id=saved_user.user_id,
            email=saved_user.email.value,
            first_name=saved_user.first_name,
            last_name=saved_user.last_name,
            role=saved_user.role,
            is_active=saved_user.is_active,
            created_at=saved_user.created_at
        )


class GetCurrentUserUseCase:
    """Use case for getting current user"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: int) -> UserResponseDTO:
        """Execute get current user"""
        
        # Find user by id
        user = await self.user_repository.find_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Return response
        return UserResponseDTO(
            user_id=user.user_id,
            email=user.email.value,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )


class ChangePasswordUseCase:
    """Use case for changing user password"""
    
    def __init__(self, user_repository: UserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self, user_id: int, password_data: PasswordChangeDTO) -> None:
        """Execute password change"""
        
        # Find user by id
        user = await self.user_repository.find_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not self.auth_service.verify_password(password_data.old_password, user.hashed_password):
            raise ValueError("Incorrect current password")
        
        # Update password
        user.hashed_password = self.auth_service.hash_password(password_data.new_password)
        
        # Save updated user
        await self.user_repository.update(user)
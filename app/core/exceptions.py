"""
Custom exception classes for the application
"""


class SynapseDTException(Exception):
    """Base exception for SynapseDT application"""
    pass


class ValidationException(SynapseDTException):
    """Raised when validation fails"""
    pass


class AuthenticationException(SynapseDTException):
    """Raised when authentication fails"""
    pass


class AuthorizationException(SynapseDTException):
    """Raised when authorization fails"""
    pass


class NotFoundException(SynapseDTException):
    """Raised when a resource is not found"""
    pass


class BusinessLogicException(SynapseDTException):
    """Raised when business logic validation fails"""
    pass


class ConflictError(SynapseDTException):
    """Raised when there's a conflict in the request"""
    pass


# Aliases for backward compatibility
class ValidationError(ValidationException):
    """Alias for ValidationException for backward compatibility"""
    pass


class NotFoundError(NotFoundException):
    """Alias for NotFoundException for backward compatibility"""
    pass


class ResourceNotFoundError(NotFoundException):
    """Alias for NotFoundException for resource-specific errors"""
    pass


class PermissionError(AuthorizationException):
    """Alias for AuthorizationException for permission errors"""
    pass


class BusinessLogicError(BusinessLogicException):
    """Alias for BusinessLogicException for backward compatibility"""
    pass


class PermissionError(AuthorizationException):
    """Alias for AuthorizationException for backward compatibility"""
    pass


class LLMException(SynapseDTException):
    """Raised when LLM operations fail"""
    pass


class FileProcessingException(SynapseDTException):
    """Raised when file processing fails"""
    pass


class DatabaseException(SynapseDTException):
    """Raised when database operations fail"""
    pass


class EmailException(SynapseDTException):
    """Raised when email operations fail"""
    pass


class SLAException(SynapseDTException):
    """Raised when SLA violations occur"""
    pass


class BusinessRuleViolation(SynapseDTException):
    """Raised when business rules are violated"""
    pass


class ResourceNotFound(NotFoundException):
    """Raised when a requested resource is not found"""
    pass
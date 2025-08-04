"""External service interfaces for the application layer"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class ILLMService(ABC):
    """Interface for LLM (Large Language Model) service"""
    
    @abstractmethod
    async def generate_test_attributes(self, report_id: int, regulatory_context: str, 
                                     report_type: str) -> List[Dict[str, Any]]:
        """Generate test attributes using LLM"""
        pass
    
    @abstractmethod
    async def generate_samples(self, report_id: int, sample_count: int, 
                             criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate sample data using LLM"""
        pass
    
    @abstractmethod
    async def analyze_document(self, document_content: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze document content using LLM"""
        pass
    
    @abstractmethod
    async def generate_test_cases(self, attribute_id: int, attribute_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases for an attribute"""
        pass


class IEmailService(ABC):
    """Interface for email service"""
    
    @abstractmethod
    async def send_email(self, to: List[str], subject: str, body: str, 
                        cc: Optional[List[str]] = None, attachments: Optional[List[str]] = None) -> bool:
        """Send an email"""
        pass
    
    @abstractmethod
    async def send_notification(self, user_id: int, notification_type: str, 
                               data: Dict[str, Any]) -> bool:
        """Send a notification to a user"""
        pass


class IFileStorageService(ABC):
    """Interface for file storage service"""
    
    @abstractmethod
    async def upload_file(self, file_data: bytes, file_name: str, 
                         folder: str) -> str:
        """Upload a file and return its URL/path"""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download a file"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str, expiry_hours: int = 24) -> str:
        """Get a temporary URL for file access"""
        pass


class IAuthService(ABC):
    """Interface for authentication service"""
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        pass
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        pass
    
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token"""
        pass
    
    @abstractmethod
    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode an access token"""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[int]:
        """Validate a token and return user_id if valid"""
        pass


class ITemporalService(ABC):
    """Interface for Temporal workflow service"""
    
    @abstractmethod
    async def start_workflow(self, workflow_name: str, workflow_id: str, 
                           params: Dict[str, Any]) -> str:
        """Start a Temporal workflow"""
        pass
    
    @abstractmethod
    async def signal_workflow(self, workflow_id: str, signal_name: str, 
                            data: Dict[str, Any]) -> bool:
        """Send a signal to a running workflow"""
        pass
    
    @abstractmethod
    async def query_workflow(self, workflow_id: str, query_name: str) -> Any:
        """Query a workflow state"""
        pass
    
    @abstractmethod
    async def terminate_workflow(self, workflow_id: str, reason: str) -> bool:
        """Terminate a running workflow"""
        pass
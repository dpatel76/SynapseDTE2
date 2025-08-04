"""Service interfaces (ports) for the application layer"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class NotificationService(ABC):
    """Interface for notification service"""
    
    @abstractmethod
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send a notification to a user"""
        pass
    
    @abstractmethod
    async def send_bulk_notifications(
        self,
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: str,
        priority: str = "medium"
    ) -> None:
        """Send notifications to multiple users"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: int, user_id: int) -> None:
        """Mark a notification as read"""
        pass
    
    @abstractmethod
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        pass


class EmailService(ABC):
    """Interface for email service"""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Send an email"""
        pass
    
    @abstractmethod
    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Send an email using a template"""
        pass
    
    @abstractmethod
    async def send_bulk_emails(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> None:
        """Send emails to multiple recipients"""
        pass


class LLMService(ABC):
    """Interface for LLM service"""
    
    @abstractmethod
    async def generate_test_attributes(
        self,
        regulatory_context: str,
        report_type: str,
        sample_size: int,
        existing_attributes: Optional[List[Dict[str, Any]]] = None,
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate test attributes using LLM"""
        pass
    
    @abstractmethod
    async def analyze_document(
        self,
        document_content: str,
        attribute_name: str,
        expected_value: Any,
        analysis_context: Dict[str, Any],
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document for specific attribute"""
        pass
    
    @abstractmethod
    async def extract_data_from_document(
        self,
        document_content: str,
        extraction_schema: Dict[str, Any],
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured data from document"""
        pass
    
    @abstractmethod
    async def generate_report_summary(
        self,
        test_results: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
        cycle_context: Dict[str, Any],
        preferred_provider: Optional[str] = None
    ) -> str:
        """Generate a summary report from test results"""
        pass
    
    @abstractmethod
    async def check_provider_health(self, provider: str) -> bool:
        """Check if a specific provider is healthy"""
        pass


class AuditService(ABC):
    """Interface for audit service"""
    
    @abstractmethod
    async def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log an audit action"""
        pass
    
    @abstractmethod
    async def log_data_change(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        operation: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a data change"""
        pass
    
    @abstractmethod
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log a security event"""
        pass
    
    @abstractmethod
    async def get_audit_trail(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        pass


class SLAService(ABC):
    """Interface for SLA tracking service"""
    
    @abstractmethod
    async def check_sla_compliance(
        self,
        cycle_id: int,
        report_id: int,
        phase: str
    ) -> Dict[str, Any]:
        """Check SLA compliance for a phase"""
        pass
    
    @abstractmethod
    async def trigger_escalation(
        self,
        cycle_id: int,
        report_id: int,
        phase: str,
        escalation_level: int
    ) -> None:
        """Trigger SLA escalation"""
        pass
    
    @abstractmethod
    async def get_sla_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get SLA performance metrics"""
        pass


class DocumentStorageService(ABC):
    """Interface for document storage service"""
    
    @abstractmethod
    async def store_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a document and return its ID"""
        pass
    
    @abstractmethod
    async def retrieve_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve a document by ID"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """Delete a document"""
        pass
    
    @abstractmethod
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get document metadata without retrieving content"""
        pass


class UnifiedStatusService(ABC):
    """Interface for unified status service"""
    
    @abstractmethod
    async def get_unified_status(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get unified status for a cycle and report"""
        pass
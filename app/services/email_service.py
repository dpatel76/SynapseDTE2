"""
Comprehensive Email Service
Handles SMTP configuration, template management, and escalation emails
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
from jinja2 import Template
import json
import logging
from pathlib import Path

from app.core.config import settings
from app.core.security import SecurityAudit

logger = logging.getLogger(__name__)


class SMTPConfiguration:
    """SMTP configuration management"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        use_ssl: bool = False
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            server.login(self.username, self.password)
            server.quit()
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False


class EmailTemplate:
    """Email template with dynamic content"""
    
    def __init__(self, subject_template: str, body_template: str, template_type: str = "text"):
        self.subject_template = Template(subject_template)
        self.body_template = Template(body_template)
        self.template_type = template_type  # text or html
    
    def render(self, **kwargs) -> Dict[str, str]:
        """Render template with provided data"""
        try:
            subject = self.subject_template.render(**kwargs)
            body = self.body_template.render(**kwargs)
            
            return {
                "subject": subject,
                "body": body,
                "type": self.template_type
            }
            
        except Exception as e:
            logger.error(f"Email template rendering failed: {str(e)}")
            raise


class EmailService:
    """Comprehensive email service"""
    
    def __init__(self, smtp_config: Optional[SMTPConfiguration] = None):
        self.smtp_config = smtp_config or self._get_default_smtp_config()
        self.templates: Dict[str, EmailTemplate] = {}
        self._load_email_templates()
    
    def _get_default_smtp_config(self) -> SMTPConfiguration:
        """Get default SMTP configuration from settings"""
        return SMTPConfiguration(
            smtp_server=getattr(settings, 'SMTP_SERVER', 'localhost'),
            smtp_port=getattr(settings, 'SMTP_PORT', 587),
            username=getattr(settings, 'SMTP_USERNAME', ''),
            password=getattr(settings, 'SMTP_PASSWORD', ''),
            use_tls=getattr(settings, 'SMTP_USE_TLS', True),
            use_ssl=getattr(settings, 'SMTP_USE_SSL', False)
        )
    
    def _load_email_templates(self):
        """Load email templates from configuration"""
        
        # SLA Warning Templates
        self.templates["sla_warning"] = EmailTemplate(
            subject_template="🟡 SLA Warning: {{report_name}} - {{sla_type}} (Due in {{hours_remaining}} hours)",
            body_template="""
            Dear {{recipient_name}},
            
            This is a warning notification that an SLA deadline is approaching:
            
            📊 Report: {{report_name}}
            🏢 LOB: {{lob_name}}
            📋 SLA Type: {{sla_type}}
            ⏰ Due Date: {{due_date}}
            ⚠️ Hours Remaining: {{hours_remaining}}
            
            Please ensure timely completion to avoid SLA violation.
            
            Testing Cycle: {{cycle_name}}
            Current Phase: {{current_phase}}
            
            {% if action_items %}
            Action Items:
            {% for item in action_items %}
            • {{item}}
            {% endfor %}
            {% endif %}
            
            You can access the system here: {{system_url}}
            
            Best regards,
            SynapseDT Data Testing Platform
            """,
            template_type="text"
        )
        
        # SLA Violation Templates
        self.templates["sla_violation"] = EmailTemplate(
            subject_template="🔴 SLA VIOLATION: {{report_name}} - {{sla_type}} ({{violation_hours}} hours overdue)",
            body_template="""
            URGENT: SLA VIOLATION DETECTED
            
            📊 Report: {{report_name}}
            🏢 LOB: {{lob_name}}
            📋 SLA Type: {{sla_type}}
            ⏰ Was Due: {{due_date}}
            🚨 Violation Hours: {{violation_hours}}
            
            This SLA has been violated and requires immediate attention.
            
            Testing Cycle: {{cycle_name}}
            Current Phase: {{current_phase}}
            Assigned To: {{assigned_user}}
            
            {% if escalation_level %}
            Escalation Level: {{escalation_level}}
            Previous Escalations: {{escalation_count}}
            {% endif %}
            
            Immediate Actions Required:
            {% for action in required_actions %}
            • {{action}}
            {% endfor %}
            
            Access the system: {{system_url}}
            
            This is an automated escalation from SynapseDT Data Testing Platform.
            """,
            template_type="text"
        )
        
        # Data Provider Request Template
        self.templates["data_owner_request"] = EmailTemplate(
            subject_template="📋 Data Provider Request: {{report_name}} - {{attribute_count}} attributes",
            body_template="""
            Dear {{data_owner_name}},
            
            You have been assigned as the Data Provider for the following testing request:
            
            📊 Report: {{report_name}}
            🏢 LOB: {{lob_name}}
            📅 Testing Cycle: {{cycle_name}}
            📋 Attributes Count: {{attribute_count}}
            ⏰ Response Due: {{due_date}}
            
            Required Information:
            {% for attribute in attributes %}
            {{loop.index}}. {{attribute.name}}
               - Description: {{attribute.description}}
               - Data Type: {{attribute.data_type}}
               {% if attribute.source_info_needed %}
               - Source Information Required
               {% endif %}
            {% endfor %}
            
            Please provide:
            ✓ Data source confirmation
            ✓ Table and column details
            ✓ Any additional context
            
            Access your assignments: {{system_url}}/data-owner
            
            For questions, contact: {{contact_email}}
            
            Thank you,
            SynapseDT Data Testing Platform
            """,
            template_type="text"
        )
        
        # Testing Complete Notification
        self.templates["testing_complete"] = EmailTemplate(
            subject_template="✅ Testing Completed: {{report_name}} - {{phase_name}}",
            body_template="""
            Testing phase has been completed successfully.
            
            📊 Report: {{report_name}}
            🏢 LOB: {{lob_name}}
            📋 Phase: {{phase_name}}
            👤 Completed By: {{completed_by}}
            📅 Completed Date: {{completion_date}}
            
            {% if observations_count > 0 %}
            🔍 Observations Found: {{observations_count}}
            {% for obs in observations %}
            • {{obs.title}} ({{obs.severity}})
            {% endfor %}
            {% else %}
            ✅ No observations found - Clean testing results
            {% endif %}
            
            {% if next_phase %}
            Next Phase: {{next_phase}}
            Assigned To: {{next_assignee}}
            {% endif %}
            
            View results: {{system_url}}/reports/{{report_id}}
            
            SynapseDT Data Testing Platform
            """,
            template_type="text"
        )
        
        logger.info("Email templates loaded successfully")
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        email_type: str = "text"
    ) -> bool:
        """Send email with comprehensive error handling"""
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config.username
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject
            
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            
            # Add body
            if email_type == "html":
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Combine all recipients
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # Send email
            self._send_smtp_email(msg, all_recipients)
            
            # Log success
            SecurityAudit.log_security_event(
                "email_sent",
                None,
                {
                    "to_count": len(to_emails),
                    "cc_count": len(cc_emails) if cc_emails else 0,
                    "subject": subject[:100],  # Truncate for logging
                    "severity": "INFO"
                }
            )
            
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            SecurityAudit.log_security_event(
                "email_failed",
                None,
                {
                    "to_count": len(to_emails),
                    "error": str(e),
                    "severity": "ERROR"
                }
            )
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP"""
        
        if self.smtp_config.use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(
                self.smtp_config.smtp_server, 
                self.smtp_config.smtp_port, 
                context=context
            )
        else:
            server = smtplib.SMTP(self.smtp_config.smtp_server, self.smtp_config.smtp_port)
            if self.smtp_config.use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
        
        server.login(self.smtp_config.username, self.smtp_config.password)
        server.send_message(msg, to_addrs=recipients)
        server.quit()
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            with open(attachment["path"], "rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment.get('filename', 'attachment')}"
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('path', 'unknown')}: {str(e)}")
    
    def send_template_email(
        self,
        template_name: str,
        to_emails: List[str],
        template_data: Dict[str, Any],
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> bool:
        """Send email using template"""
        
        try:
            if template_name not in self.templates:
                logger.error(f"Email template not found: {template_name}")
                return False
            
            template = self.templates[template_name]
            rendered = template.render(**template_data)
            
            return self.send_email(
                to_emails=to_emails,
                subject=rendered["subject"],
                body=rendered["body"],
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                email_type=rendered["type"]
            )
            
        except Exception as e:
            logger.error(f"Failed to send template email {template_name}: {str(e)}")
            return False
    
    def send_sla_warning(
        self,
        report_name: str,
        sla_type: str,
        due_date: datetime,
        hours_remaining: int,
        to_emails: List[str],
        **kwargs
    ) -> bool:
        """Send SLA warning email"""
        
        template_data = {
            "report_name": report_name,
            "sla_type": sla_type,
            "due_date": due_date.strftime("%Y-%m-%d %H:%M"),
            "hours_remaining": hours_remaining,
            "system_url": getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            **kwargs
        }
        
        return self.send_template_email(
            template_name="sla_warning",
            to_emails=to_emails,
            template_data=template_data
        )
    
    def send_sla_violation(
        self,
        report_name: str,
        sla_type: str,
        due_date: datetime,
        violation_hours: int,
        to_emails: List[str],
        **kwargs
    ) -> bool:
        """Send SLA violation email"""
        
        template_data = {
            "report_name": report_name,
            "sla_type": sla_type,
            "due_date": due_date.strftime("%Y-%m-%d %H:%M"),
            "violation_hours": violation_hours,
            "system_url": getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            **kwargs
        }
        
        return self.send_template_email(
            template_name="sla_violation",
            to_emails=to_emails,
            template_data=template_data
        )
    
    def send_data_owner_request(
        self,
        data_owner_email: str,
        report_name: str,
        attributes: List[Dict],
        due_date: datetime,
        **kwargs
    ) -> bool:
        """Send data provider request email"""
        
        template_data = {
            "report_name": report_name,
            "attributes": attributes,
            "attribute_count": len(attributes),
            "due_date": due_date.strftime("%Y-%m-%d %H:%M"),
            "system_url": getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            "contact_email": getattr(settings, 'SUPPORT_EMAIL', 'support@synapsedt.com'),
            **kwargs
        }
        
        return self.send_template_email(
            template_name="data_owner_request",
            to_emails=[data_owner_email],
            template_data=template_data
        )
    
    def update_smtp_config(self, new_config: SMTPConfiguration) -> bool:
        """Update SMTP configuration with connection test"""
        
        if new_config.test_connection():
            self.smtp_config = new_config
            logger.info("SMTP configuration updated successfully")
            return True
        else:
            logger.error("SMTP configuration update failed - connection test failed")
            return False


# Global email service instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """Get the global email service instance"""
    return email_service


# Convenience functions for common email operations
def send_sla_warning_email(report_name: str, sla_type: str, due_date: datetime, 
                          hours_remaining: int, to_emails: List[str], **kwargs) -> bool:
    """Send SLA warning email"""
    return email_service.send_sla_warning(
        report_name, sla_type, due_date, hours_remaining, to_emails, **kwargs
    )


def send_sla_violation_email(report_name: str, sla_type: str, due_date: datetime,
                           violation_hours: int, to_emails: List[str], **kwargs) -> bool:
    """Send SLA violation email"""
    return email_service.send_sla_violation(
        report_name, sla_type, due_date, violation_hours, to_emails, **kwargs
    ) 
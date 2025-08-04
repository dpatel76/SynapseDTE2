"""Implementation of EmailService"""
from typing import List, Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path
import jinja2

from app.application.interfaces.services import EmailService
from app.core.config import settings


class EmailServiceImpl(EmailService):
    """Implementation of email service using SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.FROM_EMAIL or self.smtp_username
        
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent.parent.parent / "templates" / "emails"
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir))
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Send an email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._attach_file(msg, attachment)
            
            # Send email
            await self._send_message(msg, to_email)
            
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Failed to send email to {to_email}: {str(e)}")
            # In production, this would be logged properly
    
    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Send an email using a template"""
        try:
            # Load templates
            text_template = self.template_env.get_template(f"{template_name}.txt")
            html_template = None
            try:
                html_template = self.template_env.get_template(f"{template_name}.html")
            except jinja2.TemplateNotFound:
                pass  # HTML template is optional
            
            # Render templates
            text_body = text_template.render(**context)
            html_body = html_template.render(**context) if html_template else None
            
            # Extract subject from first line of text template
            lines = text_body.split('\n')
            subject = lines[0].replace('Subject:', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            # Send email
            await self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                html_body=html_body,
                attachments=attachments
            )
            
        except jinja2.TemplateNotFound:
            # Fallback to generic email
            await self.send_email(
                to_email=to_email,
                subject=f"Notification: {template_name}",
                body=f"Template '{template_name}' not found. Context: {context}"
            )
        except Exception as e:
            print(f"Failed to send template email to {to_email}: {str(e)}")
    
    async def send_bulk_emails(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> None:
        """Send emails to multiple recipients"""
        # In production, this would use a bulk email service
        # For now, send individually
        for recipient in recipients:
            await self.send_email(
                to_email=recipient,
                subject=subject,
                body=body,
                html_body=html_body
            )
    
    async def _send_message(self, msg: MIMEMultipart, to_email: str) -> None:
        """Send the email message via SMTP"""
        try:
            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            raise Exception(f"SMTP error: {str(e)}")
    
    def _attach_file(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """Attach a file to the email"""
        try:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment['content'])
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={attachment["filename"]}'
            )
            msg.attach(part)
        except Exception as e:
            print(f"Failed to attach file: {str(e)}")
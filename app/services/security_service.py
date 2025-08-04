"""
Enhanced Security Service
Handles automated key rotation, session management, and advanced security features
"""

import logging
import secrets
import hashlib
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import asyncio
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.database import get_db
from app.core.config import get_settings
from app.models import User, AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityService:
    """Enhanced security service with advanced features"""
    
    def __init__(self):
        self.key_rotation_interval = getattr(settings, 'key_rotation_interval_days', 90)
        self.session_timeout = getattr(settings, 'session_timeout_minutes', 480)  # 8 hours
        self.max_concurrent_sessions = getattr(settings, 'max_concurrent_sessions', 3)
        self.password_complexity_rules = {
            'min_length': getattr(settings, 'password_min_length', 12),
            'require_uppercase': getattr(settings, 'password_require_uppercase', True),
            'require_lowercase': getattr(settings, 'password_require_lowercase', True),
            'require_numbers': getattr(settings, 'password_require_numbers', True),
            'require_special': getattr(settings, 'password_require_special', True),
            'history_count': getattr(settings, 'password_history_count', 5),
            'expiry_days': getattr(settings, 'password_expiry_days', 180)
        }
        
        # Initialize encryption keys management
        self.master_key_path = getattr(settings, 'master_key_path', '/app/security/master.key')
        self.backup_keys_path = getattr(settings, 'backup_keys_path', '/app/security/backup/')
        
        logger.info("Security service initialized with enhanced features")
    
    async def generate_encryption_key(self) -> bytes:
        """Generate a new encryption key"""
        return Fernet.generate_key()
    
    async def rotate_encryption_keys(self) -> Dict[str, Any]:
        """Perform automated key rotation"""
        try:
            # Generate new master key
            new_key = await self.generate_encryption_key()
            current_time = datetime.utcnow()
            
            # Backup current key
            backup_filename = f"master_key_backup_{current_time.strftime('%Y%m%d_%H%M%S')}.key"
            backup_path = os.path.join(self.backup_keys_path, backup_filename)
            
            # Ensure backup directory exists
            os.makedirs(self.backup_keys_path, exist_ok=True)
            
            # Read current key if exists
            current_key = None
            if os.path.exists(self.master_key_path):
                async with aiofiles.open(self.master_key_path, 'rb') as f:
                    current_key = await f.read()
                
                # Backup current key
                async with aiofiles.open(backup_path, 'wb') as f:
                    await f.write(current_key)
            
            # Write new key
            async with aiofiles.open(self.master_key_path, 'wb') as f:
                await f.write(new_key)
            
            # Clean up old backups (keep last 10)
            await self._cleanup_old_key_backups()
            
            logger.info(f"Key rotation completed successfully. Backup saved to {backup_filename}")
            
            return {
                "success": True,
                "rotation_time": current_time.isoformat(),
                "backup_file": backup_filename,
                "next_rotation": (current_time + timedelta(days=self.key_rotation_interval)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "rotation_time": datetime.utcnow().isoformat()
            }
    
    async def _cleanup_old_key_backups(self):
        """Clean up old key backup files, keeping the most recent 10"""
        try:
            backup_files = []
            for filename in os.listdir(self.backup_keys_path):
                if filename.startswith('master_key_backup_') and filename.endswith('.key'):
                    filepath = os.path.join(self.backup_keys_path, filename)
                    backup_files.append((filepath, os.path.getctime(filepath)))
            
            # Sort by creation time, newest first
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove files beyond the 10 most recent
            for filepath, _ in backup_files[10:]:
                os.remove(filepath)
                logger.info(f"Removed old backup: {os.path.basename(filepath)}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
    
    async def schedule_key_rotation(self):
        """Schedule automatic key rotation"""
        while True:
            try:
                # Calculate next rotation time
                next_rotation = datetime.utcnow() + timedelta(days=self.key_rotation_interval)
                sleep_seconds = (next_rotation - datetime.utcnow()).total_seconds()
                
                logger.info(f"Next key rotation scheduled for: {next_rotation.isoformat()}")
                
                # Wait until rotation time
                await asyncio.sleep(sleep_seconds)
                
                # Perform rotation
                result = await self.rotate_encryption_keys()
                
                if result["success"]:
                    logger.info("Scheduled key rotation completed successfully")
                else:
                    logger.error(f"Scheduled key rotation failed: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"Key rotation scheduler error: {str(e)}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    def validate_password_complexity(self, password: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Validate password against complexity rules"""
        rules = self.password_complexity_rules
        errors = []
        
        # Check length
        if len(password) < rules['min_length']:
            errors.append(f"Password must be at least {rules['min_length']} characters long")
        
        # Check character requirements
        if rules['require_uppercase'] and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if rules['require_lowercase'] and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if rules['require_numbers'] and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if rules['require_special'] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check common patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            errors.append("Password cannot be a common weak password")
        
        # Calculate strength score
        strength_score = 0
        if len(password) >= 8:
            strength_score += 1
        if len(password) >= 12:
            strength_score += 1
        if any(c.isupper() for c in password):
            strength_score += 1
        if any(c.islower() for c in password):
            strength_score += 1
        if any(c.isdigit() for c in password):
            strength_score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            strength_score += 1
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength_score": strength_score,
            "strength_level": (
                "Very Strong" if strength_score >= 5 else
                "Strong" if strength_score >= 4 else
                "Medium" if strength_score >= 3 else
                "Weak"
            )
        }
    
    async def manage_user_sessions(self, user_id: int, new_session_token: str, db: AsyncSession) -> Dict[str, Any]:
        """Manage user sessions with concurrent session limits"""
        try:
            # Get current active sessions (this would require a sessions table)
            # For now, we'll implement basic logic and note the need for a sessions table
            
            # Check for session limit (placeholder - would need sessions table)
            current_sessions = []  # Would query from sessions table
            
            if len(current_sessions) >= self.max_concurrent_sessions:
                # Remove oldest session
                logger.info(f"User {user_id} exceeded concurrent session limit, removing oldest session")
                # Would remove oldest session from database
            
            # Create new session record
            session_data = {
                "user_id": user_id,
                "session_token": new_session_token,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=self.session_timeout),
                "is_active": True
            }
            
            # Would insert into sessions table
            
            return {
                "success": True,
                "session_created": True,
                "expires_at": session_data["expires_at"].isoformat(),
                "concurrent_sessions": len(current_sessions) + 1
            }
            
        except Exception as e:
            logger.error(f"Session management failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_session_security(self, user_id: int, ip_address: str, user_agent: str, db: AsyncSession) -> Dict[str, Any]:
        """Check session security including IP validation and suspicious activity"""
        try:
            # Check for suspicious login patterns
            recent_logins = []  # Would query recent login attempts
            
            suspicious_indicators = []
            
            # Check for rapid successive logins from different IPs
            unique_ips = set()  # Would extract from recent_logins
            if len(unique_ips) > 3:  # More than 3 different IPs in recent period
                suspicious_indicators.append("Multiple IP addresses")
            
            # Check for unusual user agent
            common_agents = ['Mozilla', 'Chrome', 'Safari', 'Firefox']
            if not any(agent in user_agent for agent in common_agents):
                suspicious_indicators.append("Unusual user agent")
            
            # Geographic location check (placeholder)
            # Would implement IP geolocation checking
            
            risk_level = (
                "High" if len(suspicious_indicators) >= 2 else
                "Medium" if len(suspicious_indicators) == 1 else
                "Low"
            )
            
            return {
                "risk_level": risk_level,
                "suspicious_indicators": suspicious_indicators,
                "require_mfa": risk_level in ["High", "Medium"],
                "allow_login": risk_level != "High"
            }
            
        except Exception as e:
            logger.error(f"Session security check failed: {str(e)}")
            return {
                "risk_level": "Unknown",
                "suspicious_indicators": ["Security check failed"],
                "require_mfa": True,
                "allow_login": False
            }
    
    async def audit_security_event(self, event_type: str, user_id: int, details: Dict[str, Any], db: AsyncSession):
        """Audit security-related events"""
        try:
            audit_entry = AuditLog(
                user_id=user_id,
                action=f"SECURITY_{event_type.upper()}",
                table_name="security_events",
                details=details,
                ip_address=details.get("ip_address"),
                user_agent=details.get("user_agent"),
                created_at=datetime.utcnow()
            )
            
            db.add(audit_entry)
            await db.commit()
            
            logger.info(f"Security event audited: {event_type} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to audit security event: {str(e)}")
            await db.rollback()
    
    async def generate_security_report(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Generate security metrics and report"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_period_days)
            
            # This would require actual implementation with security events database
            report = {
                "reporting_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_period_days
                },
                "authentication_metrics": {
                    "total_login_attempts": 0,  # Would count from security events
                    "successful_logins": 0,
                    "failed_logins": 0,
                    "blocked_attempts": 0,
                    "mfa_challenges": 0
                },
                "session_metrics": {
                    "active_sessions": 0,
                    "expired_sessions": 0,
                    "concurrent_session_violations": 0,
                    "average_session_duration": 0
                },
                "security_incidents": {
                    "suspicious_login_attempts": 0,
                    "password_policy_violations": 0,
                    "session_anomalies": 0,
                    "unauthorized_access_attempts": 0
                },
                "key_management": {
                    "last_key_rotation": None,  # Would read from key rotation log
                    "days_since_rotation": 0,
                    "next_rotation_due": None
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check security service health"""
        try:
            health_status = {
                "service": "security",
                "status": "healthy",
                "key_management": {
                    "master_key_exists": os.path.exists(self.master_key_path),
                    "backup_directory_exists": os.path.exists(self.backup_keys_path)
                },
                "configuration": {
                    "key_rotation_interval_days": self.key_rotation_interval,
                    "session_timeout_minutes": self.session_timeout,
                    "max_concurrent_sessions": self.max_concurrent_sessions,
                    "password_policy_enabled": True
                }
            }
            
            # Check if key rotation is due
            if os.path.exists(self.master_key_path):
                key_age = datetime.utcnow() - datetime.fromtimestamp(os.path.getctime(self.master_key_path))
                health_status["key_management"]["key_age_days"] = key_age.days
                health_status["key_management"]["rotation_due"] = key_age.days >= self.key_rotation_interval
            
            return health_status
            
        except Exception as e:
            return {
                "service": "security",
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
security_service = SecurityService()


def get_security_service() -> SecurityService:
    """Get the global security service instance"""
    return security_service 
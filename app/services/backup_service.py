"""
Automated Backup Service
Handles automated file backup, recovery, and cleanup for SynapseDT system
"""

import logging
import os
import shutil
import asyncio
import aiofiles
import zipfile
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles.os

from app.core.config import get_settings
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


class BackupService:
    """Automated backup service for files and configurations"""
    
    def __init__(self):
        self.backup_root = getattr(settings, 'backup_root_path', '/app/backups')
        self.file_upload_path = getattr(settings, 'file_upload_path', '/app/uploads')
        self.security_path = getattr(settings, 'security_path', '/app/security')
        self.config_path = getattr(settings, 'config_path', '/app/config')
        
        self.backup_retention_days = getattr(settings, 'backup_retention_days', 90)
        self.backup_schedule_hours = getattr(settings, 'backup_schedule_hours', 24)
        self.max_backup_size_gb = getattr(settings, 'max_backup_size_gb', 10)
        
        # Backup categories
        self.backup_categories = {
            'files': {
                'path': self.file_upload_path,
                'description': 'User uploaded files and documents',
                'retention_days': 365,
                'compression': True
            },
            'security': {
                'path': self.security_path,
                'description': 'Security keys and certificates',
                'retention_days': 1095,  # 3 years
                'compression': False  # Don't compress security files
            },
            'config': {
                'path': self.config_path,
                'description': 'System configuration files',
                'retention_days': 180,
                'compression': True
            },
            'logs': {
                'path': getattr(settings, 'log_path', '/app/logs'),
                'description': 'System and application logs',
                'retention_days': 90,
                'compression': True
            }
        }
        
        logger.info("Backup service initialized")
    
    async def create_backup(self, category: str = 'all', backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a backup for specified category or all categories"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f"backup_{timestamp}"
            
            backup_base_path = Path(self.backup_root) / backup_name
            await aiofiles.os.makedirs(backup_base_path, exist_ok=True)
            
            backup_results = {
                "backup_name": backup_name,
                "timestamp": datetime.utcnow().isoformat(),
                "categories": {},
                "total_size_mb": 0,
                "success": True,
                "errors": []
            }
            
            if category == 'all':
                categories_to_backup = list(self.backup_categories.keys())
            else:
                categories_to_backup = [category] if category in self.backup_categories else []
            
            if not categories_to_backup:
                return {
                    "success": False,
                    "error": f"Invalid backup category: {category}"
                }
            
            for cat_name in categories_to_backup:
                try:
                    cat_config = self.backup_categories[cat_name]
                    source_path = Path(cat_config['path'])
                    
                    if not source_path.exists():
                        logger.warning(f"Source path does not exist: {source_path}")
                        backup_results["categories"][cat_name] = {
                            "status": "skipped",
                            "reason": "source_not_found"
                        }
                        continue
                    
                    # Create category backup
                    cat_result = await self._backup_category(
                        cat_name, 
                        source_path, 
                        backup_base_path, 
                        cat_config
                    )
                    
                    backup_results["categories"][cat_name] = cat_result
                    backup_results["total_size_mb"] += cat_result.get("size_mb", 0)
                    
                except Exception as e:
                    logger.error(f"Failed to backup category {cat_name}: {str(e)}")
                    backup_results["errors"].append(f"{cat_name}: {str(e)}")
                    backup_results["categories"][cat_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            # Create backup manifest
            await self._create_backup_manifest(backup_base_path, backup_results)
            
            # Check if backup size exceeds limit
            if backup_results["total_size_mb"] > (self.max_backup_size_gb * 1024):
                logger.warning(f"Backup size ({backup_results['total_size_mb']} MB) exceeds limit")
                backup_results["warnings"] = [f"Backup size exceeds {self.max_backup_size_gb} GB limit"]
            
            logger.info(f"Backup completed: {backup_name} ({backup_results['total_size_mb']} MB)")
            return backup_results
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _backup_category(self, category_name: str, source_path: Path, backup_base_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Backup a specific category"""
        try:
            category_backup_path = backup_base_path / category_name
            await aiofiles.os.makedirs(category_backup_path, exist_ok=True)
            
            files_backed_up = 0
            total_size = 0
            
            if config.get('compression', False):
                # Create compressed archive
                archive_path = category_backup_path / f"{category_name}.zip"
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(source_path)
                            zipf.write(file_path, arcname)
                            files_backed_up += 1
                            total_size += file_path.stat().st_size
                
                actual_size = archive_path.stat().st_size
                
            else:
                # Copy files without compression
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        source_file = Path(root) / file
                        relative_path = source_file.relative_to(source_path)
                        dest_file = category_backup_path / relative_path
                        
                        # Ensure destination directory exists
                        await aiofiles.os.makedirs(dest_file.parent, exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(source_file, dest_file)
                        files_backed_up += 1
                        total_size += source_file.stat().st_size
                
                actual_size = total_size
            
            return {
                "status": "completed",
                "files_count": files_backed_up,
                "size_mb": round(actual_size / (1024 * 1024), 2),
                "compression_ratio": round(actual_size / total_size * 100, 1) if total_size > 0 else 100,
                "path": str(category_backup_path)
            }
            
        except Exception as e:
            logger.error(f"Category backup failed for {category_name}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _create_backup_manifest(self, backup_path: Path, backup_results: Dict[str, Any]):
        """Create a manifest file for the backup"""
        try:
            manifest_path = backup_path / "backup_manifest.json"
            
            manifest = {
                "backup_info": {
                    "name": backup_results["backup_name"],
                    "created_at": backup_results["timestamp"],
                    "total_size_mb": backup_results["total_size_mb"],
                    "categories_count": len(backup_results["categories"]),
                    "synapse_version": getattr(settings, 'app_version', '1.0.0')
                },
                "categories": backup_results["categories"],
                "system_info": {
                    "backup_service_version": "1.0.0",
                    "retention_policy": {
                        cat: config.get('retention_days', 90) 
                        for cat, config in self.backup_categories.items()
                    }
                }
            }
            
            async with aiofiles.open(manifest_path, 'w') as f:
                import json
                await f.write(json.dumps(manifest, indent=2))
            
            logger.info(f"Backup manifest created: {manifest_path}")
            
        except Exception as e:
            logger.error(f"Failed to create backup manifest: {str(e)}")
    
    async def restore_backup(self, backup_name: str, categories: List[str] = None, target_path: str = None) -> Dict[str, Any]:
        """Restore from a backup"""
        try:
            backup_path = Path(self.backup_root) / backup_name
            
            if not backup_path.exists():
                return {
                    "success": False,
                    "error": f"Backup not found: {backup_name}"
                }
            
            # Read manifest
            manifest_path = backup_path / "backup_manifest.json"
            if manifest_path.exists():
                async with aiofiles.open(manifest_path, 'r') as f:
                    import json
                    manifest = json.loads(await f.read())
            else:
                return {
                    "success": False,
                    "error": "Backup manifest not found"
                }
            
            categories_to_restore = categories or list(manifest["categories"].keys())
            restore_results = {
                "backup_name": backup_name,
                "restore_timestamp": datetime.utcnow().isoformat(),
                "categories": {},
                "success": True,
                "errors": []
            }
            
            for category in categories_to_restore:
                if category not in manifest["categories"]:
                    restore_results["errors"].append(f"Category not found in backup: {category}")
                    continue
                
                try:
                    category_result = await self._restore_category(
                        category, 
                        backup_path, 
                        target_path
                    )
                    restore_results["categories"][category] = category_result
                    
                except Exception as e:
                    logger.error(f"Failed to restore category {category}: {str(e)}")
                    restore_results["errors"].append(f"{category}: {str(e)}")
                    restore_results["categories"][category] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            logger.info(f"Backup restore completed: {backup_name}")
            return restore_results
            
        except Exception as e:
            logger.error(f"Backup restore failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "restore_timestamp": datetime.utcnow().isoformat()
            }
    
    async def _restore_category(self, category: str, backup_path: Path, target_path: str = None) -> Dict[str, Any]:
        """Restore a specific category from backup"""
        try:
            category_backup_path = backup_path / category
            category_config = self.backup_categories.get(category, {})
            
            # Determine target path
            if target_path:
                restore_target = Path(target_path) / category
            else:
                restore_target = Path(category_config.get('path', f'/tmp/restore_{category}'))
            
            await aiofiles.os.makedirs(restore_target, exist_ok=True)
            
            files_restored = 0
            
            # Check if backup is compressed
            archive_path = category_backup_path / f"{category}.zip"
            if archive_path.exists():
                # Extract from archive
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(restore_target)
                    files_restored = len(zipf.namelist())
            else:
                # Copy files directly
                for root, dirs, files in os.walk(category_backup_path):
                    for file in files:
                        source_file = Path(root) / file
                        relative_path = source_file.relative_to(category_backup_path)
                        dest_file = restore_target / relative_path
                        
                        await aiofiles.os.makedirs(dest_file.parent, exist_ok=True)
                        shutil.copy2(source_file, dest_file)
                        files_restored += 1
            
            return {
                "status": "completed",
                "files_restored": files_restored,
                "target_path": str(restore_target)
            }
            
        except Exception as e:
            logger.error(f"Category restore failed for {category}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups based on retention policies"""
        try:
            cleanup_results = {
                "cleanup_timestamp": datetime.utcnow().isoformat(),
                "backups_removed": [],
                "space_freed_mb": 0,
                "errors": []
            }
            
            backup_root_path = Path(self.backup_root)
            if not backup_root_path.exists():
                return cleanup_results
            
            current_time = datetime.utcnow()
            
            for backup_dir in backup_root_path.iterdir():
                if not backup_dir.is_dir():
                    continue
                
                try:
                    # Check backup age
                    backup_time = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                    age_days = (current_time - backup_time).days
                    
                    # Read manifest to get category-specific retention
                    manifest_path = backup_dir / "backup_manifest.json"
                    max_retention_days = self.backup_retention_days
                    
                    if manifest_path.exists():
                        async with aiofiles.open(manifest_path, 'r') as f:
                            import json
                            manifest = json.loads(await f.read())
                            
                        # Use the maximum retention across all categories
                        retention_policies = manifest.get("system_info", {}).get("retention_policy", {})
                        if retention_policies:
                            max_retention_days = max(retention_policies.values())
                    
                    if age_days > max_retention_days:
                        # Calculate size before deletion
                        backup_size = await self._calculate_directory_size(backup_dir)
                        
                        # Remove backup
                        shutil.rmtree(backup_dir)
                        
                        cleanup_results["backups_removed"].append({
                            "name": backup_dir.name,
                            "age_days": age_days,
                            "size_mb": round(backup_size / (1024 * 1024), 2)
                        })
                        cleanup_results["space_freed_mb"] += round(backup_size / (1024 * 1024), 2)
                        
                        logger.info(f"Removed old backup: {backup_dir.name} (age: {age_days} days)")
                
                except Exception as e:
                    logger.error(f"Failed to process backup {backup_dir.name}: {str(e)}")
                    cleanup_results["errors"].append(f"{backup_dir.name}: {str(e)}")
            
            logger.info(f"Backup cleanup completed. Freed {cleanup_results['space_freed_mb']} MB")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
            return {
                "cleanup_timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory"""
        total_size = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
        return total_size
    
    async def list_backups(self) -> Dict[str, Any]:
        """List all available backups with metadata"""
        try:
            backup_root_path = Path(self.backup_root)
            backups = []
            
            if backup_root_path.exists():
                for backup_dir in backup_root_path.iterdir():
                    if not backup_dir.is_dir():
                        continue
                    
                    try:
                        backup_info = {
                            "name": backup_dir.name,
                            "created_at": datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                            "size_mb": round(await self._calculate_directory_size(backup_dir) / (1024 * 1024), 2)
                        }
                        
                        # Read manifest if available
                        manifest_path = backup_dir / "backup_manifest.json"
                        if manifest_path.exists():
                            async with aiofiles.open(manifest_path, 'r') as f:
                                import json
                                manifest = json.loads(await f.read())
                                backup_info.update(manifest.get("backup_info", {}))
                                backup_info["categories"] = list(manifest.get("categories", {}).keys())
                        
                        backups.append(backup_info)
                        
                    except Exception as e:
                        logger.error(f"Failed to read backup info for {backup_dir.name}: {str(e)}")
            
            # Sort by creation date, newest first
            backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return {
                "backups": backups,
                "total_backups": len(backups),
                "total_size_mb": sum(b.get("size_mb", 0) for b in backups)
            }
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return {
                "error": str(e),
                "backups": []
            }
    
    async def schedule_automated_backups(self):
        """Schedule automated backup creation"""
        logger.info(f"Starting automated backup scheduler (every {self.backup_schedule_hours} hours)")
        
        while True:
            try:
                # Wait for next backup time
                await asyncio.sleep(self.backup_schedule_hours * 3600)
                
                logger.info("Starting scheduled backup")
                backup_result = await self.create_backup('all', f"scheduled_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
                
                if backup_result.get("success"):
                    logger.info(f"Scheduled backup completed: {backup_result['backup_name']}")
                    
                    # Clean up old backups
                    cleanup_result = await self.cleanup_old_backups()
                    if cleanup_result.get("space_freed_mb", 0) > 0:
                        logger.info(f"Cleaned up {cleanup_result['space_freed_mb']} MB of old backups")
                else:
                    logger.error(f"Scheduled backup failed: {backup_result.get('error')}")
                
            except Exception as e:
                logger.error(f"Automated backup scheduler error: {str(e)}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backup service health"""
        try:
            backup_root_path = Path(self.backup_root)
            
            health_status = {
                "service": "backup",
                "status": "healthy",
                "configuration": {
                    "backup_root": str(backup_root_path),
                    "retention_days": self.backup_retention_days,
                    "schedule_hours": self.backup_schedule_hours,
                    "max_size_gb": self.max_backup_size_gb
                },
                "storage": {
                    "backup_directory_exists": backup_root_path.exists(),
                    "backup_directory_writable": os.access(backup_root_path.parent, os.W_OK) if backup_root_path.parent.exists() else False
                }
            }
            
            # Check available storage space
            if backup_root_path.exists():
                statvfs = os.statvfs(backup_root_path)
                free_space_gb = (statvfs.f_frsize * statvfs.f_available) / (1024**3)
                health_status["storage"]["free_space_gb"] = round(free_space_gb, 2)
                health_status["storage"]["low_space_warning"] = free_space_gb < 5  # Less than 5GB
            
            # Get backup statistics
            backup_list = await self.list_backups()
            health_status["statistics"] = {
                "total_backups": backup_list.get("total_backups", 0),
                "total_size_mb": backup_list.get("total_size_mb", 0)
            }
            
            return health_status
            
        except Exception as e:
            return {
                "service": "backup",
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
backup_service = BackupService()


def get_backup_service() -> BackupService:
    """Get the global backup service instance"""
    return backup_service 
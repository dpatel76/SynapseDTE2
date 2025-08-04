#!/bin/bash
# Restore script for backend rename operation
# Created: 2025-07-06 22:51:02

echo "Restoring backend files from backup..."

# Restore all backed up files
cp -r backup_logs/backend_rename_20250706_225102/* .

echo "✅ Files restored from backup_logs/backend_rename_20250706_225102"
echo "Note: You may need to restart the backend server"

#!/bin/bash

# ===============================================================================
# LEGACY TABLE CLEANUP EXECUTION SCRIPT
# ===============================================================================

echo "🚀 Legacy Table Cleanup for SynapseDTE"
echo "======================================="
echo ""

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: PostgreSQL client (psql) is not installed or not in PATH"
    echo "Please install PostgreSQL client first."
    exit 1
fi

# Get database connection details
echo "📋 Database Connection Setup"
echo "----------------------------"
read -p "Enter database host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Enter database name: " DB_NAME
if [ -z "$DB_NAME" ]; then
    echo "❌ Error: Database name is required"
    exit 1
fi

read -p "Enter database user: " DB_USER
if [ -z "$DB_USER" ]; then
    echo "❌ Error: Database user is required"
    exit 1
fi

read -p "Enter database port (default: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}

echo ""
echo "🔍 Step 1: Verifying tables before cleanup..."
echo "============================================"

# Run the verification script
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f check_tables_before_cleanup.sql

if [ $? -ne 0 ]; then
    echo "❌ Error: Could not connect to database or run verification script"
    exit 1
fi

echo ""
echo "⚠️  IMPORTANT WARNING ⚠️"
echo "========================"
echo "This script will PERMANENTLY DELETE legacy tables from your database."
echo "Make sure you have:"
echo "1. 📦 Created a full database backup"
echo "2. 🔍 Reviewed the verification output above"
echo "3. ✅ Confirmed the new unified planning tables exist"
echo "4. 🛑 Stopped all application processes"
echo ""

read -p "Do you want to proceed with the cleanup? (yes/no): " PROCEED
if [ "$PROCEED" != "yes" ]; then
    echo "🛑 Cleanup cancelled by user"
    exit 0
fi

echo ""
echo "🧹 Step 2: Executing legacy table cleanup..."
echo "==========================================="

# Create a backup timestamp
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "📋 Backup timestamp: $BACKUP_TIMESTAMP"

# Execute the cleanup script
echo "🔄 Running cleanup script..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f cleanup_legacy_tables_safe.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS: Legacy table cleanup completed!"
    echo "========================================="
    echo "📊 Summary:"
    echo "• Sample selection legacy tables removed"
    echo "• Versioning legacy tables removed"
    echo "• Phase tracking legacy tables removed"
    echo "• Decision tracking legacy tables removed"
    echo "• Migration tracking tables removed"
    echo "• Legacy sequences and enums removed"
    echo "• Database vacuumed and analyzed"
    echo ""
    echo "🎯 Your database is now optimized and cleaned up!"
    echo "You can now restart your application services."
else
    echo ""
    echo "❌ ERROR: Cleanup script failed!"
    echo "========================="
    echo "The cleanup was executed in a transaction, so changes may have been rolled back."
    echo "Please check the error messages above and ensure:"
    echo "1. Database connection is stable"
    echo "2. User has sufficient privileges"
    echo "3. New unified planning tables exist"
    echo ""
    echo "If you need to restore from backup, use your backup from timestamp: $BACKUP_TIMESTAMP"
    exit 1
fi

echo ""
echo "🏁 Cleanup process completed successfully!"
echo "You may now restart your application services."
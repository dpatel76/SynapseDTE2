#!/bin/bash

# Script to clean up duplicate and backup files in SynapseDTE project
# Run with --dry-run to see what would be deleted without actually deleting

DRY_RUN=false
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    echo "DRY RUN MODE - No files will be deleted"
fi

echo "SynapseDTE File Cleanup Script"
echo "=============================="

# Counter for deleted files
DELETED_COUNT=0

# Function to remove files
remove_file() {
    local file=$1
    if [ -f "$file" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  Would delete: $file"
        else
            rm "$file"
            echo "  Deleted: $file"
        fi
        ((DELETED_COUNT++))
    fi
}

# Remove backup files
echo -e "\n1. Removing backup files..."
find . -name "*.backup" -type f | while read file; do
    remove_file "$file"
done

find . -name "*.role_backup" -type f | while read file; do
    remove_file "$file"
done

# Remove clean versions (after manual verification)
echo -e "\n2. Files with '_clean' suffix (requires manual verification):"
find . -name "*_clean.py" -type f | while read file; do
    original="${file/_clean.py/.py}"
    if [ -f "$original" ]; then
        echo "  Found pair: $original <-> $file"
        echo "  ACTION REQUIRED: Manually verify which version to keep"
    fi
done

# Remove old service versions
echo -e "\n3. Old service versions (v1 when v2 exists):"
find app/services -name "*_v2.py" -type f | while read v2file; do
    v1file="${v2file/_v2.py/.py}"
    if [ -f "$v1file" ]; then
        echo "  Found pair: $v1file (old) <-> $v2file (new)"
        if [ "$DRY_RUN" = false ]; then
            echo "  ACTION REQUIRED: Manually verify v2 is working before deleting v1"
        fi
    fi
done

# Remove _refactored files
echo -e "\n4. Removing '_refactored' files..."
find . -name "*_refactored.py" -type f | while read file; do
    remove_file "$file"
done

# Remove _reconciled files from Temporal
echo -e "\n5. Removing '_reconciled' Temporal files..."
find app/temporal -name "*_reconciled.py" -type f | while read file; do
    original="${file/_reconciled.py/.py}"
    if [ -f "$original" ]; then
        echo "  Found pair: $original <-> $file"
        echo "  ACTION REQUIRED: Verify which version is active"
    fi
done

# Remove test output files
echo -e "\n6. Removing test output JSON files..."
find . -maxdepth 1 -name "test_*.json" -type f | while read file; do
    remove_file "$file"
done

# List deprecated files to remove
echo -e "\n7. Deprecated files to remove:"
deprecated_files=(
    "app/api/v1/endpoints/DEPRECATED_METRICS.md"
    ".env.refactor"
    ".env.refactored"
)

for file in "${deprecated_files[@]}"; do
    remove_file "$file"
done

# Summary
echo -e "\n=============================="
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN COMPLETE - $DELETED_COUNT files would be deleted"
    echo "Run without --dry-run to actually delete files"
else
    echo "CLEANUP COMPLETE - $DELETED_COUNT files deleted"
fi

echo -e "\nMANUAL ACTIONS REQUIRED:"
echo "1. Review and consolidate '_clean' file pairs"
echo "2. Verify v2 services before removing v1 versions"
echo "3. Check '_reconciled' Temporal files"
echo "4. Run scripts/reorganize_files.sh to organize remaining files"
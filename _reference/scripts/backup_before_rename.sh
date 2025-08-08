#!/bin/bash
# Create a backup before renaming files

BACKUP_DIR="backup_before_rename_$(date +%Y%m%d_%H%M%S)"
echo "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Files to backup based on the rename list
FILES_TO_BACKUP=(
    "frontend/src/components/phase/DynamicActivityCardsEnhanced.tsx"
    "frontend/src/pages/ReportTestingPageRedesigned.tsx"
    "frontend/src/pages/dashboards/TestExecutiveDashboardRedesigned.tsx"
    "frontend/src/pages/dashboards/TesterDashboardEnhanced.tsx"
    "frontend/src/pages/phases/DataProfilingEnhanced.tsx"
    "frontend/src/pages/phases/ObservationManagementEnhanced.tsx"
    "frontend/src/pages/phases/SimplifiedPlanningPage.tsx"
    "app/api/v1/api_clean.py"
    "app/api/v1/endpoints/data_sources_clean.py"
    "app/api/v1/endpoints/planning_clean.py"
    "app/api/v1/endpoints/reports_clean.py"
    "app/api/v1/endpoints/admin_rbac_clean.py"
    "app/api/v1/endpoints/metrics_clean.py"
    "app/api/v1/endpoints/data_profiling_clean.py"
    "app/api/v1/endpoints/llm_clean.py"
    "app/api/v1/endpoints/admin_clean.py"
    "app/api/v1/endpoints/admin_sla_clean.py"
    "app/api/v1/endpoints/scoping_clean.py"
    "app/api/v1/endpoints/cycles_clean.py"
    "app/api/v1/endpoints/dashboards_clean.py"
    "app/api/v1/endpoints/request_info_clean.py"
    "app/api/v1/endpoints/users_clean.py"
    "app/api/v1/endpoints/auth_clean.py"
    "app/api/v1/endpoints/data_owner_clean.py"
    "app/api/v1/endpoints/cycle_reports_clean.py"
    "app/api/v1/endpoints/observation_management_clean.py"
    "app/api/v1/endpoints/test_execution_clean.py"
    "app/services/activity_state_manager_v2.py"
)

echo "Backing up files..."
for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -f "$file" ]; then
        # Create directory structure in backup
        dir=$(dirname "$file")
        mkdir -p "$BACKUP_DIR/$dir"
        cp "$file" "$BACKUP_DIR/$file"
        echo "✓ Backed up: $file"
    else
        echo "⚠️  File not found: $file"
    fi
done

# Create restore script
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
# Restore files from this backup

echo "Restoring files from backup..."
for file in $(find . -type f -not -name "restore.sh" -not -name "backup_manifest.txt"); do
    target_file="${file#./}"
    if [ -f "$target_file" ]; then
        cp "$file" "/$target_file"
        echo "✓ Restored: $target_file"
    fi
done
echo "Restore complete!"
EOF

chmod +x "$BACKUP_DIR/restore.sh"

# Create manifest
echo "Backup created on: $(date)" > "$BACKUP_DIR/backup_manifest.txt"
echo "Total files: ${#FILES_TO_BACKUP[@]}" >> "$BACKUP_DIR/backup_manifest.txt"

echo ""
echo "✅ Backup complete: $BACKUP_DIR"
echo "To restore: cd $BACKUP_DIR && ./restore.sh"
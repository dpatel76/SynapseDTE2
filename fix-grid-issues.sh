#!/bin/bash

# Script to fix Grid component issues for MUI v7

echo "Fixing Grid component issues for MUI v7..."

# Files to update
files=(
  "frontend/src/components/IntelligentSamplingPanel.tsx"
  "frontend/src/components/ProfilingDashboard.tsx" 
  "frontend/src/components/versioning/SampleSelectionReview.tsx"
  "frontend/src/components/versioning/VersionManagementDashboard.tsx"
  "frontend/src/components/versioning/VersioningAnalyticsDashboard.tsx"
  "frontend/src/pages/WorkflowMonitoringDashboard.tsx"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "Processing $file..."
    
    # Replace Grid import with Grid2
    sed -i '' 's/import.*{.*Grid.*} from.*@mui\/material.*;//' "$file"
    
    # Add Grid2 import if not already present
    if ! grep -q "Grid2 as Grid" "$file"; then
      # Find the first import statement
      first_import=$(grep -n "^import" "$file" | head -1 | cut -d: -f1)
      # Insert Grid2 import after first import
      sed -i '' "${first_import}a\\
import { Grid2 as Grid } from '@mui/material';" "$file"
    fi
    
    # Replace Grid item xs={} with Grid size={{ xs: }}
    sed -i '' 's/<Grid item xs={\([0-9]*\)}>/<Grid size={{ xs: \1 }}>/g' "$file"
    sed -i '' 's/<Grid item xs={\([0-9]*\)} md={\([0-9]*\)}>/<Grid size={{ xs: \1, md: \2 }}>/g' "$file"
    sed -i '' 's/<Grid item xs={\([0-9]*\)} sm={\([0-9]*\)}>/<Grid size={{ xs: \1, sm: \2 }}>/g' "$file"
    sed -i '' 's/<Grid item xs={\([0-9]*\)} sm={\([0-9]*\)} md={\([0-9]*\)}>/<Grid size={{ xs: \1, sm: \2, md: \3 }}>/g' "$file"
    
    echo "Fixed $file"
  fi
done

echo "Grid fixes complete!"
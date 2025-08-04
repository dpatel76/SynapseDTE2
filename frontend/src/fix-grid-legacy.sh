#!/bin/bash

# Files that need Grid to be replaced with GridLegacy
files=(
  "./components/WorkflowVisualization.tsx"
  "./components/WorkflowProgressEnhanced.tsx"
  "./pages/WorkflowMonitoringDashboard.tsx"
  "./pages/phases/TestReportPage.tsx"
  "./pages/phases/ObservationManagementEnhanced.tsx"
)

for file in "${files[@]}"; do
  echo "Processing $file..."
  
  # Check if the file imports Grid from @mui/material
  if grep -q "import.*{.*Grid.*}.*from.*@mui/material" "$file"; then
    # Remove Grid from the main import
    sed -i '' 's/\(import.*{\)\(.*\)\(Grid,\)\(.*}.*from.*@mui\/material\)/\1\2\4/' "$file"
    sed -i '' 's/\(import.*{.*\), Grid\(.*}.*from.*@mui\/material\)/\1\2/' "$file"
    
    # Add GridLegacy import after the last import from @mui/material
    if ! grep -q "GridLegacy as Grid" "$file"; then
      # Find the last import line and add GridLegacy import after it
      last_import_line=$(grep -n "^import" "$file" | tail -1 | cut -d: -f1)
      sed -i '' "${last_import_line}a\\
import { GridLegacy as Grid } from '@mui/material';
" "$file"
    fi
  fi
done

echo "Done! All files have been updated to use GridLegacy."
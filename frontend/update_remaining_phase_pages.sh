#!/bin/bash

# Script to list remaining phase pages that need DynamicActivityCards integration

echo "=== Remaining Phase Pages to Update ==="
echo ""

# List of all phase pages
phase_pages=(
  "SampleSelectionPage"
  "DataOwnerPage"
  "NewRequestInfoPage"
  "TestExecutionPage"
  "ObservationManagementEnhanced"
  "TestReportPage"
)

# Check each page
for page in "${phase_pages[@]}"; do
  file="src/pages/phases/${page}.tsx"
  if [ -f "$file" ]; then
    # Check if already using DynamicActivityCards
    if grep -q "DynamicActivityCards" "$file"; then
      echo "✓ $page - Already updated"
    else
      echo "✗ $page - Needs update"
      # Check if using usePhaseStatus
      if grep -q "usePhaseStatus" "$file"; then
        echo "  └─ Uses usePhaseStatus ✓"
      else
        echo "  └─ Missing usePhaseStatus ✗"
      fi
    fi
  else
    echo "? $page - File not found"
  fi
done
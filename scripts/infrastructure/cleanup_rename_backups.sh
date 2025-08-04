#!/bin/bash

echo "Cleaning up backup files from testing_execution rename..."

# Remove backup files
rm -f app/api/v1/endpoints/testing_execution.py.backup
rm -f app/api/v1/endpoints/testing_execution_clean.py.backup
rm -f app/api/v1/endpoints/testing_execution_refactored.py.backup
rm -f app/models/testing_execution.py.backup
rm -f app/schemas/testing_execution.py.backup
rm -f app/application/use_cases/testing_execution.py.backup
rm -f frontend/src/pages/phases/TestingExecutionPage.tsx.backup

echo "Backup files removed."
echo ""
echo "Summary of renamed files:"
echo "- app/api/v1/endpoints/testing_execution.py → test_execution.py"
echo "- app/api/v1/endpoints/testing_execution_clean.py → test_execution_clean.py"
echo "- app/api/v1/endpoints/testing_execution_refactored.py → test_execution_refactored.py"
echo "- app/models/testing_execution.py → test_execution.py"
echo "- app/schemas/testing_execution.py → test_execution.py"
echo "- app/application/use_cases/testing_execution.py → test_execution.py"
echo "- frontend/src/pages/phases/TestingExecutionPage.tsx → TestExecutionPage.tsx"
echo ""
echo "All references updated in 40 files."
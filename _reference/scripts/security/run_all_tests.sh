#!/bin/bash

# SynapseDTE Security Test Runner
# Runs all security tests and generates a consolidated report

echo "🔒 SynapseDTE Security Test Suite"
echo "================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create reports directory if it doesn't exist
mkdir -p reports

# Check if running from correct directory
if [ ! -f "run_security_scan.py" ]; then
    echo -e "${RED}Error: Please run this script from the scripts/security directory${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."
MISSING_DEPS=0

for dep in bandit safety pip-audit semgrep; do
    if command_exists $dep; then
        echo -e "  ✅ $dep installed"
    else
        echo -e "  ${RED}❌ $dep not installed${NC}"
        MISSING_DEPS=1
    fi
done

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install bandit safety pip-audit semgrep trufflehog3
fi

echo ""
echo "🚀 Starting security tests..."
echo ""

# Run automated security scan
echo "1️⃣ Running automated security scan..."
python run_security_scan.py
SCAN_EXIT=$?

echo ""
echo "2️⃣ Running authentication security tests..."
python test_authentication.py
AUTH_EXIT=$?

echo ""
echo "3️⃣ Running API security tests..."
python test_api_security.py
API_EXIT=$?

echo ""
echo "4️⃣ Running data security tests..."
python test_data_security.py
DATA_EXIT=$?

# Generate summary report
echo ""
echo "📊 Generating summary report..."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SUMMARY_FILE="reports/security_summary_${TIMESTAMP}.txt"

cat > $SUMMARY_FILE << EOF
SynapseDTE Security Test Summary
Generated: $(date)
================================

Test Results:
- Automated Security Scan: $([ $SCAN_EXIT -eq 0 ] && echo "PASSED" || echo "FAILED - Critical issues found")
- Authentication Tests: $([ $AUTH_EXIT -eq 0 ] && echo "PASSED" || echo "FAILED")
- API Security Tests: $([ $API_EXIT -eq 0 ] && echo "PASSED" || echo "FAILED")
- Data Security Tests: $([ $DATA_EXIT -eq 0 ] && echo "PASSED" || echo "FAILED")

Reports Generated:
$(ls -la reports/*${TIMESTAMP}* 2>/dev/null | awk '{print "- " $9}')

Next Steps:
1. Review detailed reports in the reports/ directory
2. Address critical and high severity findings first
3. Implement remediation as per SECURITY_BEST_PRACTICES.md
4. Re-run tests after fixes to verify remediation

For detailed findings, see:
- reports/security_report_*.html (Web view)
- reports/security_report_*.json (Detailed JSON)
EOF

echo ""
echo "✅ Security testing complete!"
echo ""
echo "📄 Summary saved to: $SUMMARY_FILE"
echo ""

# Display summary
if [ $SCAN_EXIT -ne 0 ] || [ $AUTH_EXIT -ne 0 ] || [ $API_EXIT -ne 0 ] || [ $DATA_EXIT -ne 0 ]; then
    echo -e "${RED}⚠️  SECURITY ISSUES DETECTED${NC}"
    echo "Please review the reports in the 'reports' directory"
    exit 1
else
    echo -e "${GREEN}✅ All security tests passed${NC}"
    echo "No critical issues detected"
fi
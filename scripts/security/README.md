# Security Testing Suite for SynapseDTE

This directory contains comprehensive security testing tools, scripts, and documentation for the SynapseDTE application.

## Directory Structure

```
scripts/security/
├── README.md                    # This file
├── run_security_scan.py         # Main automated security scanner
├── test_authentication.py       # Authentication vulnerability tests
├── test_api_security.py         # API security tests
├── test_data_security.py        # Data at rest & in transit tests
├── docs/                        # Security documentation
│   ├── SECURITY_TESTING_PLAN.md        # Comprehensive testing methodology
│   ├── PENETRATION_TESTING_CHECKLIST.md # Detailed pentest checklist
│   └── SECURITY_BEST_PRACTICES.md      # Remediation and best practices
└── reports/                     # Generated security reports (auto-created)
```

## Quick Start

### 1. Install Dependencies

```bash
# Install required security testing tools
pip install bandit safety pip-audit semgrep trufflehog3
pip install aiohttp asyncio

# For web scanning (optional)
# Install OWASP ZAP or Burp Suite separately
```

### 2. Run Automated Security Scan

```bash
# Run comprehensive security scan
python scripts/security/run_security_scan.py

# This will:
# - Run static code analysis (Bandit)
# - Check dependencies for vulnerabilities (Safety, pip-audit)
# - Scan for hardcoded secrets (TruffleHog)
# - Perform SAST analysis (Semgrep)
# - Generate HTML and JSON reports
```

### 3. Run Specific Tests

```bash
# Test authentication security
python scripts/security/test_authentication.py

# Test API security
python scripts/security/test_api_security.py

# Test data security (at rest & in transit)
python scripts/security/test_data_security.py
```

## Security Tests Overview

### Automated Scanner (`run_security_scan.py`)
- **Static Analysis**: Identifies code-level security issues
- **Dependency Scanning**: Checks for vulnerable packages
- **Secret Detection**: Finds hardcoded credentials
- **Configuration Review**: Checks for security misconfigurations

### Authentication Tests (`test_authentication.py`)
- Brute force protection
- Password policy enforcement
- JWT security validation
- Session management
- Password reset security
- User enumeration
- Rate limiting
- Concurrent session handling

### API Security Tests (`test_api_security.py`)
- SQL injection testing
- NoSQL injection testing
- XSS vulnerability detection
- XXE injection testing
- Mass assignment vulnerabilities
- API versioning security
- CORS configuration
- HTTP method testing
- Content type validation
- DoS protection

### Data Security Tests (`test_data_security.py`)
- **Data in Transit:**
  - TLS/SSL configuration validation
  - Certificate validation and pinning
  - API encryption verification
  - Security header testing
  - Data leakage prevention
- **Data at Rest:**
  - Database encryption verification
  - File storage encryption testing
  - Backup encryption validation
  - Log data security
  - Memory protection testing
- **Data Handling:**
  - Sensitive data masking
  - Data retention policy testing
  - Secure deletion verification

## Generated Reports

Security scans generate reports in the `reports/` directory:
- `security_report_YYYYMMDD_HHMMSS.json` - Detailed JSON report
- `security_report_YYYYMMDD_HHMMSS.html` - HTML report for viewing
- `bandit_YYYYMMDD_HHMMSS.json` - Bandit specific findings
- `semgrep_YYYYMMDD_HHMMSS.json` - Semgrep analysis results

## Documentation

### [Security Testing Plan](docs/SECURITY_TESTING_PLAN.md)
Comprehensive methodology for security testing including:
- Testing phases and approach
- Risk assessment matrix
- Remediation guidelines
- Compliance considerations

### [Penetration Testing Checklist](docs/PENETRATION_TESTING_CHECKLIST.md)
Detailed checklist with 200+ test items covering:
- Authentication & authorization
- Input validation
- Business logic
- Infrastructure security
- Client-side security

### [Security Best Practices](docs/SECURITY_BEST_PRACTICES.md)
Implementation guide for:
- Secure coding practices
- Authentication & authorization
- Data protection
- Infrastructure hardening
- Incident response

### [Data Security Checklist](docs/DATA_SECURITY_CHECKLIST.md)
Comprehensive data security testing:
- Data classification & inventory
- Encryption at rest validation
- Encryption in transit testing
- Data handling procedures
- Compliance requirements

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/security.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install bandit safety pip-audit semgrep
      
      - name: Run security scan
        run: python scripts/security/run_security_scan.py
        
      - name: Upload reports
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: security-reports
          path: scripts/security/reports/
```

## Security Findings Priority

1. **Critical** (CVSS 9.0-10.0): Fix immediately
   - Remote code execution
   - Authentication bypass
   - SQL injection
   
2. **High** (CVSS 7.0-8.9): Fix within 72 hours
   - Privilege escalation
   - Sensitive data exposure
   - XSS vulnerabilities

3. **Medium** (CVSS 4.0-6.9): Fix within 1 week
   - Information disclosure
   - CSRF vulnerabilities
   - Weak cryptography

4. **Low** (CVSS 0.1-3.9): Fix within 1 month
   - Missing security headers
   - Verbose error messages
   - Minor misconfigurations

## Contact

For security-related questions or to report vulnerabilities:
- Create a private security issue
- Email: security@synapseDTE.com
- Follow responsible disclosure practices

## License

These security tools are for authorized testing only. Ensure you have written permission before testing any systems.
#!/usr/bin/env python3
"""
Automated Security Scanning Script for SynapseDTE
Runs multiple security tools and generates a consolidated report
"""

import os
import sys
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Any

class SecurityScanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "security_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
        
    def run_command(self, command: List[str], description: str) -> Dict[str, Any]:
        """Run a command and capture output"""
        print(f"\n🔍 Running: {description}")
        print(f"   Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            success = result.returncode == 0
            print(f"   {'✅' if success else '❌'} {'Success' if success else 'Failed'}")
            
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_dependencies(self):
        """Check if required tools are installed"""
        print("🔧 Checking dependencies...")
        
        tools = {
            "bandit": "pip install bandit",
            "safety": "pip install safety",
            "pip-audit": "pip install pip-audit",
            "semgrep": "pip install semgrep",
            "trufflehog": "pip install trufflehog3"
        }
        
        missing = []
        for tool, install_cmd in tools.items():
            result = subprocess.run(
                ["which", tool],
                capture_output=True
            )
            if result.returncode != 0:
                missing.append((tool, install_cmd))
        
        if missing:
            print("\n❌ Missing tools:")
            for tool, cmd in missing:
                print(f"   - {tool}: Install with '{cmd}'")
            return False
        
        print("✅ All dependencies installed")
        return True
    
    def scan_python_security(self):
        """Run Bandit for Python security issues"""
        output_file = self.reports_dir / f"bandit_{self.timestamp}.json"
        
        result = self.run_command(
            ["bandit", "-r", "app/", "-f", "json", "-o", str(output_file)],
            "Bandit - Python Security Scanner"
        )
        
        # Parse results
        if output_file.exists():
            with open(output_file) as f:
                data = json.load(f)
                issues = data.get("results", [])
                
                self.results["bandit"] = {
                    "total_issues": len(issues),
                    "high_severity": len([i for i in issues if i["issue_severity"] == "HIGH"]),
                    "medium_severity": len([i for i in issues if i["issue_severity"] == "MEDIUM"]),
                    "low_severity": len([i for i in issues if i["issue_severity"] == "LOW"])
                }
                
                # Print summary
                print(f"   Found {len(issues)} issues:")
                print(f"   - High: {self.results['bandit']['high_severity']}")
                print(f"   - Medium: {self.results['bandit']['medium_severity']}")
                print(f"   - Low: {self.results['bandit']['low_severity']}")
    
    def scan_dependencies(self):
        """Check for vulnerable dependencies"""
        # Python dependencies with Safety
        result = self.run_command(
            ["safety", "check", "--json"],
            "Safety - Python Dependency Scanner"
        )
        
        if result["success"]:
            try:
                vulns = json.loads(result["stdout"])
                self.results["safety"] = {
                    "vulnerabilities": len(vulns),
                    "packages": [v["package"] for v in vulns]
                }
                print(f"   Found {len(vulns)} vulnerable packages")
            except:
                self.results["safety"] = {"error": "Failed to parse results"}
        
        # Python dependencies with pip-audit
        result = self.run_command(
            ["pip-audit", "--format", "json"],
            "Pip-audit - Python Dependency Auditor"
        )
        
        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                vulns = data.get("vulnerabilities", [])
                self.results["pip_audit"] = {
                    "vulnerabilities": len(vulns),
                    "packages": list(set([v["name"] for v in vulns]))
                }
                print(f"   Found {len(vulns)} vulnerabilities")
            except:
                self.results["pip_audit"] = {"error": "Failed to parse results"}
        
        # JavaScript dependencies
        if (self.project_root / "frontend" / "package.json").exists():
            result = self.run_command(
                ["npm", "audit", "--json"],
                "NPM Audit - JavaScript Dependency Scanner"
            )
            
            if result["stdout"]:
                try:
                    data = json.loads(result["stdout"])
                    self.results["npm_audit"] = {
                        "vulnerabilities": data.get("metadata", {}).get("vulnerabilities", {}),
                        "total": data.get("metadata", {}).get("totalDependencies", 0)
                    }
                    
                    vulns = data.get("metadata", {}).get("vulnerabilities", {})
                    print(f"   Vulnerabilities - Critical: {vulns.get('critical', 0)}, "
                          f"High: {vulns.get('high', 0)}, "
                          f"Moderate: {vulns.get('moderate', 0)}, "
                          f"Low: {vulns.get('low', 0)}")
                except:
                    self.results["npm_audit"] = {"error": "Failed to parse results"}
    
    def scan_secrets(self):
        """Scan for hardcoded secrets"""
        output_file = self.reports_dir / f"secrets_{self.timestamp}.json"
        
        result = self.run_command(
            ["trufflehog", "filesystem", ".", "--json", "--no-update"],
            "TruffleHog - Secret Scanner"
        )
        
        secrets_found = []
        if result["stdout"]:
            for line in result["stdout"].strip().split('\n'):
                if line:
                    try:
                        secret = json.loads(line)
                        secrets_found.append(secret)
                    except:
                        pass
        
        self.results["trufflehog"] = {
            "secrets_found": len(secrets_found),
            "types": list(set([s.get("DetectorName", "Unknown") for s in secrets_found]))
        }
        
        print(f"   Found {len(secrets_found)} potential secrets")
        
        # Save detailed results
        with open(output_file, 'w') as f:
            json.dump(secrets_found, f, indent=2)
    
    def scan_sast(self):
        """Run Static Application Security Testing"""
        output_file = self.reports_dir / f"semgrep_{self.timestamp}.json"
        
        result = self.run_command(
            ["semgrep", "--config=auto", "--json", "-o", str(output_file), "app/"],
            "Semgrep - Static Analysis Security Testing"
        )
        
        if output_file.exists():
            with open(output_file) as f:
                data = json.load(f)
                findings = data.get("results", [])
                
                self.results["semgrep"] = {
                    "findings": len(findings),
                    "by_severity": {}
                }
                
                for finding in findings:
                    severity = finding.get("extra", {}).get("severity", "UNKNOWN")
                    self.results["semgrep"]["by_severity"][severity] = \
                        self.results["semgrep"]["by_severity"].get(severity, 0) + 1
                
                print(f"   Found {len(findings)} security findings")
    
    def check_security_headers(self):
        """Check for security misconfigurations"""
        print("\n🔍 Checking security configurations...")
        
        issues = []
        
        # Check for hardcoded secrets in config
        config_file = self.project_root / "app" / "core" / "config.py"
        if config_file.exists():
            with open(config_file) as f:
                content = f.read()
                
                # Check for hardcoded secrets
                if "secret_key: str = " in content and "change-me" not in content:
                    issues.append("Hardcoded secret key in config.py")
                
                # Check for debug mode
                if "debug: bool = True" in content:
                    issues.append("Debug mode enabled in production config")
                
                # Check for permissive CORS
                if 'allowed_origins: List[str] = ["*"]' in content:
                    issues.append("Overly permissive CORS configuration")
        
        # Check for .env file in repository
        if (self.project_root / ".env").exists():
            issues.append(".env file found in repository (should be in .gitignore)")
        
        self.results["config_security"] = {
            "issues": len(issues),
            "details": issues
        }
        
        print(f"   Found {len(issues)} configuration issues")
        for issue in issues:
            print(f"   - {issue}")
    
    def generate_report(self):
        """Generate consolidated security report"""
        report = {
            "scan_date": datetime.datetime.now().isoformat(),
            "project": str(self.project_root),
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0
            },
            "results": self.results
        }
        
        # Calculate totals
        if "bandit" in self.results:
            report["summary"]["high_issues"] += self.results["bandit"]["high_severity"]
            report["summary"]["medium_issues"] += self.results["bandit"]["medium_severity"]
            report["summary"]["low_issues"] += self.results["bandit"]["low_severity"]
        
        if "safety" in self.results:
            report["summary"]["critical_issues"] += self.results["safety"].get("vulnerabilities", 0)
        
        if "npm_audit" in self.results:
            vulns = self.results["npm_audit"].get("vulnerabilities", {})
            report["summary"]["critical_issues"] += vulns.get("critical", 0)
            report["summary"]["high_issues"] += vulns.get("high", 0)
            report["summary"]["medium_issues"] += vulns.get("moderate", 0)
            report["summary"]["low_issues"] += vulns.get("low", 0)
        
        if "trufflehog" in self.results:
            report["summary"]["critical_issues"] += self.results["trufflehog"]["secrets_found"]
        
        report["summary"]["total_issues"] = sum([
            report["summary"]["critical_issues"],
            report["summary"]["high_issues"],
            report["summary"]["medium_issues"],
            report["summary"]["low_issues"]
        ])
        
        # Save report
        report_file = self.reports_dir / f"security_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        self.generate_html_report(report, report_file.with_suffix('.html'))
        
        return report
    
    def generate_html_report(self, report: Dict, output_file: Path):
        """Generate HTML security report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Scan Report - {report['scan_date']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
        .high {{ color: #f57c00; font-weight: bold; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .tool-section {{ margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>Security Scan Report</h1>
    <p>Scan Date: {report['scan_date']}</p>
    <p>Project: {report['project']}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Issues: <strong>{report['summary']['total_issues']}</strong></p>
        <ul>
            <li class="critical">Critical: {report['summary']['critical_issues']}</li>
            <li class="high">High: {report['summary']['high_issues']}</li>
            <li class="medium">Medium: {report['summary']['medium_issues']}</li>
            <li class="low">Low: {report['summary']['low_issues']}</li>
        </ul>
    </div>
"""
        
        # Add tool results
        for tool, results in report['results'].items():
            html += f"""
    <div class="tool-section">
        <h2>{tool.replace('_', ' ').title()}</h2>
        <pre>{json.dumps(results, indent=2)}</pre>
    </div>
"""
        
        html += """
    <div class="tool-section">
        <h2>Recommendations</h2>
        <ol>
            <li>Address all critical and high severity issues immediately</li>
            <li>Update all vulnerable dependencies</li>
            <li>Remove any hardcoded secrets and use environment variables</li>
            <li>Implement proper input validation for all user inputs</li>
            <li>Enable security headers and proper CORS configuration</li>
            <li>Regular security scans should be part of CI/CD pipeline</li>
        </ol>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"\n📄 HTML report generated: {output_file}")
    
    def run_full_scan(self):
        """Run all security scans"""
        print("🚀 Starting Security Scan for SynapseDTE")
        print("=" * 60)
        
        if not self.check_dependencies():
            print("\n❌ Please install missing dependencies and try again")
            return
        
        # Run all scans
        self.scan_python_security()
        self.scan_dependencies()
        self.scan_secrets()
        self.scan_sast()
        self.check_security_headers()
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SCAN SUMMARY")
        print("=" * 60)
        print(f"Total Issues Found: {report['summary']['total_issues']}")
        print(f"  - Critical: {report['summary']['critical_issues']}")
        print(f"  - High: {report['summary']['high_issues']}")
        print(f"  - Medium: {report['summary']['medium_issues']}")
        print(f"  - Low: {report['summary']['low_issues']}")
        print(f"\nReports saved to: {self.reports_dir}")
        
        # Return non-zero exit code if critical issues found
        if report['summary']['critical_issues'] > 0:
            print("\n❌ Critical security issues found!")
            sys.exit(1)
        elif report['summary']['high_issues'] > 0:
            print("\n⚠️  High severity issues found!")
            sys.exit(2)
        else:
            print("\n✅ No critical issues found")


def main():
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent.parent
    
    scanner = SecurityScanner(project_root)
    scanner.run_full_scan()


if __name__ == "__main__":
    main()
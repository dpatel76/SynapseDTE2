#!/usr/bin/env python3
"""
Dependency Validation Script for SynapseDTE
Analyzes Python imports and validates against requirements.txt
"""

import ast
import os
import sys
import subprocess
from pathlib import Path
from typing import Set, Dict, List, Tuple
import json
import re

# Standard library modules to exclude
STDLIB_MODULES = {
    'asyncio', 'collections', 'datetime', 'enum', 'functools', 'json', 'logging',
    'os', 'pathlib', 're', 'sys', 'time', 'typing', 'uuid', 'hashlib', 'hmac',
    'secrets', 'random', 'math', 'itertools', 'contextlib', 'dataclasses',
    'abc', 'io', 'csv', 'tempfile', 'shutil', 'subprocess', 'urllib', 'base64',
    'decimal', 'fractions', 'statistics', 'warnings', 'traceback', 'inspect',
    'importlib', 'pkgutil', 'platform', 'socket', 'ssl', 'http', 'email',
    'mimetypes', 'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma', 'sqlite3',
    'xml', 'html', 'copy', 'weakref', 'types', 'operator', 'builtins',
    'concurrent', 'multiprocessing', 'threading', 'queue', 'asyncore',
    'asynchat', 'signal', 'errno', 'select', 'selectors', 'stat', 'string',
    'textwrap', 'unicodedata', 'locale', 'gettext', 'argparse', 'configparser',
    'pickle', 'shelve', 'marshal', 'dbm', 'struct', 'codecs', 'encodings'
}

# Known package name mappings (import name -> package name)
PACKAGE_MAPPINGS = {
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'PIL': 'pillow',
    'yaml': 'pyyaml',
    'dotenv': 'python-dotenv',
    'jose': 'python-jose',
    'passlib': 'passlib',
    'sqlalchemy': 'sqlalchemy',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'pydantic': 'pydantic',
    'pydantic_settings': 'pydantic-settings',
    'redis': 'redis',
    'celery': 'celery',
    'pytest': 'pytest',
    'httpx': 'httpx',
    'aiohttp': 'aiohttp',
    'structlog': 'structlog',
    'alembic': 'alembic',
    'asyncpg': 'asyncpg',
    'aiomysql': 'aiomysql',
    'psycopg2': 'psycopg2-binary',
    'temporalio': 'temporalio',
    'anthropic': 'anthropic',
    'google.generativeai': 'google-generativeai',
    'openai': 'openai',
    'pandas': 'pandas',
    'openpyxl': 'openpyxl',
    'pypdf2': 'pypdf2',
    'magic': 'python-magic',
    'aiosmtplib': 'aiosmtplib',
    'email_validator': 'email-validator',
    'orjson': 'orjson',
    'ujson': 'ujson',
    'click': 'click',
    'mkdocs': 'mkdocs',
    'material': 'mkdocs-material',
    'dateutil': 'python-dateutil',
    'pytz': 'pytz',
    'multipart': 'python-multipart',
    'hvac': 'hvac',
    'boto3': 'boto3',
    'botocore': 'botocore',
    'cryptography': 'cryptography',
    'jwt': 'pyjwt',
    'werkzeug': 'werkzeug',
    'jinja2': 'jinja2',
    'markupsafe': 'markupsafe',
    'itsdangerous': 'itsdangerous',
    'google': 'google-api-python-client',
    'googleapiclient': 'google-api-python-client',
    'google.auth': 'google-auth',
    'google.cloud': 'google-cloud-storage',
    'numpy': 'numpy',
    'scipy': 'scipy',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'bokeh': 'bokeh',
    'dash': 'dash',
    'flask': 'flask',
    'django': 'django',
    'tornado': 'tornado',
    'aiofiles': 'aiofiles',
    'uvloop': 'uvloop',
    'gunicorn': 'gunicorn',
    'gevent': 'gevent',
    'eventlet': 'eventlet',
    'kombu': 'kombu',
    'amqp': 'amqp',
    'billiard': 'billiard',
    'vine': 'vine',
}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements"""
    
    def __init__(self):
        self.imports = set()
        self.from_imports = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.from_imports.add(node.module.split('.')[0])
        self.generic_visit(node)


def extract_imports_from_file(filepath: Path) -> Set[str]:
    """Extract all imports from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        return visitor.imports | visitor.from_imports
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return set()


def find_python_files(directory: Path, exclude_dirs: Set[str] = None) -> List[Path]:
    """Find all Python files in directory, excluding certain directories"""
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 
                       'venv', '.venv', 'env', '.env', 'build', 'dist', '.eggs',
                       'htmlcov', '.tox', '.mypy_cache', '.ruff_cache'}
    
    python_files = []
    for path in directory.rglob('*.py'):
        # Skip if any parent directory is in exclude list
        if any(part in exclude_dirs for part in path.parts):
            continue
        python_files.append(path)
    
    return python_files


def parse_requirements_file(requirements_path: Path) -> Dict[str, str]:
    """Parse requirements.txt file and return package dict"""
    packages = {}
    
    if not requirements_path.exists():
        return packages
    
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Handle different requirement formats
            # package==version
            # package>=version
            # package[extra]==version
            match = re.match(r'^([a-zA-Z0-9\-_]+)(?:\[.*?\])?(?:[><=!~]=?.*)?', line)
            if match:
                package_name = match.group(1).lower()
                packages[package_name] = line
    
    return packages


def analyze_dependencies(project_root: Path) -> Tuple[Set[str], Set[str], Set[str]]:
    """Analyze all Python files and extract dependencies"""
    all_imports = set()
    app_files = find_python_files(project_root / 'app')
    script_files = find_python_files(project_root / 'scripts')
    test_files = find_python_files(project_root / 'tests') if (project_root / 'tests').exists() else []
    
    # Analyze app files
    for filepath in app_files:
        imports = extract_imports_from_file(filepath)
        all_imports.update(imports)
    
    # Separate script and test imports
    script_imports = set()
    for filepath in script_files:
        imports = extract_imports_from_file(filepath)
        script_imports.update(imports)
    
    test_imports = set()
    for filepath in test_files:
        imports = extract_imports_from_file(filepath)
        test_imports.update(imports)
    
    # Filter out standard library and internal imports
    external_imports = set()
    for imp in all_imports:
        if imp not in STDLIB_MODULES and not imp.startswith('app'):
            external_imports.add(imp)
    
    script_external = set()
    for imp in script_imports:
        if imp not in STDLIB_MODULES and not imp.startswith('app'):
            script_external.add(imp)
    
    test_external = set()
    for imp in test_imports:
        if imp not in STDLIB_MODULES and not imp.startswith('app'):
            test_external.add(imp)
    
    return external_imports, script_external, test_external


def map_imports_to_packages(imports: Set[str]) -> Set[str]:
    """Map import names to package names"""
    packages = set()
    
    for imp in imports:
        # Check if we have a mapping
        if imp in PACKAGE_MAPPINGS:
            packages.add(PACKAGE_MAPPINGS[imp].lower())
        else:
            # Use import name as package name
            packages.add(imp.lower().replace('_', '-'))
    
    return packages


def check_missing_dependencies(project_root: Path) -> Dict[str, any]:
    """Main function to check for missing dependencies"""
    print("🔍 Analyzing Python dependencies for SynapseDTE...")
    
    # Parse requirements.txt
    requirements_path = project_root / 'requirements.txt'
    requirements = parse_requirements_file(requirements_path)
    required_packages = set(requirements.keys())
    
    # Parse requirements-dev.txt if exists
    requirements_dev_path = project_root / 'requirements-dev.txt'
    requirements_dev = parse_requirements_file(requirements_dev_path)
    required_dev_packages = set(requirements_dev.keys())
    
    # Analyze imports
    app_imports, script_imports, test_imports = analyze_dependencies(project_root)
    
    # Map imports to packages
    app_packages = map_imports_to_packages(app_imports)
    script_packages = map_imports_to_packages(script_imports)
    test_packages = map_imports_to_packages(test_imports)
    
    # Find missing packages
    all_required_packages = app_packages | script_packages
    missing_from_requirements = all_required_packages - required_packages - required_dev_packages
    
    # Find unused packages
    unused_packages = required_packages - app_packages - script_packages - test_packages
    
    # Special handling for packages that might be imported differently
    special_cases = {
        'temporalio': ['temporal', 'temporalio'],
        'google-generativeai': ['google', 'generativeai'],
        'python-jose': ['jose'],
        'python-multipart': ['multipart'],
        'psycopg2-binary': ['psycopg2'],
    }
    
    # Refine missing packages list
    refined_missing = set()
    for pkg in missing_from_requirements:
        found = False
        for req_pkg, import_names in special_cases.items():
            if pkg in import_names and req_pkg in required_packages:
                found = True
                break
        if not found:
            refined_missing.add(pkg)
    
    results = {
        'app_imports': sorted(app_imports),
        'script_imports': sorted(script_imports),
        'test_imports': sorted(test_imports),
        'required_packages': sorted(required_packages),
        'required_dev_packages': sorted(required_dev_packages),
        'missing_packages': sorted(refined_missing),
        'unused_packages': sorted(unused_packages),
        'app_packages': sorted(app_packages),
        'script_packages': sorted(script_packages),
        'test_packages': sorted(test_packages)
    }
    
    # Print results
    print(f"\n📦 Requirements Analysis:")
    print(f"  - Packages in requirements.txt: {len(required_packages)}")
    print(f"  - Packages in requirements-dev.txt: {len(required_dev_packages)}")
    print(f"  - Unique imports found in app/: {len(app_imports)}")
    print(f"  - Unique imports found in scripts/: {len(script_imports)}")
    print(f"  - Unique imports found in tests/: {len(test_imports)}")
    
    if refined_missing:
        print(f"\n❌ Missing from requirements.txt:")
        for pkg in sorted(refined_missing):
            imports = [imp for imp in (app_imports | script_imports) if imp.lower().replace('_', '-') == pkg]
            print(f"  - {pkg} (imported as: {', '.join(imports) if imports else pkg})")
    else:
        print("\n✅ All imported packages are in requirements files!")
    
    if unused_packages:
        print(f"\n⚠️  Potentially unused packages in requirements.txt:")
        for pkg in sorted(unused_packages):
            print(f"  - {pkg}")
    
    # Check for version conflicts
    print("\n🔍 Checking for potential issues...")
    
    # Check if Temporal is properly included
    if 'temporalio' not in required_packages and ('temporal' in app_imports or 'temporalio' in app_imports):
        print("  ⚠️  Temporal is used but 'temporalio' is commented out in requirements.txt")
    
    # Save detailed report
    report_path = project_root / 'dependency_report.json'
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return results


def validate_frontend_dependencies(project_root: Path):
    """Validate frontend dependencies in package.json"""
    print("\n🔍 Analyzing Frontend dependencies...")
    
    package_json_path = project_root / 'frontend' / 'package.json'
    if not package_json_path.exists():
        print("❌ frontend/package.json not found!")
        return
    
    # Read package.json
    with open(package_json_path, 'r') as f:
        package_data = json.load(f)
    
    dependencies = package_data.get('dependencies', {})
    dev_dependencies = package_data.get('devDependencies', {})
    
    print(f"\n📦 Frontend Dependencies Analysis:")
    print(f"  - Production dependencies: {len(dependencies)}")
    print(f"  - Dev dependencies: {len(dev_dependencies)}")
    
    # Check for common missing dependencies based on imports
    # This would require parsing JS/TS files similar to Python
    
    # Check for security vulnerabilities
    print("\n🔒 Running npm audit (if npm is available)...")
    try:
        os.chdir(project_root / 'frontend')
        result = subprocess.run(['npm', 'audit', '--json'], capture_output=True, text=True)
        if result.returncode == 0:
            audit_data = json.loads(result.stdout)
            vulnerabilities = audit_data.get('metadata', {}).get('vulnerabilities', {})
            total_vulns = sum(vulnerabilities.values())
            if total_vulns > 0:
                print(f"  ⚠️  Found {total_vulns} vulnerabilities:")
                for level, count in vulnerabilities.items():
                    if count > 0:
                        print(f"    - {level}: {count}")
            else:
                print("  ✅ No vulnerabilities found!")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("  ℹ️  npm not available, skipping audit")
    finally:
        os.chdir(project_root)


if __name__ == "__main__":
    # Get project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"🏠 Project root: {project_root}")
    
    # Validate Python dependencies
    results = check_missing_dependencies(project_root)
    
    # Validate Frontend dependencies
    validate_frontend_dependencies(project_root)
    
    # Exit with error if missing dependencies
    if results['missing_packages']:
        sys.exit(1)
    else:
        print("\n✅ Dependency validation complete!")
        sys.exit(0)
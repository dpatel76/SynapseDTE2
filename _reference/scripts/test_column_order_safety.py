#!/usr/bin/env python3
"""
Automated test to detect column order dependencies in the codebase.
This script searches for patterns that indicate unsafe column access that could break
if database column order changes.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set
from collections import defaultdict

# Patterns that indicate column order dependencies
UNSAFE_PATTERNS = [
    # Direct index access patterns
    (r'row\[\d+\]', 'Direct row index access: row[0], row[1], etc.'),
    (r'result\[\d+\]', 'Direct result index access: result[0], result[1], etc.'),
    (r'\[0\].*fetchone\(\)', 'Fetchone with immediate index access'),
    (r'fetchone\(\)\)\[\d+\]', 'Fetchone followed by index access'),
    
    # Tuple unpacking from queries
    (r'for\s+\w+(?:,\s*\w+)+\s+in\s+.*\.fetchall', 'Tuple unpacking in for loop'),
    (r'=\s*.*fetchone\(\).*\n.*\[\d+\]', 'Assignment from fetchone with subsequent indexing'),
    
    # SELECT * patterns
    (r'SELECT\s+\*\s+FROM', 'SELECT * query (column order dependent)'),
    (r'select\s*\(\s*\)', 'SQLAlchemy select() without columns specified'),
]

# File patterns to include
INCLUDE_PATTERNS = [
    '*.py',
]

# Directories to exclude
EXCLUDE_DIRS = {
    '.git',
    '__pycache__',
    'venv',
    '.venv',
    'node_modules',
    '.pytest_cache',
    'htmlcov',
    'migrations/versions',  # Migration files often have raw SQL
}

# Files to exclude (known safe or intentionally using indices)
EXCLUDE_FILES = {
    'test_column_order_safety.py',  # This file
}


def is_excluded_path(path: Path) -> bool:
    """Check if a path should be excluded from scanning."""
    # Check if any parent directory is in exclude list
    for parent in path.parents:
        if parent.name in EXCLUDE_DIRS:
            return True
    
    # Check if file is in exclude list
    if path.name in EXCLUDE_FILES:
        return True
    
    return False


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a single file for column order dependencies.
    Returns list of (line_number, pattern_description, line_content) tuples.
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check each pattern
        for pattern, description in UNSAFE_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                # Find line number
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_num = content[:line_start].count('\n') + 1
                
                # Get the line content
                line_end = content.find('\n', match.start())
                if line_end == -1:
                    line_end = len(content)
                line_content = content[line_start:line_end].strip()
                
                # Skip if it's in a comment
                if '#' in line_content and line_content.index('#') < match.start() - line_start:
                    continue
                
                # Skip if it's in a string (basic check)
                if line_content.count('"') % 2 != 0 or line_content.count("'") % 2 != 0:
                    in_string = True
                    quote_positions = []
                    for i, char in enumerate(line_content):
                        if char in ['"', "'"]:
                            quote_positions.append(i)
                    
                    # Check if match is inside quotes (simplified)
                    match_pos = match.start() - line_start
                    in_string = False
                    for i in range(0, len(quote_positions), 2):
                        if i+1 < len(quote_positions):
                            if quote_positions[i] < match_pos < quote_positions[i+1]:
                                in_string = True
                                break
                    
                    if in_string:
                        continue
                
                issues.append((line_num, description, line_content))
    
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return issues


def scan_directory(root_path: Path) -> dict:
    """Scan directory tree for column order dependencies."""
    results = defaultdict(list)
    total_files = 0
    
    for pattern in INCLUDE_PATTERNS:
        for file_path in root_path.rglob(pattern):
            if is_excluded_path(file_path):
                continue
            
            total_files += 1
            issues = scan_file(file_path)
            
            if issues:
                results[str(file_path)] = issues
    
    return dict(results), total_files


def calculate_risk_score(issues: List[Tuple[int, str, str]]) -> int:
    """Calculate risk score based on issue types."""
    score = 0
    for _, description, _ in issues:
        if 'SELECT *' in description:
            score += 10
        elif 'Direct' in description:
            score += 8
        elif 'Tuple unpacking' in description:
            score += 6
        else:
            score += 4
    return score


def print_results(results: dict, total_files: int):
    """Print scan results in a formatted way."""
    if not results:
        print(f"\n✅ SUCCESS: No column order dependencies found in {total_files} files!")
        return 0
    
    print(f"\n⚠️  WARNING: Found column order dependencies in {len(results)} of {total_files} files\n")
    
    # Sort by risk score
    sorted_files = sorted(
        results.items(),
        key=lambda x: calculate_risk_score(x[1]),
        reverse=True
    )
    
    total_issues = 0
    
    for file_path, issues in sorted_files:
        risk_score = calculate_risk_score(issues)
        print(f"\n{'='*80}")
        print(f"📄 {file_path}")
        print(f"   Risk Score: {risk_score} | Issues: {len(issues)}")
        print(f"{'='*80}")
        
        # Group issues by type
        issues_by_type = defaultdict(list)
        for line_num, description, line_content in issues:
            issues_by_type[description].append((line_num, line_content))
        
        for issue_type, occurrences in issues_by_type.items():
            print(f"\n   ⚠️  {issue_type} ({len(occurrences)} occurrences):")
            for line_num, line_content in occurrences[:3]:  # Show first 3
                print(f"      Line {line_num}: {line_content[:80]}...")
            if len(occurrences) > 3:
                print(f"      ... and {len(occurrences) - 3} more")
        
        total_issues += len(issues)
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: {total_issues} total issues in {len(results)} files")
    print(f"{'='*80}\n")
    
    # Suggest fixes
    print("🔧 SUGGESTED FIXES:")
    print("1. Replace row[0] with named access: row.column_name")
    print("2. Use .mappings() for dictionary-style access: result.mappings().fetchall()")
    print("3. Replace SELECT * with explicit column lists")
    print("4. Use SQLAlchemy column labels: select(Table.column.label('name'))")
    print("5. Avoid tuple unpacking from query results")
    
    return len(results)


def main():
    """Main entry point."""
    # Get project root (assuming script is in scripts/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"🔍 Scanning for column order dependencies in: {project_root}")
    print(f"   Excluding: {', '.join(EXCLUDE_DIRS)}")
    
    results, total_files = scan_directory(project_root)
    
    exit_code = print_results(results, total_files)
    
    # Return non-zero exit code if issues found
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
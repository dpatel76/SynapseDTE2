#!/usr/bin/env python3
"""
Automated checker for common async/background job patterns.
This script can be run manually or as a pre-commit hook.
"""
import ast
import sys
import os
from pathlib import Path
from typing import List, Tuple

class AsyncPatternChecker(ast.NodeVisitor):
    """Check for common async pattern issues."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []
        self.in_async_function = False
        self.has_job_status_update = False
        self.has_session_in_async = False
        
    def visit_AsyncFunctionDef(self, node):
        """Track when we're inside an async function."""
        old_state = self.in_async_function
        old_job_status = self.has_job_status_update
        
        self.in_async_function = True
        self.has_job_status_update = False
        
        # Check if this looks like a background task
        is_background_task = any(
            keyword in node.name.lower() 
            for keyword in ['task', 'job', 'background', 'async', 'run_']
        )
        
        # Visit all child nodes
        self.generic_visit(node)
        
        # Check for missing job status update in background tasks
        if is_background_task and not self.has_job_status_update:
            # Check if function has job_id parameter or uses job_manager
            has_job_context = self._function_has_job_context(node)
            if has_job_context:
                self.issues.append((
                    node.lineno,
                    f"Background task '{node.name}' may be missing job status update to 'running'"
                ))
        
        self.in_async_function = old_state
        self.has_job_status_update = old_job_status
        
    def visit_Call(self, node):
        """Check for specific function calls."""
        # Check for job status updates
        if self._is_job_status_update(node):
            self.has_job_status_update = True
            
        # Check for session creation in async context
        if self.in_async_function and self._is_session_creation(node):
            self.has_session_in_async = True
            
        # Check for wrong job manager method
        if self._is_wrong_job_method(node):
            self.issues.append((
                node.lineno,
                "Using 'update_job_status' - should be 'update_job_progress' with status parameter"
            ))
            
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        """Check for common assignment patterns."""
        # Check for missing updated_at when modifying objects
        if self._is_object_modification(node):
            # Look for updated_at assignment nearby
            if not self._has_updated_at_nearby(node):
                self.issues.append((
                    node.lineno,
                    "Object modification without setting updated_at timestamp"
                ))
                
        self.generic_visit(node)
        
    def _is_job_status_update(self, node):
        """Check if this is a job status update call."""
        if isinstance(node.func, ast.Attribute):
            return (
                node.func.attr == 'update_job_progress' and
                any(
                    kw.arg == 'status' and 
                    isinstance(kw.value, ast.Constant) and 
                    kw.value.value in ['running', 'in_progress']
                    for kw in node.keywords
                )
            )
        return False
        
    def _is_session_creation(self, node):
        """Check if this is a database session creation."""
        if isinstance(node.func, ast.Name):
            return node.func.id in ['AsyncSessionLocal', 'get_db']
        return False
        
    def _is_wrong_job_method(self, node):
        """Check for incorrect job manager method."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'update_job_status'
        return False
        
    def _is_object_modification(self, node):
        """Check if this looks like a database object modification."""
        if isinstance(node.targets[0], ast.Attribute):
            attr_name = node.targets[0].attr
            # Common fields that indicate DB object modification
            db_fields = [
                'name', 'status', 'state', 'value', 'data',
                'classification', 'risk_level', 'flag'
            ]
            return any(field in attr_name.lower() for field in db_fields)
        return False
        
    def _has_updated_at_nearby(self, node):
        """Check if updated_at is set within 5 lines."""
        # This is a simplified check - in real implementation,
        # we'd need to analyze the AST more thoroughly
        return False  # Simplified for now
        
    def _function_has_job_context(self, node):
        """Check if function appears to be job-related."""
        # Check function parameters
        for arg in node.args.args:
            if 'job' in arg.arg.lower():
                return True
                
        # Check function body for job_manager usage
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and 'job' in child.id.lower():
                return True
                
        return False


def check_file(filepath: Path) -> List[Tuple[int, str]]:
    """Check a single Python file for async pattern issues."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        tree = ast.parse(content)
        checker = AsyncPatternChecker(str(filepath))
        checker.visit(tree)
        
        return checker.issues
    except Exception as e:
        return [(0, f"Error parsing file: {e}")]


def main():
    """Run pattern checker on modified files."""
    # Get files to check (could be from git diff or command line args)
    files_to_check = []
    
    if len(sys.argv) > 1:
        # Files provided as arguments
        files_to_check = [Path(f) for f in sys.argv[1:] if f.endswith('.py')]
    else:
        # Check all Python files in common directories
        for pattern in ['app/**/*.py', 'backend/**/*.py']:
            files_to_check.extend(Path('.').glob(pattern))
    
    all_issues = []
    
    for filepath in files_to_check:
        # Skip test files and migrations
        if 'test' in str(filepath) or 'migration' in str(filepath):
            continue
            
        issues = check_file(filepath)
        if issues:
            all_issues.append((filepath, issues))
    
    # Report issues
    if all_issues:
        print("🚨 Async Pattern Issues Found:\n")
        for filepath, issues in all_issues:
            print(f"📄 {filepath}")
            for line_no, issue in issues:
                print(f"  Line {line_no}: {issue}")
            print()
            
        print("\n📚 Review Guidelines:")
        print("- Read /docs/TROUBLESHOOTING_PLANNING_JOBS.md")
        print("- Follow patterns in /AGENT_REVIEW_CHECKLIST.md")
        
        return 1  # Exit with error
    else:
        print("✅ No async pattern issues found!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
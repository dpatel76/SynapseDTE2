#!/usr/bin/env python3
"""
Add phase_id field to all cycle_report_* model files
"""

import os
import re
from pathlib import Path

# Map of model files to their phase relationships
MODEL_PHASE_MAPPING = {
    # Planning phase
    "report_attribute.py": "planning_attributes",
    "scoping.py": {
        "PDEMappingReview": "pde_mapping_reviews",
        "PDEMappingReviewHistory": "pde_mapping_reviews",
        "AttributeScopingRecommendation": "scoping_recommendations",
        "TesterScopingDecision": "scoping_decisions", 
        "ScopingSubmission": "scoping_submissions",
        "ReportOwnerScopingReview": "scoping_reviews"
    },
    
    # Data profiling phase - already updated
    
    # Sample selection phase
    "testing.py": {
        "Sample": "samples"
    },
    
    # Test execution phase
    "test_execution.py": {
        "TestExecution": "test_executions",
        "DocumentAnalysis": "document_analyses",
        "DatabaseTest": "database_tests"
    },
    
    # Observation management phase
    "observation_management.py": {
        "ObservationRecord": "observations",
        "ObservationImpactAssessment": "impact_assessments",
        "ObservationApproval": "observation_approvals",
        "ObservationResolution": "observation_resolutions"
    },
    
    # Test report phase
    "observation_enhanced.py": {
        "TestReportSection": "report_sections"
    }
}

def add_phase_id_to_class(file_path, class_name, relationship_name):
    """Add phase_id field and relationship to a specific class in a file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if phase_id already exists
    if f'phase_id = Column(Integer, ForeignKey(\'workflow_phases.phase_id\')' in content:
        print(f"  {class_name} already has phase_id")
        return False
    
    # Find the class definition
    class_pattern = rf'class {class_name}\([^)]+\):\s*\n(.*?)__tablename__ = "([^"]+)"'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if not match:
        print(f"  Could not find class {class_name}")
        return False
    
    table_name = match.group(2)
    
    # Find where to insert phase_id (after report_id or cycle_id)
    insert_pattern = r'(report_id = Column\(Integer, ForeignKey\([^)]+\)[^)]*\))'
    if not re.search(insert_pattern, content):
        insert_pattern = r'(cycle_id = Column\(Integer, ForeignKey\([^)]+\)[^)]*\))'
    
    if not re.search(insert_pattern, content):
        print(f"  Could not find insertion point for {class_name}")
        return False
    
    # Insert phase_id after report_id or cycle_id
    phase_id_line = '\n    phase_id = Column(Integer, ForeignKey(\'workflow_phases.phase_id\'), nullable=False)'
    content = re.sub(insert_pattern, r'\1' + phase_id_line, content)
    
    # Find relationships section and add phase relationship
    rel_pattern = r'(# Relationships.*?\n)(.*?)(    \w+ = relationship)'
    match = re.search(rel_pattern, content, re.DOTALL)
    
    if match:
        phase_rel_line = f'    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="{relationship_name}")\n'
        content = re.sub(rel_pattern, r'\1' + phase_rel_line + r'\2\3', content, count=1)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  Updated {class_name}")
    return True

def process_models():
    """Process all model files to add phase_id"""
    
    models_dir = Path("/Users/dineshpatel/code/projects/SynapseDTE/app/models")
    
    for file_name, mapping in MODEL_PHASE_MAPPING.items():
        file_path = models_dir / file_name
        
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue
            
        print(f"\nProcessing {file_name}:")
        
        if isinstance(mapping, str):
            # Single class in file
            class_name = file_name.replace('.py', '').split('_')
            class_name = ''.join(word.capitalize() for word in class_name)
            add_phase_id_to_class(file_path, class_name, mapping)
        else:
            # Multiple classes in file
            for class_name, rel_name in mapping.items():
                add_phase_id_to_class(file_path, class_name, rel_name)

if __name__ == "__main__":
    process_models()
    print("\nDone! Remember to run migrations to update the database schema.")
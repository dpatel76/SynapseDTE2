"""Temporal workflow constants and configurations"""

# Task queue names
TASK_QUEUE_WORKFLOW = "synapse-workflow-queue"
TASK_QUEUE_LLM = "synapse-llm-queue"
TASK_QUEUE_NOTIFICATION = "synapse-notification-queue"
TASK_QUEUE_REPORT = "synapse-report-queue"

# Workflow names
WORKFLOW_TEST_CYCLE = "test-cycle-workflow"
WORKFLOW_REPORT_TESTING = "report-testing-workflow"
WORKFLOW_LLM_ANALYSIS = "llm-analysis-workflow"
WORKFLOW_SLA_MONITORING = "sla-monitoring-workflow"

# Activity timeouts (in seconds)
DEFAULT_ACTIVITY_TIMEOUT = 300  # 5 minutes
LLM_ACTIVITY_TIMEOUT = 600  # 10 minutes
REPORT_GENERATION_TIMEOUT = 1800  # 30 minutes

# Retry policies
DEFAULT_RETRY_ATTEMPTS = 3
LLM_RETRY_ATTEMPTS = 2
NOTIFICATION_RETRY_ATTEMPTS = 5

# Workflow phases (correct order matching database)
WORKFLOW_PHASES = [
    "Planning",
    "Data Profiling",
    "Scoping", 
    "Sample Selection",
    "Data Provider ID",  # Data Owner Identification comes after Sample Selection
    "Request Info",
    "Testing",  # Test Execution
    "Observations",
    "Finalize Test Report"  # Final phase
]

# Phase dependencies
PHASE_DEPENDENCIES = {
    "Planning": [],
    "Data Profiling": ["Planning"],
    "Scoping": ["Data Profiling"],
    "Sample Selection": ["Scoping"],  # Samples are tagged to LOBs here
    "Data Provider ID": ["Sample Selection"],  # Uses LOB tags FROM cycle_report_sample_selection_samples
    "Request Info": ["Data Provider ID"],
    "Testing": ["Request Info"],
    "Observations": ["Testing"],
    "Finalize Test Report": ["Observations"]  # After all observations are documented
}
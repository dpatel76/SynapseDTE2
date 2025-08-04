"""Data Transfer Objects for the application layer"""

from .test_cycle_dto import (
    CreateTestCycleDTO,
    UpdateTestCycleDTO,
    TestCycleDTO,
    AddReportToCycleDTO,
    AssignTesterDTO
)

from .workflow_dto import (
    PhaseStatusDTO,
    UpdatePhaseStatusDTO,
    WorkflowTransitionDTO
)

from .report_dto import (
    ReportDTO,
    ReportAttributeDTO,
    TestExecutionDTO,
    TestResultDTO
)

__all__ = [
    'CreateTestCycleDTO',
    'UpdateTestCycleDTO',
    'TestCycleDTO',
    'AddReportToCycleDTO',
    'AssignTesterDTO',
    'PhaseStatusDTO',
    'UpdatePhaseStatusDTO',
    'WorkflowTransitionDTO',
    'ReportDTO',
    'ReportAttributeDTO',
    'TestExecutionDTO',
    'TestResultDTO'
]
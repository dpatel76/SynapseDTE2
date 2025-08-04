# Database models package

# Import all models for easy access
from app.models.base import BaseModel

# New redesigned models
# from app.models.report_inventory import ReportInventory, ReportStatusEnum  # Temporarily disabled - Report model now uses report_inventory table
from app.models.planning import (
    # New unified planning models (PlanningAttribute disabled due to table conflict with ReportAttribute)
    # PlanningDataSource disabled due to table conflict with CycleReportDataSource
    PlanningVersion, PlanningPDEMapping,
    # Enums
    VersionStatus, AttributeDataType, InformationSecurityClassification,
    MappingType, Decision, Status
)
from app.models.cycle_report_data_source import CycleReportDataSource, DataSourceType
# Legacy planning models removed - replaced by unified planning models
# from app.models.cycle_report_planning import (
#     CycleReportPlanningAttributeVersionHistory,
#     SecurityClassificationEnum
# )
from app.models.lob import LOB
from app.models.user import User, user_role_enum
from app.models.rbac import (
    Permission, Role, RolePermission, UserRole,
    UserPermission, ResourcePermission, RoleHierarchy,
    PermissionAuditLog
)
from app.models.rbac_resource import Resource
from app.models.report import Report
from app.models.data_source import DataSource
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport, cycle_report_status_enum
from app.models.workflow import (
    WorkflowPhase,
    workflow_phase_enum, phase_status_enum
)
# Legacy document model removed - replaced by enhanced cycle_report_documents
# from app.models.document import Document
from app.models.request_info import document_type_enum
# ReportAttribute model - the core domain model for report attributes
from app.models.report_attribute import (
    ReportAttribute, AttributeVersionChangeLog, AttributeVersionComparison,
    mandatory_flag_enum, data_type_enum, version_change_type_enum
)
from app.models.data_dictionary import RegulatoryDataDictionary
from app.models.scoping import (
    # New consolidated scoping models
    ScopingVersion, ScopingAttribute, ScopingAuditLog,
    VersionStatus as ScopingVersionStatus, TesterDecision, ReportOwnerDecision, AttributeStatus,
    # Legacy aliases for backward compatibility
    AttributeScopingRecommendation, TesterScopingDecision, ScopingSubmission,
    ReportOwnerScopingReview,
    scoping_recommendation_enum, scoping_decision_enum, approval_status_enum
)
# Data Owner LOB Assignment models - New unified system
from app.models.data_owner_lob_assignment import (
    DataOwnerLOBAttributeVersion, DataOwnerLOBAttributeMapping,
    VersionStatus as DataOwnerVersionStatus, AssignmentStatus as DataOwnerAssignmentStatus
)

# Legacy data owner models (to be deprecated)
from app.models.data_owner import (
    # AttributeLOBAssignment removed - table doesn't exist
    HistoricalDataOwnerAssignment,
    DataOwnerSLAViolation, DataOwnerEscalationLog, DataOwnerPhaseAuditLog,
    escalation_level_enum
)
from app.models.sample_selection import (
    # New consolidated sample selection models
    SampleSelectionVersion, SampleSelectionSample,
    VersionStatus as SampleSelectionVersionStatus, SampleCategory, SampleDecision, SampleSource,
    # Active models (legacy aliases removed for deleted tables)
    # Models removed - functionality moved to metadata-based approach 
    sample_generation_method_enum, sample_status_enum,
    sample_validation_status_enum, sample_type_enum
)
# New consolidated sample selection models - now integrated into main sample_selection.py
# (imported above in the sample_selection import section)
# New consolidated scoping models - now integrated into main scoping.py
# (imported above in the scoping import section)
# Note: Individual sample models removed - functionality moved to sample_selection endpoints
# from app.models.sample_selection_phase import SampleSelectionPhase  # DEPRECATED: Use universal phase status
from app.models.testing import (
    DataOwnerAssignment,  # Sample moved to unified sample selection system
    test_result_enum, data_source_type_enum, assignment_status_enum,
    observation_type_enum, impact_level_enum, sample_status_enum, observation_status_enum
)
from app.models.audit import LLMAuditLog, AuditLog
# Clean versioning models
# NOTE: Using versioning_clean.py to avoid conflicts with existing versioning.py
# from app.models.versioning import (
#     # Enums
#     VersionStatus, ApprovalStatus, SampleSource,
#     # Base
#     VersionedEntity,
#     # Planning Phase
#     PlanningVersion, AttributeDecision,
#     # Data Profiling Phase  
#     DataProfilingVersion, CycleReportDataProfilingRules,
#     # Scoping Phase
#     ScopingVersion, ScopingDecision,
#     # CycleReportSampleSelectionSamples Selection Phase
#     SampleSelectionVersion, SampleDecision,
#     # Data Owner ID Phase
#     DataOwnerAssignment as CleanDataOwnerAssignment,
#     # Request Info Phase
#     DocumentSubmission as CleanDocumentSubmission,
#     # Test Execution Phase
#     TestExecutionAudit,
#     # Observation Management Phase
#     ObservationVersion, ObservationDecision,
#     # Test Report Phase
#     TestReportVersion, ReportSection, ReportSignoff
# )
from app.models.metrics import PhaseMetrics, ExecutionMetrics
from app.models.workflow_tracking import (
    WorkflowExecution, WorkflowStep, WorkflowTransition, WorkflowMetrics, WorkflowAlert,
    WorkflowExecutionStatus, StepType
)
from app.models.sla import SLAConfiguration, SLAEscalationRule, SLAViolationTracking, EscalationEmailLog

# Request Info models
from .request_info import (
    CycleReportTestCase, DataProviderNotification,
    RequestInfoAuditLog, document_type_enum, test_case_status_enum, 
    submission_status_enum, request_info_phase_status_enum, submission_type_enum, validation_status_enum,
    # New evidence management models
    TestCaseSourceEvidence, EvidenceValidationResult, TesterDecision,
    evidence_type_enum, evidence_validation_status_enum, validation_result_enum, tester_decision_enum,
    # Evidence models (unified into TestCaseEvidence)
    RFIEvidenceLegacy, TestCaseEvidence
)

# RFI Version models
from .rfi_versions import (
    RFIVersion,
    RFIEvidence
)

# Test Execution models
from app.models.test_execution import (
    TestExecution, TestExecutionReview, TestExecutionAudit,
    update_user_relationships, update_model_relationships
)

# Legacy test execution models (deprecated)
# from app.models.test_execution import (
#     TestExecution, # DocumentAnalysis, DatabaseTest,
#     # TestResultReview, TestComparison, BulkTestExecution, TestExecutionAuditLog,
#     # setup_test_execution_relationships
# )

# Observation Management models
from app.models.observation_management import (
    ObservationRecord, ObservationImpactAssessment,
    ObservationResolution, ObservationManagementAuditLog,
    # ObservationVersion, ObservationVersionItem,  # Commented out to avoid duplicate mapper error
    ObservationTypeEnum, ObservationSeverityEnum, ObservationStatusEnum,
    ImpactCategoryEnum, ResolutionStatusEnum
)

# Observation models from observation_management
# (ObservationRecord, Observation, ObservationClarification models removed - use ObservationRecord instead)

# Test Report models - Unified Architecture
from app.models.test_report import (
    TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS
)

# Data Profiling models - Unified Architecture
from app.models.data_profiling import (
    # New unified models
    DataProfilingRuleVersion, ProfilingRule, VersionStatus, ProfilingRuleType, ProfilingRuleStatus,
    Severity, Decision, DataSourceType,
    # Upload tracking model
    DataProfilingUpload,
    # Legacy models (deprecated)
    DataProfilingFile, ProfilingResult,
    # Aliases for backward compatibility
    DataProfilingVersion, DataProfilingRule
)

# PDE Mapping Review models
from app.models.pde_mapping_review import (
    PDEMappingReview, ReviewStatus, ReviewActionType, PDEMappingReviewHistory, PDEMappingApprovalRule
)

# Data Source and PDE models - disabled in favor of unified planning models
# from app.models.data_source_config import (
#     DataSourceType, DataSourceConfig, PDEMapping, PDEClassification
# )

# Report Owner Assignment models
# from app.models.report_owner_assignment import (
#     ReportOwnerAssignment, ReportOwnerAssignmentHistory,
#     assignment_status_enum, assignment_priority_enum, assignment_type_enum
# )

# Workflow Activity models
from app.models.workflow_activity import (
    WorkflowActivity, WorkflowActivityHistory, WorkflowActivityDependency,
    WorkflowActivityTemplate, ActivityStatus, ActivityType
)

# Enhanced models for practical application - Temporarily disabled due to relationship issues
# from app.models.data_source import (
#     DataSourceType, SecurityClassification, AttributeMapping, 
#     DataQuery, ProfilingExecution, SecureDataAccess
# )
# from app.models.profiling_enhanced import (
#     ProfilingStrategy, RuleCategory, ProfilingJob, ProfilingPartition,
#     ProfilingRuleSet, PartitionResult, ProfilingAnomalyPattern, ProfilingCache
# )
# from app.models.sample_selection_enhanced import (
#     SamplingStrategy, SampleCategory, IntelligentSamplingJob, SamplePool,
#     IntelligentSample, SamplingRule, SampleLineage
# )

# Versioned models - temporarily disabled due to table conflicts
# from app.models.versioned_models import (
#     DataProfilingRuleVersion, TestExecutionVersion, ObservationVersion,
#     ScopingDecisionVersion, VersionedAttributeScopingRecommendation
# )

# Activity Management models
from app.models.activity_definition import ActivityDefinition, ActivityState

# Universal Assignment models
from app.models.universal_assignment import UniversalAssignment, UniversalAssignmentHistory, AssignmentTemplate

# Cycle Report Document Management models (Enhanced)
from app.models.cycle_report_documents import (
    CycleReportDocument, CycleReportDocumentAccessLog, CycleReportDocumentExtraction, CycleReportDocumentRevision,
    DocumentSummary, DocumentMetrics, DocumentSearchResult, DocumentVersionInfo,
    DocumentType, FileFormat, AccessLevel, UploadStatus, ProcessingStatus, ValidationStatus
)

# Export all models
__all__ = [
    # Base
    "BaseModel",
    
    # LOB
    "LOB",
    
    # User
    "User", "user_role_enum",
    
    # RBAC
    "Permission", "Role", "RolePermission", "UserRole",
    "UserPermission", "ResourcePermission", "RoleHierarchy",
    "PermissionAuditLog", "Resource",
    
    # Report and Data Source
    "Report", "DataSource",
    
    # Test Cycle and Cycle Reports
    "TestCycle", "CycleReport", "cycle_report_status_enum",
    
    # Workflow
    "WorkflowPhase", "workflow_phase_enum", "phase_status_enum",
    
    # Legacy Document model removed - replaced by enhanced cycle_report_documents
    # "Document",
    
    # Report Attributes and Versioning - core domain model
    "ReportAttribute", "AttributeVersionChangeLog", "AttributeVersionComparison",
    "mandatory_flag_enum", "data_type_enum", "version_change_type_enum",
    
    # Regulatory Data Dictionary
    "RegulatoryDataDictionary",
    
    # Scoping - New consolidated models
    "ScopingVersion", "ScopingAttribute", "ScopingAuditLog",
    "ScopingVersionStatus", "TesterDecision", "ReportOwnerDecision", "AttributeStatus",
    # Legacy aliases for backward compatibility
    "AttributeScopingRecommendation", "TesterScopingDecision", "ScopingSubmission",
    "ReportOwnerScopingReview",
    "scoping_recommendation_enum", "scoping_decision_enum", "approval_status_enum",
    
    # Data Owner LOB Assignment - New unified system
    "DataOwnerLOBAttributeVersion", "DataOwnerLOBAttributeMapping",
    "DataOwnerVersionStatus", "DataOwnerAssignmentStatus",
    
    # Legacy Data Owner Phase (to be deprecated)
    # "AttributeLOBAssignment" removed - table doesn't exist
    "HistoricalDataOwnerAssignment",
    "DataOwnerSLAViolation", "DataOwnerEscalationLog", "DataOwnerPhaseAuditLog",
    "escalation_level_enum",
    
    # Sample Selection - New consolidated models
    "SampleSelectionVersion", "SampleSelectionSample",
    "SampleSelectionVersionStatus", "SampleCategory", "SampleDecision", "SampleSource",
    # Active models (legacy aliases removed for deleted tables)
    # Models removed - functionality moved to metadata-based approach
    "sample_generation_method_enum", "sample_status_enum", "sample_validation_status_enum", "sample_type_enum",
    
    # New consolidated scoping models are now included in the main scoping section above
    
    
    # Testing
    "DataOwnerAssignment",  # Sample moved to unified sample selection system
    "test_result_enum", "data_source_type_enum", "assignment_status_enum",
    "observation_type_enum", "impact_level_enum", "sample_status_enum", "observation_status_enum",
    
    # Test Execution - Unified Architecture
    "TestExecution", "TestExecutionReview", "TestExecutionAudit",
    
    # Legacy Test Execution (deprecated)
    "TestExecution", # "DocumentAnalysis", "DatabaseTest",
    # "TestResultReview", "TestComparison", "BulkTestExecution", "TestExecutionAuditLog",
    
    # Observation Management
    "ObservationRecord", "ObservationImpactAssessment",
    "ObservationResolution", "ObservationManagementAuditLog",
    # "ObservationVersion", "ObservationVersionItem",  # Commented out to avoid duplicate mapper error
    "ObservationTypeEnum", "ObservationSeverityEnum", "ObservationStatusEnum",
    "ImpactCategoryEnum", "ResolutionStatusEnum",
    
    # Enhanced Observation models removed - use ObservationRecord from observation_management
    
    # Test Report models - Unified Architecture  
    "TestReportSection", "TestReportGeneration", "STANDARD_REPORT_SECTIONS",
    
    # Audit
    "LLMAuditLog", "AuditLog",
    
    # Clean Versioning models - commented out to avoid conflicts
    # "VersionStatus", "ApprovalStatus", "SampleSource",
    # "VersionedEntity",
    # "PlanningVersion", "AttributeDecision",
    # "DataProfilingVersion", "ProfilingRule",
    # "ScopingVersion", "ScopingDecision",
    # "SampleSelectionVersion", "SampleDecision",
    # "CleanDataOwnerAssignment",
    # "CleanDocumentSubmission",
    # "TestExecutionAudit",
    # "ObservationVersion", "ObservationDecision",
    # "TestReportVersion", "ReportSection", "ReportSignoff",
    
    # SLA Management
    "SLAConfiguration", "SLAEscalationRule", "SLAViolationTracking", "EscalationEmailLog",

    # Request Info Management
    "CycleReportTestCase", "DataProviderNotification",
    "RequestInfoAuditLog", "document_type_enum", "test_case_status_enum", 
    "submission_status_enum", "request_info_phase_status_enum", "submission_type_enum", "validation_status_enum",
    # New evidence management models
    "TestCaseSourceEvidence", "EvidenceValidationResult", "TesterDecision",
    "evidence_type_enum", "evidence_validation_status_enum", "validation_result_enum", "tester_decision_enum",
    # Evidence models (unified into TestCaseEvidence)
    "RFIEvidenceLegacy", "TestCaseEvidence",
    # RFI Version models
    "RFIVersion", "RFIEvidence",
    
    # Data Profiling Management
    "DataProfilingUpload", "DataProfilingFile", "ProfilingRule", "ProfilingResult",
    "ProfilingRuleStatus", "ProfilingRuleType",
    
    # PDE Mapping Review
    "PDEMappingReview", "ReviewStatus", "ReviewActionType", "PDEMappingReviewHistory", "PDEMappingApprovalRule",
    
    # Data Source and PDE models - disabled in favor of unified planning models
    # "DataSourceType", "DataSourceConfig", "PDEMapping", "PDEClassification",
    
    # Versioned models - temporarily disabled due to table conflicts
    # "DataProfilingRuleVersion", "TestExecutionVersion", "ObservationVersion", 
    # "ScopingDecisionVersion", "VersionedAttributeScopingRecommendation",
    
    # Report Owner Assignment Management
    # "ReportOwnerAssignment", "ReportOwnerAssignmentHistory",
    # "assignment_status_enum", "assignment_priority_enum", "assignment_type_enum",
    
    # Workflow Activity Management
    "WorkflowActivity", "WorkflowActivityHistory", "WorkflowActivityDependency",
    "WorkflowActivityTemplate", "ActivityStatus", "ActivityType",
    
    # Enhanced models for practical application - Temporarily disabled due to relationship issues
    # "DataSourceType", "SecurityClassification", "AttributeMapping",
    # "DataQuery", "ProfilingExecution", "SecureDataAccess",
    # "ProfilingStrategy", "RuleCategory", "ProfilingJob", "ProfilingPartition",
    # "ProfilingRuleSet", "PartitionResult", "ProfilingAnomalyPattern", "ProfilingCache",
    # "SamplingStrategy", "SampleCategory", "IntelligentSamplingJob", "SamplePool",
    # "IntelligentSample", "SamplingRule", "SampleLineage",
    
    # New redesigned models
    # "ReportInventory", "ReportStatusEnum",  # Temporarily disabled - Report model now uses report_inventory table
    
    # New unified planning models (PlanningAttribute disabled due to table conflict with ReportAttribute)
    "PlanningVersion", "CycleReportDataSource", "PlanningPDEMapping",
    "VersionStatus", "DataSourceType", "AttributeDataType", "InformationSecurityClassification",
    "MappingType", "Decision", "Status",
    
    # Legacy planning models removed - replaced by unified planning models
    # "CycleReportPlanningAttributeVersionHistory",
    # "SecurityClassificationEnum",
    
    # Activity Management
    "ActivityDefinition", "ActivityState",
    
    # Universal Assignment
    "UniversalAssignment", "UniversalAssignmentHistory", "AssignmentTemplate",
    
    # Cycle Report Document Management (Enhanced)
    "CycleReportDocument", "CycleReportDocumentAccessLog", "CycleReportDocumentExtraction", "CycleReportDocumentRevision",
    "DocumentSummary", "DocumentMetrics", "DocumentSearchResult", "DocumentVersionInfo",
    "DocumentType", "FileFormat", "AccessLevel", "UploadStatus", "ProcessingStatus", "ValidationStatus"
] 

# Setup relationships - Unified Architecture
update_user_relationships()
update_model_relationships() 
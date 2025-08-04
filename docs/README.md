# SynapseDTE Documentation Index

This directory contains all project documentation organized by type and purpose.

## 🚨 CRITICAL: Required Reading for Background Jobs

If you're working on any background jobs, async tasks, or database operations in async contexts, you **MUST** read these documents:

1. **[TROUBLESHOOTING_PLANNING_JOBS.md](./TROUBLESHOOTING_PLANNING_JOBS.md)** 🔥
   - Detailed analysis of issues that took 4+ hours to debug
   - Root causes and solutions for classification data not saving
   - Job status update issues and fixes
   - SQLAlchemy session management in async contexts

2. **[../AGENT_REVIEW_CHECKLIST.md](../AGENT_REVIEW_CHECKLIST.md)** ✅
   - Quick reference checklist for async patterns
   - Common mistakes to avoid
   - Pre-implementation checklist
   - Code review guidelines

3. **[../CLAUDE.md](../CLAUDE.md#background-jobs--async-operations)** 📖
   - See section: "Background Jobs & Async Operations"
   - Phase ID architecture patterns
   - Overall architecture guidelines

### 🛠️ Tools: Run Before Committing
```bash
python scripts/check_async_patterns.py
```

### ⏱️ Time Saved by Reading These Docs: ~4+ hours

## 📁 Directory Structure

### 📊 Analysis (`/analysis/`)
Technical analysis reports and audits
- `COMPREHENSIVE_AUDIT_REPORT_REVISED.md` - Complete system audit (latest)
- `AUDIT_REPORT.md` - Initial audit report
- `PROJECT_FILE_AUDIT.md` - Detailed file analysis
- `RBAC_ANALYSIS.md` - Role-based access control analysis
- `DATABASE_SCHEMA_ANALYSIS.md` - Database design analysis
- `LLM_BATCH_SIZE_ANALYSIS.md` - LLM performance analysis
- `METRICS_IMPLEMENTATION_ANALYSIS.md` - Metrics system analysis
- `CLEAN_ARCHITECTURE_COVERAGE_ANALYSIS.md` - Architecture migration analysis
- `UI_UX_CONSISTENCY_ANALYSIS.md` - User interface analysis
- `WORKFLOW_ANALYSIS.md` - Workflow system analysis
- `SLA_TRACKING_ANALYSIS.md` - SLA system analysis
- `NOTIFICATION_TASK_ANALYSIS.md` - Notification system analysis
- `MOCK_DATA_FALLBACK_ANALYSIS.md` - Data fallback analysis
- `DYNAMIC_SAMPLE_ARCHITECTURE.md` - Sample architecture analysis
- `CODE_ORGANIZATION_OOP_ANALYSIS.md` - Code organization analysis
- `CDO_ASSIGNMENTS_SUMMARY.md` - CDO assignment analysis
- `AUDIT_VERSIONING_ANALYSIS.md` - Versioning system analysis
- `ASYNC_DATABASE_ANALYSIS.md` - Database async implementation
- `APPLICATION_READINESS_REPORT.md` - Application readiness assessment
- `versioning_analysis_report.md` - Detailed versioning analysis

### 🏗️ Architecture (`/architecture/`)
Architectural decisions and Clean Architecture migration
- `CLEAN_ARCHITECTURE_STATUS.md` - Current migration status
- `ENHANCEMENT_VALIDATION_REPORT.md` - Architecture validation

### 📋 Implementation Plans (`/implementation_plans/`)
Specific implementation roadmaps and plans
- `IMPLEMENTATION_STATUS.md` - Overall implementation progress
- `INDIVIDUAL_SAMPLES_IMPLEMENTATION.md` - Sample selection implementation
- `SCOPING_IMPLEMENTATION.md` - Scoping phase implementation
- `SCOPING_READONLY_IMPLEMENTATION.md` - Read-only scoping implementation

### 📖 Guides (`/guides/`)
Development guides and best practices
- `CLEAN_ARCHITECTURE_GUIDE.md` - Clean Architecture patterns
- `COMPREHENSIVE_TESTING_GUIDE.md` - Testing strategies
- `DEPLOYMENT_GUIDE.md` - Deployment procedures
- `DEVELOPMENT_PATTERNS.md` - Code patterns and practices
- `FUNCTIONAL_REQUIREMENTS.md` - System requirements
- `REFACTORING_VALIDATION_CHECKLIST.md` - Refactoring checklist
- `COMMON_MISTAKES.md` - Common pitfalls to avoid
- `scoping_ui_improvements.md` - UI improvement guidelines

### 📝 Summaries (`/summaries/`)
Status reports, fix summaries, and progress updates
- `COMPREHENSIVE_ENHANCEMENT_RECOMMENDATIONS.md` - Enhancement recommendations
- `COMPREHENSIVE_REVIEW_SUMMARY.md` - Overall review summary
- `COMPREHENSIVE_TEST_SUMMARY.md` - Testing summary
- `CURRENT_STATUS_SUMMARY.md` - Current project status
- `FINAL_INTEGRATION_STATUS.md` - Integration completion status
- `FINAL_REFACTORING_VALIDATION.md` - Refactoring validation
- `JOB_STATUS_FIX_SUMMARY.md` - Job status fixes
- `LLM_CONFIG_FIX_SUMMARY.md` - LLM configuration fixes
- `MIGRATION_SUMMARY.md` - Migration progress
- `PHASE_NAME_FIX_SUMMARY.md` - Phase naming fixes
- `RBAC_TEST_SUMMARY.md` - RBAC testing results
- `REMAINING_INTEGRATION_TASKS.md` - Outstanding tasks
- `RENAME_TESTING_EXECUTION_SUMMARY.md` - Rename operation summary
- `SAMPLE_FEEDBACK_DEBUG.md` - Sample feedback debugging
- `SAMPLE_FEEDBACK_ENHANCEMENTS.md` - Sample feedback improvements
- `SAMPLE_SELECTION_FIX_SUMMARY.md` - Sample selection fixes
- `SAMPLE_SELECTION_PERMISSIONS_FIX.md` - Sample permission fixes
- `SAMPLE_VERSIONING_SUMMARY.md` - Sample versioning implementation
- `TEST_RESULTS_SUMMARY.md` - Test execution results
- `TEST_SUMMARY.md` - Overall testing summary
- `TESTER_DASHBOARD_FIX.md` - Dashboard fixes
- `FEEDBACK_PROMINENCE_SUMMARY.md` - User feedback analysis
- `role_rename_impact_analysis.md` - Role rename impact
- `ISSUES_FIXED.md` - Resolved issues log

### ⚡ Temporal Workflow (`/temporal/`)
Temporal workflow system documentation
- `TEMPORAL_INTEGRATION.md` - Temporal integration guide
- `TEMPORAL_EXISTING_CODE_INTEGRATION.md` - Integration with existing code
- `TEMPORAL_HUMAN_IN_LOOP_PATTERN.md` - Human-in-the-loop workflows
- `TEMPORAL_PHASE_RECONCILIATION.md` - Phase reconciliation
- `TEMPORAL_RECONCILIATION_COMPLETE.md` - Reconciliation completion
- `TEMPORAL_RECONCILIATION_SUMMARY.md` - Reconciliation summary
- `TEMPORAL_UI_ALIGNMENT_COMPLETE.md` - UI alignment completion
- `UI_TEMPORAL_ALIGNMENT.md` - UI-Temporal integration

### 🧪 Testing (`/testing/`)
Testing procedures and workflows
- `test_scoping_workflow.md` - Scoping workflow tests

## 🔗 Quick Links

### For New Developers
1. Start with: `guides/CLEAN_ARCHITECTURE_GUIDE.md`
2. Read: `guides/DEVELOPMENT_PATTERNS.md`
3. Check: `architecture/CLEAN_ARCHITECTURE_STATUS.md`

### For System Administrators
1. Review: `guides/DEPLOYMENT_GUIDE.md`
2. Check: `analysis/COMPREHENSIVE_AUDIT_REPORT_REVISED.md`
3. Monitor: `summaries/CURRENT_STATUS_SUMMARY.md`

### For Project Managers
1. Status: `implementation_plans/IMPLEMENTATION_STATUS.md`
2. Progress: `summaries/FINAL_INTEGRATION_STATUS.md`
3. Tasks: `summaries/REMAINING_INTEGRATION_TASKS.md`

### For Architects
1. Analysis: `analysis/CLEAN_ARCHITECTURE_COVERAGE_ANALYSIS.md`
2. Status: `architecture/CLEAN_ARCHITECTURE_STATUS.md`
3. Database: `analysis/DATABASE_SCHEMA_ANALYSIS.md`

## 📋 Important Files Remaining at Root Level

- `README.md` - Main project documentation
- `CLAUDE.md` - Claude Code AI assistant instructions
- `IMPLEMENTATION_PLAN.md` - Master implementation plan

## 🔄 Document Maintenance

This documentation is organized and maintained as part of the project's Clean Architecture migration. When adding new documentation:

1. Place analysis documents in `/analysis/`
2. Place implementation plans in `/implementation_plans/`
3. Place guides and procedures in `/guides/`
4. Place status reports in `/summaries/`
5. Place Temporal-related docs in `/temporal/`
6. Place architecture docs in `/architecture/`
7. Place testing docs in `/testing/`

Last Updated: 2025-01-22
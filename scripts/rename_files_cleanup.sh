#!/bin/bash
# Auto-generated script to rename files
# Review carefully before running!

set -e  # Exit on error

echo "Starting file renaming..."


# Rename frontend_clean.log to frontend.log
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend_clean.log" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend.log" ]; then
        echo "Renaming frontend_clean.log → frontend.log"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend_clean.log" "/Users/dineshpatel/code/projects/SynapseDTE/frontend.log"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend.log"
    fi
fi

# Rename UNIVERSAL_PHASE_STATUS_FRAMEWORK_V2.md to UNIVERSAL_PHASE_STATUS_FRAMEWORK_.md
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/UNIVERSAL_PHASE_STATUS_FRAMEWORK_V2.md" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/UNIVERSAL_PHASE_STATUS_FRAMEWORK_.md" ]; then
        echo "Renaming UNIVERSAL_PHASE_STATUS_FRAMEWORK_V2.md → UNIVERSAL_PHASE_STATUS_FRAMEWORK_.md"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/UNIVERSAL_PHASE_STATUS_FRAMEWORK_V2.md" "/Users/dineshpatel/code/projects/SynapseDTE/UNIVERSAL_PHASE_STATUS_FRAMEWORK_.md"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/UNIVERSAL_PHASE_STATUS_FRAMEWORK_.md"
    fi
fi

# Rename api_clean.py to api.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/api_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/api.py" ]; then
        echo "Renaming api_clean.py → api.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/api_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/api.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/api.py"
    fi
fi

# Rename data_sources_clean.py to data_sources.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_sources_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_sources.py" ]; then
        echo "Renaming data_sources_clean.py → data_sources.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_sources_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_sources.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_sources.py"
    fi
fi

# Rename planning_clean.py to planning.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/planning_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/planning.py" ]; then
        echo "Renaming planning_clean.py → planning.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/planning_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/planning.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/planning.py"
    fi
fi

# Rename reports_clean.py to reports.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/reports_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/reports.py" ]; then
        echo "Renaming reports_clean.py → reports.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/reports_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/reports.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/reports.py"
    fi
fi

# Rename admin_rbac_clean.py to admin_rbac.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_rbac_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_rbac.py" ]; then
        echo "Renaming admin_rbac_clean.py → admin_rbac.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_rbac_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_rbac.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_rbac.py"
    fi
fi

# Rename metrics_clean.py to metrics.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/metrics_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/metrics.py" ]; then
        echo "Renaming metrics_clean.py → metrics.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/metrics_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/metrics.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/metrics.py"
    fi
fi

# Rename data_profiling_clean.py to data_profiling.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_profiling_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_profiling.py" ]; then
        echo "Renaming data_profiling_clean.py → data_profiling.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_profiling_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_profiling.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_profiling.py"
    fi
fi

# Rename llm_clean.py to llm.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/llm_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/llm.py" ]; then
        echo "Renaming llm_clean.py → llm.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/llm_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/llm.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/llm.py"
    fi
fi

# Rename admin_clean.py to admin.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin.py" ]; then
        echo "Renaming admin_clean.py → admin.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin.py"
    fi
fi

# Rename admin_sla_clean.py to admin_sla.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_sla_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_sla.py" ]; then
        echo "Renaming admin_sla_clean.py → admin_sla.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_sla_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_sla.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/admin_sla.py"
    fi
fi

# Rename scoping_clean.py to scoping.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/scoping_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/scoping.py" ]; then
        echo "Renaming scoping_clean.py → scoping.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/scoping_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/scoping.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/scoping.py"
    fi
fi

# Rename cycles_clean.py to cycles.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycles_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycles.py" ]; then
        echo "Renaming cycles_clean.py → cycles.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycles_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycles.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycles.py"
    fi
fi

# Rename dashboards_clean.py to dashboards.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/dashboards_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/dashboards.py" ]; then
        echo "Renaming dashboards_clean.py → dashboards.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/dashboards_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/dashboards.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/dashboards.py"
    fi
fi

# Rename request_info_clean.py to request_info.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/request_info_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/request_info.py" ]; then
        echo "Renaming request_info_clean.py → request_info.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/request_info_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/request_info.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/request_info.py"
    fi
fi

# Rename users_clean.py to users.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/users_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/users.py" ]; then
        echo "Renaming users_clean.py → users.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/users_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/users.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/users.py"
    fi
fi

# Rename auth_clean.py to auth.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/auth_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/auth.py" ]; then
        echo "Renaming auth_clean.py → auth.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/auth_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/auth.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/auth.py"
    fi
fi

# Rename data_owner_clean.py to data_owner.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_owner_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_owner.py" ]; then
        echo "Renaming data_owner_clean.py → data_owner.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_owner_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_owner.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/data_owner.py"
    fi
fi

# Rename cycle_reports_clean.py to cycle_reports.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycle_reports_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycle_reports.py" ]; then
        echo "Renaming cycle_reports_clean.py → cycle_reports.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycle_reports_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycle_reports.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/cycle_reports.py"
    fi
fi

# Rename observation_management_clean.py to observation_management.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/observation_management_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/observation_management.py" ]; then
        echo "Renaming observation_management_clean.py → observation_management.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/observation_management_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/observation_management.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/observation_management.py"
    fi
fi

# Rename test_execution_clean.py to test_execution.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/test_execution_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/test_execution.py" ]; then
        echo "Renaming test_execution_clean.py → test_execution.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/test_execution_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/test_execution.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/api/v1/endpoints/test_execution.py"
    fi
fi

# Rename activity_state_manager_v2.py to activity_state_manager.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/app/services/activity_state_manager_v2.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/app/services/activity_state_manager.py" ]; then
        echo "Renaming activity_state_manager_v2.py → activity_state_manager.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/app/services/activity_state_manager_v2.py" "/Users/dineshpatel/code/projects/SynapseDTE/app/services/activity_state_manager.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/app/services/activity_state_manager.py"
    fi
fi

# Rename DynamicActivityCardsEnhanced.tsx to DynamicActivityCards.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/components/phase/DynamicActivityCardsEnhanced.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/components/phase/DynamicActivityCards.tsx" ]; then
        echo "Renaming DynamicActivityCardsEnhanced.tsx → DynamicActivityCards.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/components/phase/DynamicActivityCardsEnhanced.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/components/phase/DynamicActivityCards.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/components/phase/DynamicActivityCards.tsx"
    fi
fi

# Rename ReportTestingPageRedesigned.tsx to ReportTestingPage.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/ReportTestingPageRedesigned.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/ReportTestingPage.tsx" ]; then
        echo "Renaming ReportTestingPageRedesigned.tsx → ReportTestingPage.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/ReportTestingPageRedesigned.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/ReportTestingPage.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/ReportTestingPage.tsx"
    fi
fi

# Rename TestExecutiveDashboardRedesigned.tsx to TestExecutiveDashboard.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TestExecutiveDashboardRedesigned.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TestExecutiveDashboard.tsx" ]; then
        echo "Renaming TestExecutiveDashboardRedesigned.tsx → TestExecutiveDashboard.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TestExecutiveDashboardRedesigned.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TestExecutiveDashboard.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TestExecutiveDashboard.tsx"
    fi
fi

# Rename TesterDashboardEnhanced.tsx to TesterDashboard.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TesterDashboardEnhanced.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TesterDashboard.tsx" ]; then
        echo "Renaming TesterDashboardEnhanced.tsx → TesterDashboard.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TesterDashboardEnhanced.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TesterDashboard.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/dashboards/TesterDashboard.tsx"
    fi
fi

# Rename DataProfilingEnhanced.tsx to DataProfiling.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/DataProfilingEnhanced.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/DataProfiling.tsx" ]; then
        echo "Renaming DataProfilingEnhanced.tsx → DataProfiling.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/DataProfilingEnhanced.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/DataProfiling.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/DataProfiling.tsx"
    fi
fi

# Rename ObservationManagementEnhanced.tsx to ObservationManagement.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/ObservationManagementEnhanced.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/ObservationManagement.tsx" ]; then
        echo "Renaming ObservationManagementEnhanced.tsx → ObservationManagement.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/ObservationManagementEnhanced.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/ObservationManagement.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/ObservationManagement.tsx"
    fi
fi

# Rename SimplifiedPlanningPage.tsx to planningPage.tsx
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/SimplifiedPlanningPage.tsx" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/planningPage.tsx" ]; then
        echo "Renaming SimplifiedPlanningPage.tsx → planningPage.tsx"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/SimplifiedPlanningPage.tsx" "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/planningPage.tsx"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/frontend/src/pages/phases/planningPage.tsx"
    fi
fi

# Rename fix_cdo_assignments_v2.py to fix_cdo_assignments.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/utils/fix_cdo_assignments_v2.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/utils/fix_cdo_assignments.py" ]; then
        echo "Renaming fix_cdo_assignments_v2.py → fix_cdo_assignments.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/scripts/utils/fix_cdo_assignments_v2.py" "/Users/dineshpatel/code/projects/SynapseDTE/scripts/utils/fix_cdo_assignments.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/scripts/utils/fix_cdo_assignments.py"
    fi
fi

# Rename test_workflow_clean.py to test_workflow.py
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/testing/test_workflow_clean.py" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/testing/test_workflow.py" ]; then
        echo "Renaming test_workflow_clean.py → test_workflow.py"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/scripts/testing/test_workflow_clean.py" "/Users/dineshpatel/code/projects/SynapseDTE/scripts/testing/test_workflow.py"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/scripts/testing/test_workflow.py"
    fi
fi

# Rename start_backend_clean.sh to start_backend.sh
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/start_backend_clean.sh" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/start_backend.sh" ]; then
        echo "Renaming start_backend_clean.sh → start_backend.sh"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/start_backend_clean.sh" "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/start_backend.sh"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/start_backend.sh"
    fi
fi

# Rename restart_backend_clean.sh to restart_backend.sh
if [ -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/restart_backend_clean.sh" ]; then
    if [ ! -f "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/restart_backend.sh" ]; then
        echo "Renaming restart_backend_clean.sh → restart_backend.sh"
        mv "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/restart_backend_clean.sh" "/Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/restart_backend.sh"
    else
        echo "⚠️  Target already exists: /Users/dineshpatel/code/projects/SynapseDTE/scripts/infrastructure/restart_backend.sh"
    fi
fi

echo "File renaming complete!"
echo "Remember to update all imports after renaming."

import React, { lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import theme from './theme-enhanced';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { PermissionProvider } from './contexts/PermissionContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import { withLazyLoading } from './components/common/LazyComponent';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/common/Layout';
import SLAConfigurationPage from './pages/admin/SLAConfigurationPage';
import { LOBManagementPage } from './pages/admin/LOBManagementPage';
import { UserRole } from './types/api';
import RoleDashboardRouter from './components/dashboards/RoleDashboardRouter';

// Lazy load all pages for better performance
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));
const TestCyclesPage = React.lazy(() => import('./pages/TestCyclesPage'));
const ReportsPage = React.lazy(() => import('./pages/ReportsPage'));
const AnalyticsPage = React.lazy(() => import('./pages/AnalyticsPage'));
const UsersPage = React.lazy(() => import('./pages/UsersPage'));

// Phase pages
const PlanningPage = React.lazy(() => import('./pages/phases/PlanningPage'));
const DataProfilingEnhanced = React.lazy(() => import('./pages/phases/DataProfiling'));
const ScopingPage = React.lazy(() => import('./pages/phases/ScopingPage'));
const ReportOwnerScopingReview = React.lazy(() => import('./pages/phases/ReportOwnerScopingReview'));
const ReportOwnerDataProfilingReview = React.lazy(() => import('./pages/phases/ReportOwnerDataProfilingReview'));
const SampleSelectionPage = React.lazy(() => import('./pages/phases/SampleSelectionPage'));
const SampleReviewPage = React.lazy(() => import('./pages/phases/SampleReviewPage'));
const ReportOwnerSampleReview = React.lazy(() => import('./pages/phases/ReportOwnerSampleReview'));
const TestExecutionPage = React.lazy(() => import('./pages/phases/TestExecutionPage'));
// Removed - using ObservationManagementEnhanced instead
const ObservationManagementPage = React.lazy(() => import('./pages/phases/ObservationManagement'));
const TestReportPage = React.lazy(() => import('./pages/phases/TestReportPage'));
const DataOwnerPage = React.lazy(() => import('./pages/phases/DataOwnerPage'));
const DataExecutiveAssignmentsPage = React.lazy(() => import('./pages/phases/DataExecutiveAssignmentsPage'));
const DataExecutiveAssignmentInterface = React.lazy(() => import('./pages/phases/DataExecutiveAssignmentInterface'));
const RequestInfoPage = React.lazy(() => import('./pages/phases/NewRequestInfoPage'));

// Detailed pages
const CycleDetailPage = React.lazy(() => import('./pages/CycleDetailPage'));
// Removed - using ReportTestingPageRedesigned instead
const ReportTestingPage = React.lazy(() => import('./pages/ReportTestingPage'));

// Dashboard pages
const ReportOwnerDashboard = React.lazy(() => import('./pages/dashboards/ReportOwnerDashboard'));
const DataExecutiveDashboard = React.lazy(() => import('./pages/dashboards/DataExecutiveDashboard'));
const DataOwnerDashboard = React.lazy(() => import('./pages/dashboards/DataOwnerDashboard'));
const AdminDashboard = React.lazy(() => import('./pages/dashboards/AdminDashboard'));
const WorkflowMonitoringDashboard = React.lazy(() => import('./pages/WorkflowMonitoringDashboard'));

// Admin pages
const UserManagementPage = React.lazy(() => import('./pages/admin/UserManagementPage'));
const ReportManagementPage = React.lazy(() => import('./pages/admin/ReportManagementPage'));
const DataSourcesPage = React.lazy(() => import('./pages/admin/DataSourcesPage'));
const SystemSettingsPage = React.lazy(() => import('./pages/admin/SystemSettingsPage'));
const UserSettingsPage = React.lazy(() => import('./pages/UserSettingsPage'));
const RBACManagementPage = React.lazy(() => import('./pages/admin/RBACManagementPage'));

// Test Executive pages
const SLATrackingPage = React.lazy(() => import('./pages/SLATrackingPage'));
const TeamPerformancePage = React.lazy(() => import('./pages/TeamPerformancePage'));
const QualityMetricsPage = React.lazy(() => import('./pages/QualityMetricsPage'));

// Tester pages
const TesterAssignmentsPage = React.lazy(() => import('./pages/TesterAssignmentsPage'));
// Removed - using UniversalMyAssignmentsPage instead
const UniversalMyAssignmentsPage = React.lazy(() => import('./pages/UniversalMyAssignmentsPage'));
const AssignmentsPage = React.lazy(() => import('./pages/AssignmentsPage'));
const TesterDashboardEnhanced = React.lazy(() => import('./pages/dashboards/TesterDashboard'));
const BackgroundJobsPage = React.lazy(() => import('./pages/BackgroundJobsPage'));

// Document Management
const DocumentManagementPage = React.lazy(() => import('./pages/DocumentManagementPage'));

// Wrap components with lazy loading HOC
const LazyLoginPage = withLazyLoading(LoginPage, { loadingText: 'Loading login...' });
const LazyDashboardPage = withLazyLoading(DashboardPage, { loadingText: 'Loading dashboard...' });
const LazyTestCyclesPage = withLazyLoading(TestCyclesPage, { loadingText: 'Loading test cycles...' });
const LazyReportsPage = withLazyLoading(ReportsPage, { loadingText: 'Loading reports...' });
const LazyAnalyticsPage = withLazyLoading(AnalyticsPage, { loadingText: 'Loading analytics...' });
const LazyUsersPage = withLazyLoading(UsersPage, { loadingText: 'Loading users...' });

const LazyPlanningPage = withLazyLoading(PlanningPage, { loadingText: 'Loading planning phase...' });
const LazyDataProfilingEnhanced = withLazyLoading(DataProfilingEnhanced, { loadingText: 'Loading enhanced data profiling...' });
const LazyReportOwnerDataProfilingReview = withLazyLoading(ReportOwnerDataProfilingReview, { loadingText: 'Loading data profiling review...' });
const LazyScopingPage = withLazyLoading(ScopingPage, { loadingText: 'Loading scoping phase...' });
const LazyReportOwnerScopingReview = withLazyLoading(ReportOwnerScopingReview, { loadingText: 'Loading scoping review...' });
const LazySampleSelectionPage = withLazyLoading(SampleSelectionPage, { loadingText: 'Loading sample selection...' });
const LazySampleReviewPage = withLazyLoading(SampleReviewPage, { loadingText: 'Loading sample review...' });
const LazyReportOwnerSampleReview = withLazyLoading(ReportOwnerSampleReview, { loadingText: 'Loading report owner sample review...' });
const LazyTestExecutionPage = withLazyLoading(TestExecutionPage, { loadingText: 'Loading testing execution...' });
const LazyObservationManagementPage = withLazyLoading(ObservationManagementPage, { loadingText: 'Loading observation management...' });
const LazyTestReportPage = withLazyLoading(TestReportPage, { loadingText: 'Loading test report...' });
const LazyDataProviderPage = withLazyLoading(DataOwnerPage, { loadingText: 'Loading data provider...' });
const LazyDataExecutiveAssignmentsPage = withLazyLoading(DataExecutiveAssignmentsPage, { loadingText: 'Loading Data Executive assignments...' });
const LazyDataExecutiveAssignmentInterface = withLazyLoading(DataExecutiveAssignmentInterface, { loadingText: 'Loading Data Executive assignment interface...' });
const LazyRequestInfoPage = withLazyLoading(RequestInfoPage, { loadingText: 'Loading request info...' });

const LazyCycleDetailPage = withLazyLoading(CycleDetailPage, { loadingText: 'Loading cycle details...' });
const LazyReportTestingPage = withLazyLoading(ReportTestingPage, { loadingText: 'Loading report testing...' });
const LazyReportOwnerDashboard = withLazyLoading(ReportOwnerDashboard, { loadingText: 'Loading report owner dashboard...' });
const LazyDataExecutiveDashboard = withLazyLoading(DataExecutiveDashboard, { loadingText: 'Loading Data Executive dashboard...' });
const LazyDataProviderDashboard = withLazyLoading(DataOwnerDashboard, { loadingText: 'Loading data provider dashboard...' });
const LazyAdminDashboard = withLazyLoading(AdminDashboard, { loadingText: 'Loading admin dashboard...' });
const LazyWorkflowMonitoringDashboard = withLazyLoading(WorkflowMonitoringDashboard, { loadingText: 'Loading workflow monitoring...' });

const LazyUserManagementPage = withLazyLoading(UserManagementPage);
const LazyReportManagementPage = withLazyLoading(ReportManagementPage);
const LazyDataSourcesPage = withLazyLoading(DataSourcesPage);
const LazySystemSettingsPage = withLazyLoading(SystemSettingsPage);
const LazyUserSettingsPage = withLazyLoading(UserSettingsPage);
const LazyRBACManagementPage = withLazyLoading(RBACManagementPage);

const LazySLATrackingPage = withLazyLoading(SLATrackingPage);
const LazyTeamPerformancePage = withLazyLoading(TeamPerformancePage);
const LazyQualityMetricsPage = withLazyLoading(QualityMetricsPage);

const LazyTesterAssignmentsPage = withLazyLoading(TesterAssignmentsPage, { loadingText: 'Loading assignments...' });
// Removed - using UniversalMyAssignmentsPage instead
const LazyUniversalMyAssignmentsPage = withLazyLoading(UniversalMyAssignmentsPage, { loadingText: 'Loading my assignments...' });
const LazyAssignmentsPage = withLazyLoading(AssignmentsPage, { loadingText: 'Loading assignments...' });
const LazyTesterDashboardEnhanced = withLazyLoading(TesterDashboardEnhanced, { loadingText: 'Loading enhanced tester dashboard...' });
const LazyBackgroundJobsPage = withLazyLoading(BackgroundJobsPage, { loadingText: 'Loading background jobs...' });
const LazyDocumentManagementPage = withLazyLoading(DocumentManagementPage, { loadingText: 'Loading document management...' });

// Test page for Universal Assignments
const TestUniversalAssignments = React.lazy(() => import('./pages/TestUniversalAssignments'));
const LazyTestUniversalAssignments = withLazyLoading(TestUniversalAssignments, { loadingText: 'Loading test page...' });


// Wrapper component for PlanningPage to handle URL params
const PlanningPageWrapper: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  
  // Convert string params to numbers
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  return (
    <PlanningPage 
      cycleId={cycleIdNum} 
      reportId={reportIdNum} 
      reportName="Report" // We'll fetch this inside the component if needed
    />
  );
};

// Wrapper component for ScopingPage to handle URL params
const ScopingPageWrapper: React.FC = () => {
  return <LazyScopingPage />;
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AuthProvider>
            <PermissionProvider>
              <NotificationProvider>
                <Router>
                  <Routes>
                  <Route path="/login" element={<LazyLoginPage />} />
                  <Route
                    path="/*"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <ErrorBoundary>
                            <Routes>
                              <Route path="/" element={<RoleDashboardRouter />} />
                              <Route path="/dashboard" element={<RoleDashboardRouter />} />
                              
                              {/* Management Pages */}
                              <Route path="/cycles" element={<LazyTestCyclesPage />} />
                              <Route path="/cycles/new" element={<LazyTestCyclesPage />} />
                              <Route path="/cycles/:cycleId" element={<LazyCycleDetailPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId" element={<LazyReportTestingPage />} />
                              <Route path="/reports" element={<LazyReportsPage />} />
                              <Route path="/analytics" element={<LazyAnalyticsPage />} />
                              <Route path="/settings" element={<LazyUserSettingsPage />} />
                              <Route path="/users" element={<LazyUsersPage />} />
                              
                              {/* Workflow Phase Pages */}
                              <Route path="/cycles/:cycleId/reports/:reportId/planning" element={<PlanningPageWrapper />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/data-profiling" element={<LazyDataProfilingEnhanced />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/data-profiling-review" element={<LazyReportOwnerDataProfilingReview />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/scoping" element={<LazyScopingPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/scoping-review" element={<LazyReportOwnerScopingReview />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/sample-selection" element={<LazySampleSelectionPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/sample-review/:setId" element={<LazyReportOwnerSampleReview />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/data-owner" element={<LazyDataProviderPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/data-provider-id" element={<Navigate to="../data-owner" replace />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/data-executive-assignments" element={<LazyDataExecutiveAssignmentsPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/assign-data-owners" element={<LazyDataExecutiveAssignmentInterface />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/request-info" element={<LazyRequestInfoPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/test-execution" element={<LazyTestExecutionPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/observation-management" element={<LazyObservationManagementPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/test-report" element={<LazyTestReportPage />} />
                              <Route path="/cycles/:cycleId/reports/:reportId/finalize-report" element={<LazyTestReportPage />} />
                              
                              {/* Legacy Phase Routes (keep for backwards compatibility) */}
                              <Route path="/phases/data-profiling" element={<LazyDataProfilingEnhanced />} />
                              <Route path="/phases/data-owner" element={<LazyDataProviderPage />} />
                              <Route path="/phases/sample-selection" element={<LazySampleSelectionPage />} />
                              <Route path="/phases/request-info" element={<LazyRequestInfoPage />} />
                              <Route path="/phases/test-execution" element={<LazyTestExecutionPage />} />
                              <Route path="/phases/observation-management" element={<LazyObservationManagementPage />} />

                              {/* Admin Routes */}
                              <Route path="/admin/users" element={<LazyUserManagementPage />} />
                              <Route path="/admin/lobs" element={<LOBManagementPage />} />
                              <Route path="/admin/reports" element={<LazyReportManagementPage />} />
                              <Route path="/admin/data-sources" element={<LazyDataSourcesPage />} />
                              <Route path="/admin/sla-configuration" element={<SLAConfigurationPage />} />
                              <Route path="/admin/rbac" element={<LazyRBACManagementPage />} />
                              <Route path="/admin/settings" element={<LazySystemSettingsPage />} />

                              {/* Dashboards */}
                              <Route path="/report-owner-dashboard" element={<LazyReportOwnerDashboard />} />
                              <Route path="/data-executive-dashboard" element={<LazyDataExecutiveDashboard />} />
                              <Route path="/data-owner-dashboard" element={<LazyDataProviderDashboard />} />
                              <Route path="/admin-dashboard" element={<LazyAdminDashboard />} />
                              <Route path="/workflow-monitoring" element={<LazyWorkflowMonitoringDashboard />} />
                              
                              {/* Tester Pages */}
                              <Route path="/tester/assignments" element={<LazyTesterAssignmentsPage />} />
                              <Route path="/my-assignments" element={<LazyUniversalMyAssignmentsPage />} />
                              <Route path="/assignments" element={<LazyAssignmentsPage />} />
                              <Route path="/tester-dashboard-enhanced" element={<LazyTesterDashboardEnhanced />} />
                              <Route path="/test-universal-assignments" element={<LazyTestUniversalAssignments />} />
                              <Route path="/background-jobs" element={<LazyBackgroundJobsPage />} />
                              
                              {/* Document Management */}
                              <Route path="/documents" element={<LazyDocumentManagementPage />} />
                              
                              {/* Test Executive Pages */}
                              <Route path="/sla-tracking" element={<LazySLATrackingPage />} />
                              <Route path="/team-performance" element={<LazyTeamPerformancePage />} />
                              <Route path="/quality-metrics" element={<LazyQualityMetricsPage />} />
                            </Routes>
                          </ErrorBoundary>
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Router>
            </NotificationProvider>
          </PermissionProvider>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;

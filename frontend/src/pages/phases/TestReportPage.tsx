import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  FormGroup,
  Container,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Assessment as AssessmentIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Visibility as VisibilityIcon,
  Timeline as TimelineIcon,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  PlayArrow as PlayArrowIcon,
  Task as TaskIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../api/client';
import { usePhaseStatus } from '../../hooks/useUnifiedStatus';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import ApprovalWorkflow from '../../components/test-report/ApprovalWorkflow';
import ComprehensiveReportDisplay from '../../components/test-report/ComprehensiveReportDisplay';

interface TestReportPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  started_at: string;
  completed_at?: string;
  include_executive_summary: boolean;
  include_phase_artifacts: boolean;
  include_detailed_observations: boolean;
  include_metrics_dashboard: boolean;
  report_title: string;
  report_period: string;
  regulatory_references: string[];
  final_report_document_id?: number;
  report_generated_at?: string;
  report_approved_by?: string[];
  status: string;
  // New metrics fields
  total_attributes?: number;
  scoped_attributes?: number;
  total_samples?: number;
  completed_test_cases?: number;
  finalized_observations?: number;
}

interface ReportSection {
  section_id: number;
  section_name: string;
  section_order: number;
  section_type: string;
  content_text?: string;
  content_data?: any;
  artifacts?: any[];
  metrics_summary?: any;
}

interface ReportInfo {
  report_id: number;
  report_name: string;
  lob_name: string;
  tester_name?: string;
  report_owner_name?: string;
  description?: string;
  regulatory_framework?: string;
  frequency?: string;
  due_date?: string;
  priority?: string;
}

interface ReportData {
  metadata: {
    cycle_name: string;
    cycle_year: number;
    cycle_quarter: number;
    report_name: string;
    report_type: string;
    regulatory_requirement: string;
    phases_completed: string[];
    test_period: string;
    generation_date: string;
  };
  executive_summary?: {
    total_attributes_tested: number;
    total_test_cases: number;
    test_execution_rate: number;
    total_observations: number;
    high_risk_observations: number;
    medium_risk_observations: number;
    low_risk_observations: number;
    key_findings: string[];
  };
  phase_artifacts?: any;
  phase_details?: any;
  observations?: any;
  metrics?: {
    coverage_metrics: any;
    efficiency_metrics: any;
    quality_metrics: any;
    timeline_metrics: any;
  };
  formatted_report?: {
    pdf_data_url?: string;
    [key: string]: any;
  };
}

const TestReportPage: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Parse IDs
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  // Unified status system
  const { data: unifiedPhaseStatus, refetch: refetchPhaseStatus } = usePhaseStatus('Finalize Test Report', cycleIdNum, reportIdNum);
  
  // Universal Assignments integration
  const {
    assignments,
    isLoading: assignmentsLoading,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
  } = useUniversalAssignments({
    phase: 'Finalize Test Report',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
  });

  const [loading, setLoading] = useState(true);
  const [reportPhase, setReportPhase] = useState<TestReportPhase | null>(null);
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [reportSections, setReportSections] = useState<ReportSection[]>([]);
  const [selectedTab, setSelectedTab] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [previewDialog, setPreviewDialog] = useState(false);
  const [approvalDialog, setApprovalDialog] = useState(false);
  const [phaseStarted, setPhaseStarted] = useState(false);
  const [comprehensiveReportData, setComprehensiveReportData] = useState(null);
  const [loadingComprehensive, setLoadingComprehensive] = useState(false);
  
  // Helper functions to extract data from sections
  const extractExecutiveSummary = (sections: any[]) => {
    const summarySection = sections.find(s => s.section_name === 'executive_summary');
    if (!summarySection) return null;
    
    const content = summarySection.section_content || {};
    return {
      total_attributes_tested: content.metrics?.total_attributes || 0,
      total_test_cases: content.metrics?.total_test_cases || 0,
      test_execution_rate: content.metrics?.test_pass_rate || 0,
      total_observations: content.metrics?.total_observations || 0,
      high_risk_observations: content.metrics?.critical_observations || 0,
      medium_risk_observations: 0,
      low_risk_observations: 0,
      key_findings: content.key_findings || []
    };
  };
  
  const extractPhaseArtifacts = (sections: any[]) => {
    const phaseSection = sections.find(s => s.section_name === 'phase_analysis');
    if (!phaseSection) return null;
    
    return phaseSection.section_content || {};
  };
  
  const extractObservations = (sections: any[]) => {
    const observationSection = sections.find(s => s.section_name === 'testing_results');
    if (!observationSection) return null;
    
    const content = observationSection.section_content || {};
    return {
      total_observations: content.observation_summary?.total_observations || 0,
      by_rating: content.observation_summary?.by_severity || {},
      details: []
    };
  };
  
  const extractMetrics = (sections: any[]) => {
    const metricsSection = sections.find(s => s.section_name === 'testing_coverage');
    if (!metricsSection) return null;
    
    const content = metricsSection.section_content || {};
    return {
      coverage_metrics: content.coverage_metrics || {},
      efficiency_metrics: content.efficiency_metrics || {},
      quality_metrics: content.quality_metrics || {},
      timeline_metrics: content.timeline_metrics || {}
    };
  };
  
  // Report configuration
  const [reportConfig, setReportConfig] = useState({
    include_executive_summary: true,
    include_phase_artifacts: true,
    include_detailed_observations: true,
    include_metrics_dashboard: true,
  });

  useEffect(() => {
    fetchReportData();
    // Try to fetch comprehensive report data if it exists
    fetchComprehensiveReportData();
  }, [cycleId, reportId]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      console.log('Fetching report data for cycle:', cycleId, 'report:', reportId);
      
      // Get basic report info
      try {
        const reportInfoResponse = await apiClient.get(`/cycle-reports/${cycleId}/reports/${reportId}`);
        setReportInfo(reportInfoResponse.data);
      } catch (error) {
        console.error('Error fetching report info:', error);
      }
      
      // Get report phase configuration using unified API
      const phaseResponse = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/phase`
      );
      console.log('Phase response:', phaseResponse.data);
      setReportPhase({
        ...phaseResponse.data,
        started_at: phaseResponse.data.started_at,
        report_generated_at: phaseResponse.data.generation_status?.completed_at
      });
      setPhaseStarted(phaseResponse.data?.started_at ? true : false);
      
      // Get report sections if report has been generated
      if (phaseResponse.data.generation_status?.status === 'completed') {
        console.log('Report was generated at:', phaseResponse.data.generation_status.completed_at);
        const sectionsResponse = await apiClient.get(
          `/test-report/${cycleId}/reports/${reportId}/sections`
        );
        console.log('Sections count:', sectionsResponse.data.length);
        setReportSections(sectionsResponse.data);
        
        // Transform sections into report data format for compatibility
        const reportData = {
          metadata: {
            cycle_name: `Cycle ${cycleId}`,
            cycle_year: new Date().getFullYear(),
            cycle_quarter: Math.ceil((new Date().getMonth() + 1) / 3),
            report_name: reportInfo?.report_name || 'Test Report',
            report_type: 'Finalized Test Report',
            regulatory_requirement: reportInfo?.regulatory_framework || 'N/A',
            phases_completed: [],
            test_period: phaseResponse.data.generation_status?.started_at || '',
            generation_date: phaseResponse.data.generation_status?.completed_at || ''
          },
          executive_summary: extractExecutiveSummary(sectionsResponse.data) || undefined,
          phase_artifacts: extractPhaseArtifacts(sectionsResponse.data),
          observations: extractObservations(sectionsResponse.data),
          metrics: extractMetrics(sectionsResponse.data) || undefined
        };
        setReportData(reportData);
      } else {
        console.log('Report not yet generated');
      }
      
      // Update config from phase data
      if (phaseResponse.data) {
        setReportConfig({
          include_executive_summary: phaseResponse.data.include_executive_summary,
          include_phase_artifacts: phaseResponse.data.include_phase_artifacts,
          include_detailed_observations: phaseResponse.data.include_detailed_observations,
          include_metrics_dashboard: phaseResponse.data.include_metrics_dashboard,
        });
      }
    } catch (error: any) {
      console.error('Error fetching report data:', error);
      if (error?.response) {
        console.error('Error response:', error.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      console.log('Starting report generation for cycle:', cycleId, 'report:', reportId);
      
      // Generate the report using unified API
      console.log('Generating report...');
      const response = await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/generate`,
        {
          sections: reportConfig.include_executive_summary ? ['executive_summary', 'strategic_approach', 'testing_coverage', 'phase_analysis', 'testing_results', 'value_delivery', 'recommendations', 'executive_attestation'] : undefined,
          force_refresh: false
        }
      );
      
      console.log('Report generated successfully:', response.data);
      await fetchReportData(); // Refresh all data including sections
    } catch (error: any) {
      console.error('Error generating report:', error);
      // Show error to user
      if (error?.response) {
        console.error('Error response:', error.response.data);
        alert(`Error: ${error.response.data.detail || 'Failed to generate report'}`);
      } else {
        alert('Failed to generate report. Please check console for details.');
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateComprehensiveReport = async () => {
    try {
      setLoadingComprehensive(true);
      console.log('Starting comprehensive report generation for cycle:', cycleId, 'report:', reportId);
      
      // Generate comprehensive report
      const response = await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/generate-comprehensive`,
        {
          sections: undefined, // Generate all sections
          force_refresh: false
        }
      );
      
      console.log('Comprehensive report generated successfully:', response.data);
      
      // Fetch comprehensive report data for display
      await fetchComprehensiveReportData();
      
    } catch (error: any) {
      console.error('Error generating comprehensive report:', error);
      if (error?.response) {
        console.error('Error response:', error.response.data);
        alert(`Error: ${error.response.data.detail || 'Failed to generate comprehensive report'}`);
      } else {
        alert('Failed to generate comprehensive report. Please check console for details.');
      }
    } finally {
      setLoadingComprehensive(false);
    }
  };

  const fetchComprehensiveReportData = async () => {
    try {
      setLoadingComprehensive(true);
      console.log('Fetching comprehensive report data for cycle:', cycleId, 'report:', reportId);
      
      const response = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/comprehensive-data`
      );
      
      console.log('Comprehensive report data fetched:', response.data);
      setComprehensiveReportData(response.data);
      
    } catch (error: any) {
      console.error('Error fetching comprehensive report data:', error);
      // Don't show error if data doesn't exist yet
      if (error?.response?.status !== 404) {
        console.error('Error response:', error.response?.data);
      }
    } finally {
      setLoadingComprehensive(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const response = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/download?format=pdf`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Test_Report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const handleDownloadComprehensivePDF = async () => {
    try {
      const response = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/download-pdf`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Comprehensive_Test_Report_${cycleId}_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading comprehensive PDF:', error);
      alert('Error downloading PDF. Please try again.');
    }
  };

  const handlePrintReport = () => {
    window.print();
  };

  const handleEmailReport = () => {
    // Placeholder for email functionality
    alert('Email functionality will be implemented in future release');
  };

  const handleStartPhase = async () => {
    try {
      await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/start`
      );
      setPhaseStarted(true);
      await fetchReportData();
    } catch (error) {
      console.error('Error starting phase:', error);
    }
  };

  const handleCompletePhase = async () => {
    try {
      await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/complete`
      );
      await fetchReportData();
    } catch (error) {
      console.error('Error completing phase:', error);
    }
  };

  const handleApproveReport = async () => {
    try {
      // Get all sections and approve each one
      const sectionsResponse = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/sections`
      );
      
      // Approve each section at executive level
      for (const section of sectionsResponse.data) {
        if (!section.is_fully_approved) {
          await apiClient.post(
            `/test-report/${cycleId}/reports/${reportId}/sections/${section.id}/approve`,
            {
              approval_level: 'executive',
              notes: 'Approved by executive reviewer'
            }
          );
        }
      }
      
      setApprovalDialog(false);
      await fetchReportData();
    } catch (error) {
      console.error('Error approving report:', error);
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleIdNum,
        report_id: reportIdNum,
        phase_name: 'Finalize Test Report'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      console.log(message);
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycleIdNum,
            report_id: reportIdNum,
            phase_name: 'Finalize Test Report'
          });
          console.log(`${activity.name} completed`);
        } catch (completeError: any) {
          // Ignore "already completed" errors

          if (completeError.response?.status === 400 && 

              completeError.response?.data?.detail?.includes('Cannot complete activity in status')) {

            console.log('Phase start activity already completed, ignoring error');

          } else {

            console.error('Error auto-completing phase_start activity:', completeError);

          }
        }
      }
      
      // Add a small delay to ensure backend has processed the change
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh status
      refetchPhaseStatus();
      
      // Handle special activity types after generic processing
      if (activity.activity_id === 'generate_report' && action === 'start') {
        await handleGenerateReport();
      } else if (activity.activity_id === 'approve_report' && action === 'start') {
        setApprovalDialog(true);
      }
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      alert(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };

  const renderExecutiveSummary = () => {
    if (!reportData?.executive_summary) return null;

    const summary = reportData.executive_summary;

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Executive Summary
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                <Typography variant="h4">{summary.total_attributes_tested}</Typography>
                <Typography variant="body2">Attributes Tested</Typography>
              </Paper>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
                <Typography variant="h4">{summary.test_execution_rate.toFixed(1)}%</Typography>
                <Typography variant="body2">Test Execution Rate</Typography>
              </Paper>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                <Typography variant="h4">{summary.total_observations}</Typography>
                <Typography variant="body2">Total Observations</Typography>
              </Paper>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
                <Typography variant="h4">{summary.high_risk_observations}</Typography>
                <Typography variant="body2">High Risk Observations</Typography>
              </Paper>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="subtitle1" gutterBottom>
            Key Findings
          </Typography>
          <List dense>
            {summary.key_findings.map((finding, index) => (
              <ListItem key={index}>
                <ListItemText primary={finding} />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    );
  };

  const renderPhaseArtifacts = () => {
    // Check for both phase_artifacts and phase_details
    const phaseDetails = reportData?.phase_details || {};
    const phaseArtifacts = reportData?.phase_artifacts || {};
    
    if (Object.keys(phaseDetails).length === 0 && Object.keys(phaseArtifacts).length === 0) {
      return null;
    }

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Comprehensive Phase Analysis
          </Typography>
          
          {/* Planning Phase */}
          {phaseDetails.planning && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Planning Phase</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ p: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    {phaseDetails.planning.total_attributes} total attributes analyzed:
                    {' '}{phaseDetails.planning.cde_attributes} CDEs,
                    {' '}{phaseDetails.planning.pk_attributes} Primary Keys,
                    {' '}{phaseDetails.planning.historical_issues_attributes} with historical issues.
                    {' '}{phaseDetails.planning.approved_attributes} approved for testing.
                  </Typography>
                  
                  {phaseDetails.planning.attributes?.length > 0 && (
                    <Box sx={{ mt: 2, overflowX: 'auto' }}>
                      <Typography variant="subtitle2" gutterBottom>All Attributes ({phaseDetails.planning.attributes.length})</Typography>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Line #</TableCell>
                            <TableCell>Attribute Name</TableCell>
                            <TableCell>Description</TableCell>
                            <TableCell>MDRM</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Badges</TableCell>
                            <TableCell>Status</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {phaseDetails.planning.attributes.map((attr: any, idx: number) => (
                            <TableRow key={idx}>
                              <TableCell>{attr.line_item_number}</TableCell>
                              <TableCell>{attr.attribute_name}</TableCell>
                              <TableCell>{attr.description?.substring(0, 50)}...</TableCell>
                              <TableCell>{attr.mdrm || '-'}</TableCell>
                              <TableCell>{attr.mandatory_flag ? 'M' : 'O'}</TableCell>
                              <TableCell>
                                {attr.cde_flag && <Chip size="small" label="CDE" color="primary" />}
                                {attr.is_primary_key && <Chip size="small" label="PK" color="secondary" />}
                                {attr.historical_issues_flag && <Chip size="small" label="Issues" color="warning" />}
                              </TableCell>
                              <TableCell>{attr.approval_status}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      {phaseDetails.planning.attributes.length > 0 && (
                        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                          Showing all {phaseDetails.planning.attributes.length} attributes
                        </Typography>
                      )}
                    </Box>
                  )}
                  
                  {phaseDetails.planning.execution_time && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2">Execution Time</Typography>
                      <Typography variant="body2">
                        Total: {phaseDetails.planning.execution_time.total_days} days ({phaseDetails.planning.execution_time.total_hours} hours)
                      </Typography>
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
          
          {/* Data Profiling Phase */}
          {phaseDetails.data_profiling && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Data Profiling Phase</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ p: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    Generated {phaseDetails.data_profiling.rules_generated} rules,
                    {' '}{phaseDetails.data_profiling.rules_approved} approved for execution.
                  </Typography>
                  
                  {phaseDetails.data_profiling.approved_rules?.length > 0 && (
                    <Box sx={{ mt: 2, overflowX: 'auto' }}>
                      <Typography variant="subtitle2" gutterBottom>Approved Rules</Typography>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Rule Name</TableCell>
                            <TableCell>Attribute</TableCell>
                            <TableCell>DQ Dimension</TableCell>
                            <TableCell>Description</TableCell>
                            <TableCell>Expected Result</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {phaseDetails.data_profiling.approved_rules.map((rule: any, idx: number) => (
                            <TableRow key={idx}>
                              <TableCell>{rule.rule_name}</TableCell>
                              <TableCell>{rule.attribute_name}</TableCell>
                              <TableCell>{rule.dq_dimension}</TableCell>
                              <TableCell>{rule.rule_description}</TableCell>
                              <TableCell>{rule.expected_result}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
          
          {/* Scoping Phase */}
          {phaseDetails.scoping && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Scoping Phase</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ p: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    From {phaseDetails.scoping.non_pk_attributes_total} non-PK attributes,
                    {' '}{phaseDetails.scoping.attributes_submitted_by_tester} selected for testing
                    {' '}({((phaseDetails.scoping.attributes_submitted_by_tester / phaseDetails.scoping.non_pk_attributes_total) * 100).toFixed(2)}% coverage).
                  </Typography>
                  
                  {phaseDetails.scoping.approved_attributes?.length > 0 && (
                    <Box sx={{ mt: 2, overflowX: 'auto' }}>
                      <Typography variant="subtitle2" gutterBottom>Selected Attributes for Testing</Typography>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Line #</TableCell>
                            <TableCell>Attribute Name</TableCell>
                            <TableCell>Risk Score</TableCell>
                            <TableCell>Data Type</TableCell>
                            <TableCell>Risk Rationale</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {phaseDetails.scoping.approved_attributes.map((attr: any, idx: number) => (
                            <TableRow key={idx}>
                              <TableCell>{attr.line_item_number}</TableCell>
                              <TableCell>{attr.attribute_name}</TableCell>
                              <TableCell>
                                <Chip 
                                  size="small" 
                                  label={attr.risk_score || 0} 
                                  color={attr.risk_score > 7 ? 'error' : attr.risk_score > 4 ? 'warning' : 'default'}
                                />
                              </TableCell>
                              <TableCell>{attr.data_type}</TableCell>
                              <TableCell>{attr.llm_risk_rationale?.substring(0, 100)}...</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
          
          {/* Other phases from phase_artifacts for backward compatibility */}
          {Object.entries(phaseArtifacts).map(([phase, artifacts]: [string, any]) => {
            // Skip phases already handled by phase_details
            if (['planning', 'data_profiling', 'scoping'].includes(phase)) return null;
            
            return (
              <Accordion key={phase} defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                    {phase.replace('_', ' ')} Phase
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ p: 2 }}>
                    <Typography variant="body1" gutterBottom color="text.secondary">
                      {artifacts.summary}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mt: 2 }}>
                      {phase === 'testing' && (
                        <>
                          <Box>
                            <Typography variant="h4" color="primary.main">{artifacts.execution_count}</Typography>
                            <Typography variant="body2" color="text.secondary">Test Cases Executed</Typography>
                          </Box>
                        </>
                      )}
                      
                      {phase === 'observations' && (
                        <>
                          <Box>
                            <Typography variant="h4" color={artifacts.observation_count > 0 ? "warning.main" : "success.main"}>
                              {artifacts.observation_count}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">Observations Found</Typography>
                          </Box>
                        </>
                      )}
                    </Box>
                  </Box>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </CardContent>
      </Card>
    );
  };

  const renderObservations = () => {
    if (!reportData?.observations) return null;

    const observations = reportData.observations;

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detailed Observations
          </Typography>
          
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4">{observations.total_observations}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Observations
                  </Typography>
                </Paper>
              </Box>
              <Box sx={{ flex: '2 1 600px', minWidth: 0 }}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>By Rating</Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    {Object.entries(observations.by_rating).map(([rating, items]: [string, any]) => (
                      <Chip
                        key={rating}
                        label={`${rating}: ${items.length}`}
                        color={
                          rating === 'High' ? 'error' :
                          rating === 'Medium' ? 'warning' :
                          'info'
                        }
                      />
                    ))}
                  </Box>
                </Paper>
              </Box>
            </Box>
          </Box>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Attribute</TableCell>
                <TableCell>Issue Type</TableCell>
                <TableCell>Rating</TableCell>
                <TableCell>Test Cases</TableCell>
                <TableCell>Samples</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {observations.details?.map((obs: any) => (
                <TableRow key={obs.group_id}>
                  <TableCell>{obs.attribute_name}</TableCell>
                  <TableCell>{obs.issue_type}</TableCell>
                  <TableCell>
                    <Chip
                      label={obs.rating}
                      size="small"
                      color={
                        obs.rating === 'High' ? 'error' :
                        obs.rating === 'Medium' ? 'warning' :
                        'info'
                      }
                    />
                  </TableCell>
                  <TableCell>{obs.total_test_cases}</TableCell>
                  <TableCell>{obs.total_samples}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
  };

  const renderMetricsDashboard = () => {
    if (!reportData?.metrics) return null;

    const metrics = reportData.metrics;

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Metrics Dashboard
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            {/* Coverage Metrics */}
            <Box sx={{ flex: '1 1 400px', minWidth: 0 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PieChartIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle1">Coverage Metrics</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Attribute Coverage
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={metrics.coverage_metrics.attribute_coverage} 
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.coverage_metrics.attribute_coverage.toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Sample Coverage
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={metrics.coverage_metrics.sample_coverage} 
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.coverage_metrics.sample_coverage.toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* Efficiency Metrics */}
            <Box sx={{ flex: '1 1 400px', minWidth: 0 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrendingUpIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle1">Efficiency Metrics</Typography>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 50%', minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      Avg Test Time
                    </Typography>
                    <Typography variant="h6">
                      {metrics.efficiency_metrics.average_test_execution_time.toFixed(1)} min
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 50%', minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Duration
                    </Typography>
                    <Typography variant="h6">
                      {metrics.efficiency_metrics.total_testing_duration_days} days
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* Quality Metrics */}
            <Box sx={{ width: '100%' }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <BarChartIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle1">Quality Metrics</Typography>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      Pass Rate
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {metrics.quality_metrics.test_pass_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      Fail Rate
                    </Typography>
                    <Typography variant="h6" color="error.main">
                      {metrics.quality_metrics.test_fail_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Tests
                    </Typography>
                    <Typography variant="h6">
                      {metrics.quality_metrics.total_tests_executed}
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      Document Revisions
                    </Typography>
                    <Typography variant="h6">
                      {metrics.efficiency_metrics.document_revision_count}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  };


  const renderFormattedSections = () => {
    // Check if we have formatted report data from the API
    if (reportData?.formatted_report) {
      return (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Comprehensive Test Report
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadReport}
                >
                  Download PDF
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<PrintIcon />}
                  onClick={() => window.print()}
                >
                  Print
                </Button>
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ p: 3 }}>
              {/* Display formatted report content */}
              {Object.entries(reportData.formatted_report).map(([key, value]) => (
                <Box key={key} sx={{ mb: 4 }}>
                  <Typography variant="h5" gutterBottom sx={{ textTransform: 'capitalize' }}>
                    {key.replace(/_/g, ' ')}
                  </Typography>
                  <Typography variant="body1" component="div">
                    {typeof value === 'object' ? (
                      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    ) : (
                      value
                    )}
                  </Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      );
    }
    
    if (!reportSections || reportSections.length === 0) return null;

    // Find markdown or HTML section for rich display
    const markdownSection = reportSections.find(s => s.section_type === 'markdown');
    const htmlSection = reportSections.find(s => s.section_type === 'html');
    
    if (htmlSection?.content_text) {
      return (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Comprehensive Test Report
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadReport}
                >
                  Download PDF
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<PrintIcon />}
                  onClick={() => window.print()}
                >
                  Print
                </Button>
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Box
              dangerouslySetInnerHTML={{ __html: htmlSection.content_text }}
              sx={{
                '& h1, & h2, & h3': { 
                  color: 'primary.main',
                  mt: 3,
                  mb: 2
                },
                '& p': { mb: 2 },
                '& ul, & ol': { mb: 2 },
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                  mb: 3,
                  '& th, & td': {
                    border: '1px solid #ddd',
                    padding: '8px',
                    textAlign: 'left'
                  },
                  '& th': {
                    backgroundColor: '#f5f5f5',
                    fontWeight: 'bold'
                  }
                }
              }}
            />
          </CardContent>
        </Card>
      );
    }
    
    // Fallback to structured sections
    return (
      <Box sx={{ mb: 3 }}>
        {reportSections
          .filter(s => s.section_type !== 'markdown' && s.section_type !== 'html')
          .sort((a, b) => a.section_order - b.section_order)
          .map((section) => (
            <Accordion key={section.section_id} defaultExpanded={section.section_order <= 3}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">{section.section_name}</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {section.content_data ? (
                  <Box>
                    {renderSectionContent(section)}
                  </Box>
                ) : (
                  <Typography>{section.content_text || 'No content available'}</Typography>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
      </Box>
    );
  };

  const renderSectionContent = (section: ReportSection) => {
    try {
      const data = typeof section.content_data === 'string' 
        ? JSON.parse(section.content_data) 
        : section.content_data;
      
      // Render based on section type
      switch (section.section_type) {
        case 'summary':
          return renderFormattedExecutiveSummary(data);
        case 'coverage':
          return renderFormattedCoverage(data);
        case 'results':
          return renderFormattedResults(data);
        case 'attestation':
          return renderFormattedAttestation(data);
        default:
          return <pre>{JSON.stringify(data, null, 2)}</pre>;
      }
    } catch (e) {
      return <Typography>{section.content_text || 'Unable to parse content'}</Typography>;
    }
  };

  const renderFormattedExecutiveSummary = (data: any) => (
    <Box>
      <Typography variant="body1" paragraph>{data.overview}</Typography>
      {data.key_achievements && (
        <>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Key Achievements
          </Typography>
          <List>
            {data.key_achievements.map((achievement: string, idx: number) => (
              <ListItem key={idx}>
                <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                <ListItemText primary={achievement} />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Box>
  );

  const renderFormattedCoverage = (data: any) => (
    <Box>
      <Typography variant="body1" paragraph>{data.coverage_narrative}</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
        <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary">{data.coverage_percentage}%</Typography>
            <Typography variant="body2">Coverage</Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">{data.risk_coverage_percentage}%</Typography>
            <Typography variant="body2">Risk Coverage</Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 200px', minWidth: 0 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="info.main">{data.materiality_coverage_percentage}%</Typography>
            <Typography variant="body2">Materiality Coverage</Typography>
          </Paper>
        </Box>
      </Box>
    </Box>
  );

  const renderFormattedResults = (data: any) => (
    <Box>
      {data.quality_achievements && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body1" paragraph>
            {data.quality_achievements.description}
          </Typography>
          {data.quality_achievements.metrics && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              {Object.entries(data.quality_achievements.metrics).map(([key, value]) => (
                <Box sx={{ flex: '1 1 200px', minWidth: 0 }} key={key}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="body2" color="text.secondary">{key}</Typography>
                    <Typography variant="h6">{value as string}</Typography>
                  </Paper>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );

  const renderFormattedAttestation = (data: any) => (
    <Box>
      <Typography variant="h6" gutterBottom>{data.type}</Typography>
      <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }} paragraph>
        {data.text}
      </Typography>
      {data.signatories && (
        <Box sx={{ mt: 3 }}>
          {data.signatories.map((signatory: any, idx: number) => (
            <Box key={idx} sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">{signatory.role}</Typography>
              <Typography variant="body1">{signatory.name}</Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );


  const renderConfiguration = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Report Configuration
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Select which sections to include in the final test report
        </Typography>
        
        <FormGroup>
          <FormControlLabel
            control={
              <Switch
                checked={reportConfig.include_executive_summary}
                onChange={(e) => setReportConfig({ 
                  ...reportConfig, 
                  include_executive_summary: e.target.checked 
                })}
              />
            }
            label="Executive Summary"
          />
          <FormControlLabel
            control={
              <Switch
                checked={reportConfig.include_phase_artifacts}
                onChange={(e) => setReportConfig({ 
                  ...reportConfig, 
                  include_phase_artifacts: e.target.checked 
                })}
              />
            }
            label="Phase Artifacts and Results"
          />
          <FormControlLabel
            control={
              <Switch
                checked={reportConfig.include_detailed_observations}
                onChange={(e) => setReportConfig({ 
                  ...reportConfig, 
                  include_detailed_observations: e.target.checked 
                })}
              />
            }
            label="Detailed Observations"
          />
          <FormControlLabel
            control={
              <Switch
                checked={reportConfig.include_metrics_dashboard}
                onChange={(e) => setReportConfig({ 
                  ...reportConfig, 
                  include_metrics_dashboard: e.target.checked 
                })}
              />
            }
            label="Metrics Dashboard"
          />
        </FormGroup>

        <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGenerateReport}
            disabled={generating}
            startIcon={generating ? <CircularProgress size={20} /> : <AssessmentIcon />}
          >
            {generating ? 'Generating...' : 'Generate Standard Report'}
          </Button>
          
          <Button
            variant="contained"
            color="secondary"
            onClick={handleGenerateComprehensiveReport}
            disabled={loadingComprehensive}
            startIcon={loadingComprehensive ? <CircularProgress size={20} /> : <AssessmentIcon />}
          >
            {loadingComprehensive ? 'Generating...' : 'Generate Comprehensive Report'}
          </Button>
          
          {reportData && (
            <Button
              variant="outlined"
              onClick={() => setPreviewDialog(true)}
              startIcon={<VisibilityIcon />}
            >
              Preview
            </Button>
          )}

          {comprehensiveReportData && (
            <Button
              variant="outlined"
              onClick={handleDownloadComprehensivePDF}
              startIcon={<DownloadIcon />}
            >
              Download Comprehensive PDF
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 3 }}>
      {/* Universal Assignments Alert */}
      {assignments.length > 0 && assignments[0] && (
        <UniversalAssignmentAlert
          assignment={assignments[0]}
          onAcknowledge={acknowledgeAssignment}
          onStart={startAssignment}
          onComplete={completeAssignment}
        />
      )}
      
      {/* Report Metadata Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase info */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AssignmentIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Finalize Test Report Phase - Generate and approve final testing report
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BusinessIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">LOB:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.lob_name || 'Unknown'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Tester:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.tester_name || 'Not assigned'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Owner:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.report_owner_name || 'Not specified'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary">ID:</Typography>
                <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                  {reportId}
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {reportPhase?.report_approved_by && reportPhase.report_approved_by.length > 0 && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Report approved by: {reportPhase.report_approved_by.join(', ')}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 3 }}>
        {reportPhase?.final_report_document_id && (
          <>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadReport}
            >
              Download PDF
            </Button>
            <Button
              variant="outlined"
              startIcon={<PrintIcon />}
              onClick={() => window.print()}
            >
              Print
            </Button>
            <Button
              variant="outlined"
              startIcon={<EmailIcon />}
            >
              Email
            </Button>
          </>
        )}
      </Box>

      {/* Row 1: Six Key Metrics */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
        <Box sx={{ flex: '1 1 0', minWidth: 150 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {reportPhase?.total_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                Total Attributes
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 0', minWidth: 150 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {reportPhase?.scoped_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                Scoped Attributes
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 0', minWidth: 150 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h4" color="info.main" fontWeight="bold">
                {reportPhase?.total_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                Samples
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 0', minWidth: 150 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {reportPhase?.completed_test_cases || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                Test Cases
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 0', minWidth: 150 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {reportPhase?.finalized_observations || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                Observations
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 0', minWidth: 150 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {(() => {
                  const startDate = reportPhase?.started_at;
                  const completedDate = reportPhase?.completed_at;
                  if (!startDate) return 0;
                  const end = completedDate ? new Date(completedDate) : new Date();
                  const start = new Date(startDate);
                  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
                })()}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                {reportPhase?.completed_at ? 'Completion Time (days)' : 'Days Elapsed'}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Row 2: On-Time Status + Phase Controls */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
        <Box sx={{ flex: '1 1 400px', minWidth: 0 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography 
                variant="h3" 
                color={
                  reportPhase?.status === 'finalized' ? 
                    'success.main' :
                  reportPhase?.status === 'approved' ?
                    'primary.main' : 'warning.main'
                } 
                component="div"
                sx={{ fontSize: '1.5rem' }}
              >
                {reportPhase?.status === 'finalized' ? 
                  'Yes - Completed On-Time' :
                reportPhase?.status === 'approved' ?
                  'On Track' : 'In Progress'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {reportPhase?.status === 'finalized' ? 'On-Time Completion Status' : 'Current Schedule Status'}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 400px', minWidth: 0 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                  Phase Controls
                </Typography>
                
                {/* Status Update Controls */}
                {reportPhase?.status !== 'finalized' && (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label="At Risk"
                      size="small"
                      color="warning"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      sx={{ fontSize: '0.7rem' }}
                    />
                    <Chip
                      label="Off Track"
                      size="small"
                      color="error"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                )}
              </Box>
              
              {/* Completion Requirements */}
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {reportPhase?.status === 'finalized' ? (
                    'Phase completed successfully - all requirements met'
                  ) : (
                    'To complete: Generate and approve final test report'
                  )}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Workflow Steps Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AssignmentIcon color="primary" />
            Finalize Test Report Phase Workflow
          </Typography>
          
          {unifiedPhaseStatus?.activities ? (
            <DynamicActivityCards
              activities={unifiedPhaseStatus.activities}
              cycleId={cycleIdNum}
              reportId={reportIdNum}
              phaseName="Finalize Test Report"
              phaseStatus={unifiedPhaseStatus.phase_status}
              overallCompletion={unifiedPhaseStatus.overall_completion_percentage}
              onActivityAction={handleActivityAction}
            />
          ) : (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              minHeight: 200, 
              flexDirection: 'column', 
              gap: 2 
            }}>
              <CircularProgress />
              <Typography variant="body2" color="text.secondary">
                Loading finalize test report activities...
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      <Tabs value={selectedTab} onChange={(_, value) => setSelectedTab(value)} sx={{ mb: 2 }}>
        <Tab label="Configuration" />
        <Tab label="Comprehensive Report" disabled={!comprehensiveReportData} />
        <Tab label="Approvals" disabled={reportSections.length === 0} />
        <Tab label="Formatted Report" disabled={reportSections.length === 0 && !reportData?.formatted_report} />
        <Tab label="Executive Summary" disabled={!reportData?.executive_summary} />
        <Tab label="Phase Artifacts" disabled={!reportData?.phase_artifacts} />
        <Tab label="Observations" disabled={!reportData?.observations} />
        <Tab label="Metrics" disabled={!reportData?.metrics} />
      </Tabs>

      <Box sx={{ mt: 2 }}>
        {selectedTab === 0 && renderConfiguration()}
        {selectedTab === 1 && comprehensiveReportData && (
          <ComprehensiveReportDisplay
            reportData={comprehensiveReportData}
            onDownloadPDF={handleDownloadComprehensivePDF}
            onPrint={handlePrintReport}
            onEmail={handleEmailReport}
            loading={loadingComprehensive}
          />
        )}
        {selectedTab === 2 && (
          <ApprovalWorkflow
            cycleId={cycleIdNum}
            reportId={reportIdNum}
            userRole={user?.role || 'User'}
            onPhaseComplete={fetchReportData}
          />
        )}
        {selectedTab === 3 && renderFormattedSections()}
        {selectedTab === 4 && renderExecutiveSummary()}
        {selectedTab === 5 && renderPhaseArtifacts()}
        {selectedTab === 6 && renderObservations()}
        {selectedTab === 7 && renderMetricsDashboard()}
      </Box>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialog}
        onClose={() => setPreviewDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Report Preview</DialogTitle>
        <DialogContent>
          <Box sx={{ p: 2 }}>
            {reportSections.length > 0 ? (
              renderFormattedSections()
            ) : reportData ? (
              <>
                {renderExecutiveSummary()}
                <Box sx={{ mt: 2 }}>{renderPhaseArtifacts()}</Box>
                <Box sx={{ mt: 2 }}>{renderObservations()}</Box>
                <Box sx={{ mt: 2 }}>{renderMetricsDashboard()}</Box>
              </>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No report data available. Please generate the report first.
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Approval Dialog */}
      <Dialog
        open={approvalDialog}
        onClose={() => setApprovalDialog(false)}
      >
        <DialogTitle>Approve Test Report</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to approve this test report? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialog(false)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={handleApproveReport}>
            Approve
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TestReportPage;
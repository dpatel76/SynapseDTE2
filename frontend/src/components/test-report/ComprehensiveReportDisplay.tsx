import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Paper,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
} from '@mui/material';
import Grid from '@mui/material/GridLegacy';
import {
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Styled components
const MetricCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  textAlign: 'center',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));

const SectionCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  '& .MuiAccordionSummary-root': {
    backgroundColor: theme.palette.primary.light,
    color: theme.palette.primary.contrastText,
  },
}));

const StakeholderChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  '& .MuiChip-avatar': {
    backgroundColor: theme.palette.secondary.main,
  },
}));

interface ComprehensiveReportData {
  basic_info: {
    cycle: {
      cycle_name: string;
      cycle_year: number;
      cycle_quarter: number;
    };
    report: {
      report_name: string;
      description: string;
      lob_name: string;
      regulation: string;
      risk_rating: string;
    };
  };
  stakeholders: {
    report_owner?: { name: string; email: string; role: string };
    tester?: { name: string; email: string; role: string };
    data_provider?: { name: string; email: string; role: string };
    data_executive_by_lob?: { name: string; email: string; role: string };
  };
  phase_data: {
    planning: any;
    data_profiling: any;
    scoping: any;
    sample_selection: any;
    request_info: any;
    test_execution: any;
    observations: any;
  };
  execution_metrics: {
    total_duration_days: number;
    time_per_phase: Record<string, any>;
    role_breakdown: Record<string, number>;
    cycle_efficiency: { efficiency_percentage: number };
  };
}

interface ComprehensiveReportDisplayProps {
  reportData: ComprehensiveReportData;
  onDownloadPDF: () => void;
  onPrint: () => void;
  onEmail: () => void;
  loading?: boolean;
}

const ComprehensiveReportDisplay: React.FC<ComprehensiveReportDisplayProps> = ({
  reportData,
  onDownloadPDF,
  onPrint,
  onEmail,
  loading = false,
}) => {
  const [expandedSection, setExpandedSection] = useState<string | false>('executive-summary');

  const handleSectionChange = (section: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedSection(isExpanded ? section : false);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Generating comprehensive report...
        </Typography>
      </Box>
    );
  }

  if (!reportData) {
    return (
      <Alert severity="info">
        No report data available. Please generate the report first.
      </Alert>
    );
  }

  const renderExecutiveSummary = () => {
    const { basic_info, stakeholders, phase_data, execution_metrics } = reportData;
    
    // Calculate key metrics
    const planningData = phase_data.planning?.summary || {};
    const testData = phase_data.test_execution?.summary || {};
    const obsData = phase_data.observations?.summary || {};

    return (
      <SectionCard>
        <Accordion 
          expanded={expandedSection === 'executive-summary'} 
          onChange={handleSectionChange('executive-summary')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon />
              <Typography variant="h6">Executive Summary</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {/* Report Information */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Report Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Report Name</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {basic_info.report.report_name}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Line of Business</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {basic_info.report.lob_name}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Regulation</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {basic_info.report.regulation}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Risk Rating</Typography>
                  <Chip 
                    label={basic_info.report.risk_rating} 
                    color={basic_info.report.risk_rating === 'High' ? 'error' : 'default'}
                    size="small"
                  />
                </Grid>
              </Grid>
            </Box>

            {/* Stakeholders */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Stakeholders
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(stakeholders).map(([role, person]) => 
                  person && (
                    <StakeholderChip
                      key={role}
                      avatar={<PersonIcon />}
                      label={`${role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${person.name}`}
                      variant="outlined"
                    />
                  )
                )}
              </Box>
            </Box>

            {/* Key Metrics */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Key Metrics
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={6} md={2}>
                  <MetricCard>
                    <Typography variant="h4" color="primary" fontWeight="bold">
                      {planningData.total_attributes || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Attributes
                    </Typography>
                  </MetricCard>
                </Grid>
                <Grid item xs={6} md={2}>
                  <MetricCard>
                    <Typography variant="h4" color="success.main" fontWeight="bold">
                      {testData.pass_rate ? `${testData.pass_rate.toFixed(1)}%` : '0%'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Test Pass Rate
                    </Typography>
                  </MetricCard>
                </Grid>
                <Grid item xs={6} md={2}>
                  <MetricCard>
                    <Typography variant="h4" color="warning.main" fontWeight="bold">
                      {obsData.total_observations || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Observations
                    </Typography>
                  </MetricCard>
                </Grid>
                <Grid item xs={6} md={2}>
                  <MetricCard>
                    <Typography variant="h4" color="info.main" fontWeight="bold">
                      {execution_metrics.total_duration_days || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Days to Complete
                    </Typography>
                  </MetricCard>
                </Grid>
                <Grid item xs={6} md={2}>
                  <MetricCard>
                    <Typography variant="h4" color="secondary.main" fontWeight="bold">
                      {planningData.cde_count || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      CDEs Identified
                    </Typography>
                  </MetricCard>
                </Grid>
                <Grid item xs={6} md={2}>
                  <MetricCard>
                    <Typography variant="h4" color="primary.main" fontWeight="bold">
                      {execution_metrics.cycle_efficiency?.efficiency_percentage?.toFixed(0) || 0}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Efficiency
                    </Typography>
                  </MetricCard>
                </Grid>
              </Grid>
            </Box>

            {/* Summary Text */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Summary
              </Typography>
              <Typography variant="body1" paragraph>
                The {basic_info.cycle.cycle_name} testing cycle for {basic_info.report.report_name} 
                has been completed successfully. This comprehensive testing program evaluated{' '}
                {planningData.total_attributes || 0} attributes through a risk-based approach, 
                achieving a {testData.pass_rate ? testData.pass_rate.toFixed(1) : 0}% test pass rate.
              </Typography>
              <Typography variant="body1">
                Key accomplishments include thorough planning and scoping phases, comprehensive 
                data profiling with AI-powered rule generation, systematic sample selection, 
                and rigorous test execution. {obsData.total_observations || 0} observations were 
                identified and managed through our structured observation management process.
              </Typography>
            </Box>
          </AccordionDetails>
        </Accordion>
      </SectionCard>
    );
  };

  const renderPlanningSection = () => {
    const planningData = phase_data.planning;
    
    if (!planningData || planningData.status === 'not_found') {
      return (
        <SectionCard>
          <Accordion 
            expanded={expandedSection === 'planning'} 
            onChange={handleSectionChange('planning')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Planning Phase Section</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="info">Planning phase data not available</Alert>
            </AccordionDetails>
          </Accordion>
        </SectionCard>
      );
    }

    const summary = planningData.summary || {};
    const attributes = planningData.attributes || [];

    return (
      <SectionCard>
        <Accordion 
          expanded={expandedSection === 'planning'} 
          onChange={handleSectionChange('planning')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon />
              <Typography variant="h6">Planning Phase Section</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {/* Planning Summary */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Planning Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="primary">{summary.total_attributes || 0}</Typography>
                    <Typography variant="caption">Total Attributes</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="secondary">{summary.cde_count || 0}</Typography>
                    <Typography variant="caption">CDEs</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="warning.main">{summary.pk_count || 0}</Typography>
                    <Typography variant="caption">Primary Keys</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="success.main">{summary.approved_count || 0}</Typography>
                    <Typography variant="caption">Approved</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            {/* Approval Progress */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Approval Progress
              </Typography>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Approval Rate: {planningData.approval_summary?.approval_rate?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={planningData.approval_summary?.approval_rate || 0} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </Box>

            {/* Attributes Table */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Attributes Analysis (First 10)
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Line #</TableCell>
                    <TableCell>Attribute Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Flags</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {attributes.slice(0, 10).map((attr: any, index: number) => (
                    <TableRow key={index}>
                      <TableCell>{attr.line_item_number}</TableCell>
                      <TableCell>{attr.attribute_name}</TableCell>
                      <TableCell>{attr.data_type}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {attr.cde_flag && <Chip label="CDE" size="small" color="primary" />}
                          {attr.is_primary_key && <Chip label="PK" size="small" color="secondary" />}
                          {attr.historical_issues_flag && <Chip label="Issues" size="small" color="warning" />}
                          {attr.mandatory_flag && <Chip label="Mandatory" size="small" color="default" />}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={attr.approval_status} 
                          size="small" 
                          color={attr.approval_status === 'approved' ? 'success' : 'default'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {attributes.length > 10 && (
                <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                  Showing 10 of {attributes.length} total attributes
                </Typography>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      </SectionCard>
    );
  };

  const renderTestExecutionSection = () => {
    const executionData = phase_data.test_execution;
    
    if (!executionData || executionData.status === 'not_found') {
      return (
        <SectionCard>
          <Accordion 
            expanded={expandedSection === 'test-execution'} 
            onChange={handleSectionChange('test-execution')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Test Execution Section</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="info">Test execution data not available</Alert>
            </AccordionDetails>
          </Accordion>
        </SectionCard>
      );
    }

    const summary = executionData.summary || {};
    const resultsByAttribute = executionData.results_by_attribute || {};

    return (
      <SectionCard>
        <Accordion 
          expanded={expandedSection === 'test-execution'} 
          onChange={handleSectionChange('test-execution')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon />
              <Typography variant="h6">Test Execution Section</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {/* Execution Summary */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Test Execution Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="primary">{summary.total_test_executions || 0}</Typography>
                    <Typography variant="caption">Total Tests</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="success.main">{summary.passed_tests || 0}</Typography>
                    <Typography variant="caption">Passed</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="error.main">{summary.failed_tests || 0}</Typography>
                    <Typography variant="caption">Failed</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="warning.main">{summary.inconclusive_tests || 0}</Typography>
                    <Typography variant="caption">Inconclusive</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            {/* Pass Rate Progress */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Overall Pass Rate
              </Typography>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Pass Rate: {summary.pass_rate?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={summary.pass_rate || 0} 
                  color={summary.pass_rate >= 90 ? 'success' : summary.pass_rate >= 70 ? 'warning' : 'error'}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </Box>

            {/* Results by Attribute */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Results by Attribute
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Attribute Name</TableCell>
                    <TableCell align="right">Total</TableCell>
                    <TableCell align="right">Passed</TableCell>
                    <TableCell align="right">Failed</TableCell>
                    <TableCell align="right">Pass Rate</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(resultsByAttribute).slice(0, 10).map(([attrName, results]: [string, any]) => {
                    const passRate = results.total > 0 ? (results.passed / results.total * 100) : 0;
                    return (
                      <TableRow key={attrName}>
                        <TableCell>{attrName}</TableCell>
                        <TableCell align="right">{results.total}</TableCell>
                        <TableCell align="right">{results.passed}</TableCell>
                        <TableCell align="right">{results.failed}</TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2">
                              {passRate.toFixed(1)}%
                            </Typography>
                            {passRate >= 90 ? (
                              <CheckCircleIcon color="success" fontSize="small" />
                            ) : passRate >= 70 ? (
                              <WarningIcon color="warning" fontSize="small" />
                            ) : (
                              <ErrorIcon color="error" fontSize="small" />
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              {Object.keys(resultsByAttribute).length > 10 && (
                <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                  Showing 10 of {Object.keys(resultsByAttribute).length} tested attributes
                </Typography>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      </SectionCard>
    );
  };

  const renderObservationSection = () => {
    const obsData = phase_data.observations;
    const summary = obsData?.summary || {};

    return (
      <SectionCard>
        <Accordion 
          expanded={expandedSection === 'observations'} 
          onChange={handleSectionChange('observations')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon />
              <Typography variant="h6">Observation Management Section</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {/* Observation Summary */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Observation Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="primary">{summary.total_observations || 0}</Typography>
                    <Typography variant="caption">Total Observations</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="success.main">
                      {summary.resolution_rate?.toFixed(1) || 0}%
                    </Typography>
                    <Typography variant="caption">Resolution Rate</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            {/* Observations by Severity */}
            {summary.by_severity && Object.keys(summary.by_severity).length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  Observations by Severity
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(summary.by_severity).map(([severity, count]: [string, any]) => (
                    <Grid item xs={6} md={2} key={severity}>
                      <Box textAlign="center">
                        <Typography 
                          variant="h5" 
                          color={
                            severity === 'High' ? 'error.main' : 
                            severity === 'Medium' ? 'warning.main' : 
                            'info.main'
                          }
                        >
                          {count}
                        </Typography>
                        <Typography variant="caption">{severity}</Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}

            {/* Observations by Status */}
            {summary.by_status && Object.keys(summary.by_status).length > 0 && (
              <Box>
                <Typography variant="h6" gutterBottom color="primary">
                  Observations by Status
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(summary.by_status).map(([status, count]: [string, any]) => (
                    <Grid item xs={6} md={2} key={status}>
                      <Box textAlign="center">
                        <Typography 
                          variant="h5" 
                          color={
                            status === 'Resolved' || status === 'Closed' ? 'success.main' : 
                            status === 'In Progress' ? 'warning.main' : 
                            'error.main'
                          }
                        >
                          {count}
                        </Typography>
                        <Typography variant="caption">{status}</Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      </SectionCard>
    );
  };

  const renderExecutionMetrics = () => {
    const metrics = execution_metrics;

    return (
      <SectionCard>
        <Accordion 
          expanded={expandedSection === 'execution-metrics'} 
          onChange={handleSectionChange('execution-metrics')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimelineIcon />
              <Typography variant="h6">Execution Metrics</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {/* Overall Metrics */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Overall Metrics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="primary">{metrics.total_duration_days}</Typography>
                    <Typography variant="caption">Total Days</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="success.main">
                      {metrics.cycle_efficiency?.efficiency_percentage?.toFixed(0) || 0}%
                    </Typography>
                    <Typography variant="caption">Efficiency</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            {/* Time per Phase */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary">
                Time per Phase
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Phase Name</TableCell>
                    <TableCell align="right">Duration (Days)</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(metrics.time_per_phase || {}).map(([phaseName, phaseInfo]: [string, any]) => (
                    <TableRow key={phaseName}>
                      <TableCell>{phaseName}</TableCell>
                      <TableCell align="right">{phaseInfo.duration_days}</TableCell>
                      <TableCell>
                        <Chip 
                          label={phaseInfo.status} 
                          size="small" 
                          color={phaseInfo.status === 'Complete' ? 'success' : 'default'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            {/* Role Breakdown */}
            <Box>
              <Typography variant="h6" gutterBottom color="primary">
                Role Contribution
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(metrics.role_breakdown || {}).map(([role, percentage]: [string, any]) => (
                  <Grid item xs={6} md={3} key={role}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="secondary">{percentage}%</Typography>
                      <Typography variant="caption">{role}</Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </AccordionDetails>
        </Accordion>
      </SectionCard>
    );
  };

  const { basic_info, phase_data, execution_metrics } = reportData;

  return (
    <Box>
      {/* Header with Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" color="primary">
          Comprehensive Test Report
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={onDownloadPDF}
          >
            Download PDF
          </Button>
          <Button
            variant="outlined"
            startIcon={<PrintIcon />}
            onClick={onPrint}
          >
            Print
          </Button>
          <Button
            variant="outlined"
            startIcon={<EmailIcon />}
            onClick={onEmail}
          >
            Email
          </Button>
        </Box>
      </Box>

      {/* Report Sections */}
      {renderExecutiveSummary()}
      {renderPlanningSection()}
      {renderTestExecutionSection()}
      {renderObservationSection()}
      {renderExecutionMetrics()}
    </Box>
  );
};

export default ComprehensiveReportDisplay;
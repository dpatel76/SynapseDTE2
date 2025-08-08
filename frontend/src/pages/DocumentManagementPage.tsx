import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  CircularProgress,
  Tooltip,
  FormControlLabel,
  Switch,
  Divider
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  History as HistoryIcon,
  Assessment as StatsIcon,
  CloudUpload as CloudUploadIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { useNotifications } from '../contexts/NotificationContext';
import DocumentManagementAPI, { Document, DocumentUploadRequest, DocumentMetrics } from '../api/documentManagement';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const DocumentManagementPage: React.FC = () => {
  // State management
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [metrics, setMetrics] = useState<DocumentMetrics | null>(null);
  
  // Dialog states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [filterDialogOpen, setFilterDialogOpen] = useState(false);
  const [versionDialogOpen, setVersionDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  
  // Filter states
  const [filters, setFilters] = useState({
    cycle_id: '',
    report_id: '',
    phase_id: '',
    document_type: '',
    include_archived: false,
    latest_only: true
  });
  
  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  
  // Upload states
  const [uploadData, setUploadData] = useState<DocumentUploadRequest>({
    cycle_id: 0,
    report_id: 0,
    phase_id: 0,
    test_case_id: '',
    document_type: 'report_sample_data',
    document_title: '',
    document_description: '',
    document_category: 'general',
    access_level: 'phase_restricted',
    required_for_completion: false,
    approval_required: false,
    workflow_stage: ''
  });
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useNotifications();

  // Load documents on component mount and when filters change
  useEffect(() => {
    loadDocuments();
  }, [page, rowsPerPage, filters]);

  // Load metrics
  useEffect(() => {
    loadMetrics();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await DocumentManagementAPI.listDocuments({
        ...filters,
        cycle_id: filters.cycle_id ? parseInt(filters.cycle_id) : undefined,
        report_id: filters.report_id ? parseInt(filters.report_id) : undefined,
        phase_id: filters.phase_id ? parseInt(filters.phase_id) : undefined,
        page: page + 1,
        page_size: rowsPerPage
      });
      
      setDocuments(response.documents);
      setTotalCount(response.pagination.total_count);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
      showToast('error', 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const metrics = await DocumentManagementAPI.getDocumentStatistics();
      setMetrics(metrics);
    } catch (err: any) {
      console.error('Failed to load metrics:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setIsSearchMode(false);
      loadDocuments();
      return;
    }

    try {
      setLoading(true);
      const response = await DocumentManagementAPI.searchDocuments({
        search_query: searchQuery,
        page: page + 1,
        page_size: rowsPerPage
      });
      
      setSearchResults(response.search_results);
      setTotalCount(response.pagination.total_count);
      setIsSearchMode(true);
    } catch (err: any) {
      showToast('error', 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      showToast('error', 'Please select a file');
      return;
    }

    try {
      setLoading(true);
      const result = await DocumentManagementAPI.uploadDocument(selectedFile, uploadData);
      
      if (result.success) {
        showToast('success', 'Document uploaded successfully');
        setUploadDialogOpen(false);
        setSelectedFile(null);
        setUploadData({
          cycle_id: 0,
          report_id: 0,
          phase_id: 0,
          test_case_id: '',
          document_type: 'report_sample_data',
          document_title: '',
          document_description: '',
          document_category: 'general',
          access_level: 'phase_restricted',
          required_for_completion: false,
          approval_required: false,
          workflow_stage: ''
        });
        loadDocuments();
        loadMetrics();
      } else {
        showToast('error', result.error || 'Upload failed');
      }
    } catch (err: any) {
      showToast('error', 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (docData: Document) => {
    try {
      const blob = await DocumentManagementAPI.downloadDocument(docData.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = docData.original_filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      showToast('success', 'Document downloaded');
    } catch (err: any) {
      showToast('error', 'Download failed');
    }
  };

  const handleDelete = async (document: Document) => {
    if (!window.confirm(`Are you sure you want to delete "${document.document_title}"?`)) {
      return;
    }

    try {
      const result = await DocumentManagementAPI.deleteDocument(document.id, false);
      
      if (result.success) {
        showToast('success', 'Document deleted');
        loadDocuments();
        loadMetrics();
      } else {
        showToast('error', result.error || 'Delete failed');
      }
    } catch (err: any) {
      showToast('error', 'Delete failed');
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!uploadData.document_title) {
        setUploadData(prev => ({
          ...prev,
          document_title: file.name.split('.')[0]
        }));
      }
    }
  };

  const renderDocumentTable = () => {
    const dataToShow = isSearchMode 
      ? searchResults.map(result => result.document)
      : documents;

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Document</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Test Case</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dataToShow.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell>
                  <Box>
                    <Typography variant="subtitle2">
                      {DocumentManagementAPI.getFileIcon(doc.file_format)} {doc.document_title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {doc.original_filename}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={doc.document_type.replace(/_/g, ' ')}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  {doc.test_case_id ? (
                    <Chip
                      label={doc.test_case_id}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Phase-level
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {DocumentManagementAPI.formatFileSize(doc.file_size)}
                </TableCell>
                <TableCell>
                  <Chip
                    label={doc.upload_status}
                    size="small"
                    color={DocumentManagementAPI.getStatusColor(doc.upload_status) as any}
                  />
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    <Typography variant="body2">{doc.document_version}</Typography>
                    {doc.is_latest_version && (
                      <Chip label="Latest" size="small" color="primary" sx={{ ml: 1 }} />
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="Download">
                      <IconButton 
                        size="small" 
                        onClick={() => handleDownload(doc)}
                        color="primary"
                      >
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="View Details">
                      <IconButton 
                        size="small" 
                        onClick={() => setSelectedDocument(doc)}
                        color="info"
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Version History">
                      <IconButton 
                        size="small" 
                        onClick={() => {
                          setSelectedDocument(doc);
                          setVersionDialogOpen(true);
                        }}
                        color="secondary"
                      >
                        <HistoryIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton 
                        size="small" 
                        onClick={() => handleDelete(doc)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </TableContainer>
    );
  };

  const renderMetricsCards = () => {
    if (!metrics) return null;

    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Documents
              </Typography>
              <Typography variant="h4">
                {metrics.total_documents}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Size
              </Typography>
              <Typography variant="h4">
                {(metrics.total_size_mb ?? 0).toFixed(1)} MB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Document Types
              </Typography>
              <Typography variant="h4">
                {Object.keys(metrics.by_document_type).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                File Formats
              </Typography>
              <Typography variant="h4">
                {Object.keys(metrics.by_file_format).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Document Management</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<SearchIcon />}
            onClick={() => setSearchDialogOpen(true)}
          >
            Search
          </Button>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setFilterDialogOpen(true)}
          >
            Filter
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              setIsSearchMode(false);
              setSearchQuery('');
              loadDocuments();
              loadMetrics();
            }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
          >
            Upload Document
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Tabs value={selectedTab} onChange={(_, newValue) => setSelectedTab(newValue)}>
        <Tab label="Documents" />
        <Tab label="Statistics" />
      </Tabs>

      <TabPanel value={selectedTab} index={0}>
        {renderMetricsCards()}
        {loading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : (
          renderDocumentTable()
        )}
      </TabPanel>

      <TabPanel value={selectedTab} index={1}>
        <Typography variant="h6" gutterBottom>
          Document Statistics
        </Typography>
        {metrics && (
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  By Document Type
                </Typography>
                {Object.entries(metrics.by_document_type).map(([type, data]) => (
                  <Box key={type} display="flex" justifyContent="space-between" py={1}>
                    <Typography>{type.replace(/_/g, ' ')}</Typography>
                    <Typography>{data.count} documents</Typography>
                  </Box>
                ))}
              </Paper>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  By File Format
                </Typography>
                {Object.entries(metrics.by_file_format).map(([format, data]) => (
                  <Box key={format} display="flex" justifyContent="space-between" py={1}>
                    <Typography>{format.toUpperCase()}</Typography>
                    <Typography>{data.count} files</Typography>
                  </Box>
                ))}
              </Paper>
            </Grid>
          </Grid>
        )}
      </TabPanel>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              accept=".csv,.txt,.xlsx,.xls,.docx,.pdf,.jpg,.jpeg,.png"
            />
            <Button
              variant="outlined"
              startIcon={<CloudUploadIcon />}
              onClick={() => fileInputRef.current?.click()}
              fullWidth
              sx={{ mb: 2 }}
            >
              {selectedFile ? selectedFile.name : 'Select File'}
            </Button>
            
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Cycle ID"
                  type="number"
                  value={uploadData.cycle_id}
                  onChange={(e) => setUploadData(prev => ({ ...prev, cycle_id: parseInt(e.target.value) }))}
                  fullWidth
                  required
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Report ID"
                  type="number"
                  value={uploadData.report_id}
                  onChange={(e) => setUploadData(prev => ({ ...prev, report_id: parseInt(e.target.value) }))}
                  fullWidth
                  required
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Phase ID"
                  type="number"
                  value={uploadData.phase_id}
                  onChange={(e) => setUploadData(prev => ({ ...prev, phase_id: parseInt(e.target.value) }))}
                  fullWidth
                  required
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth required>
                  <InputLabel>Document Type</InputLabel>
                  <Select
                    value={uploadData.document_type}
                    onChange={(e) => setUploadData(prev => ({ ...prev, document_type: e.target.value }))}
                  >
                    <MenuItem value="report_sample_data">Report Sample Data</MenuItem>
                    <MenuItem value="report_underlying_transaction_data">Report Underlying Transaction Data</MenuItem>
                    <MenuItem value="report_source_transaction_data">Report Source Transaction Data</MenuItem>
                    <MenuItem value="report_source_document">Report Source Document</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField
                  label="Test Case ID (Optional)"
                  value={uploadData.test_case_id}
                  onChange={(e) => setUploadData(prev => ({ ...prev, test_case_id: e.target.value }))}
                  fullWidth
                  placeholder="Enter test case ID for granular tracking"
                  helperText="Optional - leave empty for phase-level documents"
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField
                  label="Document Title"
                  value={uploadData.document_title}
                  onChange={(e) => setUploadData(prev => ({ ...prev, document_title: e.target.value }))}
                  fullWidth
                  required
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField
                  label="Description"
                  value={uploadData.document_description}
                  onChange={(e) => setUploadData(prev => ({ ...prev, document_description: e.target.value }))}
                  fullWidth
                  multiline
                  rows={3}
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={uploadData.required_for_completion}
                      onChange={(e) => setUploadData(prev => ({ ...prev, required_for_completion: e.target.checked }))}
                    />
                  }
                  label="Required for Completion"
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={uploadData.approval_required}
                      onChange={(e) => setUploadData(prev => ({ ...prev, approval_required: e.target.checked }))}
                    />
                  }
                  label="Approval Required"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpload} variant="contained" disabled={!selectedFile}>
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* Search Dialog */}
      <Dialog open={searchDialogOpen} onClose={() => setSearchDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Search Documents</DialogTitle>
        <DialogContent>
          <TextField
            label="Search Query"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            fullWidth
            margin="normal"
            placeholder="Enter keywords to search..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSearchDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => {
            setSearchDialogOpen(false);
            handleSearch();
          }} variant="contained">
            Search
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentManagementPage;
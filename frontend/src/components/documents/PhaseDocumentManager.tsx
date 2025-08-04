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
  Alert,
  FormControlLabel,
  Switch,
  CircularProgress,
  Tooltip,
  Collapse,
  Card,
  CardContent,
  CardActions,
  Divider
} from '@mui/material';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  History as HistoryIcon,
  CloudUpload as CloudUploadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  AttachFile as AttachFileIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useNotifications } from '../../contexts/NotificationContext';
import DocumentManagementAPI, { Document, DocumentUploadRequest } from '../../api/documentManagement';

interface PhaseDocumentManagerProps {
  cycleId: number;
  reportId: number;
  phaseId: number;
  phaseName: string;
  testCaseId?: string;
  allowedDocumentTypes?: string[];
  requiredDocumentTypes?: string[];
  compact?: boolean;
  hideUpload?: boolean;
  title?: string;
}

const PhaseDocumentManager: React.FC<PhaseDocumentManagerProps> = ({
  cycleId,
  reportId,
  phaseId,
  phaseName,
  testCaseId,
  allowedDocumentTypes = [
    'report_sample_data',
    'report_underlying_transaction_data',
    'report_source_transaction_data',
    'report_source_document'
  ],
  requiredDocumentTypes = [],
  compact = false,
  hideUpload = false,
  title
}) => {
  // State management
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(compact ? 5 : 10);
  const [totalCount, setTotalCount] = useState(0);
  const [expanded, setExpanded] = useState(!compact);
  
  // Dialog states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  
  // Upload states
  const [uploadData, setUploadData] = useState<DocumentUploadRequest>({
    cycle_id: cycleId,
    report_id: reportId,
    phase_id: phaseId,
    test_case_id: testCaseId || '',
    document_type: allowedDocumentTypes[0] || 'report_sample_data',
    document_title: '',
    document_description: '',
    document_category: 'general',
    access_level: 'phase_restricted',
    required_for_completion: false,
    approval_required: false,
    workflow_stage: phaseName
  });
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useNotifications();

  // Load documents on component mount and when filters change
  useEffect(() => {
    loadDocuments();
  }, [cycleId, reportId, phaseId, testCaseId, page, rowsPerPage]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await DocumentManagementAPI.listDocuments({
        cycle_id: cycleId,
        report_id: reportId,
        phase_id: phaseId,
        test_case_id: testCaseId,
        page: page + 1,
        page_size: rowsPerPage,
        latest_only: true,
        include_archived: false
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
          cycle_id: cycleId,
          report_id: reportId,
          phase_id: phaseId,
          test_case_id: testCaseId || '',
          document_type: allowedDocumentTypes[0] || 'report_sample_data',
          document_title: '',
          document_description: '',
          document_category: 'general',
          access_level: 'phase_restricted',
          required_for_completion: false,
          approval_required: false,
          workflow_stage: phaseName
        });
        loadDocuments();
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

  const getDocumentTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      'report_sample_data': 'Sample Data',
      'report_underlying_transaction_data': 'Underlying Transaction Data',
      'report_source_transaction_data': 'Source Transaction Data',
      'report_source_document': 'Source Document'
    };
    return typeMap[type] || type.replace(/_/g, ' ');
  };

  const getMissingRequiredDocuments = () => {
    const uploadedTypes = documents.map(doc => doc.document_type);
    return requiredDocumentTypes.filter(type => !uploadedTypes.includes(type));
  };

  const missingRequired = getMissingRequiredDocuments();

  const renderDocumentTable = () => {
    if (loading) {
      return (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress size={24} />
        </Box>
      );
    }

    if (documents.length === 0) {
      return (
        <Box textAlign="center" py={4}>
          <Typography variant="body2" color="text.secondary">
            No documents found for this {testCaseId ? 'test case' : 'phase'}
          </Typography>
        </Box>
      );
    }

    return (
      <>
        <TableContainer component={Paper} variant="outlined">
          <Table size={compact ? 'small' : 'medium'}>
            <TableHead>
              <TableRow>
                <TableCell>Document</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2" noWrap>
                        {DocumentManagementAPI.getFileIcon(doc.file_format)} {doc.document_title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {doc.original_filename}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getDocumentTypeLabel(doc.document_type)}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {DocumentManagementAPI.formatFileSize(doc.file_size)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={doc.upload_status}
                      size="small"
                      color={DocumentManagementAPI.getStatusColor(doc.upload_status) as any}
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5}>
                      <Tooltip title="Download">
                        <IconButton 
                          size="small" 
                          onClick={() => handleDownload(doc)}
                          color="primary"
                        >
                          <DownloadIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View Details">
                        <IconButton 
                          size="small" 
                          onClick={() => setSelectedDocument(doc)}
                          color="info"
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton 
                          size="small" 
                          onClick={() => handleDelete(doc)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        {totalCount > rowsPerPage && (
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
            rowsPerPageOptions={compact ? [5, 10] : [5, 10, 25]}
          />
        )}
      </>
    );
  };

  const renderContent = () => (
    <Box>
      {/* Missing Required Documents Alert */}
      {missingRequired.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">Missing Required Documents:</Typography>
          {missingRequired.map(type => (
            <Chip
              key={type}
              label={getDocumentTypeLabel(type)}
              size="small"
              color="warning"
              variant="outlined"
              sx={{ mr: 1, mt: 0.5 }}
            />
          ))}
        </Alert>
      )}

      {/* Header with Actions */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AttachFileIcon />
            {title || `${phaseName} Documents`}
            {testCaseId && (
              <Chip label={`Test Case: ${testCaseId}`} size="small" color="secondary" />
            )}
          </Typography>
          <Chip 
            label={`${documents.length} documents`} 
            size="small" 
            variant="outlined" 
          />
        </Box>
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadDocuments} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          {!hideUpload && (
            <Button
              variant="contained"
              startIcon={<UploadIcon />}
              onClick={() => setUploadDialogOpen(true)}
              size="small"
            >
              Upload
            </Button>
          )}
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Documents Table */}
      {renderDocumentTable()}
    </Box>
  );

  // Compact view with collapsible content
  if (compact) {
    return (
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent sx={{ pb: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AttachFileIcon />
              {title || `${phaseName} Documents`}
              <Chip label={`${documents.length}`} size="small" />
              {missingRequired.length > 0 && (
                <Chip label={`${missingRequired.length} missing`} size="small" color="warning" />
              )}
            </Typography>
            <IconButton 
              onClick={() => setExpanded(!expanded)}
              size="small"
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </CardContent>
        <Collapse in={expanded}>
          <CardContent sx={{ pt: 0 }}>
            <Divider sx={{ mb: 2 }} />
            {renderContent()}
          </CardContent>
        </Collapse>
      </Card>
    );
  }

  // Full view
  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      {renderContent()}

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Document - {phaseName}</DialogTitle>
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
              <Grid size={{ xs: 12 }}>
                <FormControl fullWidth required>
                  <InputLabel>Document Type</InputLabel>
                  <Select
                    value={uploadData.document_type}
                    onChange={(e) => setUploadData(prev => ({ ...prev, document_type: e.target.value }))}
                  >
                    {allowedDocumentTypes.map(type => (
                      <MenuItem key={type} value={type}>
                        {getDocumentTypeLabel(type)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
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
                  rows={2}
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
    </Paper>
  );
};

export default PhaseDocumentManager;
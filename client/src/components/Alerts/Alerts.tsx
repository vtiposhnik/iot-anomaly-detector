import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Button,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Grid,
  Card,
  CardContent,
  Alert as MuiAlert,
  Snackbar,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { Alert, getAlerts, acknowledgeAlert, acknowledgeAllAlerts, getAlertStatistics } from '../../services/alertsService';

/**
 * Alerts component for displaying and managing system alerts
 */
const Alerts: React.FC = () => {
  // State for alerts data
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for statistics
  const [statistics, setStatistics] = useState<{
    by_severity: Record<string, number>;
    by_status: Record<string, number>;
    daily: Record<string, number>;
    total: number;
  }>({
    by_severity: { info: 0, warning: 0, critical: 0 },
    by_status: { acknowledged: 0, unacknowledged: 0 },
    daily: {},
    total: 0
  });
  
  // State for pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // State for filters
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  // State for snackbar
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info' | 'warning'
  });

  // Fetch alerts and statistics
  const fetchData = async () => {
    setLoading(true);
    try {
      // Determine filter values
      const severity = severityFilter !== 'all' ? severityFilter : undefined;
      const acknowledged = statusFilter !== 'all' 
        ? statusFilter === 'acknowledged' 
        : undefined;
      
      // Fetch alerts with filters
      const alertsData = await getAlerts(
        rowsPerPage,
        page * rowsPerPage,
        severity,
        acknowledged
      );
      setAlerts(alertsData);
      
      // Fetch statistics
      const statsData = await getAlertStatistics();
      setStatistics(statsData);
      
      setError(null);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('Failed to load alerts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchData();
    // Set up polling every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [page, rowsPerPage, severityFilter, statusFilter]);

  // Handle page change
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Handle severity filter change
  const handleSeverityFilterChange = (event: SelectChangeEvent) => {
    setSeverityFilter(event.target.value);
    setPage(0);
  };

  // Handle status filter change
  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    setStatusFilter(event.target.value);
    setPage(0);
  };

  // Handle acknowledging an alert
  const handleAcknowledge = async (alertId: number) => {
    try {
      const result = await acknowledgeAlert(alertId);
      if (result) {
        // Update the local state
        setAlerts(alerts.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        ));
        
        // Show success message
        setSnackbar({
          open: true,
          message: 'Alert acknowledged successfully',
          severity: 'success'
        });
        
        // Refresh data
        fetchData();
      }
    } catch (err) {
      console.error('Error acknowledging alert:', err);
      setSnackbar({
        open: true,
        message: 'Failed to acknowledge alert',
        severity: 'error'
      });
    }
  };

  // Handle acknowledging all alerts
  const handleAcknowledgeAll = async () => {
    try {
      const severity = severityFilter !== 'all' ? severityFilter : undefined;
      const count = await acknowledgeAllAlerts(severity);
      
      // Show success message
      setSnackbar({
        open: true,
        message: `${count} alerts acknowledged successfully`,
        severity: 'success'
      });
      
      // Refresh data
      fetchData();
    } catch (err) {
      console.error('Error acknowledging all alerts:', err);
      setSnackbar({
        open: true,
        message: 'Failed to acknowledge alerts',
        severity: 'error'
      });
    }
  };

  // Close snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
      default:
        return <InfoIcon color="info" />;
    }
  };

  // Get severity color
  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
      default:
        return 'info';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Alerts
      </Typography>
      
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Alerts
              </Typography>
              <Typography variant="h4">
                {statistics.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Critical Alerts
              </Typography>
              <Typography variant="h4" color="error">
                {statistics.by_severity.critical || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Warning Alerts
              </Typography>
              <Typography variant="h4" color="warning.main">
                {statistics.by_severity.warning || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Unacknowledged
              </Typography>
              <Typography variant="h4" color="info.main">
                {statistics.by_status.unacknowledged || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Filters and Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="severity-filter-label">Severity</InputLabel>
            <Select
              labelId="severity-filter-label"
              value={severityFilter}
              label="Severity"
              onChange={handleSeverityFilterChange}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="info">Info</MenuItem>
              <MenuItem value="warning">Warning</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="status-filter-label">Status</InputLabel>
            <Select
              labelId="status-filter-label"
              value={statusFilter}
              label="Status"
              onChange={handleStatusFilterChange}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="acknowledged">Acknowledged</MenuItem>
              <MenuItem value="unacknowledged">Unacknowledged</MenuItem>
            </Select>
          </FormControl>
        </Box>
        
        <Box>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleAcknowledgeAll}
            disabled={loading || statistics.by_status.unacknowledged === 0}
            startIcon={<CheckCircleIcon />}
          >
            Acknowledge All
          </Button>
          <IconButton 
            color="primary" 
            onClick={fetchData} 
            disabled={loading}
            sx={{ ml: 1 }}
          >
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>
      
      {/* Error Alert */}
      {error && (
        <MuiAlert severity="error" sx={{ mb: 2 }}>
          {error}
        </MuiAlert>
      )}
      
      {/* Alerts Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 440 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Severity</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>Raised At</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <CircularProgress size={24} sx={{ my: 2 }} />
                  </TableCell>
                </TableRow>
              ) : alerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No alerts found
                  </TableCell>
                </TableRow>
              ) : (
                alerts.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getSeverityIcon(alert.severity)}
                        <Typography sx={{ ml: 1 }}>
                          {alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{alert.message}</TableCell>
                    <TableCell>
                      {format(parseISO(alert.raised_at), 'MMM d, yyyy HH:mm:ss')}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={alert.acknowledged ? "Acknowledged" : "Unacknowledged"}
                        color={alert.acknowledged ? "success" : "default"}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        variant="outlined"
                        size="small"
                        color={getSeverityColor(alert.severity)}
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={alert.acknowledged}
                      >
                        Acknowledge
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={statistics.total}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <MuiAlert
          elevation={6}
          variant="filled"
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </MuiAlert>
      </Snackbar>
    </Box>
  );
};

export default Alerts;

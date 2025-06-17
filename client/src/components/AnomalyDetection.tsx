import React, { useState } from 'react';
import { Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import api from '../services/api';
import { DeviceData, FormattedAnomaly } from '../types';

// Using DeviceData and FormattedAnomaly from shared types

interface AnomalyDetectionProps {
  anomalies: FormattedAnomaly[];
  deviceData: DeviceData[];
}

const AnomalyDetection: React.FC<AnomalyDetectionProps> = ({ anomalies }) => {
  const [selectedAnomaly, setSelectedAnomaly] = useState<FormattedAnomaly | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolvedBy, setResolvedBy] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  // Handle resolve button click
  const handleResolveClick = (anomaly: FormattedAnomaly) => {
    setSelectedAnomaly(anomaly);
    setDialogOpen(true);
  };

  // Handle dialog close
  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedAnomaly(null);
    setResolutionNotes('');
    setResolvedBy('');
  };

  // Handle anomaly resolution
  const handleResolveAnomaly = async () => {
    if (!selectedAnomaly) return;

    try {
      await api.resolveAnomaly(selectedAnomaly.id, {
        notes: resolutionNotes,
        resolvedBy
      });

      // Remove the resolved anomaly from the list
      // In a real app, you would update the state through a proper state management system
      const updatedAnomaly = { ...selectedAnomaly, resolved: true };
      const index = anomalies.findIndex(a => a.id === selectedAnomaly.id);
      if (index !== -1) {
        anomalies.splice(index, 1, updatedAnomaly);
      }

      handleDialogClose();
    } catch (error) {
      console.error('Error resolving anomaly:', error);
    }
  };

  // Each anomaly now has a guaranteed unique ID
  
  return (
    <Box sx={{
      borderRadius: 2,
      overflow: 'hidden',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      bgcolor: 'background.paper',
    }}>
      <Box sx={{ 
        p: 2, 
        borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="h6" component="h2">
          Anomaly Detection
        </Typography>
        <Chip 
          label={`${anomalies.length} ${anomalies.length === 1 ? 'anomaly' : 'anomalies'}`} 
          color={anomalies.length > 0 ? 'error' : 'default'}
          size="small"
          sx={{ fontWeight: 500 }}
        />
      </Box>
      
      {anomalies.length > 0 ? (
        <TableContainer sx={{ 
          maxHeight: 400, 
          flex: 1,
          '& .MuiTableRow-root:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Time</TableCell>
                <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Severity</TableCell>
                <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {anomalies.map((anomaly, index) => (
                <TableRow 
                  key={`${anomaly.id}-${index}`} 
                  sx={{ 
                    '&:last-child td, &:last-child th': { border: 0 },
                    bgcolor: index % 2 === 0 ? 'background.paper' : 'background.default',
                  }}
                >
                  <TableCell>{formatTime(anomaly.timestamp)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={anomaly.type} 
                      size="small" 
                      color={anomaly.type === 'network' ? 'secondary' : 'default'}
                      sx={{ 
                        fontWeight: 500,
                        minWidth: '90px',
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={anomaly.severity} 
                      size="small" 
                      color={getSeverityColor(anomaly.severity) as any}
                      sx={{ 
                        fontWeight: 500,
                        minWidth: '80px',
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ maxWidth: '300px', whiteSpace: 'normal', wordBreak: 'break-word' }}>
                    {anomaly.description}
                  </TableCell>
                  <TableCell>
                    <Button 
                      variant="contained" 
                      size="small" 
                      color={anomaly.resolved ? 'success' : 'primary'}
                      onClick={() => handleResolveClick(anomaly)}
                      disabled={anomaly.resolved}
                      sx={{ 
                        textTransform: 'none',
                        boxShadow: 'none',
                        '&:hover': {
                          boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
                        }
                      }}
                    >
                      {anomaly.resolved ? 'Resolved' : 'Resolve'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box sx={{ 
          textAlign: 'center', 
          py: 8,
          px: 2,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          bgcolor: 'background.default',
          borderRadius: 1,
          m: 2,
        }}>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
            No anomalies detected
          </Typography>
          <Typography variant="body2" color="text.secondary">
            The system is monitoring network traffic for suspicious patterns
          </Typography>
        </Box>
      )}
      
      {/* Resolution Dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose}>
        <DialogTitle>Resolve Anomaly</DialogTitle>
        <DialogContent>
          {selectedAnomaly && (
            <>
              <Typography variant="body1" gutterBottom>
                {selectedAnomaly.description}
              </Typography>
              <Typography variant="caption" display="block" gutterBottom>
                Detected at: {formatTime(selectedAnomaly.timestamp)}
              </Typography>
              
              <TextField
                margin="dense"
                label="Resolved By"
                fullWidth
                variant="outlined"
                value={resolvedBy}
                onChange={(e) => setResolvedBy(e.target.value)}
              />
              
              <TextField
                margin="dense"
                label="Resolution Notes"
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button onClick={handleResolveAnomaly} variant="contained" color="primary">
            Resolve
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AnomalyDetection;
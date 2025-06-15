import React, { useState, useEffect } from 'react';
import { Box, Grid, Card, CardContent, Typography, CircularProgress, Tooltip } from '@mui/material';
import {
  Speed as SpeedIcon,
  Warning as WarningIcon,
  Router as RouterIcon,
  DataUsage as DataUsageIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import axios from 'axios';

// Import constants and auth service
const API_URL = '/api/v1';
const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * KPI Dashboard component for displaying key performance indicators
 */
const KPIDashboard: React.FC = () => {
  // State for KPI data
  const [kpiData, setKpiData] = useState({
    packetsPerSecond: 0,
    anomaliesToday: 0,
    devicesOnline: 0,
    totalTraffic: 0,
    detectionAccuracy: 0
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Define response type for dashboard statistics
  interface DashboardStatisticsResponse {
    packets_per_second: number;
    anomalies_today: number;
    devices_online: number;
    total_traffic_mb: number;
    detection_accuracy: number;
    anomaly_stats: Record<string, any>;
  }

  // Fetch KPI data from API
  const fetchKpiData = async () => {
    try {
      setLoading(true);
      
      // Get statistics from API
      const response = await axios.get<DashboardStatisticsResponse>(
        `${API_URL}/statistics/dashboard`,
        { headers: getAuthHeader() }
      );
      
      setKpiData({
        packetsPerSecond: response.data.packets_per_second || 0,
        anomaliesToday: response.data.anomalies_today || 0,
        devicesOnline: response.data.devices_online || 0,
        totalTraffic: response.data.total_traffic_mb || 0,
        detectionAccuracy: response.data.detection_accuracy || 0
      });
      
      setError(null);
    } catch (err) {
      console.error('Error fetching KPI data:', err);
      
      // Use mock data if API fails
      setKpiData({
        packetsPerSecond: 245,
        anomaliesToday: 12,
        devicesOnline: 8,
        totalTraffic: 1254,
        detectionAccuracy: 92.5
      });
      
      setError('Using sample data - API connection failed');
    } finally {
      setLoading(false);
    }
  };

  // Initial data load and polling
  useEffect(() => {
    fetchKpiData();
    
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchKpiData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // KPI card items
  const kpiItems = [
    {
      title: 'Packets/Second',
      value: kpiData.packetsPerSecond,
      icon: <SpeedIcon fontSize="large" color="primary" />,
      tooltip: 'Current network traffic rate',
      unit: 'pkt/s',
      color: 'primary.main'
    },
    {
      title: 'Anomalies Today',
      value: kpiData.anomaliesToday,
      icon: <WarningIcon fontSize="large" color="error" />,
      tooltip: 'Anomalies detected in the last 24 hours',
      unit: '',
      color: 'error.main'
    },
    {
      title: 'Devices Online',
      value: kpiData.devicesOnline,
      icon: <RouterIcon fontSize="large" color="success" />,
      tooltip: 'Number of active devices currently being monitored',
      unit: '',
      color: 'success.main'
    },
    {
      title: 'Total Traffic',
      value: kpiData.totalTraffic,
      icon: <DataUsageIcon fontSize="large" color="info" />,
      tooltip: 'Total network traffic processed today',
      unit: 'MB',
      color: 'info.main'
    },
    {
      title: 'Detection Accuracy',
      value: kpiData.detectionAccuracy,
      icon: <SecurityIcon fontSize="large" color="secondary" />,
      tooltip: 'Current model detection accuracy based on validation',
      unit: '%',
      color: 'secondary.main'
    }
  ];

  return (
    <Box sx={{ width: '100%', mb: 3 }}>
      {error && (
        <Typography 
          variant="caption" 
          color="error" 
          sx={{ display: 'block', mb: 1, textAlign: 'center' }}
        >
          {error}
        </Typography>
      )}
      
      <Grid container spacing={2}>
        {kpiItems.map((item) => (
          <Grid item xs={12} sm={6} md={4} lg={2.4} key={item.title}>
            <Tooltip title={item.tooltip} arrow placement="top">
              <Card 
                elevation={2} 
                sx={{ 
                  height: '100%',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-5px)',
                    boxShadow: 6
                  }
                }}
              >
                <CardContent sx={{ textAlign: 'center', p: 2 }}>
                  <Box sx={{ mb: 1 }}>
                    {item.icon}
                  </Box>
                  
                  <Typography variant="h6" component="div" gutterBottom>
                    {item.title}
                  </Typography>
                  
                  {loading ? (
                    <CircularProgress size={24} thickness={4} />
                  ) : (
                    <Typography 
                      variant="h4" 
                      component="div" 
                      sx={{ fontWeight: 'bold', color: item.color }}
                    >
                      {item.value}{item.unit}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Tooltip>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default KPIDashboard;

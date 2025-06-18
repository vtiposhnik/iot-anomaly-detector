import React, { useState } from 'react';
import {
  Typography,
  Box,
  Tabs,
  Tab,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Area,
  ComposedChart
} from 'recharts';
import { DeviceData } from '../types';
import { FilterAlt as FilterIcon } from '@mui/icons-material';

interface DataVisualizationProps {
  data: DeviceData[];
}

// Helper function to get the value from a device data object
const getMetricValue = (data: any, metricKey: string): number => {
  if (metricKey === 'throughput' || metricKey === 'latency' || metricKey === 'connectionCount') {
    return data.network?.[metricKey] || 0;
  }
  return data[metricKey] || 0;
};

// Format timestamp for display
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
};

const DataVisualization: React.FC<DataVisualizationProps> = ({ data }) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [showAnomaliesOnly, setShowAnomaliesOnly] = useState(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleViewToggle = (_event: React.MouseEvent<HTMLElement>, newView: string) => {
    setShowAnomaliesOnly(newView === 'anomalies');
  };

  // Define network metrics to visualize
  const metrics = [
    { name: 'Packet Size', key: 'packetSize', color: '#e74c3c', unit: 'bytes' },
    { name: 'Throughput', key: 'throughput', color: '#3498db', unit: 'bytes/s' },
    { name: 'Latency', key: 'latency', color: '#2ecc71', unit: 'ms' },
    { name: 'Connection Count', key: 'connectionCount', color: '#f39c12', unit: 'conn' }
  ];

  // Sort data by timestamp
  const sortedData = [...data].sort((a, b) =>
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Filter data based on the toggle selection
  const filteredData = showAnomaliesOnly
    ? sortedData.filter(item => item.status === 'anomaly')
    : sortedData;

  // Prepare data for Recharts
  const currentMetric = metrics[selectedTab];
  const chartData = filteredData.map(item => ({
    timestamp: formatTimestamp(item.timestamp),
    rawTimestamp: item.timestamp,
    value: getMetricValue(item, currentMetric.key),
    isAnomaly: item.status === 'anomaly',
    deviceId: (item as any).deviceId || 'unknown', // Handle deviceId property safely
  }));

  // Custom tooltip for the chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box sx={{
          bgcolor: 'background.paper',
          p: 1.5,
          border: '1px solid rgba(0, 0, 0, 0.12)',
          borderRadius: 1,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          fontSize: '0.875rem'
        }}>
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            {new Date(data.rawTimestamp).toLocaleString()}
          </Typography>
          <Typography variant="body2" sx={{
            color: data.isAnomaly ? '#e74c3c' : 'text.primary',
            fontWeight: data.isAnomaly ? 'bold' : 'normal'
          }}>
            {currentMetric.name}: {data.value} {currentMetric.unit}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Device ID: {data.deviceId}
          </Typography>
          {data.isAnomaly && (
            <Typography variant="body2" sx={{ color: '#e74c3c', fontWeight: 'bold', mt: 0.5 }}>
              Anomaly Detected!
            </Typography>
          )}
        </Box>
      );
    }
    return null;
  };

  return (
    <Box sx={{
      borderRadius: 2,
      height: '100%',
      bgcolor: 'background.paper',
      flexGrow: 1,
      border: '1px solid rgba(0, 0, 0, 0.08)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Box sx={{
        p: 2,
        borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="h6" component="h2">
          Network Traffic Visualization
        </Typography>
        <ToggleButtonGroup
          size="small"
          value={showAnomaliesOnly ? 'anomalies' : 'all'}
          exclusive
          onChange={handleViewToggle}
          aria-label="traffic view"
        >
          <ToggleButton value="all" aria-label="all traffic">
            All
          </ToggleButton>
          <ToggleButton value="anomalies" aria-label="anomalies only">
            <FilterIcon fontSize="small" sx={{ mr: 0.5 }} />
            Anomalies
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Tabs
        value={selectedTab}
        onChange={handleTabChange}
        aria-label="network metrics tabs"
        variant="fullWidth"
        indicatorColor="secondary"
        textColor="secondary"
        sx={{
          borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
          '& .MuiTab-root': {
            fontWeight: 500,
            py: 1.5,
          },
        }}
      >
        {metrics.map((metric, index) => (
          <Tab
            key={metric.key}
            label={metric.name}
            id={`metric-tab-${index}`}
            icon={<Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                bgcolor: metric.color,
                display: 'inline-block',
                mr: 1
              }}
            />}
            iconPosition="start"
          />
        ))}
      </Tabs>

      <Box
        className="chart-container"
        sx={{
          p: { xs: 1, sm: 2 },
          pt: 1,
          pb: 2,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '250px',
          overflow: 'visible'
        }}
      >
        {filteredData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.6} />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12 }}
                label={{
                  value: 'Time',
                  position: 'insideBottomRight',
                  offset: -10,
                  fontSize: 12
                }}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                label={{
                  value: `${currentMetric.name} (${currentMetric.unit})`,
                  angle: -90,
                  position: 'insideLeft',
                  fontSize: 12
                }}
              />
              <RechartsTooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                fill={`${currentMetric.color}20`}
                stroke="none"
                activeDot={false}
              />
              <Line
                key={filteredData.length}
                type="monotone"
                dataKey="value"
                stroke={currentMetric.color}
                strokeWidth={2}
                dot={(props: any) => {
                  const { cx, cy, payload } = props;
                  const isAnomaly = payload.isAnomaly;
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isAnomaly ? 5 : 3.5}
                      fill={isAnomaly ? '#e74c3c' : currentMetric.color}
                      stroke={isAnomaly ? '#c0392b' : 'none'}
                      strokeWidth={isAnomaly ? 1.5 : 0}
                    />
                  );
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <Box sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            p: 4,
            bgcolor: '#fff',
            borderRadius: 2,
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
            width: '100%'
          }}>
            <Typography variant="body2" color="text.secondary">
              {showAnomaliesOnly ? 'No anomalies detected for this metric' : 'No data available for this device'}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default DataVisualization;
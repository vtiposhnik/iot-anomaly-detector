import axios from 'axios';
import applyCaseMiddleware from 'axios-case-converter';
import { DeviceData, FormattedAnomaly, Device } from '../types';
import { TOKEN_KEY } from '@/constants/constants';

// Using Device from shared types

// Raw traffic data from the API
interface TrafficData {
  logId: number;
  deviceId: number;
  timestamp: string;
  sourceIp: string;
  sourcePort: number;
  destIp: string;
  destPort: number;
  protocol: string;
  service: string;
  duration: number;
  origBytes: number;
  respBytes: number;
  packetSize: number;
  connState: string;
  label: string;
  attackType: string;
}

// Raw anomaly data from the API
interface Anomaly {
  anomalyId: number;
  logId: number;
  deviceId: number;
  typeId: number;
  score: number;
  isGenuine: boolean;
  modelUsed: string;
  detectedAt: string;
}

// Using DeviceData from shared types

// Aggregated network data
interface AggregatedData {
  timestamp: string;
  packetSize: number;
  throughput: number;
  latency: number;
  connectionCount: number;
}

// Using FormattedAnomaly from shared types

// Using relative path for proxy to avoid CORS issues
const API_URL = '/api/v1';

// Create axios instance with case converter middleware
const api = applyCaseMiddleware(axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
}));

api.interceptors.request.use((config: any) => {
  const token = localStorage.getItem(TOKEN_KEY); // or from context/store
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error: any) => {
  return Promise.reject(error);
});

// Device API calls
export const fetchDevices = async (): Promise<Device[]> => {
  const response = await api.get<Device[]>('/devices');
  return response.data;
};

export const fetchDeviceById = async (deviceId: string): Promise<Device | undefined> => {
  // Filter devices to find the specific one
  const devices = await fetchDevices();
  return devices.find(device => device.deviceId.toString() === deviceId);
};

export const fetchDeviceStats = async (deviceId: string) => {
  // Get traffic data for the device and calculate stats
  const trafficData = await fetchDeviceData(deviceId);

  // Calculate some basic stats from the traffic data
  return {
    totalTraffic: trafficData.length,
    lastSeen: trafficData.length > 0 ? trafficData[0].timestamp : null,
    anomalyCount: (await fetchDeviceAnomalies(deviceId)).length
  };
};

// Traffic data API calls
export const fetchDeviceData = async (deviceId: string, limit = 100): Promise<DeviceData[]> => {
  // With axios-case-converter, we can use camelCase in our code
  // It will automatically convert to snake_case when sending to the API
  const response = await api.get<TrafficData[]>('/data', {
    params: { deviceId, limit }
  });

  // Transform the data to match the frontend's expected format with actual network metrics
  return response.data.map((item: TrafficData) => ({
    id: item.deviceId.toString(),
    timestamp: item.timestamp,
    packetSize: item.packetSize,
    origBytes: item.origBytes,
    respBytes: item.respBytes,
    duration: item.duration,
    status: item.label === 'Benign' ? 'normal' : 'anomaly',
    network: {
      packetLoss: Math.min(5, Math.random() * (item.label === 'Benign' ? 1 : 5)), // Lower for benign traffic
      latency: item.duration * 1000, // Convert to milliseconds
      throughput: (item.origBytes + item.respBytes) / (item.duration || 1), // Bytes per second
      connectionCount: Math.floor(Math.random() * (item.label === 'Benign' ? 5 : 15)) // Higher for anomalous traffic
    }
  }));
};

export const fetchAggregatedData = async (deviceId: string, _timeframe = 'day'): Promise<AggregatedData[]> => {
  // For now, we'll just use the regular data and mock aggregation
  const data = await fetchDeviceData(deviceId);

  // Group by hour (simple mock aggregation)
  const aggregated: Record<number, {
    count: number;
    packetSize: number;
    throughput: number;
    latency: number;
    connectionCount: number;
    timestamp: string;
  }> = {};

  data.forEach(item => {
    const date = new Date(item.timestamp);
    const hour = date.getHours();

    if (!aggregated[hour]) {
      aggregated[hour] = {
        count: 0,
        packetSize: 0,
        throughput: 0,
        latency: 0,
        connectionCount: 0,
        timestamp: `${date.toISOString().split('T')[0]}T${hour}:00:00Z`
      };
    }

    aggregated[hour].count++;
    aggregated[hour].packetSize += item.packetSize;
    aggregated[hour].throughput += item.network.throughput;
    aggregated[hour].latency += item.network.latency;
    aggregated[hour].connectionCount += item.network.connectionCount;
  });

  // Calculate averages
  return Object.values(aggregated).map(item => ({
    timestamp: item.timestamp,
    packetSize: item.packetSize / item.count,
    throughput: item.throughput / item.count,
    latency: item.latency / item.count,
    connectionCount: item.connectionCount / item.count
  }));
};

// Anomaly API calls
export const fetchAnomalies = async (params = {}): Promise<FormattedAnomaly[]> => {
  const response = await api.get<Anomaly[]>('/anomalies', { params });

  // Create a Set to track used IDs and ensure uniqueness
  const usedIds = new Set<string>();

  // Transform the data to match the frontend's expected format
  return response.data.map((item: Anomaly, index: number) => {
    // Create a base ID from the anomalyId
    let baseId = item.anomalyId.toString();

    // If this ID is already used, make it unique by appending the index
    let uniqueId = baseId;
    if (usedIds.has(baseId)) {
      uniqueId = `${baseId}-${index}`;
    }

    // Add the ID to the set of used IDs
    usedIds.add(uniqueId);

    return {
      id: uniqueId,
      deviceId: item.deviceId.toString(),
      timestamp: item.detectedAt,
      type: item.modelUsed || 'Unknown',
      severity: item.score > 0.8 ? 'high' : item.score > 0.5 ? 'medium' : 'low',
      value: item.score,
      threshold: 0.5,
      description: `Anomaly detected by ${item.modelUsed} with score ${item.score.toFixed(2)}`,
      resolved: !item.isGenuine
    };
  });
};

export const fetchDeviceAnomalies = async (deviceId: string, params = {}): Promise<FormattedAnomaly[]> => {
  // With axios-case-converter, we can use camelCase in our code
  const allAnomalies = await fetchAnomalies({
    ...params,
    deviceId // This will be automatically converted to device_id
  });

  return allAnomalies;
};

export const resolveAnomaly = async (anomalyId: string, data: any) => {
  // The backend doesn't have this endpoint yet, so we'll mock it
  console.log(`Resolving anomaly ${anomalyId} with data:`, data);

  // Return a mock response
  return {
    success: true,
    anomalyId,
    resolved: true,
    message: 'Anomaly marked as resolved'
  };
};

export const fetchAnomalyStats = async () => {
  // Get all anomalies and calculate stats
  const anomalies = await fetchAnomalies();

  const highSeverity = anomalies.filter(a => a.severity === 'high').length;
  const mediumSeverity = anomalies.filter(a => a.severity === 'medium').length;
  const lowSeverity = anomalies.filter(a => a.severity === 'low').length;

  return {
    total: anomalies.length,
    resolved: anomalies.filter(a => a.resolved).length,
    unresolved: anomalies.filter(a => !a.resolved).length,
    bySeverity: {
      high: highSeverity,
      medium: mediumSeverity,
      low: lowSeverity
    }
  };
};

export default {
  fetchDevices,
  fetchDeviceById,
  fetchDeviceStats,
  fetchDeviceData,
  fetchAggregatedData,
  fetchAnomalies,
  fetchDeviceAnomalies,
  resolveAnomaly,
  fetchAnomalyStats
};

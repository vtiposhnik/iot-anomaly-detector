// Shared types for the application

export interface DeviceData {
  id: string;
  timestamp: string;
  packetSize: number;
  origBytes: number;
  respBytes: number;
  duration: number;
  status: string;
  network: {
    packetLoss: number;
    latency: number;
    throughput: number;
    connectionCount: number;
  };
}

export interface FormattedAnomaly {
  id: string;
  deviceId: string;
  timestamp: string;
  type: string;
  severity: string;
  value: number;
  threshold: number;
  description: string;
  resolved: boolean;
}

export interface Device {
  deviceId: number;
  ipAddress: string;
  typeId: number;
  status: boolean;
  lastSeen: string;
  name?: string;
  type?: string;
  location?: string;
}

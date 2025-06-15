// Mock socket service since the Python backend doesn't support WebSockets yet
import api from './api';

class SocketService {
  private connected: boolean = false;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private pollingInterval: number | null = null;
  private lastAnomalyCount: number = 0;
  private simulationInterval: number | null = null;

  // Initialize connection
  connect() {
    if (this.connected) return;
    this.connected = true;
    console.log('Socket simulation started');

    // Start polling for anomalies every 10 seconds
    this.pollingInterval = window.setInterval(() => {
      this.pollForAnomalies();
    }, 10000);

    // Simulate data updates every 5 seconds
    this.simulationInterval = window.setInterval(() => {
      this.simulateDataUpdates();
    }, 5000);
  }

  // Disconnect
  disconnect() {
    this.connected = false;
    if (this.pollingInterval) {
      window.clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    if (this.simulationInterval) {
      window.clearInterval(this.simulationInterval);
      this.simulationInterval = null;
    }
    console.log('Socket simulation stopped');
  }

  // Poll for new anomalies
  private async pollForAnomalies() {
    if (!this.connected) return;

    try {
      const anomalies = await api.fetchAnomalies();
      
      // Check if we have new anomalies
      if (anomalies.length > this.lastAnomalyCount) {
        // Get new anomalies
        const newAnomalies = anomalies.slice(0, anomalies.length - this.lastAnomalyCount);
        
        // Notify listeners about each new anomaly
        newAnomalies.forEach((anomaly: any) => {
          this.notifyListeners('anomaly_alert', anomaly);
        });
        
        this.lastAnomalyCount = anomalies.length;
      }
    } catch (error) {
      console.error('Error polling for anomalies:', error);
    }
  }

  // Simulate real-time data updates
  private simulateDataUpdates() {
    if (!this.connected) return;

    // Generate a mock data update
    const mockData = {
      id: Math.floor(Math.random() * 50).toString(), // Random device ID between 0-49
      timestamp: new Date().toISOString(),
      temperature: 20 + Math.random() * 10,
      humidity: 30 + Math.random() * 40,
      pressure: 900 + Math.random() * 200,
      vibration: Math.random() * 5,
      status: Math.random() > 0.9 ? 'anomaly' : 'normal',
      network: {
        packetLoss: Math.random() * 5,
        latency: 10 + Math.random() * 100,
        throughput: 100 + Math.random() * 900,
        connectionCount: Math.floor(Math.random() * 10)
      }
    };

    // Notify listeners
    this.notifyListeners('data_update', mockData);

    // Occasionally simulate a device status change
    if (Math.random() > 0.8) {
      const deviceStatus = {
        deviceId: Math.floor(Math.random() * 50).toString(),
        status: Math.random() > 0.5 ? 'online' : 'offline',
        lastSeen: new Date().toISOString()
      };
      this.notifyListeners('device_status', deviceStatus);
    }

    // Occasionally simulate an anomaly
    if (Math.random() > 0.9) {
      const anomaly = {
        _id: Date.now().toString(),
        deviceId: Math.floor(Math.random() * 50).toString(),
        timestamp: new Date().toISOString(),
        type: Math.random() > 0.5 ? 'Isolation Forest' : 'Local Outlier Factor',
        severity: Math.random() > 0.7 ? 'high' : Math.random() > 0.4 ? 'medium' : 'low',
        value: Math.random(),
        threshold: 0.5,
        description: `Simulated anomaly detected at ${new Date().toLocaleTimeString()}`,
        resolved: false
      };
      this.notifyListeners('anomaly_alert', anomaly);
    }
  }

  // Add event listener
  addEventListener(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
  }

  // Remove event listener
  removeEventListener(event: string, callback: (data: any) => void) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)?.delete(callback);
    }
  }

  // Notify all listeners for an event
  private notifyListeners(event: string, data: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)?.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }
}

// Create singleton instance
const socketService = new SocketService();

export default socketService;

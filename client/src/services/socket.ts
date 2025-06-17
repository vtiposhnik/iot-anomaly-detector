// Real-time WebSocket service for IoT anomaly detection system
// No need to import api as we're using real WebSockets now

class SocketService {
  private listeners: Record<string, Function[]> = {};
  private connected: boolean = false;
  private dataSocket: WebSocket | null = null;
  private anomalySocket: WebSocket | null = null;
  private reconnectInterval: number | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;

  // Get WebSocket base URL
  private getWebSocketUrl(): string {
    // Convert HTTP/HTTPS to WS/WSS
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    // If we're in development mode, use the backend server directly
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return `${protocol}//localhost:5000/api/v1/ws`;
    }
    
    // In production, use the same host (assuming backend and frontend are served from the same domain)
    return `${protocol}//${host}/api/v1/ws`;
  }

  // Connect to WebSockets
  connect() {
    if (this.connected) return;
    
    try {
      const baseUrl = this.getWebSocketUrl();
      
      // Connect to data WebSocket
      this.dataSocket = new WebSocket(`${baseUrl}/data`);
      this.setupDataSocketListeners();
      
      // Connect to anomaly WebSocket
      this.anomalySocket = new WebSocket(`${baseUrl}/anomalies`);
      this.setupAnomalySocketListeners();
      
      this.connected = true;
      console.log('WebSocket connections established');
      
      // Reset reconnect attempts on successful connection
      this.reconnectAttempts = 0;
    } catch (error) {
      console.error('Error connecting to WebSockets:', error);
      this.scheduleReconnect();
    }
  }

  // Set up listeners for the data WebSocket
  private setupDataSocketListeners() {
    if (!this.dataSocket) return;
    
    this.dataSocket.onopen = () => {
      console.log('Data WebSocket connected');
    };
    
    this.dataSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type && this.listeners[data.type]) {
          this.notifyListeners(data.type, data.data);
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };
    
    this.dataSocket.onclose = () => {
      console.log('Data WebSocket disconnected');
      if (this.connected) {
        this.scheduleReconnect();
      }
    };
    
    this.dataSocket.onerror = (error) => {
      console.error('Data WebSocket error:', error);
    };
  }

  // Set up listeners for the anomaly WebSocket
  private setupAnomalySocketListeners() {
    if (!this.anomalySocket) return;
    
    this.anomalySocket.onopen = () => {
      console.log('Anomaly WebSocket connected');
    };
    
    this.anomalySocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type && this.listeners[data.type]) {
          this.notifyListeners(data.type, data.data);
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };
    
    this.anomalySocket.onclose = () => {
      console.log('Anomaly WebSocket disconnected');
      if (this.connected) {
        this.scheduleReconnect();
      }
    };
    
    this.anomalySocket.onerror = (error) => {
      console.error('Anomaly WebSocket error:', error);
    };
  }

  // Schedule reconnection attempt
  private scheduleReconnect() {
    if (this.reconnectInterval) {
      window.clearTimeout(this.reconnectInterval);
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
      
      this.reconnectInterval = window.setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error(`Failed to reconnect after ${this.maxReconnectAttempts} attempts`);
    }
  }

  // Disconnect from WebSockets
  disconnect() {
    this.connected = false;
    
    if (this.reconnectInterval) {
      window.clearTimeout(this.reconnectInterval);
      this.reconnectInterval = null;
    }
    
    if (this.dataSocket) {
      this.dataSocket.close();
      this.dataSocket = null;
    }
    
    if (this.anomalySocket) {
      this.anomalySocket.close();
      this.anomalySocket = null;
    }
    
    console.log('WebSocket connections closed');
  }

  // Send a message to the data WebSocket
  sendToDataSocket(message: any) {
    if (this.dataSocket && this.dataSocket.readyState === WebSocket.OPEN) {
      this.dataSocket.send(JSON.stringify(message));
    } else {
      console.error('Cannot send message: Data WebSocket not connected');
    }
  }

  // Send a message to the anomaly WebSocket
  sendToAnomalySocket(message: any) {
    if (this.anomalySocket && this.anomalySocket.readyState === WebSocket.OPEN) {
      this.anomalySocket.send(JSON.stringify(message));
    } else {
      console.error('Cannot send message: Anomaly WebSocket not connected');
    }
  }

  // Subscribe to a specific device's data
  subscribeToDevice(deviceId: string) {
    this.sendToDataSocket({
      type: 'subscribe_device',
      deviceId: deviceId
    });
  }

  // Add event listener
  addEventListener(event: string, callback: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  // Remove event listener
  removeEventListener(event: string, callback: (data: any) => void) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  // Notify all listeners of an event
  private notifyListeners(event: string, data: any) {
    if (!this.listeners[event]) return;
    
    this.listeners[event].forEach(callback => {
      (callback as Function)(data);
    });
  }
}

// Create singleton instance
const socketService = new SocketService();

export default socketService;

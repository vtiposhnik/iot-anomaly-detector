import authService from './authService';

class SocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

    const token = authService.getToken();
    const url = token
      ? `ws://localhost:5000/ws?token=${encodeURIComponent(token)}`
      : 'ws://localhost:5000/ws';

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event) {
          this.notifyListeners(msg.event, msg.data);
        }
      } catch (e) {
        console.error('Invalid websocket message', e);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.ws = null;
    };

    this.ws.onerror = (err) => {
      console.error('WebSocket error', err);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  addEventListener(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
  }

  removeEventListener(event: string, callback: (data: any) => void) {
    this.listeners.get(event)?.delete(callback);
  }

  private notifyListeners(event: string, data: any) {
    this.listeners.get(event)?.forEach(cb => {
      try {
        cb(data);
      } catch (err) {
        console.error(`Error in ${event} listener`, err);
      }
    });
  }
}

const socketService = new SocketService();
export default socketService;

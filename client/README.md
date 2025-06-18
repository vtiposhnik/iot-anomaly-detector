# IoT Anomaly Monitor

A React application for monitoring IoT devices and detecting anomalies in sensor data using artificial intelligence techniques.

## Features

- Real-time monitoring of multiple IoT devices
- Interactive data visualization of sensor metrics (temperature, humidity, pressure, vibration)
- Anomaly detection with customizable threshold rules
- Responsive dashboard UI with Material UI

## Technology Stack

- React 18 with TypeScript for the frontend
- D3.js for data visualization
- CSV-Parse for data processing
- Material UI for the user interface components

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm 8.x or higher

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/iot-anomaly-monitor.git
cd iot-anomaly-monitor
```

2. Install dependencies:
```
npm install
```

### Environment Variables

Create a `.env` file in the `client` directory with the following variables or copy and rename `.env.example`:

```
VITE_API_URL=http://localhost:5000/api/v1
VITE_WS_URL=ws://localhost:5000/ws
```

These values configure the backend API endpoint and WebSocket server used by the frontend.

3. Run the development server:
```
npm start
```

4. Open your browser and navigate to `http://localhost:3000`

## How It Works

The application loads IoT sensor data from CSV files (simulating real device data) and performs analysis to detect anomalies based on predefined thresholds:

- Temperature > 80°C indicates potential overheating
- Vibration > 15Hz indicates potential mechanical issues

In a production environment, this would be connected to real IoT devices via APIs and could employ more sophisticated machine learning algorithms for anomaly detection.

## Project Structure

- `/src/components` - React components for the UI
- `/public/data` - Sample CSV data for demonstration
- `/src/App.tsx` - Main application component

## Future Enhancements

- Implement machine learning algorithms for more sophisticated anomaly detection
- Add real-time data streaming from IoT devices
- Implement notifications for critical anomalies
- Add user authentication and device management features 

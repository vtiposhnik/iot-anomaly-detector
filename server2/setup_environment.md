# Setting Up the Environment for IoT Anomaly Detection

This guide will help you set up a compatible Python environment for the IoT Anomaly Detection system.

## Python Version Compatibility

The application uses Flask 2.0.1, which is not fully compatible with Python 3.13. For best results, we recommend using Python 3.9-3.11.

## Option 1: Install Python 3.11 (Recommended)

1. Download Python 3.11 from the official website:
   - Visit [python.org/downloads](https://www.python.org/downloads/)
   - Select Python 3.11.x (latest 3.11 version)
   - Run the installer and check "Add Python to PATH"

2. Create a virtual environment:
   ```powershell
   # Navigate to your project directory
   cd c:\Users\akzho\OneDrive\Documents\backup\new\server2
   
   # Create a virtual environment
   python3.11 -m venv venv
   
   # Activate the virtual environment
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```powershell
   # Install required packages
   pip install -r requirements.txt
   ```

4. Initialize the database and models:
   ```powershell
   # Initialize the database
   python -c "from utils.database import init_db, import_csv_to_db; init_db(); import_csv_to_db()"
   
   # Initialize the ML models
   python init_ml_models.py
   ```

5. Run the application:
   ```powershell
   python app.py
   ```

## Option 2: Use a Conda Environment

If you have Anaconda or Miniconda installed:

1. Create a new environment:
   ```powershell
   conda create -n iot-anomaly python=3.11
   conda activate iot-anomaly
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Initialize and run as in Option 1 steps 4-5.

## Option 3: Update Flask (Alternative)

If you prefer to keep using Python 3.13:

1. Update the requirements.txt file:
   ```
   flask>=2.3.0
   flask-cors>=4.0.0
   numpy>=1.20.0
   pandas>=1.3.0
   scikit-learn>=0.24.2
   matplotlib>=3.4.2
   python-dotenv>=0.19.0
   ```

2. Install the updated dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Troubleshooting

If you encounter issues with the Flask application:

1. Check that you're using a compatible Python version:
   ```powershell
   python --version
   ```

2. Ensure all dependencies are installed:
   ```powershell
   pip list
   ```

3. Check for error messages in the console output.

4. If all else fails, use the `run_anomaly_detection.py` script to verify that the core functionality works:
   ```powershell
   python run_anomaly_detection.py
   ```

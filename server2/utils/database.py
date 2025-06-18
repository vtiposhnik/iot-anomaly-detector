"""
Database utility for the IoT Anomaly Detection System

This module provides functions for database operations.
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime
from utils.logger import get_logger

# Get logger
logger = get_logger()

# Constants
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'iot_anomaly.db')

# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)

def get_db_connection():
    """
    Get a connection to the SQLite database
    
    Returns:
        Connection object
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database with required tables
    
    Returns:
        Boolean indicating success
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create devices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id INTEGER PRIMARY KEY,
            ip_address TEXT NOT NULL,
            type_id INTEGER DEFAULT 1,
            status BOOLEAN DEFAULT 1,
            last_seen TIMESTAMP
        )
        ''')
        
        # Create traffic table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic (
            log_id INTEGER PRIMARY KEY,
            link_id INTEGER,
            device_id INTEGER,
            timestamp TIMESTAMP,
            source_ip TEXT,
            source_port INTEGER,
            dest_ip TEXT,
            dest_port INTEGER,
            protocol TEXT,
            service TEXT,
            duration REAL,
            orig_bytes INTEGER,
            resp_bytes INTEGER,
            packet_size INTEGER,
            conn_state TEXT,
            label TEXT,
            attack_type TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (device_id)
        )
        ''')
        
        # Create links table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY,
            abonent_id INTEGER,
            address_id INTEGER,
            FOREIGN KEY (abonent_id) REFERENCES devices (device_id),
            FOREIGN KEY (address_id) REFERENCES devices (device_id)
        )
        ''')
        
        # Create anomalies table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS anomalies (
            anomaly_id INTEGER PRIMARY KEY,
            log_id INTEGER,
            device_id INTEGER,
            type_id INTEGER,
            score REAL,
            is_genuine BOOLEAN,
            model_used TEXT,
            detected_at TIMESTAMP,
            FOREIGN KEY (log_id) REFERENCES traffic (log_id),
            FOREIGN KEY (device_id) REFERENCES devices (device_id)
        )
        ''')

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            full_name TEXT,
            disabled BOOLEAN DEFAULT 0,
            hashed_password TEXT NOT NULL,
            roles TEXT
        )
        ''')
        
        conn.commit()

        # Create default admin user if none exist
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed = pwd_context.hash("Admin123!")
            cursor.execute(
                "INSERT INTO users (username, email, full_name, disabled, hashed_password, roles) "
                "VALUES (?, ?, ?, 0, ?, ?)",
                ("admin", "admin@example.com", "Administrator", hashed, "admin"),
            )
            conn.commit()

        conn.close()

        logger.info("Database initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def import_csv_to_db():
    """
    Import processed CSV data to the database
    
    Returns:
        Boolean indicating success
    """
    try:
        # Check if processed data exists
        processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')
        devices_path = os.path.join(processed_dir, 'devices.csv')
        traffic_path = os.path.join(processed_dir, 'traffic.csv')
        links_path = os.path.join(processed_dir, 'links.csv')
        anomalies_path = os.path.join(processed_dir, 'anomalies.csv')
        
        if not all(os.path.exists(p) for p in [devices_path, traffic_path, links_path, anomalies_path]):
            logger.error("Processed data not found")
            return False
        
        # Initialize database
        init_db()
        
        conn = get_db_connection()
        
        # Import devices
        devices_df = pd.read_csv(devices_path)
        devices_df.to_sql('devices', conn, if_exists='replace', index=False)
        
        # Import traffic
        traffic_df = pd.read_csv(traffic_path)
        traffic_df.to_sql('traffic', conn, if_exists='replace', index=False)
        
        # Import links
        links_df = pd.read_csv(links_path)
        links_df.to_sql('links', conn, if_exists='replace', index=False)
        
        # Import anomalies
        anomalies_df = pd.read_csv(anomalies_path)
        anomalies_df.to_sql('anomalies', conn, if_exists='replace', index=False)
        
        conn.close()
        
        logger.info("Data imported to database successfully")
        logger.info(f"Devices: {len(devices_df)}")
        logger.info(f"Traffic records: {len(traffic_df)}")
        logger.info(f"Links: {len(links_df)}")
        logger.info(f"Anomalies: {len(anomalies_df)}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error importing data to database: {str(e)}")
        return False

def get_user_by_username(username: str):
    """Retrieve a single user by username."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            user = dict(row)
            user["roles"] = user.get("roles", "").split(",") if user.get("roles") else []
            return user
        return None
    except Exception as e:
        logger.error(f"Error getting user {username}: {str(e)}")
        return None

def get_all_users():
    """Return a list of all users."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()
        users = []
        for row in rows:
            user = dict(row)
            user["roles"] = user.get("roles", "").split(",") if user.get("roles") else []
            users.append(user)
        return users
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return []

def create_user(user: dict):
    """Insert a new user into the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, full_name, disabled, hashed_password, roles)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.get("username"),
                user.get("email"),
                user.get("full_name"),
                1 if user.get("disabled") else 0,
                user.get("hashed_password"),
                ",".join(user.get("roles", [])),
            ),
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except Exception as e:
        logger.error(f"Error creating user {user.get('username')}: {str(e)}")
        return None

def update_user(username: str, update_data: dict) -> bool:
    """Update an existing user."""
    try:
        if not update_data:
            return True
        conn = get_db_connection()
        cursor = conn.cursor()
        fields = []
        params = []
        for key, value in update_data.items():
            if key == "roles" and isinstance(value, list):
                value = ",".join(value)
            fields.append(f"{key} = ?")
            params.append(value)
        params.append(username)
        query = f"UPDATE users SET {', '.join(fields)} WHERE username = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating user {username}: {str(e)}")
        return False

def delete_user(username: str) -> bool:
    """Delete a user by username."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting user {username}: {str(e)}")
        return False

def get_devices(limit=100):
    """
    Get devices from the database
    
    Args:
        limit: Maximum number of devices to return
    
    Returns:
        List of devices
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM devices LIMIT {limit}')
        devices = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return devices
    
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return []

def get_traffic(limit=100):
    """
    Get traffic data from the database
    
    Args:
        limit: Maximum number of records to return
    
    Returns:
        List of traffic records
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM traffic LIMIT {limit}')
        traffic = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return traffic
    
    except Exception as e:
        logger.error(f"Error getting traffic data: {str(e)}")
        return []

def get_anomalies(limit=100):
    """
    Get anomalies from the database
    
    Args:
        limit: Maximum number of anomalies to return
    
    Returns:
        List of anomalies
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT a.*, t.source_ip, t.dest_ip, t.protocol, t.service, t.attack_type
        FROM anomalies a
        JOIN traffic t ON a.log_id = t.log_id
        LIMIT {limit}
        ''')
        anomalies = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return anomalies
    
    except Exception as e:
        logger.error(f"Error getting anomalies: {str(e)}")
        return []

def add_anomaly(anomaly):
    """
    Add a new anomaly to the database
    
    Args:
        anomaly: Dictionary containing anomaly data
    
    Returns:
        ID of the inserted anomaly
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO anomalies (
            log_id, device_id, type_id, score, is_genuine, model_used, detected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            anomaly.get('log_id'),
            anomaly.get('device_id'),
            anomaly.get('type_id', 1),
            anomaly.get('score', 0.0),
            anomaly.get('is_genuine', True),
            anomaly.get('model_used', 'Unknown'),
            anomaly.get('detected_at', datetime.now().isoformat())
        ))
        
        anomaly_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return anomaly_id
    
    except Exception as e:
        logger.error(f"Error adding anomaly: {str(e)}")
        return None

def insert_anomalies(anomalies_df):
    """
    Insert detected anomalies into the database
    
    Args:
        anomalies_df: DataFrame containing detected anomalies
    
    Returns:
        Number of anomalies inserted
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        count = 0
        
        for _, row in anomalies_df.iterrows():
            # Extract device ID
            device_id = row['device_id']
            
            # Get or create log ID
            cursor.execute(
                "INSERT INTO traffic_logs (device_id, timestamp, source_ip, source_port, dest_ip, dest_port, protocol) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (device_id, row['timestamp'], row['src_ip'], row['src_port'], row['dst_ip'], row['dst_port'], row['protocol'])
            )
            log_id = cursor.lastrowid
            
            # Calculate score
            score = row.get('combined_score', row.get('if_score', row.get('lof_score', 0.5)))
            
            # Insert anomaly
            cursor.execute(
                "INSERT INTO anomalies (log_id, device_id, type_id, score, is_genuine, model_used, detected_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (log_id, device_id, 1, score, True, row.get('model_used', 'generic'), row['timestamp'])
            )
            
            count += 1
        
        conn.commit()
        logger.info(f"Inserted {count} anomalies into the database")
        return count
    
    except Exception as e:
        logger.error(f"Error inserting anomalies: {str(e)}")
        return 0

def get_anomalies_by_timerange(start_time, end_time, limit=100):
    """
    Get anomalies within a specific time range
    
    Args:
        start_time: Start timestamp (ISO format string or datetime object)
        end_time: End timestamp (ISO format string or datetime object)
        limit: Maximum number of records to return
    
    Returns:
        List of anomalies within the specified time range
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT a.*, t.source_ip, t.dest_ip, t.protocol, t.service, t.attack_type
        FROM anomalies a
        JOIN traffic t ON a.log_id = t.log_id
        WHERE a.detected_at BETWEEN ? AND ?
        ORDER BY a.detected_at DESC
        LIMIT ?
        ''', (start_time, end_time, limit))
        
        anomalies = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return anomalies
    
    except Exception as e:
        logger.error(f"Error getting anomalies by time range: {str(e)}")
        return []

def get_anomaly_statistics(days=7):
    """
    Get statistics about anomalies for dashboard visualization
    
    Args:
        days: Number of days to include in statistics
    
    Returns:
        Dictionary with anomaly statistics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get count by day for the last N days
        cursor.execute('''
            SELECT 
                date(detected_at) as day,
                COUNT(*) as count
            FROM 
                anomalies
            WHERE 
                detected_at >= date('now', ?) 
            GROUP BY 
                day
            ORDER BY 
                day
        ''', (f'-{days} days',))
        
        daily_counts = {row['day']: row['count'] for row in cursor.fetchall()}
        
        # Get count by model
        cursor.execute('''
            SELECT 
                model_used,
                COUNT(*) as count
            FROM 
                anomalies
            WHERE 
                detected_at >= date('now', ?)
            GROUP BY 
                model_used
        ''', (f'-{days} days',))
        
        model_counts = {row['model_used']: row['count'] for row in cursor.fetchall()}
        
        # Get count by device
        cursor.execute('''
            SELECT 
                device_id,
                COUNT(*) as count
            FROM 
                anomalies
            WHERE 
                detected_at >= date('now', ?)
            GROUP BY 
                device_id
            ORDER BY 
                count DESC
            LIMIT 10
        ''', (f'-{days} days',))
        
        device_counts = {row['device_id']: row['count'] for row in cursor.fetchall()}
        
        # Get total count
        cursor.execute('''
            SELECT 
                COUNT(*) as total
            FROM 
                anomalies
            WHERE 
                detected_at >= date('now', ?)
        ''', (f'-{days} days',))
        
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return {
            'total': total,
            'daily_counts': daily_counts,
            'model_counts': model_counts,
            'device_counts': device_counts
        }
    
    except Exception as e:
        logger.error(f"Error getting anomaly statistics: {str(e)}")
        return {
            'total': 0,
            'daily_counts': {},
            'model_counts': {},
            'device_counts': {}
        }

if __name__ == "__main__":
    # Initialize database and import data
    init_db()
    import_csv_to_db()

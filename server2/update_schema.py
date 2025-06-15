"""Update Database Schema

This script updates the database schema to add new features:
1. Enhanced device information (name, mac_addr, type, first_seen)
2. Improved traffic logs
3. New alerts table for notifications and user interactions
"""

import os
import sqlite3
from datetime import datetime
from utils.logger import get_logger
from utils.database import DB_PATH, get_db_connection

# Setup logger
logger = get_logger()

def update_schema():
    """
    Update the database schema with new tables and columns
    
    Returns:
        Boolean indicating success
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if database exists and has tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
        if not cursor.fetchone():
            logger.error("Database not initialized. Please run init_db() first.")
            return False
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Update devices table
        logger.info("Updating devices table...")
        try:
            # Add new columns to devices table
            cursor.execute("ALTER TABLE devices ADD COLUMN name TEXT")
            cursor.execute("ALTER TABLE devices ADD COLUMN mac_addr TEXT")
            cursor.execute("ALTER TABLE devices ADD COLUMN type TEXT")
            cursor.execute("ALTER TABLE devices ADD COLUMN first_seen TIMESTAMP")
            
            # Update existing devices with default names
            cursor.execute("UPDATE devices SET name = 'Device ' || device_id WHERE name IS NULL")
            cursor.execute("UPDATE devices SET type = 'unknown' WHERE type IS NULL")
            cursor.execute("UPDATE devices SET first_seen = last_seen WHERE first_seen IS NULL")
            
            logger.info("Devices table updated successfully")
        except sqlite3.OperationalError as e:
            # Columns might already exist
            logger.warning(f"Note when updating devices table: {str(e)}")
        
        # 2. Update traffic table
        logger.info("Updating traffic table...")
        try:
            # Rename for clarity if needed
            cursor.execute("ALTER TABLE traffic RENAME COLUMN packet_size TO pkt_len")
            logger.info("Traffic table updated successfully")
        except sqlite3.OperationalError as e:
            logger.warning(f"Note when updating traffic table: {str(e)}")
        
        # 3. Create alerts table
        logger.info("Creating alerts table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            anomaly_id INTEGER,
            raised_at TIMESTAMP,
            cleared_at TIMESTAMP,
            severity TEXT,
            message TEXT,
            acknowledged BOOLEAN DEFAULT 0,
            FOREIGN KEY (anomaly_id) REFERENCES anomalies (anomaly_id)
        )
        ''')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info("Database schema updated successfully")
        return True
        
    except Exception as e:
        # Rollback in case of error
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"Error updating database schema: {str(e)}")
        return False

def populate_initial_alerts():
    """
    Populate initial alerts based on existing anomalies
    
    Returns:
        Number of alerts created
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get existing anomalies
        cursor.execute("""
        SELECT anomaly_id, device_id, score, detected_at 
        FROM anomalies 
        WHERE is_genuine = 1
        ORDER BY detected_at DESC
        LIMIT 100
        """)
        
        anomalies = cursor.fetchall()
        count = 0
        
        for anomaly in anomalies:
            # Determine severity based on score
            score = anomaly['score']
            if score >= 0.9:
                severity = "critical"
            elif score >= 0.7:
                severity = "warning"
            else:
                severity = "info"
            
            # Create alert message
            device_id = anomaly['device_id']
            cursor.execute("SELECT name FROM devices WHERE device_id = ?", (device_id,))
            device = cursor.fetchone()
            device_name = device['name'] if device and device['name'] else f"Device {device_id}"
            
            message = f"Anomaly detected on {device_name} with score {score:.2f}"
            
            # Check if alert already exists
            cursor.execute("""
            SELECT id FROM alerts WHERE anomaly_id = ?
            """, (anomaly['anomaly_id'],))
            
            if not cursor.fetchone():
                # Insert new alert
                cursor.execute("""
                INSERT INTO alerts (anomaly_id, raised_at, severity, message, acknowledged)
                VALUES (?, ?, ?, ?, 0)
                """, (anomaly['anomaly_id'], anomaly['detected_at'], severity, message))
                count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created {count} initial alerts")
        return count
        
    except Exception as e:
        logger.error(f"Error populating alerts: {str(e)}")
        return 0

if __name__ == "__main__":
    logger.info("Starting database schema update")
    if update_schema():
        populate_initial_alerts()
    logger.info("Schema update complete")

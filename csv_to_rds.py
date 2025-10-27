#!/usr/bin/env python3
"""
Transfer CSV files to Amazon RDS
Reads sleep_data.csv, exercise_data.csv, and blood_glucose.csv
and uploads them to MySQL RDS database
"""

import csv
import pymysql
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('RDS_HOST', 'localhost'),
    'user': os.getenv('RDS_USER', 'root'),
    'password': os.getenv('RDS_PASSWORD', ''),
    'database': os.getenv('RDS_DATABASE', 'health_data'),
    'port': int(os.getenv('RDS_PORT', 3306)),
    'charset': 'utf8mb4'
}

def connect_to_database():
    """Connect to RDS database"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        logger.info("✅ Connected to database")
        return connection
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

def create_tables(connection):
    """Create tables if they don't exist"""
    cursor = connection.cursor()
    
    # Sleep data table
    sleep_table = """
    CREATE TABLE IF NOT EXISTS sleep_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL,
        bedtime DATETIME,
        wake_time DATETIME,
        sleep_duration_minutes INT,
        deep_sleep_minutes INT,
        light_sleep_minutes INT,
        rem_sleep_minutes INT,
        sleep_efficiency DECIMAL(5,2),
        heart_rate_avg INT,
        heart_rate_min INT,
        heart_rate_max INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY unique_date (date)
    )
    """
    
    # Exercise data table
    exercise_table = """
    CREATE TABLE IF NOT EXISTS exercise_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        activity_type VARCHAR(100),
        duration_minutes INT,
        calories_burned DECIMAL(8,2),
        distance_km DECIMAL(8,3),
        steps INT,
        heart_rate_avg INT,
        heart_rate_max INT,
        active_energy_kcal DECIMAL(8,2),
        resting_energy_kcal DECIMAL(8,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_timestamp (timestamp)
    )
    """
    
    # Blood glucose table
    glucose_table = """
    CREATE TABLE IF NOT EXISTS blood_glucose (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        value DECIMAL(6,2),
        unit VARCHAR(10),
        source VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_timestamp (timestamp)
    )
    """
    
    cursor.execute(sleep_table)
    cursor.execute(exercise_table)
    cursor.execute(glucose_table)
    connection.commit()
    logger.info("✅ Tables created/verified")

def upload_sleep_data(connection):
    """Upload sleep data from CSV to RDS"""
    cursor = connection.cursor()
    count = 0
    skip_count = 0
    
    try:
        with open('sleep_data.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row.get('date'):
                    continue
                
                try:
                    sleep_data = {
                        'date': row.get('date'),
                        'bedtime': row.get('bedtime') or None,
                        'wake_time': row.get('wake_time') or None,
                        'sleep_duration_minutes': int(row['sleep_duration_minutes']) if row.get('sleep_duration_minutes') else None,
                        'deep_sleep_minutes': int(row['deep_sleep_minutes']) if row.get('deep_sleep_minutes') else None,
                        'light_sleep_minutes': int(row['light_sleep_minutes']) if row.get('light_sleep_minutes') else None,
                        'rem_sleep_minutes': int(row['rem_sleep_minutes']) if row.get('rem_sleep_minutes') else None,
                        'sleep_efficiency': float(row['sleep_efficiency']) if row.get('sleep_efficiency') else None,
                        'heart_rate_avg': int(row['heart_rate_avg']) if row.get('heart_rate_avg') else None,
                        'heart_rate_min': int(row['heart_rate_min']) if row.get('heart_rate_min') else None,
                        'heart_rate_max': int(row['heart_rate_max']) if row.get('heart_rate_max') else None
                    }
                    
                    insert_query = """
                    INSERT INTO sleep_data 
                    (date, bedtime, wake_time, sleep_duration_minutes, deep_sleep_minutes, 
                     light_sleep_minutes, rem_sleep_minutes, sleep_efficiency, 
                     heart_rate_avg, heart_rate_min, heart_rate_max)
                    VALUES (%(date)s, %(bedtime)s, %(wake_time)s, %(sleep_duration_minutes)s, 
                            %(deep_sleep_minutes)s, %(light_sleep_minutes)s, %(rem_sleep_minutes)s, 
                            %(sleep_efficiency)s, %(heart_rate_avg)s, %(heart_rate_min)s, %(heart_rate_max)s)
                    ON DUPLICATE KEY UPDATE
                    bedtime = VALUES(bedtime),
                    wake_time = VALUES(wake_time),
                    sleep_duration_minutes = VALUES(sleep_duration_minutes),
                    deep_sleep_minutes = VALUES(deep_sleep_minutes),
                    light_sleep_minutes = VALUES(light_sleep_minutes),
                    rem_sleep_minutes = VALUES(rem_sleep_minutes),
                    sleep_efficiency = VALUES(sleep_efficiency),
                    heart_rate_avg = VALUES(heart_rate_avg),
                    heart_rate_min = VALUES(heart_rate_min),
                    heart_rate_max = VALUES(heart_rate_max),
                    updated_at = CURRENT_TIMESTAMP
                    """
                    
                    cursor.execute(insert_query, sleep_data)
                    count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error saving sleep record: {e}")
                    skip_count += 1
                    continue
        
        connection.commit()
        logger.info(f"✅ Uploaded {count} sleep records to RDS (skipped {skip_count})")
        
    except FileNotFoundError:
        logger.warning("⚠️ sleep_data.csv not found, skipping")

def upload_exercise_data(connection):
    """Upload exercise data from CSV to RDS"""
    cursor = connection.cursor()
    count = 0
    skip_count = 0
    
    try:
        with open('exercise_data.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row.get('timestamp'):
                    continue
                
                try:
                    exercise_data = {
                        'timestamp': row.get('timestamp'),
                        'activity_type': row.get('activity_type'),
                        'duration_minutes': int(row['duration_minutes']) if row.get('duration_minutes') else None,
                        'calories_burned': float(row['calories_burned']) if row.get('calories_burned') else None,
                        'distance_km': float(row['distance_km']) if row.get('distance_km') else None,
                        'steps': int(row['steps']) if row.get('steps') else None,
                        'heart_rate_avg': int(row['heart_rate_avg']) if row.get('heart_rate_avg') else None,
                        'heart_rate_max': int(row['heart_rate_max']) if row.get('heart_rate_max') else None,
                        'active_energy_kcal': float(row['active_energy_kcal']) if row.get('active_energy_kcal') else None,
                        'resting_energy_kcal': float(row['resting_energy_kcal']) if row.get('resting_energy_kcal') else None
                    }
                    
                    insert_query = """
                    INSERT INTO exercise_data 
                    (timestamp, activity_type, duration_minutes, calories_burned, distance_km, 
                     steps, heart_rate_avg, heart_rate_max, active_energy_kcal, resting_energy_kcal)
                    VALUES (%(timestamp)s, %(activity_type)s, %(duration_minutes)s, %(calories_burned)s, 
                            %(distance_km)s, %(steps)s, %(heart_rate_avg)s, %(heart_rate_max)s, 
                            %(active_energy_kcal)s, %(resting_energy_kcal)s)
                    ON DUPLICATE KEY UPDATE
                    activity_type = VALUES(activity_type),
                    duration_minutes = VALUES(duration_minutes),
                    calories_burned = VALUES(calories_burned),
                    distance_km = VALUES(distance_km),
                    steps = VALUES(steps),
                    heart_rate_avg = VALUES(heart_rate_avg),
                    heart_rate_max = VALUES(heart_rate_max),
                    active_energy_kcal = VALUES(active_energy_kcal),
                    resting_energy_kcal = VALUES(resting_energy_kcal)
                    """
                    
                    cursor.execute(insert_query, exercise_data)
                    count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error saving exercise record: {e}")
                    skip_count += 1
                    continue
        
        connection.commit()
        logger.info(f"✅ Uploaded {count} exercise records to RDS (skipped {skip_count})")
        
    except FileNotFoundError:
        logger.warning("⚠️ exercise_data.csv not found, skipping")

def upload_glucose_data(connection):
    """Upload blood glucose data from CSV to RDS"""
    cursor = connection.cursor()
    count = 0
    skip_count = 0
    
    try:
        with open('blood_glucose.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row.get('timestamp'):
                    continue
                
                try:
                    glucose_data = {
                        'timestamp': row.get('timestamp'),
                        'value': float(row['value']) if row.get('value') else None,
                        'unit': row.get('unit', 'mg/dL'),
                        'source': row.get('source')
                    }
                    
                    insert_query = """
                    INSERT INTO blood_glucose 
                    (timestamp, value, unit, source)
                    VALUES (%(timestamp)s, %(value)s, %(unit)s, %(source)s)
                    ON DUPLICATE KEY UPDATE
                    value = VALUES(value),
                    unit = VALUES(unit),
                    source = VALUES(source)
                    """
                    
                    cursor.execute(insert_query, glucose_data)
                    count += 1
                    
                    # Log progress every 1000 records
                    if count % 1000 == 0:
                        logger.info(f"📊 Processed {count} glucose records...")
                    
                except Exception as e:
                    logger.error(f"❌ Error saving glucose record: {e}")
                    skip_count += 1
                    continue
        
        connection.commit()
        logger.info(f"✅ Uploaded {count} glucose records to RDS (skipped {skip_count})")
        
    except FileNotFoundError:
        logger.warning("⚠️ blood_glucose.csv not found, skipping")

def main():
    """Main function to upload all CSV data to RDS"""
    logger.info("🚀 Starting CSV to RDS upload...")
    
    try:
        # Connect to database
        connection = connect_to_database()
        
        # Create tables
        create_tables(connection)
        
        # Upload data
        logger.info("📊 Uploading sleep data...")
        upload_sleep_data(connection)
        
        logger.info("📊 Uploading exercise data...")
        upload_exercise_data(connection)
        
        logger.info("📊 Uploading glucose data...")
        upload_glucose_data(connection)
        
        connection.close()
        logger.info("✅ CSV to RDS upload completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise

if __name__ == "__main__":
    main()


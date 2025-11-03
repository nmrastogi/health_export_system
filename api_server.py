#!/usr/bin/env python3
"""
Health Data API Server
Receives health data from iPhone Shortcuts/mobile apps and stores in Amazon RDS
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
import logging
import pymysql

# CSV file paths
SLEEP_CSV = 'sleep_data.csv'
EXERCISE_CSV = 'exercise_data.csv'
GLUCOSE_CSV = 'blood_glucose.csv'

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app requests

# Database configuration
DB_CONFIG = {
    'host': os.getenv('RDS_HOST', 'localhost'),
    'user': os.getenv('RDS_USER', 'root'),
    'password': os.getenv('RDS_PASSWORD', ''),
    'database': os.getenv('RDS_DATABASE', 'health_data'),
    'port': int(os.getenv('RDS_PORT', 3306)),
    'charset': 'utf8mb4'
}

# Global database connection
db_connection = None

def get_db_connection():
    """Get or create database connection"""
    global db_connection
    try:
        if db_connection is None:
            db_connection = pymysql.connect(**DB_CONFIG)
            logger.info("✅ Connected to RDS database")
        else:
            # Test if connection is still alive
            db_connection.ping(reconnect=True)
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        try:
            db_connection = pymysql.connect(**DB_CONFIG)
            logger.info("✅ Reconnected to RDS database")
        except:
            return None
    return db_connection

def create_tables():
    """Create tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        logger.warning("⚠️ Could not connect to database, skipping table creation")
        return
    
    cursor = conn.cursor()
    
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
    
    try:
        cursor.execute(sleep_table)
        cursor.execute(exercise_table)
        cursor.execute(glucose_table)
        conn.commit()
        logger.info("✅ RDS tables created/verified")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        conn.rollback()

# Initialize CSV files with headers if they don't exist
def initialize_csv_files():
    """Create CSV files with headers if they don't exist"""
    # Sleep data CSV
    if not os.path.exists(SLEEP_CSV):
        with open(SLEEP_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'date', 'bedtime', 'wake_time', 'sleep_duration_minutes',
                'deep_sleep_minutes', 'light_sleep_minutes', 'rem_sleep_minutes',
                'sleep_efficiency', 'heart_rate_avg', 'heart_rate_min', 'heart_rate_max',
                'timestamp'
            ])
        logger.info(f"✅ Created {SLEEP_CSV}")
    
    # Exercise data CSV
    if not os.path.exists(EXERCISE_CSV):
        with open(EXERCISE_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'activity_type', 'duration_minutes', 'calories_burned',
                'distance_km', 'steps', 'heart_rate_avg', 'heart_rate_max',
                'active_energy_kcal', 'resting_energy_kcal'
            ])
        logger.info(f"✅ Created {EXERCISE_CSV}")
    
    # Blood glucose data CSV
    if not os.path.exists(GLUCOSE_CSV):
        with open(GLUCOSE_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'value', 'unit', 'source'
            ])
        logger.info(f"✅ Created {GLUCOSE_CSV}")

# Initialize CSV files on startup (optional backup)
# initialize_csv_files()

# Initialize RDS tables on startup
create_tables()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Health Export API is running'})

def save_sleep_to_rds(sleep_records):
    """Save sleep data to RDS"""
    if not sleep_records:
        return 0
    
    conn = get_db_connection()
    if not conn:
        logger.error("⚠️ Database not available, skipping save")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    for record in sleep_records:
        try:
            sleep_data = {
                'date': record.get('date', ''),
                'bedtime': record.get('bedtime') or None,
                'wake_time': record.get('wake_time') or None,
                'sleep_duration_minutes': int(record.get('sleep_duration_minutes', 0)) if record.get('sleep_duration_minutes') else None,
                'deep_sleep_minutes': int(record.get('deep_sleep_minutes', 0)) if record.get('deep_sleep_minutes') else None,
                'light_sleep_minutes': int(record.get('light_sleep_minutes', 0)) if record.get('light_sleep_minutes') else None,
                'rem_sleep_minutes': int(record.get('rem_sleep_minutes', 0)) if record.get('rem_sleep_minutes') else None,
                'sleep_efficiency': float(record.get('sleep_efficiency', 0)) if record.get('sleep_efficiency') else None,
                'heart_rate_avg': int(record.get('heart_rate_avg', 0)) if record.get('heart_rate_avg') else None,
                'heart_rate_min': int(record.get('heart_rate_min', 0)) if record.get('heart_rate_min') else None,
                'heart_rate_max': int(record.get('heart_rate_max', 0)) if record.get('heart_rate_max') else None
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
            continue
    
    conn.commit()
    return count

@app.route('/api/sleep', methods=['POST'])
def receive_sleep_data():
    """Receive sleep data from iPhone"""
    try:
        # Log raw request data for debugging
        raw_data = request.get_data(as_text=True)
        logger.info(f"📥 Raw request data: {raw_data[:200]}...")  # First 200 chars
        
        request_data = request.get_json()
        logger.info(f"📥 Parsed JSON data structure: {type(request_data)}")
        
        # Extract sleep data from Auto Export app format
        # Format: {'data': {'metrics': [{'data': [...]}]}}
        sleep_records = []
        
        if request_data and 'data' in request_data:
            if 'metrics' in request_data['data']:
                for metric in request_data['data']['metrics']:
                    if 'data' in metric:
                        # Extract individual sleep records
                        for record in metric['data']:
                            # Parse the sleep record
                            parsed_record = {
                                'date': record.get('date', '').split()[0] if record.get('date') else '',  # Just the date part
                                'bedtime': record.get('inBedStart', ''),
                                'wake_time': record.get('inBedEnd', record.get('inBedEnd', '')),
                                'sleep_duration_minutes': int(record.get('totalSleep', 0) * 60) if record.get('totalSleep') else '',
                                'deep_sleep_minutes': int(record.get('deep', 0) * 60) if record.get('deep') else '',
                                'light_sleep_minutes': int(record.get('core', 0) * 60) if record.get('core') else '',
                                'rem_sleep_minutes': int(record.get('rem', 0) * 60) if record.get('rem') else '',
                                'sleep_efficiency': '',
                                'heart_rate_avg': '',
                                'heart_rate_min': '',
                                'heart_rate_max': ''
                            }
                            sleep_records.append(parsed_record)
        
        logger.info(f"📥 Extracted {len(sleep_records)} sleep record(s) from data")
        
        # Save to RDS
        count = save_sleep_to_rds(sleep_records)
        logger.info(f"✅ Saved {count} sleep records to RDS")
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {count} sleep records',
            'database': 'RDS',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing sleep data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def save_exercise_to_rds(exercise_records):
    """Save exercise data to RDS"""
    if not exercise_records:
        return 0
    
    conn = get_db_connection()
    if not conn:
        logger.error("⚠️ Database not available, skipping save")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    for record in exercise_records:
        try:
            exercise_data = {
                'timestamp': record.get('timestamp', ''),
                'activity_type': record.get('activity_type'),
                'duration_minutes': int(record.get('duration_minutes', 0)) if record.get('duration_minutes') else None,
                'calories_burned': float(record.get('calories_burned', 0)) if record.get('calories_burned') else None,
                'distance_km': float(record.get('distance_km', 0)) if record.get('distance_km') else None,
                'steps': int(record.get('steps', 0)) if record.get('steps') else None,
                'heart_rate_avg': int(record.get('heart_rate_avg', 0)) if record.get('heart_rate_avg') else None,
                'heart_rate_max': int(record.get('heart_rate_max', 0)) if record.get('heart_rate_max') else None,
                'active_energy_kcal': float(record.get('active_energy_kcal', 0)) if record.get('active_energy_kcal') else None,
                'resting_energy_kcal': float(record.get('resting_energy_kcal', 0)) if record.get('resting_energy_kcal') else None
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
            continue
    
    conn.commit()
    return count

@app.route('/api/exercise', methods=['POST'])
def receive_exercise_data():
    """Receive exercise data from iPhone"""
    try:
        # Log raw request data for debugging
        raw_data = request.get_data(as_text=True)
        logger.info(f"📥 Raw exercise request data: {raw_data[:200]}...")  # First 200 chars
        
        request_data = request.get_json()
        logger.info(f"📥 Parsed exercise JSON structure: {type(request_data)}")
        
        # Extract exercise data from Auto Export app format
        # Format: {'data': {'metrics': [{'data': [...]}]}}
        exercise_records = []
        
        if request_data and 'data' in request_data:
            # Check for workout data (with metadata)
            if 'workouts' in request_data['data']:
                logger.info("🎯 Found workouts data with metadata!")
                for workout in request_data['data']['workouts']:
                    # Parse workout metadata
                    # Get start time
                    start_time = workout.get('start', '')
                    
                    # Extract calories from activeEnergyBurned if present
                    calories = ''
                    if 'activeEnergyBurned' in workout and workout['activeEnergyBurned']:
                        calories = workout['activeEnergyBurned'].get('qty', '')
                    
                    # Get workout type
                    activity_type = workout.get('workoutName', workout.get('workoutActivityType', 'Exercise'))
                    
                    parsed_record = {
                        'timestamp': start_time,
                        'activity_type': activity_type,
                        'duration_minutes': '',
                        'calories_burned': calories,
                        'distance_km': '',
                        'steps': '',
                        'heart_rate_avg': '',
                        'heart_rate_max': '',
                        'active_energy_kcal': calories,  # Active energy from workout
                        'resting_energy_kcal': ''
                    }
                    exercise_records.append(parsed_record)
                    logger.info(f"📊 Workout: {activity_type}, Calories: {calories}, Start: {start_time}")
            # Check for metric data (apple_exercise_time format)
            elif 'metrics' in request_data['data']:
                for metric in request_data['data']['metrics']:
                    if 'data' in metric:
                        # Extract individual exercise records
                        for record in metric['data']:
                            # Parse the exercise record
                            parsed_record = {
                                'timestamp': record.get('date', ''),
                                'activity_type': 'Exercise',  # Generic since we have exercise time
                                'duration_minutes': record.get('qty', ''),  # Minutes of exercise
                                'calories_burned': '',
                                'distance_km': '',
                                'steps': '',
                                'heart_rate_avg': '',
                                'heart_rate_max': '',
                                'active_energy_kcal': '',
                                'resting_energy_kcal': ''
                            }
                            exercise_records.append(parsed_record)
        
        logger.info(f"📥 Extracted {len(exercise_records)} exercise record(s) from data")
        
        # Save to RDS
        count = save_exercise_to_rds(exercise_records)
        logger.info(f"✅ Saved {count} exercise records to RDS")
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {count} exercise records',
            'database': 'RDS',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing exercise data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def save_glucose_to_rds(glucose_records):
    """Save blood glucose data to RDS"""
    if not glucose_records:
        return 0
    
    conn = get_db_connection()
    if not conn:
        logger.error("⚠️ Database not available, skipping save")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    for record in glucose_records:
        try:
            # Validate and clean data
            timestamp = record.get('timestamp', '') or record.get('date', '')
            value = record.get('value', '') or record.get('qty', '')
            
            # Skip records with missing required fields
            if not timestamp or not value:
                logger.warning(f"⚠️ Skipping record with missing timestamp or value: {record}")
                continue
            
            # Try to convert value to float
            try:
                value_float = float(value)
                if value_float <= 0:  # Invalid glucose reading
                    continue
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Skipping record with invalid value: {value}")
                continue
            
            glucose_data = {
                'timestamp': timestamp,
                'value': value_float,
                'unit': record.get('unit', 'mg/dL') or 'mg/dL',
                'source': record.get('source') or None
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
            logger.error(f"   Record data: {record}")
            continue
    
    try:
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Error committing glucose data: {e}")
        conn.rollback()
    
    return count

@app.route('/api/glucose', methods=['POST'])
def receive_glucose_data():
    """Receive blood glucose data from iPhone"""
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"📥 Raw glucose request data: {raw_data[:200]}...")
        
        request_data = request.get_json()
        logger.info(f"📥 Parsed glucose JSON structure: {type(request_data)}")
        
        glucose_records = []
        
        # Extract blood glucose data from Auto Export app format
        if request_data and 'data' in request_data:
            if 'metrics' in request_data['data']:
                for metric in request_data['data']['metrics']:
                    if 'data' in metric:
                        for record in metric['data']:
                            parsed_record = {
                                'timestamp': record.get('date', ''),
                                'value': record.get('qty', ''),
                                'unit': 'mg/dL',
                                'source': record.get('source', '')
                            }
                            glucose_records.append(parsed_record)
        
        logger.info(f"📥 Extracted {len(glucose_records)} glucose record(s) from data")
        
        # Save to RDS
        count = save_glucose_to_rds(glucose_records)
        
        if count > 0:
            logger.info(f"✅ Saved {count} glucose records to RDS")
            return jsonify({
                'status': 'success',
                'message': f'Processed {count} glucose records',
                'database': 'RDS',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            logger.warning(f"⚠️ No glucose records were saved (all may have been invalid)")
            return jsonify({
                'status': 'warning',
                'message': 'No valid glucose records to save',
                'total_extracted': len(glucose_records)
            }), 200  # Return 200 even if no records saved
        
    except Exception as e:
        logger.error(f"❌ Error processing glucose data: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify connectivity"""
    return jsonify({
        'status': 'success',
        'message': 'API is accessible',
        'endpoints': {
            'sleep': '/api/sleep',
            'exercise': '/api/exercise',
            'glucose': '/api/glucose',
            'test': '/api/test'
        }
    })

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5001))
    
    logger.info(f"🚀 Starting Health Data API Server on {host}:{port}")
    logger.info(f"📡 Endpoints available:")
    logger.info(f"   - POST http://{host}:{port}/api/sleep")
    logger.info(f"   - POST http://{host}:{port}/api/exercise")
    logger.info(f"   - POST http://{host}:{port}/api/glucose")
    logger.info(f"   - GET http://{host}:{port}/api/test")
    
    app.run(host=host, port=port, debug=False)


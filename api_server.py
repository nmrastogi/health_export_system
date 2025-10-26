#!/usr/bin/env python3
"""
Health Data API Server
Receives health data from iPhone Shortcuts/mobile apps and stores in CSV files
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
import logging

# CSV file paths
SLEEP_CSV = 'sleep_data.csv'
EXERCISE_CSV = 'exercise_data.csv'

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app requests

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

# Initialize CSV files on startup
initialize_csv_files()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Health Export API is running'})

def save_sleep_to_csv(sleep_records):
    """Save sleep data to CSV file"""
    if not sleep_records:
        return 0
    
    count = 0
    with open(SLEEP_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        for record in sleep_records:
            row = [
                record.get('date', ''),
                record.get('bedtime', ''),
                record.get('wake_time', ''),
                record.get('sleep_duration_minutes', ''),
                record.get('deep_sleep_minutes', ''),
                record.get('light_sleep_minutes', ''),
                record.get('rem_sleep_minutes', ''),
                record.get('sleep_efficiency', ''),
                record.get('heart_rate_avg', ''),
                record.get('heart_rate_min', ''),
                record.get('heart_rate_max', ''),
                datetime.now().isoformat()
            ]
            writer.writerow(row)
            count += 1
    
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
        
        # Save to CSV
        count = save_sleep_to_csv(sleep_records)
        logger.info(f"✅ Saved {count} sleep records to {SLEEP_CSV}")
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {count} sleep records',
            'file': SLEEP_CSV,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing sleep data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def save_exercise_to_csv(exercise_records):
    """Save exercise data to CSV file"""
    if not exercise_records:
        return 0
    
    count = 0
    with open(EXERCISE_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        for record in exercise_records:
            row = [
                record.get('timestamp', ''),
                record.get('activity_type', ''),
                record.get('duration_minutes', ''),
                record.get('calories_burned', ''),
                record.get('distance_km', ''),
                record.get('steps', ''),
                record.get('heart_rate_avg', ''),
                record.get('heart_rate_max', ''),
                record.get('active_energy_kcal', ''),
                record.get('resting_energy_kcal', '')
            ]
            writer.writerow(row)
            count += 1
    
    return count

@app.route('/api/exercise', methods=['POST'])
def receive_exercise_data():
    """Receive exercise data from iPhone"""
    try:
        data = request.get_json()
        logger.info(f"📥 Received exercise data: {len(data) if isinstance(data, list) else 1} records")
        
        # Process the data
        if isinstance(data, dict):
            data = [data]
        
        # Save to CSV
        count = save_exercise_to_csv(data)
        logger.info(f"✅ Saved {count} exercise records to {EXERCISE_CSV}")
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {count} exercise records',
            'file': EXERCISE_CSV,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing exercise data: {e}")
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
    logger.info(f"   - GET http://{host}:{port}/api/test")
    
    app.run(host=host, port=port, debug=False)


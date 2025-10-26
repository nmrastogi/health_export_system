#!/usr/bin/env python3
"""
Health Data API Server
Receives health data from iPhone Shortcuts/mobile apps and stores in RDS
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging

# Import the exporter class
from main import HealthDataExporter

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app requests

# Initialize the exporter
exporter = HealthDataExporter()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Health Export API is running'})

@app.route('/api/sleep', methods=['POST'])
def receive_sleep_data():
    """Receive sleep data from iPhone"""
    try:
        data = request.get_json()
        logger.info(f"📥 Received sleep data: {len(data) if isinstance(data, list) else 1} records")
        
        # Process the data
        if isinstance(data, dict):
            data = [data]
        
        # Save to database
        exporter.save_sleep_data(data)
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(data)} sleep records',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing sleep data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/exercise', methods=['POST'])
def receive_exercise_data():
    """Receive exercise data from iPhone"""
    try:
        data = request.get_json()
        logger.info(f"📥 Received exercise data: {len(data) if isinstance(data, list) else 1} records")
        
        # Process the data
        if isinstance(data, dict):
            data = [data]
        
        # Save to database
        exporter.save_exercise_data(data)
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(data)} exercise records',
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
    port = int(os.getenv('API_PORT', 5000))
    
    logger.info(f"🚀 Starting Health Data API Server on {host}:{port}")
    logger.info(f"📡 Endpoints available:")
    logger.info(f"   - POST http://{host}:{port/api/sleep")
    logger.info(f"   - POST http://{host}:{port/api/exercise")
    logger.info(f"   - GET http://{host}:{port/api/test")
    
    app.run(host=host, port=port, debug=False)


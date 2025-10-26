#!/usr/bin/env python3
"""
Test database connection and setup
"""

import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def test_database_connection():
    """Test connection to Amazon RDS"""
    try:
        connection = pymysql.connect(
            host=os.getenv('RDS_HOST'),
            user=os.getenv('RDS_USER'),
            password=os.getenv('RDS_PASSWORD'),
            database=os.getenv('RDS_DATABASE'),
            port=int(os.getenv('RDS_PORT', 3306)),
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"✅ Database connection successful!")
        print(f"📊 MySQL version: {version[0]}")
        
        # Test table creation
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📋 Existing tables: {[table[0] for table in tables]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_health_api():
    """Test health API endpoints"""
    import requests
    
    sleep_endpoint = os.getenv('HEALTH_SLEEP_ENDPOINT')
    exercise_endpoint = os.getenv('HEALTH_EXERCISE_ENDPOINT')
    api_key = os.getenv('HEALTH_API_KEY')
    
    if not all([sleep_endpoint, exercise_endpoint, api_key]):
        print("⚠️ Health API configuration incomplete")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test sleep endpoint
        response = requests.get(sleep_endpoint, headers=headers, timeout=10)
        print(f"🛏️ Sleep API: {response.status_code}")
        
        # Test exercise endpoint
        response = requests.get(exercise_endpoint, headers=headers, timeout=10)
        print(f"🏃 Exercise API: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Health Data Export System...")
    print()
    
    print("1. Testing database connection...")
    db_ok = test_database_connection()
    print()
    
    print("2. Testing health API endpoints...")
    api_ok = test_health_api()
    print()
    
    if db_ok and api_ok:
        print("🎉 All tests passed! System is ready to run.")
    else:
        print("⚠️ Some tests failed. Please check your configuration.")

#!/usr/bin/env python3
"""
iPhone Health Data Export System
Exports sleep and exercise data to Amazon RDS
- Sleep data: Every 6 hours
- Exercise data: Every 15 minutes
"""

import os
import json
import time
import schedule
import requests
import pandas as pd
import pymysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('RDS_HOST'),
    'user': os.getenv('RDS_USER'),
    'password': os.getenv('RDS_PASSWORD'),
    'database': os.getenv('RDS_DATABASE'),
    'port': int(os.getenv('RDS_PORT', 3306)),
    'charset': 'utf8mb4'
}

# Health app configuration
HEALTH_CONFIG = {
    'sleep_endpoint': os.getenv('HEALTH_SLEEP_ENDPOINT'),
    'exercise_endpoint': os.getenv('HEALTH_EXERCISE_ENDPOINT'),
    'api_key': os.getenv('HEALTH_API_KEY')
}

class HealthDataExporter:
    def __init__(self):
        self.db_connection = None
        self.setup_database()
    
    def setup_database(self):
        """Initialize database connection and create tables if needed"""
        try:
            self.db_connection = pymysql.connect(**DB_CONFIG)
            self.create_tables()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def create_tables(self):
        """Create tables for sleep and exercise data"""
        cursor = self.db_connection.cursor()
        
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
            calories_burned INT,
            distance_km DECIMAL(8,3),
            steps INT,
            heart_rate_avg INT,
            heart_rate_max INT,
            active_energy_kcal INT,
            resting_energy_kcal INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_timestamp (timestamp)
        )
        """
        
        cursor.execute(sleep_table)
        cursor.execute(exercise_table)
        self.db_connection.commit()
        logger.info("✅ Database tables created/verified")
    
    def fetch_sleep_data(self):
        """Fetch sleep data from Health app"""
        try:
            # Calculate date range (last 6 hours)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=6)
            
            params = {
                'start_date': start_time.isoformat(),
                'end_date': end_time.isoformat(),
                'data_type': 'sleep'
            }
            
            headers = {
                'Authorization': f'Bearer {HEALTH_CONFIG["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                HEALTH_CONFIG['sleep_endpoint'],
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Sleep data fetched: {len(data.get('data', []))} records")
                return data.get('data', [])
            else:
                logger.error(f"❌ Sleep data fetch failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching sleep data: {e}")
            return []
    
    def fetch_exercise_data(self):
        """Fetch exercise data from Health app"""
        try:
            # Calculate time range (last 15 minutes)
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=15)
            
            params = {
                'start_date': start_time.isoformat(),
                'end_date': end_time.isoformat(),
                'data_type': 'exercise'
            }
            
            headers = {
                'Authorization': f'Bearer {HEALTH_CONFIG["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                HEALTH_CONFIG['exercise_endpoint'],
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Exercise data fetched: {len(data.get('data', []))} records")
                return data.get('data', [])
            else:
                logger.error(f"❌ Exercise data fetch failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching exercise data: {e}")
            return []
    
    def save_sleep_data(self, sleep_records):
        """Save sleep data to RDS"""
        if not sleep_records:
            logger.info("No sleep data to save")
            return
        
        cursor = self.db_connection.cursor()
        
        for record in sleep_records:
            try:
                # Extract sleep data fields
                sleep_data = {
                    'date': record.get('date'),
                    'bedtime': record.get('bedtime'),
                    'wake_time': record.get('wake_time'),
                    'sleep_duration_minutes': record.get('sleep_duration_minutes'),
                    'deep_sleep_minutes': record.get('deep_sleep_minutes'),
                    'light_sleep_minutes': record.get('light_sleep_minutes'),
                    'rem_sleep_minutes': record.get('rem_sleep_minutes'),
                    'sleep_efficiency': record.get('sleep_efficiency'),
                    'heart_rate_avg': record.get('heart_rate_avg'),
                    'heart_rate_min': record.get('heart_rate_min'),
                    'heart_rate_max': record.get('heart_rate_max')
                }
                
                # Insert or update sleep data
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
                
            except Exception as e:
                logger.error(f"❌ Error saving sleep record: {e}")
                continue
        
        self.db_connection.commit()
        logger.info(f"✅ Saved {len(sleep_records)} sleep records to database")
    
    def save_exercise_data(self, exercise_records):
        """Save exercise data to RDS"""
        if not exercise_records:
            logger.info("No exercise data to save")
            return
        
        cursor = self.db_connection.cursor()
        
        for record in exercise_records:
            try:
                # Extract exercise data fields
                exercise_data = {
                    'timestamp': record.get('timestamp'),
                    'activity_type': record.get('activity_type'),
                    'duration_minutes': record.get('duration_minutes'),
                    'calories_burned': record.get('calories_burned'),
                    'distance_km': record.get('distance_km'),
                    'steps': record.get('steps'),
                    'heart_rate_avg': record.get('heart_rate_avg'),
                    'heart_rate_max': record.get('heart_rate_max'),
                    'active_energy_kcal': record.get('active_energy_kcal'),
                    'resting_energy_kcal': record.get('resting_energy_kcal')
                }
                
                # Insert or update exercise data
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
                
            except Exception as e:
                logger.error(f"❌ Error saving exercise record: {e}")
                continue
        
        self.db_connection.commit()
        logger.info(f"✅ Saved {len(exercise_records)} exercise records to database")
    
    def export_sleep_data(self):
        """Export sleep data (called every 6 hours)"""
        logger.info("🛏️ Starting sleep data export...")
        sleep_data = self.fetch_sleep_data()
        self.save_sleep_data(sleep_data)
    
    def export_exercise_data(self):
        """Export exercise data (called every 15 minutes)"""
        logger.info("🏃 Starting exercise data export...")
        exercise_data = self.fetch_exercise_data()
        self.save_exercise_data(exercise_data)
    
    def close_connection(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            logger.info("✅ Database connection closed")

def main():
    """Main function to run the health data exporter"""
    exporter = HealthDataExporter()
    
    try:
        # Schedule sleep data export every 6 hours
        schedule.every(6).hours.do(exporter.export_sleep_data)
        
        # Schedule exercise data export every 15 minutes
        schedule.every(15).minutes.do(exporter.export_exercise_data)
        
        # Run initial exports
        logger.info("🚀 Starting initial data exports...")
        exporter.export_sleep_data()
        exporter.export_exercise_data()
        
        logger.info("⏰ Scheduler started:")
        logger.info("   - Sleep data: Every 6 hours")
        logger.info("   - Exercise data: Every 15 minutes")
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down health data exporter...")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        exporter.close_connection()

if __name__ == "__main__":
    main()

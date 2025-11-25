#!/usr/bin/env python3

import os
import logging
from datetime import datetime
from concurrent import futures

import grpc
import pymysql
from dotenv import load_dotenv

import health_export_pb2 as pb2
import health_export_pb2_grpc as pb2_grpc
from google.protobuf.empty_pb2 import Empty

load_dotenv()

# Configure logging to both file and console
log_file = os.path.join(os.path.dirname(__file__), 'grpc_server.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("RDS_HOST", "localhost"),
    "user": os.getenv("RDS_USER", "root"),
    "password": os.getenv("RDS_PASSWORD", ""),
    "database": os.getenv("RDS_DATABASE", "health_data"),
    "port": int(os.getenv("RDS_PORT", 3306)),
    "charset": "utf8mb4",
}

db_connection = None

def get_db_connection():
    global db_connection
    try:
        if db_connection is None:
            db_connection = pymysql.connect(**DB_CONFIG)
            logger.info("Connected to RDS")
        else:
            db_connection.ping(reconnect=True)
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        try:
            db_connection = pymysql.connect(**DB_CONFIG)
            logger.info("Reconnected to RDS")
        except:
            return None
    return db_connection

def create_tables():
    conn = get_db_connection()
    if not conn:
        logger.warning("No DB connection, skipping table creation")
        return

    cursor = conn.cursor()

    cursor.execute("""
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
    """)

    cursor.execute("""
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
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blood_glucose (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        value DECIMAL(6,2),
        unit VARCHAR(10),
        source VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_timestamp (timestamp)
    )
    """)

    conn.commit()
    logger.info("Tables created and verified")

class HealthExportServicer(pb2_grpc.HealthExportServiceServicer):

    def ExportSleep(self, request, context):
        logger.info(f"📥 Received sleep data: {len(request.records)} record(s)")
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database unavailable for sleep data")
            return pb2.IngestResponse(
                status="error",
                message="Database unavailable",
                processed=0,
                timestamp=datetime.now().isoformat()
            )

        cursor = conn.cursor()
        processed = 0

        sql = """
        INSERT INTO sleep_data
        (date, bedtime, wake_time, sleep_duration_minutes,
         deep_sleep_minutes, light_sleep_minutes, rem_sleep_minutes,
         sleep_efficiency, heart_rate_avg, heart_rate_min, heart_rate_max)
        VALUES (%(date)s, %(bedtime)s, %(wake_time)s, %(sleep_duration_minutes)s,
                %(deep_sleep_minutes)s, %(light_sleep_minutes)s, %(rem_sleep_minutes)s,
                %(sleep_efficiency)s, %(heart_rate_avg)s, %(heart_rate_min)s, %(heart_rate_max)s)
        ON DUPLICATE KEY UPDATE
        bedtime=VALUES(bedtime),
        wake_time=VALUES(wake_time),
        sleep_duration_minutes=VALUES(sleep_duration_minutes),
        deep_sleep_minutes=VALUES(deep_sleep_minutes),
        light_sleep_minutes=VALUES(light_sleep_minutes),
        rem_sleep_minutes=VALUES(rem_sleep_minutes),
        sleep_efficiency=VALUES(sleep_efficiency),
        heart_rate_avg=VALUES(heart_rate_avg),
        heart_rate_min=VALUES(heart_rate_min),
        heart_rate_max=VALUES(heart_rate_max),
        updated_at=CURRENT_TIMESTAMP
        """

        for r in request.records:
            data = {
                "date": r.date,
                "bedtime": r.bedtime or None,
                "wake_time": r.wake_time or None,
                "sleep_duration_minutes": r.sleep_duration_minutes or None,
                "deep_sleep_minutes": r.deep_sleep_minutes or None,
                "light_sleep_minutes": r.light_sleep_minutes or None,
                "rem_sleep_minutes": r.rem_sleep_minutes or None,
                "sleep_efficiency": r.sleep_efficiency or None,
                "heart_rate_avg": r.heart_rate_avg or None,
                "heart_rate_min": r.heart_rate_min or None,
                "heart_rate_max": r.heart_rate_max or None,
            }
            cursor.execute(sql, data)
            processed += 1

        conn.commit()
        logger.info(f"✅ Saved {processed} sleep record(s) to database")

        return pb2.IngestResponse(
            status="success",
            message=f"Processed {processed} sleep records",
            processed=processed,
            timestamp=datetime.now().isoformat()
        )

    def ExportExercise(self, request, context):
        logger.info(f"📥 Received exercise data: {len(request.records)} record(s)")
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database unavailable for exercise data")
            return pb2.IngestResponse(status="error", message="DB down", processed=0)

        cursor = conn.cursor()
        processed = 0

        sql = """
        INSERT INTO exercise_data
        (timestamp, activity_type, duration_minutes, calories_burned,
         distance_km, steps, heart_rate_avg, heart_rate_max,
         active_energy_kcal, resting_energy_kcal)
        VALUES (%(timestamp)s, %(activity_type)s, %(duration_minutes)s,
                %(calories_burned)s, %(distance_km)s, %(steps)s,
                %(heart_rate_avg)s, %(heart_rate_max)s,
                %(active_energy_kcal)s, %(resting_energy_kcal)s)
        ON DUPLICATE KEY UPDATE
        activity_type=VALUES(activity_type),
        duration_minutes=VALUES(duration_minutes),
        calories_burned=VALUES(calories_burned),
        distance_km=VALUES(distance_km),
        steps=VALUES(steps),
        heart_rate_avg=VALUES(heart_rate_avg),
        heart_rate_max=VALUES(heart_rate_max),
        active_energy_kcal=VALUES(active_energy_kcal),
        resting_energy_kcal=VALUES(resting_energy_kcal)
        """

        for r in request.records:
            data = {
                "timestamp": r.timestamp,
                "activity_type": r.activity_type,
                "duration_minutes": r.duration_minutes or None,
                "calories_burned": r.calories_burned or None,
                "distance_km": r.distance_km or None,
                "steps": r.steps or None,
                "heart_rate_avg": r.heart_rate_avg or None,
                "heart_rate_max": r.heart_rate_max or None,
                "active_energy_kcal": r.active_energy_kcal or None,
                "resting_energy_kcal": r.resting_energy_kcal or None,
            }
            cursor.execute(sql, data)
            processed += 1

        conn.commit()
        logger.info(f"✅ Saved {processed} exercise record(s) to database")

        return pb2.IngestResponse(
            status="success",
            message=f"Processed {processed} exercise records",
            processed=processed,
            timestamp=datetime.now().isoformat()
        )

    def ExportGlucose(self, request, context):
        logger.info(f"📥 Received glucose data: {len(request.records)} record(s)")
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database unavailable for glucose data")
            return pb2.IngestResponse(status="error", message="DB down", processed=0)

        cursor = conn.cursor()
        processed = 0

        sql = """
        INSERT INTO blood_glucose (timestamp, value, unit, source)
        VALUES (%(timestamp)s, %(value)s, %(unit)s, %(source)s)
        ON DUPLICATE KEY UPDATE
        value=VALUES(value),
        unit=VALUES(unit),
        source=VALUES(source)
        """

        for r in request.records:
            if r.value <= 0:
                continue

            data = {
                "timestamp": r.timestamp,
                "value": r.value,
                "unit": r.unit or "mg/dL",
                "source": r.source or None,
            }

            cursor.execute(sql, data)
            processed += 1

        conn.commit()
        logger.info(f"✅ Saved {processed} glucose record(s) to database")

        return pb2.IngestResponse(
            status="success",
            message=f"Processed {processed} glucose records",
            processed=processed,
            timestamp=datetime.now().isoformat()
        )

    def HealthCheck(self, request: Empty, context):
        return pb2.IngestResponse(
            status="ok",
            message="gRPC Health Server Running",
            processed=0,
            timestamp=datetime.now().isoformat()
        )

def serve():
    create_tables()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_HealthExportServiceServicer_to_server(
        HealthExportServicer(),
        server
    )

    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", 5001))

    server.add_insecure_port(f"{host}:{port}")
    logger.info(f"🚀 gRPC server running on {host}:{port}")
    logger.info(f"📝 Logging to: {log_file}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

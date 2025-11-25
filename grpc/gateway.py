import grpc
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import health_export_pb2 as pb2
import health_export_pb2_grpc as pb2_grpc

app = FastAPI()

# Connect to gRPC backend
channel = grpc.insecure_channel("localhost:50051")
# Wait for channel to be ready (with timeout)
try:
    grpc.channel_ready_future(channel).result(timeout=5)
except grpc.FutureTimeoutError:
    print("Warning: gRPC channel not ready, but continuing...")
client = pb2_grpc.HealthExportServiceStub(channel)

@app.post("/api/sleep")
async def ingest_sleep(request: Request):
    data = await request.json()
    sleep_records = []

    # Auto Export format: data.metrics[].data[]
    if "data" in data and "metrics" in data["data"]:
        for metric in data["data"]["metrics"]:
            for r in metric.get("data", []):
                rec = pb2.SleepRecord(
                    date=r.get("date", "").split()[0] if r.get("date") else "",
                    bedtime=r.get("inBedStart", ""),
                    wake_time=r.get("inBedEnd", ""),
                    sleep_duration_minutes=int(r.get("totalSleep", 0) * 60),
                    deep_sleep_minutes=int(r.get("deep", 0) * 60),
                    light_sleep_minutes=int(r.get("core", 0) * 60),
                    rem_sleep_minutes=int(r.get("rem", 0) * 60),
                )
                sleep_records.append(rec)

    batch = pb2.SleepBatch(records=sleep_records)
    resp = client.ExportSleep(batch)

    return JSONResponse({
        "status": resp.status,
        "message": resp.message,
        "processed": resp.processed,
        "timestamp": resp.timestamp
    })

@app.post("/api/exercise")
async def ingest_exercise(request: Request):
    body = await request.json()
    exercise_records = []

    if "data" in body:

        # Workouts format
        if "workouts" in body["data"]:
            for w in body["data"]["workouts"]:
                rec = pb2.ExerciseRecord(
                    timestamp=w.get("start", ""),
                    activity_type=w.get("workoutName", "Exercise"),
                    calories_burned=float(w["activeEnergyBurned"]["qty"]) if w.get("activeEnergyBurned") else 0
                )
                exercise_records.append(rec)

        # Exercise metrics format
        if "metrics" in body["data"]:
            for metric in body["data"]["metrics"]:
                for r in metric.get("data", []):
                    rec = pb2.ExerciseRecord(
                        timestamp=r.get("date", ""),
                        activity_type="Exercise",
                        duration_minutes=int(r.get("qty", 0))
                    )
                    exercise_records.append(rec)

    batch = pb2.ExerciseBatch(records=exercise_records)
    resp = client.ExportExercise(batch)

    return JSONResponse({
        "status": resp.status,
        "message": resp.message,
        "processed": resp.processed,
        "timestamp": resp.timestamp
    })

@app.post("/api/glucose")
async def ingest_glucose(request: Request):
    body = await request.json()
    glucose_records = []

    if "data" in body and "metrics" in body["data"]:
        for metric in body["data"]["metrics"]:
            for r in metric.get("data", []):
                try:
                    rec = pb2.GlucoseRecord(
                        timestamp=r.get("date", ""),
                        value=float(r.get("qty", 0)),
                        unit="mg/dL",
                        source=r.get("source", "")
                    )
                    glucose_records.append(rec)
                except:
                    continue

    batch = pb2.GlucoseBatch(records=glucose_records)
    resp = client.ExportGlucose(batch)

    return JSONResponse({
        "status": resp.status,
        "message": resp.message,
        "processed": resp.processed,
        "timestamp": resp.timestamp
    })

@app.get("/")
def root():
    return {"status": "ok", "gateway": "REST to gRPC"}

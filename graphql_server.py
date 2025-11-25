from datetime import datetime
from ariadne import QueryType, MutationType, make_executable_schema, graphql_sync
from ariadne.asgi import GraphQL
import pymysql
import os

type_defs = open("schema.graphql").read()
query = QueryType()
mutation = MutationType()

@query.field("healthCheck")
def resolve_health(*_):
    return "GraphQL Health Server Running"

@mutation.field("ingestSleep")
def resolve_ingest_sleep(_, info, records):
    conn = get_db()
    cursor = conn.cursor()
    count = 0

    query_sql = """INSERT INTO sleep_data
    (date, bedtime, wake_time, sleep_duration_minutes, deep_sleep_minutes,
     light_sleep_minutes, rem_sleep_minutes, sleep_efficiency,
     heart_rate_avg, heart_rate_min, heart_rate_max)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
    heart_rate_max=VALUES(heart_rate_max)"""

    for r in records:
        values = (
            r["date"],
            r.get("bedtime"),
            r.get("wake_time"),
            r.get("sleep_duration_minutes"),
            r.get("deep_sleep_minutes"),
            r.get("light_sleep_minutes"),
            r.get("rem_sleep_minutes"),
            r.get("sleep_efficiency"),
            r.get("heart_rate_avg"),
            r.get("heart_rate_min"),
            r.get("heart_rate_max"),
        )
        cursor.execute(query_sql, values)
        count += 1

    conn.commit()
    return {
        "status": "success",
        "message": f"Saved {count} sleep records",
        "processed": count,
        "timestamp": datetime.now().isoformat(),
    }

schema = make_executable_schema(type_defs, query, mutation)
app = GraphQL(schema, debug=True)

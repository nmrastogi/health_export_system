import requests
from fastapi import FastAPI, Request

app = FastAPI()

GRAPHQL_URL = "http://localhost:4000/graphql"

@app.post("/api/sleep")
async def rest_sleep(req: Request):
    data = await req.json()
    sleep_records = extract_sleep(data)

    graphql_query = """
    mutation($records: [SleepRecordInput!]!) {
      ingestSleep(records: $records) {
        status
        message
        processed
        timestamp
      }
    }
    """

    response = requests.post(GRAPHQL_URL, json={
        "query": graphql_query,
        "variables": {"records": sleep_records}
    })

    return response.json()

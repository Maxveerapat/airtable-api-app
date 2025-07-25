from fastapi import FastAPI
import requests
import os
import json

app = FastAPI()

# Load your Airtable token (from env var or hardcoded here)
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN") or "patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"

# Load all base configurations from bases.json
with open("bases.json") as f:
    BASES = json.load(f)

def fetch_airtable_data(base_id, table_name):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json().get("records", [])

@app.get("/query/{source}")
def query_airtable(source: str):
    config = BASES.get(source)
    if not config:
        return {"error": "Invalid source. Use /sources to see valid options."}
    
    records = fetch_airtable_data(config["base_id"], config["table"])
    
    return {
        "source": source,
        "records": [
            {
                "id": record["id"],
                "fields": record["fields"]
            }
            for record in records
        ]
    }

@app.get("/sources")
def list_sources():
    return {"available_sources": list(BASES.keys())}

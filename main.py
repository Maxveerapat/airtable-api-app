import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env variables if running locally
load_dotenv()

app = FastAPI()

# Allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Your actual Airtable token (with fallback for local dev)
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN") or "patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"

# ✅ Mapping of base + table by name
DATA_SOURCES = {
    "ivy": {
        "base_id": "appcICyZQ3zPn2jyu",
        "table": "Ivy Sathorn 10"
    },
    "master": {
        "base_id": "appoCDPIuhneJ0vwm",
        "table": "Master Condo List"
    }
}

# ✅ Endpoint to fetch all records from a given source
@app.get("/records/{source}")
async def get_all_records(source: str):
    if source not in DATA_SOURCES:
        raise HTTPException(status_code=404, detail="Source not found")

    base_id = DATA_SOURCES[source]["base_id"]
    table_name = DATA_SOURCES[source]["table"]
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}"
    }

    all_records = []
    params = {}

    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())

        data = response.json()
        all_records.extend(data.get("records", []))

        if "offset" in data:
            params["offset"] = data["offset"]
        else:
            break

    return {"source": source, "records": all_records}

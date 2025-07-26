import requests
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load bases.json
with open("bases.json") as f:
    BASES = json.load(f)

@app.get("/records/{source}")
def get_records(source: str):
    if source not in BASES:
        raise HTTPException(status_code=404, detail="Source not found")

    base_id = BASES[source]["base_id"]
    table_name = BASES[source]["table"]
    headers = {
        "Authorization": "Bearer patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"
    }

    all_records = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset

        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        res = requests.get(url, headers=headers, params=params)

        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)

        data = res.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break

    return {
        "source": source,
        "records": all_records
    }

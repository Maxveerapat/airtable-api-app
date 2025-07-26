from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import json

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN") or "patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"

with open("bases.json") as f:
    DATA_SOURCES = json.load(f)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/qu/{source}")
async def get_filtered_records(source: str, request: Request):
    if source not in DATA_SOURCES:
        raise HTTPException(status_code=404, detail="Source not found")

    base_id = DATA_SOURCES[source]["base_id"]
    table_name = DATA_SOURCES[source]["table"]
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = { "Authorization": f"Bearer {AIRTABLE_TOKEN}" }

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

    # Parse filters like RENT_lte=15000 or FL_gt=10
    filters = {}
    for key, value in request.query_params.items():
        if "_" not in key:
            continue
        field, op = key.rsplit("_", 1)
        filters.setdefault(field, []).append((op, value))

    def passes_filters(fields):
        for field, conditions in filters.items():
            if field not in fields:
                return False
            raw_value = fields[field]

            for op, value in conditions:
                try:
                    # Convert both to numbers if possible
                    val_num = float(str(value).replace(",", ""))
                    raw_num = float(str(raw_value).replace(",", ""))
                except:
                    val_num = value.strip().lower()
                    raw_num = str(raw_value).strip().lower()

                if op == "eq" and raw_num != val_num:
                    return False
                elif op == "neq" and raw_num == val_num:
                    return False
                elif op == "gt" and raw_num <= val_num:
                    return False
                elif op == "gte" and raw_num < val_num:
                    return False
                elif op == "lt" and raw_num >= val_num:
                    return False
                elif op == "lte" and raw_num > val_num:
                    return False
        return True

    filtered_records = [rec for rec in all_records if passes_filters(rec.get("fields", {}))]

    return { "source": source, "records": filtered_records }

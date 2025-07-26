import os
import json
import difflib
from typing import Dict
import requests
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN") or "patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"
AIRTABLE_URL = "https://api.airtable.com/v0"

app = FastAPI()

# Enable CORS for Custom GPT & external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load base config
with open("bases.json", "r") as f:
    BASES = json.load(f)

def get_closest_source_key(requested_key: str, valid_keys: list) -> str:
    matches = difflib.get_close_matches(requested_key.lower(), valid_keys, n=1, cutoff=0.8)
    return matches[0] if matches else None

def cast_numeric(value):
    try:
        return float(str(value).replace(",", ""))
    except:
        return None

def check_condition(field_val, op, compare_val):
    num_val = cast_numeric(field_val)
    num_cmp = cast_numeric(compare_val)
    if num_val is None or num_cmp is None:
        return False
    if op == "lt": return num_val < num_cmp
    if op == "lte": return num_val <= num_cmp
    if op == "gt": return num_val > num_cmp
    if op == "gte": return num_val >= num_cmp
    return False

@app.get("/qu/{source}")
def query_airtable(
    source: str = Path(..., description="The source name from bases.json"),
    offset: str = Query(None),
    **query_params: str
):
    valid_keys = list(BASES.keys())
    matched_key = get_closest_source_key(source, valid_keys)
    if not matched_key:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown source '{source}'. Available: {valid_keys}"},
        )

    base_id = BASES[matched_key]["base_id"]
    table_name = BASES[matched_key]["table"]

    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    url = f"{AIRTABLE_URL}/{base_id}/{table_name}"

    # Get all records (handle pagination)
    all_records = []
    params = {}
    if offset:
        params["offset"] = offset
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return JSONResponse(
                status_code=response.status_code,
                content={"error": "Failed to fetch from Airtable", "details": response.text},
            )
        data = response.json()
        all_records.extend(data.get("records", []))
        if "offset" not in data:
            break
        params["offset"] = data["offset"]

    # Apply filters manually
    filtered = []
    for record in all_records:
        fields = record.get("fields", {})
        match = True
        for key, val in query_params.items():
            if key.endswith("_lt"):
                field = key[:-3]
                if not check_condition(fields.get(field), "lt", val):
                    match = False
                    break
            elif key.endswith("_lte"):
                field = key[:-4]
                if not check_condition(fields.get(field), "lte", val):
                    match = False
                    break
            elif key.endswith("_gt"):
                field = key[:-3]
                if not check_condition(fields.get(field), "gt", val):
                    match = False
                    break
            elif key.endswith("_gte"):
                field = key[:-4]
                if not check_condition(fields.get(field), "gte", val):
                    match = False
                    break
            elif key.endswith("_ne"):
                field = key[:-3]
                if str(fields.get(field)).strip() == val:
                    match = False
                    break
            else:
                if str(fields.get(key)).strip() != val:
                    match = False
                    break
        if match:
            filtered.append(record)

    return {
        "source": matched_key,
        "records": filtered,
        "offset": None
    }

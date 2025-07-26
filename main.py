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

# CORS for Render + Custom GPT access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load base mappings
with open("bases.json", "r") as f:
    BASES = json.load(f)

# Match user input to closest base
def get_closest_source_key(requested_key: str, valid_keys: list) -> str:
    matches = difflib.get_close_matches(requested_key.lower(), valid_keys, n=1, cutoff=0.8)
    return matches[0] if matches else None

# Main route for Airtable query
@app.get("/qu/{source}")
def query_airtable(
    source: str = Path(..., description="The source name from bases.json"),
    offset: str = Query(None),
    **query_params: str
):
    # Match source
    valid_keys = list(BASES.keys())
    matched_key = get_closest_source_key(source, valid_keys)
    if not matched_key:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown source '{source}'. Available: {valid_keys}"},
        )

    base_id = BASES[matched_key]["base_id"]
    table_name = BASES[matched_key]["table"]

    # Convert query params into Airtable formula
    conditions = []
    for key, val in query_params.items():
        if key.endswith("_lte"):
            field = key[:-4]
            conditions.append(f"AND(NOT({{{field}}} = BLANK()), {{{field}}} <= {val})")
        elif key.endswith("_gte"):
            field = key[:-4]
            conditions.append(f"AND(NOT({{{field}}} = BLANK()), {{{field}}} >= {val})")
        elif key.endswith("_lt"):
            field = key[:-3]
            conditions.append(f"AND(NOT({{{field}}} = BLANK()), {{{field}}} < {val})")
        elif key.endswith("_gt"):
            field = key[:-3]
            conditions.append(f"AND(NOT({{{field}}} = BLANK()), {{{field}}} > {val})")
        elif key.endswith("_ne"):
            field = key[:-3]
            conditions.append(f"AND(NOT({{{field}}} = BLANK()), NOT({{{field}}} = '{val}'))")
        else:
            conditions.append(f"AND(NOT({{{key}}} = BLANK()), {{{key}}} = '{val}')")

    formula = f"AND({','.join(conditions)})" if conditions else None

    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    params = {"filterByFormula": formula} if formula else {}
    if offset:
        params["offset"] = offset

    url = f"{AIRTABLE_URL}/{base_id}/{table_name}"
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Failed to fetch from Airtable", "details": response.text},
        )

    data = response.json()
    return {
        "source": matched_key,
        "records": data.get("records", []),
        "offset": data.get("offset"),
    }

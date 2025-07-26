import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN") or "patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}"
}

with open("bases.json") as f:
    BASES = json.load(f)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/qu/{source}")
async def get_airtable_data(source: str, request: Request):
    source = unquote(source)
    if source not in BASES:
        return {"error": f"Unknown source: {source}"}

    base_id = BASES[source]["base_id"]
    table = BASES[source]["table"]
    url = f"https://api.airtable.com/v0/{base_id}/{table}"

    params = request.query_params.multi_items()
    query_params = {}

    filters = []
    for key, value in params:
        if "_" in key:
            field, operator = key.split("_", 1)
            if operator == "lte":
                filters.append(f"{{{field}}} <= {value}")
            elif operator == "gte":
                filters.append(f"{{{field}}} >= {value}")
            elif operator == "lt":
                filters.append(f"{{{field}}} < {value}")
            elif operator == "gt":
                filters.append(f"{{{field}}} > {value}")
            elif operator == "eq":
                filters.append(f"{{{field}}} = '{value}'")
        else:
            filters.append(f"{{{key}}} = '{value}'")

    if filters:
        formula = "AND(" + ", ".join(filters) + ")"
        query_params["filterByFormula"] = formula

    all_records = []
    offset = None
    while True:
        if offset:
            query_params["offset"] = offset
        response = requests.get(url, headers=HEADERS, params=query_params)
        if response.status_code != 200:
            return {"error": f"Airtable API error: {response.status_code}", "detail": response.text}

        data = response.json()
        all_records.extend(data.get("records", []))

        offset = data.get("offset")
        if not offset:
            break

    return {"source": source, "records": all_records}

from fastapi import FastAPI, HTTPException
import requests
import json
import os

app = FastAPI()

AIRTABLE_TOKEN = "patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"

with open("bases.json", "r") as f:
    BASES = json.load(f)

def get_all_records(base_id: str, table: str):
    url = f"https://api.airtable.com/v0/{base_id}/{table}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    params = {"pageSize": 100}
    all_records = []
    offset = None

    while True:
        if offset:
            params["offset"] = offset
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Error: {response.text}")
        data = response.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break

    return all_records

@app.get("/")
def root():
    return {"message": "Airtable API app is running!"}

@app.get("/records/{key}")
def read_records(key: str):
    if key not in BASES:
        raise HTTPExcep

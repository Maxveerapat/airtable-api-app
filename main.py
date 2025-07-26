@app.get("/records/{source}")
def get_records(source: str):
    if source not in BASES:
        raise HTTPException(status_code=404, detail="Source not found")

    base_id = BASES[source]["base_id"]
    table_name = BASES[source]["table"]
    headers = {
        "Authorization": f"Bearer patD44eAmwBtOGZ4l.c24106c64563ac416643f50718f4a702859fcec80734cc8b2f4825e814f4648e"
    }

    all_records = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset

        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        all_records.extend(data.get("records", []))
        offset = data.get("offset")

        if not offset:
            break

    return {
        "source": source,
        "records": all_records
    }

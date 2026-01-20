import pandas as pd
import requests

KEV_URL = "https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv"

def fetch_kev(run_date: str) -> pd.DataFrame:
    r = requests.get(KEV_URL, timeout=60)
    r.raise_for_status()

    df = pd.read_csv(pd.io.common.BytesIO(r.content))
    df = df.rename(columns={
        "cveID": "cve_id",
        "vendorProject": "vendor_project",
        "product": "product",
        "vulnerabilityName": "vulnerability_name",
        "dateAdded": "date_added",
        "shortDescription": "short_description",
        "requiredAction": "required_action",
        "dueDate": "due_date",
        "notes": "notes",
    })

    for col in ["date_added", "due_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    df["source_url"] = KEV_URL
    df["run_date"] = pd.to_datetime(run_date).date()
    return df


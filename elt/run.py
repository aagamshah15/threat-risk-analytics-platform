import json
import pandas as pd

from config import MINIO, POSTGRES, RUN_DATE
from loaders.minio import s3_client, put_bytes
from loaders.postgres import pg_conn, insert_rows
from sources.cisa_kev import fetch_kev
from sources.urlhaus import fetch_urlhaus_recent


def df_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


def normalize_value(v):
    """
    Convert pandas/numpy-friendly values into psycopg2-friendly Python values.
    - pd.NA / NaN / NaT -> None
    - pandas Timestamp -> Python datetime
    """
    if pd.isna(v):
        return None
    # pandas Timestamp (including tz-aware) -> python datetime
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    return v


def df_to_rows(df: pd.DataFrame, cols: list[str]) -> list[tuple]:
    """
    Build row tuples with value-level sanitation (most reliable way).
    """
    rows = []
    for row in df[cols].itertuples(index=False, name=None):
        rows.append(tuple(normalize_value(v) for v in row))
    return rows


def main():
    # 1) Extract
    kev = fetch_kev(RUN_DATE)
    urlhaus = fetch_urlhaus_recent(RUN_DATE)

    # 2) Land Bronze in MinIO (immutable snapshot files)
    s3 = s3_client(MINIO["endpoint"], MINIO["access_key"], MINIO["secret_key"])
    date_part = RUN_DATE

    put_bytes(
        s3,
        MINIO["bucket"],
        f"bronze/cisa_kev/run_date={date_part}/kev.parquet",
        df_to_parquet_bytes(kev),
        "application/octet-stream",
    )

    put_bytes(
        s3,
        MINIO["bucket"],
        f"bronze/urlhaus/run_date={date_part}/urlhaus_recent.parquet",
        df_to_parquet_bytes(urlhaus),
        "application/octet-stream",
    )

    # 3) Load Raw into Postgres
    conn = pg_conn(POSTGRES)

    # --- KEV -> raw.kev ---
    kev_cols = [
        "cve_id",
        "vendor_project",
        "product",
        "vulnerability_name",
        "date_added",
        "short_description",
        "required_action",
        "due_date",
        "notes",
        "source_url",
        "run_date",
    ]

    insert_rows(
        conn,
        "raw.kev",
        kev_cols,
        df_to_rows(kev, kev_cols),
    )

    # --- URLhaus -> raw.urlhaus_recent ---
    expected = [
        "url",
        "url_status",
        "host",
        "date_added",
        "threat",
        "tags",
        "urlhaus_link",
        "reporter",
        "larted",
        "source_url",
        "run_date",
    ]

    # URLhaus feed columns can vary; guarantee expected columns exist
    for c in expected:
        if c not in urlhaus.columns:
            urlhaus[c] = None

    # Ensure date_added is datetime (timezone-aware is fine for TIMESTAMPTZ)
    if "date_added" in urlhaus.columns:
        urlhaus["date_added"] = pd.to_datetime(urlhaus["date_added"], errors="coerce", utc=True)

    insert_rows(
        conn,
        "raw.urlhaus_recent",
        expected,
        df_to_rows(urlhaus, expected),
    )

    conn.close()

    print(
        json.dumps(
            {
                "status": "ok",
                "run_date": RUN_DATE,
                "bronze": [
                    f"s3://{MINIO['bucket']}/bronze/cisa_kev/run_date={date_part}/kev.parquet",
                    f"s3://{MINIO['bucket']}/bronze/urlhaus/run_date={date_part}/urlhaus_recent.parquet",
                ],
                "raw_tables": ["raw.kev", "raw.urlhaus_recent"],
                "counts": {
                    "kev_rows": int(len(kev)),
                    "urlhaus_rows": int(len(urlhaus)),
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()


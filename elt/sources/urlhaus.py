import io
import pandas as pd
import requests

URLHAUS_RECENT = "https://urlhaus.abuse.ch/downloads/csv_recent/"

COLS = [
    "id",
    "date_added",
    "url",
    "url_status",
    "last_online",
    "threat",
    "tags",
    "urlhaus_link",
    "reporter",
]

def _read_noheader(text: str) -> pd.DataFrame:
    lines = [ln for ln in text.splitlines() if not ln.startswith("#") and ln.strip() != ""]
    body = "\n".join(lines)

    # Try common delimiters; accept the first parse that yields >= 9 columns
    for sep in ["\t", ",", ";"]:
        try:
            df = pd.read_csv(
                io.StringIO(body),
                sep=sep,
                header=None,
                names=COLS,
                engine="python",
                on_bad_lines="skip",
            )
            # If url column looks like URLs for most rows, we accept
            if df["url"].astype(str).str.startswith("http").mean() > 0.8:
                return df
        except Exception:
            continue

    raise RuntimeError("URLhaus parse failed: could not parse with expected delimiters/columns")

def fetch_urlhaus_recent(run_date: str) -> pd.DataFrame:
    r = requests.get(URLHAUS_RECENT, timeout=60)
    r.raise_for_status()

    text = r.content.decode("utf-8", errors="replace")
    df = _read_noheader(text)

    # Type cleanup
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce", utc=True)
    df["last_online"] = pd.to_datetime(df["last_online"], errors="coerce", utc=True)

    # Optional fields for our raw table (we don't have these in this feed)
    df["host"] = None
    df["larted"] = None

    df["source_url"] = URLHAUS_RECENT
    df["run_date"] = pd.to_datetime(run_date).date()
    return df


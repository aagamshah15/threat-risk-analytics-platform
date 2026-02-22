from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "5"))

st.set_page_config(page_title="Threat & Risk Demo", layout="wide")


@st.cache_data(ttl=30)
def api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def render_pipeline_health() -> None:
    st.subheader("Pipeline Health")
    summary = api_get("/v1/pipeline/summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stream Events", summary["stream_events_total"])
    col2.metric("Threat Events (Mart)", summary["threat_rows_total"])
    col3.metric("KEV Rows", summary["kev_rows_total"])
    col4.metric("Ingest Lag (min)", summary["stream_ingest_lag_minutes"])

    st.caption(f"Latest stream ingest: {summary['latest_stream_ingested_at']}")
    st.caption(f"Consumer heartbeat lag (min): {summary['consumer_heartbeat_lag_minutes']}")


def render_stream_freshness_lag() -> None:
    st.subheader("Stream Freshness / Lag Trends")
    lag = api_get("/v1/trends/stream-lag", params={"hours": 24})
    df = pd.DataFrame(lag["series"])
    if df.empty:
        st.info("No stream lag data yet.")
        return

    df["bucket_hour"] = pd.to_datetime(df["bucket_hour"])
    df = df.sort_values("bucket_hour")

    st.line_chart(df.set_index("bucket_hour")[["avg_event_delay_seconds"]])
    st.dataframe(df, use_container_width=True)


def render_top_malicious_hosts() -> None:
    st.subheader("Top Malicious URLs/Hosts")
    top = api_get("/v1/threat/top-hosts", params={"days": 7, "limit": 10})
    rows = pd.DataFrame(top["rows"])
    if rows.empty:
        st.info("No threat host data yet.")
        return

    st.bar_chart(rows.set_index("host")[["event_count"]])
    st.dataframe(rows, use_container_width=True)


def render_kev_highlights() -> None:
    st.subheader("KEV Highlights")
    kev = api_get("/v1/risk/kev-summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("KEV Total", kev["kev_total"])
    col2.metric("Unique CVEs", kev["unique_cves"])
    col3.metric("Overdue", kev["overdue_count"])

    st.caption(f"First Added: {kev['first_added']} | Latest Added: {kev['latest_added']}")

    vendors = pd.DataFrame(kev.get("top_vendors", []))
    if not vendors.empty:
        st.bar_chart(vendors.set_index("vendor")[["cve_count"]])
        st.dataframe(vendors, use_container_width=True)


def main() -> None:
    st.title("Threat & Risk Analytics Platform")
    st.caption("Phase 4: Consumption + Reliability Hardening")

    try:
        health = api_get("/health")
        st.success(f"API status: {health['status']}")
    except Exception as exc:
        st.error(f"API unavailable: {exc}")
        st.stop()

    page = st.sidebar.radio(
        "Demo Pages",
        [
            "Pipeline Health",
            "Stream Freshness/Lag Trends",
            "Top Malicious URLs/Hosts",
            "KEV Highlights",
        ],
    )

    if page == "Pipeline Health":
        render_pipeline_health()
    elif page == "Stream Freshness/Lag Trends":
        render_stream_freshness_lag()
    elif page == "Top Malicious URLs/Hosts":
        render_top_malicious_hosts()
    else:
        render_kev_highlights()


if __name__ == "__main__":
    main()

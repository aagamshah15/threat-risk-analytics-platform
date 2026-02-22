from __future__ import annotations

import os


def build_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "threat_risk")
    user = os.getenv("POSTGRES_USER", "app")
    password = os.getenv("POSTGRES_PASSWORD", "app")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


DB_DSN = os.getenv("DATABASE_URL", build_dsn())
APP_NAME = "Threat & Risk API"
APP_VERSION = "0.1.0"

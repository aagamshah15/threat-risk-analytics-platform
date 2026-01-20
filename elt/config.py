import os

def env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return v

POSTGRES = {
    "host": env("POSTGRES_HOST"),
    "port": int(env("POSTGRES_PORT", "5432")),
    "db": env("POSTGRES_DB"),
    "user": env("POSTGRES_USER"),
    "password": env("POSTGRES_PASSWORD"),
}

MINIO = {
    "endpoint": env("MINIO_ENDPOINT"),
    "access_key": env("MINIO_ACCESS_KEY"),
    "secret_key": env("MINIO_SECRET_KEY"),
    "bucket": env("MINIO_BUCKET"),
}

RUN_DATE = env("RUN_DATE", "2026-01-19")


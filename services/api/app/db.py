from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from .config import DB_DSN


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(DB_DSN)
    try:
        yield conn
    finally:
        conn.close()

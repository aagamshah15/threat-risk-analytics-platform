import psycopg2
from psycopg2.extras import execute_values

def pg_conn(cfg: dict):
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["db"],
        user=cfg["user"],
        password=cfg["password"],
    )

def insert_rows(conn, table: str, columns: list[str], rows: list[tuple]):
    if not rows:
        return
    cols = ",".join(columns)
    sql = f"INSERT INTO {table} ({cols}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=5000)
    conn.commit()


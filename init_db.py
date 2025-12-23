from app.db import get_db_connection
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "sql" / "schema.sql"

def init_db():
    conn = get_db_connection()
    with open(SCHEMA_PATH, "r") as f:
        sql = f.read()
        conn.executescript(sql)
    conn.commit()
    conn.close()
    print("Database initialized successfully with tables!")

if __name__ == "__main__":
    init_db()

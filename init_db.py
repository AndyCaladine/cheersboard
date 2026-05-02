import sqlite3
import os

DATABASE = os.path.join(os.getcwd(), "instance", "database.db")
SCHEMA = os.path.join(os.getcwd(), "schema.sql")


def init_db():
    os.makedirs("instance", exist_ok=True)

    with open(SCHEMA, "r") as f:
        schema = f.read()

    conn = sqlite3.connect(DATABASE)
    conn.executescript(schema)
    conn.commit()
    conn.close()

    print("Database initialised successfully.")


if __name__ == "__main__":
    init_db()
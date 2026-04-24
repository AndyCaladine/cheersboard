import sqlite3
import os

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')
SCHEMA = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'schema.sql')

def init_db():
    conn = sqlite3.connect(DATABASE)
    with open(SCHEMA, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database has initialised from schema.sql")

if __name__ == '__main__':
    init_db()

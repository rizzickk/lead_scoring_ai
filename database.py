import sqlite3
from datetime import datetime, timedelta

DB_NAME = "leads.db"


def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent TEXT,
        buyer_name TEXT,
        buyer_phone TEXT,
        score INTEGER,
        tier TEXT,
        probability REAL,
        max_price REAL,
        report_file TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def insert_lead(agent, buyer_name, buyer_phone, score, tier, probability, max_price, report_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO leads (agent, buyer_name, buyer_phone, score, tier, probability, max_price, report_file)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent,
        buyer_name,
        buyer_phone,
        score,
        tier,
        probability,
        max_price,
        report_path
    ))

    conn.commit()
    conn.close()


def get_stale_report_paths(days: int = 90) -> list[tuple[int, str]]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, report_file FROM leads WHERE timestamp < ?",
        (cutoff,)
    )
    rows = cursor.fetchall()

    conn.close()
    return rows


def delete_stale_leads(days: int = 90) -> None:
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM leads WHERE timestamp < ?", (cutoff,))

    conn.commit()
    conn.close()


def get_leads():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads ORDER BY id DESC")
    leads = cursor.fetchall()

    conn.close()
    return leads

import sqlite3
from datetime import datetime, timedelta

DB_FILE = "database.db"

def insert_email(sender, recipient, subject, body):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (sender, recipient, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (sender, recipient, subject, body, 'Pending')
    )
    conn.commit()
    conn.close()

def get_pending_emails():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE status = 'Pending'")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_status(email_id, status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET status = ? WHERE id = ?", (status, email_id))
    conn.commit()
    conn.close()

def save_to_memory(body):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO approved_memory (body) VALUES (?)", (body,))
    conn.commit()
    conn.close()

def get_approved_memory():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT body FROM approved_memory")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_manager_email(employee):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT manager_email, manager_manager_email FROM employees WHERE employee = ?", (employee,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]  # manager_email, manager's manager
    return None, None

def is_older_than_24hrs(dt_str):
    """Check if a datetime string is older than 24 hours"""
    try:
        # First try ISO format (with 'T' and microseconds)
        request_time = datetime.fromisoformat(dt_str)
    except ValueError:
        try:
            # Fallback to your original format
            request_time = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"Unsupported datetime format: {dt_str}") from e

    return datetime.now() - request_time > timedelta(hours=24)

def mark_status(email_id, status):
    """
    Update the status of an email request in the database.
    """
    return update_status(email_id, status)

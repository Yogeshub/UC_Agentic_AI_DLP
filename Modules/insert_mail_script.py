# import sqlite3
# from datetime import datetime, timedelta
#
# DB_FILE = "database.db"
#
# conn = sqlite3.connect(DB_FILE)
# cursor = conn.cursor()
#
# # Duplicate email
# cursor.execute(
#     "INSERT INTO requests (employee, datetime, type, details, destination, status, comment, attachment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     (
#         "alice@example.com",
#         datetime.now(),
#         "email",
#         "Subject: Sample Mail\nBody: This is a repeat message for test.",
#         "bob@external.com",
#         "Pending",
#         None,
#         None,
#     ),
# )
#
# # New & Sensitive
# cursor.execute(
#     "INSERT INTO requests (employee, datetime, type, details, destination, status, comment, attachment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     (
#         "alice@example.com",
#         datetime.now(),
#         "email",
#         "Subject: Test data Mail\nBody: This contains confidential salary info and secret.",
#         "bob@external.com",
#         "Pending",
#         None,
#         None,
#     ),
# )
#
# # New & Not Sensitive
# cursor.execute(
#     "INSERT INTO requests (employee, datetime, type, details, destination, status, comment, attachment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     (
#         "alice@example.com",
#         datetime.now(),
#         "email",
#         "Subject: Normal Mail\nBody: Hello, this is a normal message.",
#         "bob@external.com",
#         "Pending",
#         None,
#         None,
#     ),
# )
#
# # Older than 24 hrs
# older_time = datetime.now() - timedelta(days=2)
# cursor.execute(
#     "INSERT INTO requests (employee, datetime, type, details, destination, status, comment, attachment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     (
#         "alice@example.com",
#         older_time,
#         "email",
#         "Subject: Old Mail\nBody: Please review this old message.",
#         "bob@external.com",
#         "Pending",
#         None,
#         None,
#     ),
# )
#
# conn.commit()
# conn.close()
# print("Inserted 4 test rows into requests table!")
#

#UPDATE QUERY

import sqlite3
from datetime import datetime

DB_FILE = "database.db"


def reset_error_status():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Execute update with parameterized query
        cursor.execute(
            "UPDATE requests SET status = ? WHERE status = ?",
            ('Approved', 'Responded')
        )

        # Get number of affected rows
        affected_rows = cursor.rowcount
        print(f"Updated {affected_rows} records")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()

    finally:
        if conn:
            conn.close()


# Execute the function
reset_error_status()
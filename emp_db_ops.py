import sqlite3
from typing import Optional, List, Tuple, Dict, Any


class DatabaseManager:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize all database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Requests table (your existing structure)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    status TEXT NOT NULL,
                    comment TEXT
                )
            """)

            # Employees table (new structure)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_email TEXT PRIMARY KEY,
                    manager_email TEXT
                )
            """)
            conn.commit()

    # ----- Requests Operations (Your existing functionality) -----
    def get_requests_by_status(self, status: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, employee, datetime, type, details, destination 
                FROM requests WHERE status = ?
            """, (status,))
            return [dict(row) for row in cursor.fetchall()]

    def update_request(self, request_id: int, status: str, comment: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE requests 
                SET status = ?, comment = ? 
                WHERE id = ?
            """, (status, comment, request_id))
            conn.commit()
            return cursor.rowcount > 0

    # ----- Employee Operations (New functionality) -----
    def add_employee(self, employee_email: str, manager_email: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO employees VALUES (?, ?)
                """, (employee_email, manager_email))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_employees(self) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            return [dict(row) for row in cursor.fetchall()]

    def update_employee(self, employee_email: str, new_manager_email: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE employees 
                SET manager_email = ? 
                WHERE employee_email = ?
            """, (new_manager_email, employee_email))
            conn.commit()
            return cursor.rowcount > 0

    def delete_employee(self, employee_email: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM employees 
                WHERE employee_email = ?
            """, (employee_email,))
            conn.commit()
            return cursor.rowcount > 0
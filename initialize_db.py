import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee TEXT,
        datetime TEXT,
        type TEXT,
        details TEXT,
        destination TEXT,
        status TEXT,
        comment TEXT,
        attachment TEXT
    )
''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS approved_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        body TEXT
    )
''')
cursor.execute('''
    CREATE TABLE employees (
        employee_email TEXT PRIMARY KEY,
        manager_email TEXT
    )   
''')

conn.commit()
conn.close()
print("✅ DB initialized.")



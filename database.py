from sqlite3 import connect

def con():
    return connect("users.db")

def Table():
    conn = con()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert(username, email, password):
    conn = con()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def LoginCheck(email, password):
    conn = con()
    cur = conn.cursor()
    cur.execute(
        "SELECT password FROM users WHERE email = ?",
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return False
    return row[0] == password

if __name__ == "__main__":
    Table()
    print("Database ready")

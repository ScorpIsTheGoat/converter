import sqlite3
import uuid
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        Id TEXT PRIMARY KEY,
        Username TEXT UNIQUE NOT NULL,
        Email TEXT UNIQUE NOT NULL,
        Passwordhash TEXT NOT NULL
    );           
""")
conn.commit()
conn.close

def get_column_names(table_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    column_names = [row[1] for row in cursor.fetchall()]
    conn.commit()
    conn.close()
    return column_names

def get_all(table_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    items = cursor.fetchall()
    for item in items:
        yield item
    conn.commit()
    conn.close()
        
def delete_duplicate_users():
    try:
        # Find duplicate usernames
        cursor.execute("""
        SELECT username
        FROM users
        GROUP BY username
        HAVING COUNT(*) > 1
        ORDER BY username
        """)

        # Fetch all duplicate usernames
        duplicate_usernames = set(row[0] for row in cursor.fetchall())

        # Delete all but one instance of each duplicate username
        for username in duplicate_usernames:
            cursor.execute("""
            DELETE FROM users
            WHERE username IN (
                SELECT username
                FROM users
                GROUP BY username
                HAVING COUNT(*) > 1
                ORDER BY id ASC
                LIMIT 1 OFFSET 1
            )
            """, (username, username))

        conn.commit()
        print(f"Deleted {len(duplicate_usernames)} duplicate user entries.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        
def convert_to_blob(file_path):
    with open(file_path, 'rb') as file:
        blob_data = file.read()
    return blob_data
    
def add_user(username, email, passwordhash):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, email, Passwordhash) VALUES (?,?,?)", (username, email, passwordhash))
    except:
        return("User is already registered")
    print("Success")
    conn.commit()
    conn.close()

def verify_user(username: str, passwordhash: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE Username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[3] == passwordhash:
        return True
    return False
  
def delete_user(id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    id = int(id)
    cursor.execute("DELETE FROM users WHERE Id = ?", (id))
    conn.commit()
    conn.close()
    print("Successfully deleted")

def change_email(user_id, new_email):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET Email = ? WHERE Id = ?", (new_email, user_id))
    conn.commit()
    conn.close
    print(f"Sucessfully updated Email to{new_email}")

def change_passwordhash(user_id, new_passwordhash):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET Passwordhash = ? WHERE Id = ?", (new_passwordhash, user_id))
    conn.commit()
    conn.close
    print(f"Sucessfully updated Passwordhash to{new_passwordhash}")

def change_username(user_id, new_username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET Username = ? WHERE Id = ?", (new_username, user_id))
    conn.commit()
    conn.close
    print(f"Sucessfully updated Username to{new_username}")
    

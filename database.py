import os
import sqlite3
import uuid
import re
import bcrypt
import shutil
import glob
from config.constants import SALT
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        SessionId TEXT,
        Username TEXT UNIQUE NOT NULL,
        Email TEXT UNIQUE NOT NULL,
        Passwordhash TEXT NOT NULL
    );           
""")
conn.commit()
conn.close
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Password is valid."
def is_valid_email(email):
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
    if re.match(regex, email):
        return True
    else:
        return False
def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), SALT)
    return hashed_password.decode('utf-8')
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
    
def add_user(username, email, passwordhash):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, email, Passwordhash) VALUES (?,?,?)", (username, email, passwordhash))
    except:
        return("User is already registered")
    print("Success")
    cursor.execute("SELECT * FROM Users WHERE Username=?", (username,))
    user = cursor.fetchone()
    print(f"User attributes for '{username}':")
    print(f"SessionId: {user[0]}")
    print(f"Username: {user[1]}")
    print(f"Email: {user[2]}")
    print(f"Passwordhash: {user[3]}")
    directory = f"uploads/{username}"
    try:
        os.mkdir(directory)
    except:
        files = glob.glob(f"{directory}/*")
        for file in files:
            if os.path.isfile(file):
                os.remove(file)
    conn.commit()
    conn.close()

def get_user_by_session(session_id: str):
    conn = sqlite3.connect("your_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE SessionId=?", (session_id,))
    user = cursor.fetchone()
    conn.close()
    
    return user

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


def get_user_by_username(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Query to select user attributes based on username
    cursor.execute("""
        SELECT SessionId, Username, Email, Passwordhash FROM Users WHERE Username = ?
    """, (username,))

    # Fetch and display user information
    user = cursor.fetchone()
    conn.close()
    
    if user:
        print(f"User attributes for '{username}':")
        print(f"SessionId: {user[0]}")
        print(f"Username: {user[1]}")
        print(f"Email: {user[2]}")
        print(f"Passwordhash: {user[3]}")
    else:
        print(f"No user found with username '{username}'.")

def add_session_to_user(username, session_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Update the SessionId for the user with the specified username
    cursor.execute("""
        UPDATE Users
        SET SessionId = ?
        WHERE Username = ?;
    """, (session_id, username))
    
    # Check if the update was successful
    if cursor.rowcount == 0:
        print(f"User '{username}' not found. No session ID was updated.")
    else:
        print(f"Session ID '{session_id}' successfully updated for user '{username}'.")
    
    # Commit the transaction and close the connection
    conn.commit()
    conn.close()
    print(get_user_by_username("Blackknight"))
    return



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
        Passwordhash TEXT NOT NULL,
        AmountOfConvertedFiles INTEGER
    );           
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS UploadedFiles (
        Hash TEXT PRIMARY KEY,
        Path TEXT NOT NULL,
        Username TEXT NOT NULL,
        Private INTEGER DEFAULT 0,
        FileName TEXT NOT NULL,
        FileType TEXT NOT NULL,      
        FileSize INTEGER NOT NULL,  
        Thumbnail BLOB,             
        Duration INTEGER,           
        Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
    );
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ConvertedFiles (
        OriginHash TEXT NOT NULL,
        Hash TEXT PRIMARY KEY,    
        Path TEXT NOT NULL,       
        Username TEXT NOT NULL,   
        Private INTEGER DEFAULT 0
    );
""")
conn.commit()
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
        cursor.execute("""INSERT INTO Users (Username, Email, Passwordhash, AmountOfConvertedFiles) VALUES (?, ?, ?, ?)""", (username, email, passwordhash, 0))
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
    try:
        os.mkdir(f"{directory}/uploaded")
        os.mkdir(f"{directory}/converted")
    except:
        print("Folders already created")
    conn.commit()
    conn.close()

def get_user_by_session(session_id: str):
    conn = sqlite3.connect("users.db")
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

def get_user_by_username(username: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

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

def remove_session_from_db(session_id: str):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET SessionId = NULL WHERE SessionId = ?", (session_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error removing session from db: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove session")

def add_file(hash: str, path: str, username: str, private: bool, filename: str, filetype: str, filesize: int, thumbnail: bytes, duration=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        private_value = 1 if private else 0
        
        cursor.execute("""
            INSERT INTO UploadedFiles (Hash, Path, Username, Private, FileName, FileType, FileSize, Thumbnail, Duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (hash, path, username, private_value, filename, filetype, filesize, thumbnail, duration))
        conn.commit()
        print(f"File with hash '{hash}' added successfully.")
    except sqlite3.IntegrityError as e:
        print(f"Error adding file: {e}")
    finally:
        conn.close()

def is_hash_in_table(hash: str) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM UploadedFiles WHERE Hash = ? LIMIT 1;", (hash,))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()

def get_file_path_by_hash(hash: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Path FROM UploadedFiles WHERE Hash = ?", (hash,))
        result = cursor.fetchone()
        if result:
            return result[0] 
        else:
            return None  
    finally:
        conn.close()

def all_file_hashes() -> list:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Hash FROM UploadedFiles")
        hashes = cursor.fetchall() 
        return [hash[0] for hash in hashes]  
    finally:
        conn.close()

def delete_all_file_hash_mappings():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM UploadedFiles") 
        conn.commit()
        print("Alle Einträge in UploadedFiles wurden gelöscht.")
    finally:
        conn.close()

def file_is_private(filehash: str) -> bool:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Private FROM UploadedFiles WHERE hash = ?", (filehash,))
        result = cursor.fetchone()
        if result:
            return bool(result[0])  #1 meaning true, 0 meaning false
        return False  
    finally:
        conn.close()

def get_username_by_filehash(filehash: str) -> str:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Username FROM UploadedFiles WHERE hash = ?", (filehash,))
        result = cursor.fetchone()
        if result:
            return result[0]  
        return None
    finally:
        conn.close()

def delete_hash(hash_to_delete):
    try:
        conn = sqlite3.connect('users.db')  
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM UploadedFiles
            WHERE Hash = ?;
        """, (hash_to_delete,))
        conn.commit()
        return ("success")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return ("false")  
    finally:
        conn.close()

def add_converted_file(origin_hash, file_hash, path, username, private=0):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ConvertedFiles (
                OriginHash, Hash, Path, Username, Private
            )
            VALUES (?, ?, ?, ?, ?);
        """, (origin_hash, file_hash, path, username, private))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

def cleanup_table(table_name):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    if table_name == "UploadedFiles":
        index_of_path = 1
    else:
        index_of_path = 2
    for row in rows:
        file_path = row[index_of_path]
        if not os.path.exists(file_path):
            print(f"File missing: {file_path}. Removing entry from {table_name}.")
            cursor.execute(f"DELETE FROM {table_name} WHERE Path = ?", (file_path,))
            conn.commit()
        else:
            print(f"File found at {file_path}")
    print(f"Cleaned up table {table_name}")
    conn.close()
    return

def delete_all_entries(table_name):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()  
        print(f"All entries deleted from the table: {table_name}")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
    return

def get_hash_by_path(file_path):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Hash FROM UploadedFiles WHERE Path = ?;
        """, (file_path,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()
def increase_amount_of_converted_files(session_id, increment):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Users
            SET AmountOfConvertedFiles = AmountOfConvertedFiles + ?
            WHERE SessionId = ?;
        """, (increment, session_id))
        conn.commit()
        if cursor.rowcount == 0:
            print("No user found with the given SessionId.")
        else:
            print(f"Successfully updated {cursor.rowcount} record(s).")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the connection
        conn.close()
def update_privacy_db(filehash, privacy):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    privacy_value = 0 if privacy.lower() == 'public' else 1 if privacy.lower() == 'private' else None
    if privacy_value is None:
        print("Invalid privacy value. Please use 'public' or 'private'.")
        return
    cursor.execute("""
        UPDATE UploadedFiles
        SET Private = ?
        WHERE Hash = ?
    """, (privacy_value, filehash))
    conn.commit()
    if cursor.rowcount == 0:
        print(f"No file found with hash {filehash}.")
    else:
        print(f"Privacy of file {filehash} updated to {privacy}.")
def get_file_properties(file_path: str, username: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * 
            FROM UploadedFiles
            WHERE Path = ? AND Username = ?;
        """, (file_path, username))
        file = cursor.fetchone()

        if file:
            file_properties = {
                "hash": file[0],         
                "path": file[1],         
                "username": file[2],     
                "private": file[3],      
                "file_name": file[4],    
                "file_type": file[5],    
                "file_size": file[6],    
                "thumbnail": file[7],    
                "duration": file[8],     
                "date": file[9],         
            }
            return file_properties
        else:
            return None
    finally:
        conn.close()
        
def get_file_type_by_hash(filehash: str) -> str:
    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT FileType FROM UploadedFiles WHERE Hash = ?", (filehash,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()
#delete_all_entries("Users")
for user in get_all("Users"):
    print(user)
for item in get_all("UploadedFiles"):
    print(item)

cleanup_table("UploadedFiles")
cleanup_table("ConvertedFiles")

print(all_file_hashes())
#delete_all_file_hash_mappings()
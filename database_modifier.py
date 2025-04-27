import sqlite3 

def cleartable(tablename: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tablename}")
    print(f"All entries cleared from table: {table_name}")
def delete_entry(tablename: str, column: str, value: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {tablename} WHERE {column} = ?;", (value,))
    entry = cursor.fetchone()
    if entry:
        print(f"Found entry: {entry}")
        cursor.execute(f"DELETE FROM {tablename} WHERE {column} = ?;", (value,))
        conn.commit()
        print(f"Entry with {column} = {value} deleted from {tablename}.")
        cursor.execute(f"SELECT * FROM {tablename} WHERE {column} = ?;", (value,))
        verify = cursor.fetchone()
        if not verify:
            print("Deletion verified: Entry no longer exists.")
        else:
            print("Deletion failed: Entry still exists.")
    else:
        print(f"No entry found with {column} = {value} in {tablename}.")
    conn.close()


delete_entry("ConvertedFiles", "Hash", "90cc4f35445bd1c4b3367af7b9a756b4a56723f19e0e20cc2ee1cced576303a8")
import sqlite3
import sys

def print_table_names(db_file):

    conn = sqlite3.connect(db_file)

    cur = conn.cursor()

    query = "SELECT name from sqlite_master where type='table';"

    try:
        cur.execute(query)
        tables = cur.fetchall()

        for table in tables:
            print(f"Table: {table[0]}")

        conn.close()
    except:
        print("Unable to read table")

print_table_names(sys.argv[1])

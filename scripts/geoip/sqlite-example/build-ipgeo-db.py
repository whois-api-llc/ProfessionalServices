import csv
import sqlite3
import sys

def create_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS geoip_table (
                        mark INTEGER PRIMARY KEY,
                        isp TEXT,
                        connectionType TEXT,
                        country TEXT,
                        region TEXT,
                        city TEXT,
                        lat REAL,
                        long REAL,
                        postalCode TEXT,
                        timeZone TEXT,
                        geonameId INTEGER
                    )''')

def insert_data(cursor, row):
    cursor.execute('''INSERT OR IGNORE INTO geoip_table (mark, isp, connectionType, \
                        country, region, city, lat, long, postalCode, timeZone, geonameId) \
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)

def read_csv_and_insert_into_sqlite(csv_filename, sqlite_filename):

    conn = sqlite3.connect(sqlite_filename)
    cursor = conn.cursor()

    create_table(cursor)

    print("ETL Process Started...")

    with open(csv_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader, None)
        
        for row in csv_reader:
            row[0] = int(row[0]) if row[0].isdigit() else None
            row[10] = int(row[10]) if row[10].isdigit() else None
            insert_data(cursor, row)

    # Commit and close
    conn.commit()
    conn.close()

    print("ETL Process Complete.")

print("\nLOAD-GEO-IPv4 by WHOIS.  ETL: <input_csv_filename> <database_filename.db> to create")
print("\tThis may take a few minutes depending on your system.\n")

read_csv_and_insert_into_sqlite(sys.argv[1], sys.argv[2])

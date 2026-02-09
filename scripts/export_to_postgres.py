#!/usr/bin/env python3
"""
Export SQLite database to PostgreSQL format.
Creates SQL dump that can be imported to Neon or any PostgreSQL database.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
from tqdm import tqdm

# Database paths
SQLITE_DB = 'data/bitcoin_ohlcv.db'
OUTPUT_SQL = 'data/bitcoin_ohlcv_postgres.sql'


def export_to_postgres_sql():
    """Export SQLite database to PostgreSQL-compatible SQL."""

    print("=" * 70)
    print("EXPORT SQLITE TO POSTGRESQL")
    print("=" * 70)
    print(f"Source: {SQLITE_DB}")
    print(f"Output: {OUTPUT_SQL}")
    print()

    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    # Get total row count
    cursor.execute("SELECT COUNT(*) FROM ohlcv")
    total_rows = cursor.fetchone()[0]
    print(f"Total rows to export: {total_rows:,}")
    print()

    # Open output file
    with open(OUTPUT_SQL, 'w') as f:
        # Write header
        f.write("-- Bitcoin OHLCV Data Export\n")
        f.write(f"-- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total rows: {total_rows:,}\n")
        f.write("\n")

        # Create table
        f.write("-- Create table\n")
        f.write("""
CREATE TABLE IF NOT EXISTS ohlcv (
    timestamp BIGINT PRIMARY KEY,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL,
    trades INTEGER,
    taker_buy_base REAL,
    taker_buy_quote REAL,
    CONSTRAINT check_high_low CHECK (high >= low),
    CONSTRAINT check_volume CHECK (volume >= 0)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_timestamp ON ohlcv(timestamp);
CREATE INDEX IF NOT EXISTS idx_timestamp_close ON ohlcv(timestamp, close);

""")

        print("Writing data...")

        # Export data in batches
        batch_size = 10000
        cursor.execute("SELECT * FROM ohlcv ORDER BY timestamp")

        inserted = 0
        batch = []

        for row in tqdm(cursor, total=total_rows, desc="Exporting"):
            # Format values for PostgreSQL
            values = ", ".join([
                str(row[0]),  # timestamp
                str(row[1]),  # open
                str(row[2]),  # high
                str(row[3]),  # low
                str(row[4]),  # close
                str(row[5]),  # volume
                str(row[6]) if row[6] is not None else 'NULL',  # quote_volume
                str(row[7]) if row[7] is not None else 'NULL',  # trades
                str(row[8]) if row[8] is not None else 'NULL',  # taker_buy_base
                str(row[9]) if row[9] is not None else 'NULL'   # taker_buy_quote
            ])

            batch.append(f"({values})")
            inserted += 1

            # Write batch
            if len(batch) >= batch_size:
                f.write(f"INSERT INTO ohlcv VALUES\n")
                f.write(",\n".join(batch))
                f.write(";\n\n")
                batch = []

        # Write remaining batch
        if batch:
            f.write(f"INSERT INTO ohlcv VALUES\n")
            f.write(",\n".join(batch))
            f.write(";\n\n")

    conn.close()

    # Get file size
    file_size = os.path.getsize(OUTPUT_SQL) / (1024 * 1024)

    print()
    print("=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"Exported rows: {inserted:,}")
    print(f"Output file: {OUTPUT_SQL}")
    print(f"File size: {file_size:.1f} MB")
    print()
    print("Next steps:")
    print("1. Sign up at https://console.neon.tech/")
    print("2. Create a new project")
    print("3. Copy the connection string")
    print("4. Import the SQL file using psql or the Neon console")
    print()
    print("Import command:")
    print(f"  psql YOUR_POSTGRES_URL < {OUTPUT_SQL}")
    print()


if __name__ == "__main__":
    export_to_postgres_sql()

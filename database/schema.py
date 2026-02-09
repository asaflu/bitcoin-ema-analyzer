"""
Database schema definitions and initialization.
"""

# OHLCV table schema
CREATE_OHLCV_TABLE = """
CREATE TABLE IF NOT EXISTS ohlcv (
    timestamp INTEGER PRIMARY KEY,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL NOT NULL,
    trades INTEGER NOT NULL,
    taker_buy_base REAL NOT NULL,
    taker_buy_quote REAL NOT NULL,
    CHECK (high >= low),
    CHECK (volume >= 0),
    CHECK (quote_volume >= 0)
)
"""

# Metadata table for tracking fetch progress
CREATE_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS fetch_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    start_timestamp INTEGER NOT NULL,
    end_timestamp INTEGER NOT NULL,
    records_fetched INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# Indexes for optimized queries
CREATE_OHLCV_TIMESTAMP_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp
ON ohlcv(timestamp)
"""

CREATE_OHLCV_COMPOSITE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp_close
ON ohlcv(timestamp, close)
"""

CREATE_METADATA_SYMBOL_INDEX = """
CREATE INDEX IF NOT EXISTS idx_metadata_symbol
ON fetch_metadata(symbol, interval)
"""

# All schema creation statements in order
SCHEMA_STATEMENTS = [
    CREATE_OHLCV_TABLE,
    CREATE_METADATA_TABLE,
    CREATE_OHLCV_TIMESTAMP_INDEX,
    CREATE_OHLCV_COMPOSITE_INDEX,
    CREATE_METADATA_SYMBOL_INDEX,
]


def initialize_schema(conn):
    """
    Initialize database schema with all tables and indexes.

    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()

    for statement in SCHEMA_STATEMENTS:
        cursor.execute(statement)

    conn.commit()

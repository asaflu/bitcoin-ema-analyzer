"""
Optimized query functions for OHLCV data operations.
Supports both SQLite and PostgreSQL.
"""

from typing import List, Tuple, Optional, Union
import sqlite3

# Try to import PostgreSQL support
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def _get_placeholder(conn) -> str:
    """Get the correct parameter placeholder for the database type."""
    if POSTGRES_AVAILABLE and isinstance(conn, psycopg2.extensions.connection):
        return '%s'
    return '?'


def _is_postgres(conn) -> bool:
    """Check if connection is PostgreSQL."""
    if POSTGRES_AVAILABLE:
        return isinstance(conn, psycopg2.extensions.connection)
    return False


def insert_ohlcv_batch(conn, records: List[Tuple]) -> int:
    """
    Bulk insert OHLCV records with transaction batching.
    Uses INSERT OR IGNORE (SQLite) or ON CONFLICT DO NOTHING (PostgreSQL).

    Args:
        conn: Database connection
        records: List of tuples (timestamp, open, high, low, close, volume,
                 quote_volume, trades, taker_buy_base, taker_buy_quote)

    Returns:
        Number of records inserted (excluding duplicates)
    """
    cursor = conn.cursor()
    placeholder = _get_placeholder(conn)

    if _is_postgres(conn):
        # PostgreSQL syntax
        insert_query = f"""
        INSERT INTO ohlcv
        (timestamp, open, high, low, close, volume, quote_volume, trades,
         taker_buy_base, taker_buy_quote)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        ON CONFLICT (timestamp) DO NOTHING
        """
    else:
        # SQLite syntax
        insert_query = f"""
        INSERT OR IGNORE INTO ohlcv
        (timestamp, open, high, low, close, volume, quote_volume, trades,
         taker_buy_base, taker_buy_quote)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """

    cursor.executemany(insert_query, records)
    inserted_count = cursor.rowcount

    return inserted_count


def get_latest_timestamp(conn, symbol: str = None) -> Optional[int]:
    """
    Get the most recent timestamp in the database.
    Used for resume capability.

    Args:
        conn: Database connection
        symbol: Symbol filter (currently unused, for future multi-symbol support)

    Returns:
        Latest timestamp in milliseconds, or None if table is empty
    """
    cursor = conn.cursor()

    query = "SELECT MAX(timestamp) FROM ohlcv"
    cursor.execute(query)

    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else None


def get_earliest_timestamp(conn) -> Optional[int]:
    """
    Get the earliest timestamp in the database.

    Args:
        conn: Database connection

    Returns:
        Earliest timestamp in milliseconds, or None if table is empty
    """
    cursor = conn.cursor()

    query = "SELECT MIN(timestamp) FROM ohlcv"
    cursor.execute(query)

    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else None


def count_records(conn) -> int:
    """
    Count total number of OHLCV records.

    Args:
        conn: Database connection

    Returns:
        Total record count
    """
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM ohlcv"
    cursor.execute(query)

    result = cursor.fetchone()
    return result[0] if result else 0


def query_ohlcv_range(
    conn,
    start_timestamp: int,
    end_timestamp: int
) -> List[Tuple]:
    """
    Query OHLCV data within a timestamp range.
    Optimized for backtesting queries.

    Args:
        conn: Database connection
        start_timestamp: Start time in milliseconds
        end_timestamp: End time in milliseconds

    Returns:
        List of OHLCV records as tuples
    """
    cursor = conn.cursor()
    placeholder = _get_placeholder(conn)

    query = f"""
    SELECT timestamp, open, high, low, close, volume, quote_volume,
           trades, taker_buy_base, taker_buy_quote
    FROM ohlcv
    WHERE timestamp >= {placeholder} AND timestamp <= {placeholder}
    ORDER BY timestamp ASC
    """

    cursor.execute(query, (start_timestamp, end_timestamp))
    return cursor.fetchall()


def find_gaps(conn, interval_ms: int = 60000) -> List[Tuple[int, int]]:
    """
    Find gaps in the time series (missing minutes).

    Args:
        conn: Database connection
        interval_ms: Expected interval in milliseconds (default: 60000 for 1 minute)

    Returns:
        List of (gap_start, gap_end) timestamp tuples
    """
    cursor = conn.cursor()

    # Find consecutive timestamps with gaps larger than the interval
    query = """
    SELECT
        timestamp as gap_start,
        LEAD(timestamp) OVER (ORDER BY timestamp) as next_timestamp
    FROM ohlcv
    """

    cursor.execute(query)
    results = cursor.fetchall()

    gaps = []
    for current, next_ts in results:
        if next_ts and (next_ts - current) > interval_ms:
            gaps.append((current, next_ts))

    return gaps


def insert_fetch_metadata(
    conn,
    symbol: str,
    interval: str,
    start_timestamp: int,
    end_timestamp: int,
    records_fetched: int,
    status: str
) -> int:
    """
    Insert metadata record for a fetch operation.

    Args:
        conn: Database connection
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1m')
        start_timestamp: Fetch start time
        end_timestamp: Fetch end time
        records_fetched: Number of records fetched
        status: Status ('success', 'partial', 'failed')

    Returns:
        ID of inserted metadata record
    """
    cursor = conn.cursor()
    placeholder = _get_placeholder(conn)

    query = f"""
    INSERT INTO fetch_metadata
    (symbol, interval, start_timestamp, end_timestamp, records_fetched, status)
    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
    """

    cursor.execute(query, (symbol, interval, start_timestamp, end_timestamp,
                          records_fetched, status))

    if _is_postgres(conn):
        # PostgreSQL doesn't have lastrowid, need to use RETURNING
        return cursor.fetchone()[0] if cursor.rowcount > 0 else None
    else:
        return cursor.lastrowid


def get_last_fetch_metadata(
    conn,
    symbol: str,
    interval: str
) -> Optional[Tuple]:
    """
    Get the most recent fetch metadata for a symbol/interval.

    Args:
        conn: Database connection
        symbol: Trading symbol
        interval: Time interval

    Returns:
        Metadata tuple or None
    """
    cursor = conn.cursor()
    placeholder = _get_placeholder(conn)

    query = f"""
    SELECT id, symbol, interval, start_timestamp, end_timestamp,
           records_fetched, status, created_at, updated_at
    FROM fetch_metadata
    WHERE symbol = {placeholder} AND interval = {placeholder}
    ORDER BY created_at DESC
    LIMIT 1
    """

    cursor.execute(query, (symbol, interval))
    return cursor.fetchone()

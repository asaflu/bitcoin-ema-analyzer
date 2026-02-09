#!/usr/bin/env python3
"""
Verify data integrity and detect gaps in the database.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db
from database.queries import (
    count_records,
    get_earliest_timestamp,
    get_latest_timestamp,
    find_gaps
)
from utils.logger import logger


def format_timestamp(timestamp_ms):
    """Format timestamp for display."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_duration(milliseconds):
    """Format duration in human-readable format."""
    minutes = milliseconds // 60000
    hours = minutes // 60
    days = hours // 24

    if days > 0:
        return f"{days} days, {hours % 24} hours"
    elif hours > 0:
        return f"{hours} hours, {minutes % 60} minutes"
    else:
        return f"{minutes} minutes"


def verify_database():
    """Verify database integrity and report statistics."""

    print("=" * 70)
    print("DATABASE VERIFICATION REPORT")
    print("=" * 70)
    print()

    # Check if database exists
    if not db.db_path.exists():
        logger.error(f"Database not found at {db.db_path}")
        return 1

    try:
        with db.connection() as conn:
            # Basic statistics
            total_records = count_records(conn)
            earliest = get_earliest_timestamp(conn)
            latest = get_latest_timestamp(conn)

            print("BASIC STATISTICS")
            print("-" * 70)
            print(f"Total records:       {total_records:,}")

            if earliest and latest:
                print(f"Earliest timestamp:  {format_timestamp(earliest)}")
                print(f"Latest timestamp:    {format_timestamp(latest)}")

                # Calculate coverage
                coverage_ms = latest - earliest
                coverage_minutes = coverage_ms // 60000
                expected_records = coverage_minutes + 1

                print(f"Time coverage:       {format_duration(coverage_ms)}")
                print(f"Expected records:    {expected_records:,}")

                # Calculate completeness
                completeness = (total_records / expected_records) * 100 if expected_records > 0 else 0
                print(f"Completeness:        {completeness:.2f}%")
            else:
                print("No data in database")

            print()

            # Database file size
            db_size = db.db_path.stat().st_size
            db_size_mb = db_size / (1024 * 1024)
            print(f"Database file size:  {db_size_mb:.2f} MB")
            print()

            # Gap detection
            if total_records > 0:
                print("GAP DETECTION")
                print("-" * 70)
                print("Searching for missing minutes...")

                gaps = find_gaps(conn, interval_ms=60000)

                if gaps:
                    print(f"\nFound {len(gaps)} gap(s):\n")

                    # Show first 10 gaps
                    for i, (gap_start, gap_end) in enumerate(gaps[:10], 1):
                        gap_duration_ms = gap_end - gap_start - 60000  # Subtract one interval
                        gap_minutes = gap_duration_ms // 60000

                        print(f"  Gap #{i}:")
                        print(f"    From: {format_timestamp(gap_start)}")
                        print(f"    To:   {format_timestamp(gap_end)}")
                        print(f"    Duration: {format_duration(gap_duration_ms)} ({gap_minutes:,} minutes)")
                        print()

                    if len(gaps) > 10:
                        print(f"  ... and {len(gaps) - 10} more gaps")
                        print()

                    # Calculate total missing minutes
                    total_missing = sum((gap_end - gap_start - 60000) // 60000 for gap_start, gap_end in gaps)
                    print(f"Total missing minutes: {total_missing:,}")

                else:
                    print("\n✓ No gaps detected - data is continuous!")

                print()

            # Query performance test
            print("QUERY PERFORMANCE TEST")
            print("-" * 70)

            if earliest and latest:
                # Test query on 1 day of data
                test_start = earliest
                test_end = min(earliest + 86400000, latest)  # 1 day or less

                import time
                start_time = time.time()

                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM ohlcv WHERE timestamp >= ? AND timestamp <= ?",
                    (test_start, test_end)
                )
                result = cursor.fetchone()

                query_time = (time.time() - start_time) * 1000

                print(f"Query time (1 day range): {query_time:.2f} ms")
                print(f"Records returned: {result[0]:,}")
            else:
                print("Insufficient data for performance test")

            print()

            # Recommendations
            print("RECOMMENDATIONS")
            print("-" * 70)

            if total_records == 0:
                print("⚠ Database is empty. Run fetch_historical_data.py to populate it.")
            elif completeness < 95:
                print(f"⚠ Data completeness is {completeness:.1f}%. Consider re-running the fetch")
                print("  to fill gaps or check for issues during fetching.")
            elif gaps:
                print(f"⚠ Found {len(gaps)} gap(s) in the data. These may be due to:")
                print("  - Binance API downtime or maintenance")
                print("  - Network interruptions during fetching")
                print("  - Low trading volume periods (unlikely for BTCUSDT)")
            else:
                print("✓ Database looks healthy with continuous data coverage!")

            print()
            print("=" * 70)

            return 0

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main execution function."""
    return verify_database()


if __name__ == "__main__":
    sys.exit(main())

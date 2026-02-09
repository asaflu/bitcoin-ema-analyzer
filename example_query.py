#!/usr/bin/env python3
"""
Example script demonstrating how to query the Bitcoin OHLCV database.
"""

from database.connection import db
from database.queries import query_ohlcv_range, count_records, get_latest_timestamp
from datetime import datetime


def format_timestamp(timestamp_ms):
    """Format timestamp for display."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Query examples."""
    print("Bitcoin OHLCV Database - Query Examples")
    print("=" * 60)

    with db.connection() as conn:
        # Get total records
        total = count_records(conn)
        print(f"\nTotal records in database: {total:,}")

        if total == 0:
            print("\nDatabase is empty. Run fetch_historical_data.py first.")
            return

        # Get latest timestamp
        latest = get_latest_timestamp(conn)
        print(f"Latest data: {format_timestamp(latest)}")

        # Query last 60 minutes of data
        start = latest - (60 * 60000)  # 60 minutes ago
        end = latest

        print(f"\nQuerying last 60 minutes ({format_timestamp(start)} to {format_timestamp(end)}):")
        print("-" * 60)

        data = query_ohlcv_range(conn, start, end)

        print(f"{'Timestamp':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
        print("-" * 60)

        # Show first 10 and last 5 records
        display_data = data[:10] + data[-5:] if len(data) > 15 else data

        for i, record in enumerate(display_data):
            timestamp, open_, high, low, close, volume = record[:6]

            # Add separator between first 10 and last 5
            if i == 10 and len(data) > 15:
                print(f"... ({len(data) - 15} records omitted) ...")

            dt = format_timestamp(timestamp)
            print(f"{dt:<20} {open_:<10.2f} {high:<10.2f} {low:<10.2f} {close:<10.2f} {volume:<12.6f}")

        print("-" * 60)
        print(f"Total records returned: {len(data)}")

        # Calculate some basic statistics
        if data:
            closes = [record[4] for record in data]
            highs = [record[2] for record in data]
            lows = [record[3] for record in data]
            volumes = [record[5] for record in data]

            print(f"\nStatistics for queried period:")
            print(f"  Price range: ${min(lows):.2f} - ${max(highs):.2f}")
            print(f"  Start price: ${data[0][1]:.2f}")
            print(f"  End price: ${data[-1][4]:.2f}")
            print(f"  Change: ${data[-1][4] - data[0][1]:.2f} ({((data[-1][4] / data[0][1]) - 1) * 100:.2f}%)")
            print(f"  Total volume: {sum(volumes):.2f} BTC")
            print(f"  Avg volume/minute: {sum(volumes) / len(volumes):.2f} BTC")


if __name__ == "__main__":
    main()

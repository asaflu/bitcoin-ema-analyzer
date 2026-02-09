#!/usr/bin/env python3
"""
Main script to fetch historical Bitcoin price data from Binance.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_fetcher.fetcher import DataFetcher
from utils.progress import ProgressTracker, format_timestamp
from utils.logger import logger
from database.connection import db
from database.queries import count_records


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch historical Bitcoin OHLCV data from Binance"
    )

    parser.add_argument(
        "--start",
        type=int,
        help="Start timestamp in milliseconds (default: earliest available)"
    )

    parser.add_argument(
        "--end",
        type=int,
        help="End timestamp in milliseconds (default: current time)"
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Trading symbol (default: BTCUSDT)"
    )

    parser.add_argument(
        "--interval",
        type=str,
        default="1m",
        help="Candle interval (default: 1m)"
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()

    print("=" * 60)
    print("BITCOIN HISTORICAL DATA FETCHER")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Interval: {args.interval}")
    print()

    # Check if database exists
    if not db.db_path.exists():
        logger.error(f"Database not found at {db.db_path}")
        logger.error("Please run 'python scripts/init_database.py' first")
        return 1

    # Initialize fetcher
    fetcher = DataFetcher(symbol=args.symbol, interval=args.interval)

    # Get initial database stats
    try:
        with db.connection() as conn:
            initial_count = count_records(conn)
        print(f"Current records in database: {initial_count:,}\n")
    except Exception as e:
        logger.error(f"Failed to query database: {e}")
        return 1

    # Calculate fetch range
    try:
        start_timestamp, end_timestamp = fetcher.calculate_fetch_range()

        # Override with command-line arguments if provided
        if args.start:
            start_timestamp = args.start
            print(f"Using custom start time: {format_timestamp(start_timestamp)}")

        if args.end:
            end_timestamp = args.end
            print(f"Using custom end time: {format_timestamp(end_timestamp)}")

        # Calculate progress tracking parameters
        total_minutes = (end_timestamp - start_timestamp) // 60000
        total_batches = (total_minutes // 1000) + 1

    except Exception as e:
        logger.error(f"Failed to calculate fetch range: {e}")
        return 1

    # Progress callback
    progress_tracker = None

    def progress_callback(batch_num, total_batches, current_timestamp):
        nonlocal progress_tracker

        if progress_tracker is None:
            progress_tracker = ProgressTracker(
                total=total_batches,
                desc="Fetching batches"
            ).__enter__()

        progress_tracker.update(
            1,
            timestamp=format_timestamp(current_timestamp)
        )

    # Fetch data
    try:
        print("Starting data fetch...")
        print("(Press Ctrl+C to interrupt - progress will be saved)\n")

        stats = fetcher.fetch_historical_data(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            progress_callback=progress_callback
        )

        # Clean up progress tracker
        if progress_tracker:
            progress_tracker.__exit__(None, None, None)

        # Print summary
        fetcher.print_summary()

        return 0

    except KeyboardInterrupt:
        print("\n\nFetch interrupted by user.")
        if progress_tracker:
            progress_tracker.__exit__(None, None, None)

        fetcher.print_summary()
        print("\nProgress has been saved. Run this script again to resume.")
        return 0

    except Exception as e:
        logger.error(f"Fetch failed with error: {e}")
        if progress_tracker:
            progress_tracker.__exit__(None, None, None)

        fetcher.print_summary()
        return 1


if __name__ == "__main__":
    sys.exit(main())

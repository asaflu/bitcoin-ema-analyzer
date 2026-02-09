"""
Main data fetching orchestration.
"""

import time
from typing import Optional, List, Tuple
from datetime import datetime

from config import MAX_CANDLES_PER_REQUEST, SYMBOL, INTERVAL, MIN_TIMESTAMP
from database.connection import db
from database.queries import (
    insert_ohlcv_batch,
    get_latest_timestamp,
    insert_fetch_metadata,
    count_records
)
from data_fetcher.binance_client import BinanceClient, BinanceAPIError
from data_fetcher.validators import (
    parse_binance_kline,
    validate_ohlcv_batch,
    validate_timestamp_continuity
)


class DataFetcher:
    """
    Orchestrates fetching historical OHLCV data from Binance.
    """

    def __init__(self, symbol: str = SYMBOL, interval: str = INTERVAL):
        """
        Initialize data fetcher.

        Args:
            symbol: Trading symbol
            interval: Candle interval
        """
        self.symbol = symbol
        self.interval = interval
        self.client = BinanceClient(symbol, interval)
        self.stats = {
            "total_fetched": 0,
            "total_inserted": 0,
            "total_duplicates": 0,
            "total_invalid": 0,
            "api_calls": 0,
            "errors": []
        }

    def calculate_fetch_range(self) -> Tuple[int, int]:
        """
        Calculate the timestamp range to fetch based on database state.

        Returns:
            Tuple of (start_timestamp, end_timestamp) in milliseconds
        """
        with db.connection() as conn:
            latest_db_timestamp = get_latest_timestamp(conn)

        # Get current time in milliseconds
        current_time_ms = int(time.time() * 1000)

        if latest_db_timestamp:
            # Resume from last timestamp + 1 minute
            start_timestamp = latest_db_timestamp + 60000
            print(f"Resuming from existing data: {self._format_timestamp(start_timestamp)}")
        else:
            # Start from earliest available (Binance BTCUSDT launch)
            start_timestamp = MIN_TIMESTAMP
            print(f"Starting fresh fetch from: {self._format_timestamp(start_timestamp)}")

        # Fetch up to current time
        end_timestamp = current_time_ms

        return start_timestamp, end_timestamp

    def fetch_historical_data(
        self,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        progress_callback=None
    ) -> dict:
        """
        Fetch historical OHLCV data in batches.

        Args:
            start_timestamp: Start time in milliseconds (auto-calculated if None)
            end_timestamp: End time in milliseconds (auto-calculated if None)
            progress_callback: Optional callback function for progress updates

        Returns:
            Statistics dictionary
        """
        # Calculate fetch range if not provided
        if start_timestamp is None or end_timestamp is None:
            start_timestamp, end_timestamp = self.calculate_fetch_range()

        # Validate range
        if start_timestamp >= end_timestamp:
            print("No new data to fetch. Database is up to date.")
            return self.stats

        # Calculate total batches for progress tracking
        total_minutes = (end_timestamp - start_timestamp) // 60000
        total_batches = (total_minutes // MAX_CANDLES_PER_REQUEST) + 1

        print(f"\nFetch Range:")
        print(f"  Start: {self._format_timestamp(start_timestamp)}")
        print(f"  End:   {self._format_timestamp(end_timestamp)}")
        print(f"  Total minutes: {total_minutes:,}")
        print(f"  Estimated batches: {total_batches:,}")
        print(f"  Estimated time: {total_batches * 0.5 / 60:.1f} minutes\n")

        # Fetch data in batches
        current_start = start_timestamp
        batch_num = 0

        while current_start < end_timestamp:
            batch_num += 1

            try:
                # Fetch batch
                klines = self.client.fetch_klines(
                    start_time=current_start,
                    end_time=end_timestamp,
                    limit=MAX_CANDLES_PER_REQUEST
                )

                self.stats["api_calls"] += 1

                if not klines:
                    print("No more data available from Binance")
                    break

                # Parse and validate
                parsed_records = [parse_binance_kline(k) for k in klines]
                valid_records, validation_errors = validate_ohlcv_batch(parsed_records)

                # Log validation errors
                if validation_errors:
                    self.stats["total_invalid"] += len(validation_errors)
                    for error in validation_errors[:5]:  # Log first 5 errors
                        print(f"  Validation error: {error}")
                    if len(validation_errors) > 5:
                        print(f"  ... and {len(validation_errors) - 5} more errors")

                # Check timestamp continuity (warnings only)
                continuity_warnings = validate_timestamp_continuity(valid_records)
                if continuity_warnings:
                    for warning in continuity_warnings[:3]:  # Log first 3 warnings
                        print(f"  Warning: {warning}")

                # Insert into database
                if valid_records:
                    with db.connection() as conn:
                        inserted = insert_ohlcv_batch(conn, valid_records)

                    self.stats["total_fetched"] += len(valid_records)
                    self.stats["total_inserted"] += inserted
                    self.stats["total_duplicates"] += len(valid_records) - inserted

                # Update progress
                if progress_callback:
                    progress_callback(batch_num, total_batches, valid_records[-1][0] if valid_records else current_start)

                # Move to next batch (start from last timestamp + 1 minute)
                if valid_records:
                    current_start = valid_records[-1][0] + 60000
                else:
                    # If no valid records, skip forward to avoid infinite loop
                    current_start += MAX_CANDLES_PER_REQUEST * 60000

            except BinanceAPIError as e:
                error_msg = f"Batch {batch_num} failed: {str(e)}"
                print(f"  ERROR: {error_msg}")
                self.stats["errors"].append(error_msg)

                # For rate limit errors, wait longer
                if "rate limit" in str(e).lower():
                    print("  Waiting 60 seconds due to rate limit...")
                    time.sleep(60)

                # Continue to next batch
                current_start += MAX_CANDLES_PER_REQUEST * 60000

            except Exception as e:
                error_msg = f"Unexpected error in batch {batch_num}: {str(e)}"
                print(f"  ERROR: {error_msg}")
                self.stats["errors"].append(error_msg)
                break

        # Save metadata
        self._save_metadata(start_timestamp, end_timestamp)

        return self.stats

    def _save_metadata(self, start_timestamp: int, end_timestamp: int):
        """
        Save fetch metadata to database.

        Args:
            start_timestamp: Fetch start time
            end_timestamp: Fetch end time
        """
        status = "success" if not self.stats["errors"] else "partial"

        try:
            with db.connection() as conn:
                insert_fetch_metadata(
                    conn,
                    self.symbol,
                    self.interval,
                    start_timestamp,
                    end_timestamp,
                    self.stats["total_inserted"],
                    status
                )
        except Exception as e:
            print(f"Warning: Failed to save metadata: {e}")

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """
        Format timestamp for display.

        Args:
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Formatted datetime string
        """
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def print_summary(self):
        """Print fetch summary statistics."""
        print("\n" + "=" * 60)
        print("FETCH SUMMARY")
        print("=" * 60)
        print(f"Total records fetched:  {self.stats['total_fetched']:,}")
        print(f"Total records inserted: {self.stats['total_inserted']:,}")
        print(f"Duplicates skipped:     {self.stats['total_duplicates']:,}")
        print(f"Invalid records:        {self.stats['total_invalid']:,}")
        print(f"API calls made:         {self.stats['api_calls']:,}")
        print(f"Errors encountered:     {len(self.stats['errors'])}")

        if self.stats["errors"]:
            print("\nErrors:")
            for error in self.stats["errors"][:10]:
                print(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")

        # Get final database stats
        try:
            with db.connection() as conn:
                total_records = count_records(conn)
            print(f"\nTotal records in database: {total_records:,}")
        except Exception as e:
            print(f"\nWarning: Could not get database stats: {e}")

        print("=" * 60)

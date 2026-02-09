#!/usr/bin/env python3
"""
Automated data update script - fetches latest 1-minute data
Designed to run on a schedule (every 4 hours)
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import db
from database.queries import get_latest_timestamp
from data_fetcher.fetcher import DataFetcher
from utils.logger import setup_logger

logger = setup_logger('update_data')


def update_data():
    """Fetch and insert the latest data since last update"""

    logger.info("=" * 70)
    logger.info("AUTOMATED DATA UPDATE - BITCOIN 1-MINUTE OHLCV")
    logger.info("=" * 70)
    logger.info(f"Update started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Get the latest timestamp in database
        with db.connection() as conn:
            latest_ms = get_latest_timestamp(conn)

        latest_date = datetime.fromtimestamp(latest_ms / 1000)
        logger.info(f"Latest data in database: {latest_date.strftime('%Y-%m-%d %H:%M:%S')}")

        # Get current time
        now_ms = int(datetime.now().timestamp() * 1000)
        now_date = datetime.fromtimestamp(now_ms / 1000)

        # Calculate how much data to fetch
        time_diff_hours = (now_ms - latest_ms) / (1000 * 60 * 60)

        if time_diff_hours < 0.016:  # Less than ~1 minute
            logger.info("Database is already up to date (less than 1 minute behind)")
            logger.info("No update needed.")
            return 0

        logger.info(f"Current time: {now_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Time gap: {time_diff_hours:.2f} hours ({int(time_diff_hours * 60)} minutes)")

        # Fetch the missing data
        # Start from 1 minute after the latest to avoid duplicates
        start_ms = latest_ms + (60 * 1000)

        logger.info(f"Fetching data from {datetime.fromtimestamp(start_ms/1000)} to {now_date}")

        # Initialize fetcher
        fetcher = DataFetcher()

        # Fetch data
        result = fetcher.fetch_historical_data(
            start_timestamp=start_ms,
            end_timestamp=now_ms
        )

        records_added = result.get('records_fetched', 0)

        logger.info(f"Successfully added {records_added} new records")
        logger.info("=" * 70)
        logger.info(f"Update completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"Error during data update: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(update_data())

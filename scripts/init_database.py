#!/usr/bin/env python3
"""
Initialize the database schema.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db
from database.schema import initialize_schema
from utils.logger import logger


def main():
    """Initialize database schema."""
    try:
        logger.info("Initializing database schema...")

        with db.connection() as conn:
            initialize_schema(conn)

        logger.info(f"Database initialized successfully at: {db.db_path}")
        logger.info("Schema created:")
        logger.info("  - ohlcv table (with indexes)")
        logger.info("  - fetch_metadata table")

        return 0

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

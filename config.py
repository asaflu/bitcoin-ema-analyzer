"""
Configuration constants for Bitcoin price database system.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "bitcoin_ohlcv.db"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Binance API Configuration
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_KLINES_ENDPOINT = f"{BINANCE_BASE_URL}/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"

# API Rate Limiting
REQUEST_DELAY_MS = 500  # Conservative 500ms delay between requests
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1  # Base delay in seconds for exponential backoff
MAX_CANDLES_PER_REQUEST = 1000  # Binance API limit

# Database Configuration
BATCH_INSERT_SIZE = 1000  # Number of records per transaction
DB_PRAGMAS = {
    "journal_mode": "WAL",  # Write-Ahead Logging for concurrent reads
    "synchronous": "NORMAL",  # Balance between safety and performance
    "cache_size": -64000,  # 64MB cache
    "temp_store": "MEMORY",  # Use memory for temporary tables
    "mmap_size": 268435456,  # 256MB memory-mapped I/O
}

# Data Validation
MIN_TIMESTAMP = 1502942400000  # August 17, 2017 (Binance launch for BTCUSDT)

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Bitcoin Price Database

A local Bitcoin price database system that fetches and stores 1-minute resolution OHLCV (Open, High, Low, Close, Volume) data from Binance for backtesting trading strategies.

## Features

- **Historical Data**: Fetches up to 8+ years of Bitcoin price data (from August 2017)
- **High Resolution**: 1-minute candles for precise backtesting
- **Optimized Storage**: SQLite with WAL mode and optimized indexes
- **Resume Capability**: Automatically resumes interrupted fetches
- **Data Validation**: Validates OHLCV integrity and detects gaps
- **Rate Limiting**: Respects Binance API limits with exponential backoff retry

## Project Structure

```
roiema/
├── requirements.txt              # Python dependencies
├── config.py                     # Configuration constants
├── database/                     # Database layer
│   ├── schema.py                 # Schema definitions
│   ├── connection.py             # Connection management
│   └── queries.py                # Query functions
├── data_fetcher/                 # Data fetching layer
│   ├── binance_client.py         # Binance API client
│   ├── fetcher.py                # Main fetching orchestration
│   └── validators.py             # Data validation
├── utils/                        # Utilities
│   ├── logger.py                 # Logging configuration
│   └── progress.py               # Progress tracking
├── scripts/                      # Executable scripts
│   ├── init_database.py          # Initialize database
│   ├── fetch_historical_data.py  # Fetch data from Binance
│   └── verify_data.py            # Verify data integrity
└── data/
    └── bitcoin_ohlcv.db          # SQLite database (created on init)
```

## Installation

1. **Clone or navigate to the project directory**

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   python scripts/init_database.py
   ```

## Usage

### Fetch Historical Data

**Note**: Make sure to activate the virtual environment first:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Fetch all available historical data (from August 2017 to present):

```bash
python scripts/fetch_historical_data.py
```

This will:
- Check for existing data and resume from the last timestamp
- Fetch data in batches of 1000 candles
- Display progress with a progress bar
- Take approximately 30-40 minutes for full historical data
- Save progress automatically (Ctrl+C to interrupt safely)

**Custom date range:**

```bash
# Fetch specific time range (timestamps in milliseconds)
python3 scripts/fetch_historical_data.py --start 1609459200000 --end 1612137600000
```

**Options:**
- `--start`: Start timestamp in milliseconds
- `--end`: End timestamp in milliseconds
- `--symbol`: Trading symbol (default: BTCUSDT)
- `--interval`: Candle interval (default: 1m)

### Verify Data

Check database integrity and detect gaps:

```bash
python3 scripts/verify_data.py
```

This provides:
- Total record count and date range
- Data completeness percentage
- Gap detection (missing minutes)
- Database file size
- Query performance metrics

## Database Schema

### `ohlcv` Table

Stores 1-minute OHLCV candles:

| Column | Type | Description |
|--------|------|-------------|
| timestamp | INTEGER | Unix timestamp in milliseconds (primary key) |
| open | REAL | Opening price |
| high | REAL | Highest price |
| low | REAL | Lowest price |
| close | REAL | Closing price |
| volume | REAL | Base asset volume |
| quote_volume | REAL | Quote asset volume |
| trades | INTEGER | Number of trades |
| taker_buy_base | REAL | Taker buy base volume |
| taker_buy_quote | REAL | Taker buy quote volume |

**Indexes:**
- Primary key on `timestamp`
- Composite index on `(timestamp, close)` for fast time-series queries

### `fetch_metadata` Table

Tracks fetching operations for monitoring and debugging.

## Querying the Database

Example queries for backtesting:

```python
from database.connection import db
from database.queries import query_ohlcv_range

# Query 1 day of data
start = 1609459200000  # 2021-01-01 00:00:00
end = start + 86400000  # +1 day

with db.connection() as conn:
    data = query_ohlcv_range(conn, start, end)

for timestamp, open_, high, low, close, volume, *_ in data:
    print(f"{timestamp}: O={open_}, H={high}, L={low}, C={close}, V={volume}")
```

## Configuration

Edit `config.py` to customize:

- **Database path**: `DATABASE_PATH`
- **API settings**: `REQUEST_DELAY_MS`, `MAX_RETRIES`
- **Batch size**: `BATCH_INSERT_SIZE`
- **Database pragmas**: `DB_PRAGMAS`

## Expected Results

After fetching full historical data:
- **Records**: ~2.6-4 million (depending on current date)
- **Coverage**: August 2017 to present
- **Database size**: 200-400 MB
- **Fetch time**: 30-40 minutes

## Data Validation

The system validates:
- OHLCV integrity (high ≥ low, volumes ≥ 0)
- Timestamp chronological order
- No duplicate timestamps
- Data type correctness

## Error Handling

- **Network errors**: Automatic retry with exponential backoff
- **Rate limits**: Adaptive delay adjustment
- **Data validation errors**: Logged and skipped
- **Interruptions**: Progress saved, resume on next run

## Troubleshooting

**Database locked error:**
- Ensure no other process is accessing the database
- WAL mode should prevent most lock issues

**Rate limit errors:**
- The system automatically handles rate limits
- If persistent, increase `REQUEST_DELAY_MS` in `config.py`

**Gaps in data:**
- Some gaps may be due to Binance maintenance periods
- Use `verify_data.py` to identify specific gaps
- Re-run the fetcher to attempt filling gaps

## Future Enhancements

- Multiple cryptocurrencies support
- Multiple timeframes (5m, 15m, 1h, 1d)
- Automated daily updates
- REST API for data access
- Export to CSV/Parquet

## License

MIT License

## Acknowledgments

- Data provided by [Binance](https://www.binance.com) public API
- Built with Python 3.14+

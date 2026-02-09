# Quick Start Guide

## Setup (One-time)

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python scripts/init_database.py
```

## Fetch Historical Data

### Full Historical Fetch (Recommended)

Fetch all available Bitcoin price data from August 2017 to present (~8+ years):

```bash
source venv/bin/activate
python scripts/fetch_historical_data.py
```

**Expected time**: 30-40 minutes
**Expected records**: ~2.6-4 million (depending on current date)
**Database size**: 200-400 MB

The script will:
- Show progress with a progress bar
- Display estimated time remaining
- Save progress automatically (safe to interrupt with Ctrl+C)
- Resume from last timestamp on next run

### Test Fetch (Optional)

Test with a small date range first (2 days):

```bash
source venv/bin/activate
python scripts/fetch_historical_data.py --start 1502942400000 --end 1503115200000
```

This takes ~2 seconds and creates 2,881 records.

## Verify Data

Check database integrity after fetching:

```bash
source venv/bin/activate
python scripts/verify_data.py
```

This will show:
- Total records and date coverage
- Data completeness percentage
- Any gaps in the time series
- Database file size
- Query performance metrics

## Query the Data

Run the example query script:

```bash
source venv/bin/activate
python example_query.py
```

Or query programmatically:

```python
from database.connection import db
from database.queries import query_ohlcv_range

# Query 1 hour of data
start = 1502942400000  # Unix timestamp in milliseconds
end = start + 3600000   # +1 hour

with db.connection() as conn:
    data = query_ohlcv_range(conn, start, end)

for timestamp, open_, high, low, close, volume, *_ in data:
    print(f"{timestamp}: O={open_:.2f}, H={high:.2f}, L={low:.2f}, C={close:.2f}")
```

## Resume Interrupted Fetch

If the fetch is interrupted (Ctrl+C, network issue, etc.), simply run the fetch command again:

```bash
source venv/bin/activate
python scripts/fetch_historical_data.py
```

The system automatically detects the last timestamp in the database and resumes from there.

## Timestamps

All timestamps are in **milliseconds** (Unix epoch format).

Convert human date to timestamp:

```python
from datetime import datetime

dt = datetime(2021, 1, 1, 0, 0, 0)
timestamp_ms = int(dt.timestamp() * 1000)
print(timestamp_ms)  # 1609459200000
```

Convert timestamp to human date:

```python
from datetime import datetime

timestamp_ms = 1609459200000
dt = datetime.fromtimestamp(timestamp_ms / 1000)
print(dt.strftime("%Y-%m-%d %H:%M:%S"))  # 2021-01-01 00:00:00
```

## Common Commands

```bash
# Activate virtual environment (always do this first)
source venv/bin/activate

# Fetch full historical data
python scripts/fetch_historical_data.py

# Verify data integrity
python scripts/verify_data.py

# Query example
python example_query.py

# Deactivate virtual environment when done
deactivate
```

## Troubleshooting

**"Database not found" error:**
- Run `python scripts/init_database.py` first

**"Module not found" error:**
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Rate limit errors:**
- The system handles this automatically with retry logic
- If persistent, increase the delay in `config.py`

**Database locked:**
- Ensure only one fetch process is running
- WAL mode should prevent most lock issues

## Next Steps

After fetching data:

1. **Develop trading indicators**: Use the OHLCV data to create and backtest indicators
2. **Query patterns**: Explore different query patterns for your backtesting needs
3. **Daily updates**: Consider setting up a daily fetch to keep data current

See `README.md` for detailed documentation.
